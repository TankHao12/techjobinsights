"""
TechInsights  - Data Processing Service
Advanced data processing, validation, and quality management
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import logging

from src.repositories import (
    JobRepository,
    CompanyRepository,
    TechStackRepository,
    JobTechRequirementRepository,
    DataSourceRepository
)
from src.models.job import Job
from src.models.company import Company
from src.models.job_tech_requirement import JobTechRequirement
from src.utils.text_processing import normalize_company_name, clean_html

logger = logging.getLogger(__name__)


class DataProcessingService:
    """
    Service for advanced data processing, validation, and quality management.
    
    Handles:
    - Data cleaning and normalization
    - Duplicate detection and management
    - Data quality scoring
    - Company profile enrichment
    - Technology trend analysis
    """
    
    def __init__(self, db: Session):
        """
        Initialize the data processing service.
        
        Args:
            db: Database session
        """
        self.db = db
        
        # Initialize repositories
        self.job_repo = JobRepository(db)
        self.company_repo = CompanyRepository(db)
        self.tech_stack_repo = TechStackRepository(db)
        self.job_tech_req_repo = JobTechRequirementRepository(db)
        self.data_source_repo = DataSourceRepository(db)
    
    def process_duplicate_detection(
        self,
        similarity_threshold: float = 0.8,
        time_window_days: int = 30
    ) -> Dict[str, Any]:
        """
        Detect and mark duplicate job postings.
        
        Args:
            similarity_threshold: Similarity threshold for duplicate detection
            time_window_days: Time window to check for duplicates
            
        Returns:
            Dict[str, Any]: Processing results
        """
        logger.info("Starting duplicate detection process")
        
        results = {
            'duplicates_found': 0,
            'jobs_processed': 0,
            'duplicates_marked': 0,
            'errors': []
        }
        
        try:
            # Get recent active jobs
            cutoff_date = datetime.now() - timedelta(days=time_window_days)
            recent_jobs = self.job_repo.get_multi(
                filters={
                    'is_active': True,
                    'is_duplicate': False
                },
                limit=10000  # Process in batches for large datasets
            )
            
            results['jobs_processed'] = len(recent_jobs)
            
            # Group jobs by company for more efficient processing
            jobs_by_company = {}
            for job in recent_jobs:
                company_id = job.company_id or 'unknown'
                if company_id not in jobs_by_company:
                    jobs_by_company[company_id] = []
                jobs_by_company[company_id].append(job)
            
            # Detect duplicates within each company
            for company_id, company_jobs in jobs_by_company.items():
                if len(company_jobs) < 2:
                    continue
                
                duplicates = self._find_duplicate_jobs(
                    company_jobs, similarity_threshold
                )
                
                # Mark duplicates
                for original_job, duplicate_jobs in duplicates.items():
                    for duplicate_job in duplicate_jobs:
                        try:
                            self.job_repo.update(duplicate_job.job_id, {
                                'is_duplicate': True,
                                'duplicate_of': original_job.job_id,
                                'is_active': False
                            })
                            results['duplicates_marked'] += 1
                        except Exception as e:
                            results['errors'].append(f"Error marking duplicate {duplicate_job.job_id}: {e}")
                
                results['duplicates_found'] += sum(len(dups) for dups in duplicates.values())
            
            logger.info(f"Duplicate detection completed: {results['duplicates_found']} duplicates found")
            return results
            
        except Exception as e:
            logger.error(f"Error in duplicate detection: {e}")
            results['errors'].append(str(e))
            return results
    
    def _find_duplicate_jobs(
        self,
        jobs: List[Job],
        similarity_threshold: float
    ) -> Dict[Job, List[Job]]:
        """
        Find duplicate jobs within a list.
        
        Args:
            jobs: List of jobs to check
            similarity_threshold: Similarity threshold
            
        Returns:
            Dict[Job, List[Job]]: Original jobs mapped to their duplicates
        """
        duplicates = {}
        processed_jobs = set()
        
        for i, job1 in enumerate(jobs):
            if job1.job_id in processed_jobs:
                continue
            
            job_duplicates = []
            
            for j, job2 in enumerate(jobs[i+1:], i+1):
                if job2.job_id in processed_jobs:
                    continue
                
                similarity = self._calculate_job_similarity(job1, job2)
                
                if similarity >= similarity_threshold:
                    job_duplicates.append(job2)
                    processed_jobs.add(job2.job_id)
            
            if job_duplicates:
                duplicates[job1] = job_duplicates
                processed_jobs.add(job1.job_id)
        
        return duplicates
    
    def _calculate_job_similarity(self, job1: Job, job2: Job) -> float:
        """
        Calculate similarity between two jobs.
        
        Args:
            job1: First job
            job2: Second job
            
        Returns:
            float: Similarity score (0.0-1.0)
        """
        similarity_score = 0.0
        total_weight = 0.0
        
        # Title similarity (weight: 0.4)
        if job1.title and job2.title:
            title_similarity = self._calculate_text_similarity(
                job1.title.lower(), job2.title.lower()
            )
            similarity_score += title_similarity * 0.4
            total_weight += 0.4
        
        # Company similarity (weight: 0.3)
        if job1.company_id == job2.company_id and job1.company_id is not None:
            similarity_score += 0.3
            total_weight += 0.3
        elif job1.company_id != job2.company_id:
            total_weight += 0.3  # No similarity for different companies
        
        # Location similarity (weight: 0.2)
        if job1.location and job2.location:
            location_similarity = self._calculate_text_similarity(
                job1.location.lower(), job2.location.lower()
            )
            similarity_score += location_similarity * 0.2
            total_weight += 0.2
        
        # Posted date proximity (weight: 0.1)
        if job1.posted_date and job2.posted_date:
            date_diff = abs((job1.posted_date - job2.posted_date).days)
            if date_diff <= 7:  # Posted within a week
                date_similarity = max(0, 1 - (date_diff / 7))
                similarity_score += date_similarity * 0.1
            total_weight += 0.1
        
        # Normalize score
        if total_weight > 0:
            return similarity_score / total_weight
        
        return 0.0
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity using simple token-based approach.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            float: Similarity score (0.0-1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # Simple token-based similarity
        tokens1 = set(text1.split())
        tokens2 = set(text2.split())
        
        if not tokens1 and not tokens2:
            return 1.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        if not union:
            return 0.0
        
        # Jaccard similarity
        return len(intersection) / len(union)
    
    def enrich_company_profiles(self) -> Dict[str, Any]:
        """
        Enrich company profiles with additional information.
        
        Returns:
            Dict[str, Any]: Processing results
        """
        logger.info("Starting company profile enrichment")
        
        results = {
            'companies_processed': 0,
            'companies_enriched': 0,
            'errors': []
        }
        
        try:
            # Get companies with limited information
            companies = self.company_repo.get_multi(limit=1000)
            results['companies_processed'] = len(companies)
            
            for company in companies:
                try:
                    enriched = self._enrich_single_company(company)
                    if enriched:
                        results['companies_enriched'] += 1
                        
                except Exception as e:
                    results['errors'].append(f"Error enriching company {company.company_id}: {e}")
            
            logger.info(f"Company enrichment completed: {results['companies_enriched']} companies enriched")
            return results
            
        except Exception as e:
            logger.error(f"Error in company enrichment: {e}")
            results['errors'].append(str(e))
            return results
    
    def _enrich_single_company(self, company: Company) -> bool:
        """
        Enrich a single company profile.
        
        Args:
            company: Company to enrich
            
        Returns:
            bool: True if company was enriched
        """
        enrichment_data = {}
        enriched = False
        
        # Calculate job posting statistics
        job_stats = self._calculate_company_job_stats(company.company_id)
        if job_stats:
            enrichment_data.update(job_stats)
            enriched = True
        
        # Normalize company name if not already done
        if not company.normalized_name and company.company_name:
            enrichment_data['normalized_name'] = normalize_company_name(company.company_name)
            enriched = True
        
        # Update company if we have enrichment data
        if enriched and enrichment_data:
            self.company_repo.update(company.company_id, enrichment_data)
        
        return enriched
    
    def _calculate_company_job_stats(self, company_id: int) -> Dict[str, Any]:
        """
        Calculate job posting statistics for a company.
        
        Args:
            company_id: Company ID
            
        Returns:
            Dict[str, Any]: Job statistics
        """
        try:
            # Count total jobs posted by company
            total_jobs = self.job_repo.count({'company_id': company_id, 'is_active': True})
            
            stats = {
                'total_jobs_posted': total_jobs
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating company job stats for {company_id}: {e}")
            return {}
    
    def update_technology_popularity_scores(self) -> Dict[str, Any]:
        """
        Update popularity scores for all technologies based on job mentions.
        
        Returns:
            Dict[str, Any]: Update results
        """
        logger.info("Starting technology popularity score update")
        
        results = {
            'technologies_processed': 0,
            'technologies_updated': 0,
            'errors': []
        }
        
        try:
            # Get all technologies
            technologies = self.tech_stack_repo.get_multi(limit=10000)
            results['technologies_processed'] = len(technologies)
            
            # Calculate total number of active jobs for normalization
            total_active_jobs = self.job_repo.count({'is_active': True})
            
            if total_active_jobs == 0:
                logger.warning("No active jobs found for popularity calculation")
                return results
            
            for tech in technologies:
                try:
                    # Count job mentions for this technology
                    job_mentions = self.job_tech_req_repo.count({'tech_id': tech.tech_id})
                    
                    # Calculate popularity score (percentage of jobs mentioning this tech)
                    popularity_score = (job_mentions / total_active_jobs) * 100
                    
                    # Update technology record
                    self.tech_stack_repo.update(tech.tech_id, {
                        'job_mentions_count': job_mentions,
                        'popularity_score': min(100.0, popularity_score),  # Cap at 100%
                        'last_updated_stats': datetime.now()
                    })
                    
                    results['technologies_updated'] += 1
                    
                except Exception as e:
                    results['errors'].append(f"Error updating tech {tech.tech_id}: {e}")
            
            logger.info(f"Technology popularity update completed: {results['technologies_updated']} technologies updated")
            return results
            
        except Exception as e:
            logger.error(f"Error updating technology popularity scores: {e}")
            results['errors'].append(str(e))
            return results
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """
        Clean up old inactive job postings.
        
        Args:
            days_to_keep: Number of days to keep inactive jobs
            
        Returns:
            Dict[str, Any]: Cleanup results
        """
        logger.info(f"Starting cleanup of data older than {days_to_keep} days")
        
        results = {
            'jobs_cleaned': 0,
            'errors': []
        }
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Mark old inactive jobs for archival
            old_jobs = self.job_repo.get_multi(
                filters={
                    'is_active': False,
                    ('posted_date', '<=', cutoff_date)
                },
                limit=10000
            )
            
            for job in old_jobs:
                try:
                    # Update to archived status instead of deleting
                    self.job_repo.update(job.job_id, {
                        'processing_status': 'archived'
                    })
                    results['jobs_cleaned'] += 1
                    
                except Exception as e:
                    results['errors'].append(f"Error archiving job {job.job_id}: {e}")
            
            logger.info(f"Data cleanup completed: {results['jobs_cleaned']} jobs archived")
            return results
            
        except Exception as e:
            logger.error(f"Error in data cleanup: {e}")
            results['errors'].append(str(e))
            return results
    
    def validate_data_quality(self) -> Dict[str, Any]:
        """
        Validate overall data quality and generate report.
        
        Returns:
            Dict[str, Any]: Data quality report
        """
        logger.info("Starting data quality validation")
        
        try:
            report = {
                'total_jobs': 0,
                'active_jobs': 0,
                'jobs_with_descriptions': 0,
                'jobs_with_companies': 0,
                'jobs_with_salaries': 0,
                'jobs_with_tech_requirements': 0,
                'average_quality_score': 0.0,
                'quality_distribution': {},
                'source_quality': {},
                'recommendations': []
            }
            
            # Get basic counts
            report['total_jobs'] = self.job_repo.count()
            report['active_jobs'] = self.job_repo.count({'is_active': True})
            report['jobs_with_descriptions'] = self.job_repo.count({'description_cleaned': ('!=', None)})
            report['jobs_with_companies'] = self.job_repo.count({'company_id': ('!=', None)})
            
            # Calculate quality metrics
            jobs_with_quality_scores = self.db.query(Job).filter(
                Job.data_quality_score.isnot(None)
            ).all()
            
            if jobs_with_quality_scores:
                total_score = sum(job.data_quality_score for job in jobs_with_quality_scores)
                report['average_quality_score'] = total_score / len(jobs_with_quality_scores)
            
            # Generate recommendations based on quality issues
            if report['active_jobs'] > 0:
                description_coverage = report['jobs_with_descriptions'] / report['active_jobs']
                company_coverage = report['jobs_with_companies'] / report['active_jobs']
                
                if description_coverage < 0.8:
                    report['recommendations'].append(
                        "Low description coverage - consider improving scraping to capture more job descriptions"
                    )
                
                if company_coverage < 0.9:
                    report['recommendations'].append(
                        "Low company coverage - improve company extraction and matching"
                    )
                
                if report['average_quality_score'] < 0.7:
                    report['recommendations'].append(
                        "Low overall quality score - review data collection and processing pipeline"
                    )
            
            logger.info("Data quality validation completed")
            return report
            
        except Exception as e:
            logger.error(f"Error in data quality validation: {e}")
            return {'error': str(e)}

