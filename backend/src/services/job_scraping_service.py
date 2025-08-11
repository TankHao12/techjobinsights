"""
TechInsights  - Job Scraping Service
Orchestrates job scraping from multiple sources and data storage
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from src.scrapers import ScraperFactory, ScrapingResult
from src.repositories import (
    DataSourceRepository,
    CompanyRepository,
    JobRepository,
    TechStackRepository,
    JobTechRequirementRepository
)
from src.models.data_source import DataSource
from src.models.job import Job
from src.utils.tech_detection import TechStackDetector
from src.services.data_processing_service import DataProcessingService
from src.core.database import db_session

logger = logging.getLogger(__name__)


class JobScrapingService:
    """
    Service for orchestrating job scraping from multiple sources.
    
    Handles:
    - Scraper initialization and management
    - Data collection from multiple sources
    - Data processing and storage
    - Error handling and monitoring
    - Progress tracking and reporting
    """
    
    def __init__(self, db: Session):
        """
        Initialize the job scraping service.
        
        Args:
            db: Database session
        """
        self.db = db
        
        # Initialize repositories
        self.data_source_repo = DataSourceRepository(db)
        self.company_repo = CompanyRepository(db)
        self.job_repo = JobRepository(db)
        self.tech_stack_repo = TechStackRepository(db)
        self.job_tech_req_repo = JobTechRequirementRepository(db)
        
        # Initialize processing service
        self.data_processor = DataProcessingService(db)
        
        # Initialize tech detector
        self.tech_detector = TechStackDetector()
    
    async def scrape_all_sources(
        self,
        max_pages_per_source: int = 10,
        include_job_details: bool = True,
        process_tech_requirements: bool = True
    ) -> Dict[str, ScrapingResult]:
        """
        Scrape jobs from all active sources.
        
        Args:
            max_pages_per_source: Maximum pages to scrape per source
            include_job_details: Whether to fetch detailed job information
            process_tech_requirements: Whether to process tech requirements
            
        Returns:
            Dict[str, ScrapingResult]: Results keyed by source name
        """
        logger.info("Starting job scraping from all active sources")
        
        # Get active data sources
        active_sources = self.data_source_repo.get_active_sources()
        
        if not active_sources:
            logger.warning("No active data sources found")
            return {}
        
        results = {}
        
        # Create scrapers for active sources
        try:
            scrapers = ScraperFactory.create_all_active_scrapers()
        except Exception as e:
            logger.error(f"Failed to create scrapers: {e}")
            return {}
        
        # Scrape from each source
        for source in active_sources:
            source_name = source.source_name
            
            if source_name not in scrapers:
                logger.warning(f"No scraper available for source: {source_name}")
                continue
            
            try:
                logger.info(f"Starting scraping from {source_name}")
                
                # Update source as being scraped
                self.data_source_repo.update_last_scraped(source.source_id)
                
                # Perform scraping
                result = await self.scrape_source(
                    source_name=source_name,
                    max_pages=max_pages_per_source,
                    include_job_details=include_job_details,
                    process_tech_requirements=process_tech_requirements
                )
                
                results[source_name] = result
                
                # Update source statistics
                self.data_source_repo.update_statistics(
                    source_id=source.source_id,
                    jobs_collected=result.jobs_created + result.jobs_updated,
                    success_count=result.jobs_processed,
                    total_attempts=result.jobs_found
                )
                
                logger.info(
                    f"Completed scraping from {source_name}: "
                    f"{result.jobs_processed}/{result.jobs_found} jobs processed"
                )
                
            except Exception as e:
                logger.error(f"Error scraping from {source_name}: {e}")
                results[source_name] = ScrapingResult(
                    success=False,
                    errors=[str(e)]
                )
        
        logger.info(f"Completed scraping from {len(results)} sources")
        return results
    
    async def scrape_source(
        self,
        source_name: str,
        max_pages: int = 10,
        keywords: Optional[str] = None,
        location: Optional[str] = None,
        include_job_details: bool = True,
        process_tech_requirements: bool = True
    ) -> ScrapingResult:
        """
        Scrape jobs from a specific source.
        
        Args:
            source_name: Name of the source to scrape
            max_pages: Maximum number of pages to scrape
            keywords: Search keywords
            location: Location filter
            include_job_details: Whether to fetch detailed job information
            process_tech_requirements: Whether to process tech requirements
            
        Returns:
            ScrapingResult: Scraping results and metadata
        """
        result = ScrapingResult(success=False)
        
        try:
            # Get data source record
            data_source = self.data_source_repo.get_by_name(source_name)
            if not data_source:
                result.add_error(f"Data source '{source_name}' not found")
                return result
            
            # Create scraper
            scraper = ScraperFactory.create_scraper(source_name)
            
            # Perform scraping
            async with scraper:
                scraping_result = await scraper.scrape_jobs(
                    max_pages=max_pages,
                    keywords=keywords,
                    location=location,
                    include_job_details=include_job_details
                )
            
            if not scraping_result.success:
                result.errors = scraping_result.errors
                result.warnings = scraping_result.warnings
                return result
            
            # Process and store the scraped data
            jobs_data = scraping_result.metadata.get('jobs_data', [])
            
            for job_data in jobs_data:
                try:
                    # Set source ID
                    job_data['source_id'] = data_source.source_id
                    
                    # Process and store job
                    stored_job = await self._process_and_store_job(
                        job_data, 
                        process_tech_requirements
                    )
                    
                    if stored_job:
                        if hasattr(stored_job, '_sa_instance_state') and stored_job._sa_instance_state.persistent:
                            result.jobs_updated += 1
                        else:
                            result.jobs_created += 1
                    
                except Exception as e:
                    result.jobs_failed += 1
                    result.add_error(f"Error processing job {job_data.get('external_job_id', 'unknown')}: {e}")
            
            # Update result metrics
            result.jobs_found = scraping_result.jobs_found
            result.jobs_processed = result.jobs_created + result.jobs_updated
            result.success = result.jobs_processed > 0
            result.processing_time = scraping_result.processing_time
            result.metadata = scraping_result.metadata
            
            return result
            
        except Exception as e:
            result.add_error(f"Fatal error scraping {source_name}: {e}")
            return result
    
    async def _process_and_store_job(
        self,
        job_data: Dict[str, Any],
        process_tech_requirements: bool = True
    ) -> Optional[Job]:
        """
        Process and store a single job.
        
        Args:
            job_data: Raw job data from scraper
            process_tech_requirements: Whether to process tech requirements
            
        Returns:
            Optional[Job]: Stored job record or None if failed
        """
        try:
            # Find or create company
            company = None
            if job_data.get('company_name'):
                company_data = {
                    'company_name': job_data['company_name'],
                    'website_url': job_data.get('company_url'),
                    'location': job_data.get('location')
                }
                company = self.company_repo.find_or_create_company(company_data)
                job_data['company_id'] = company.company_id
            
            # Check if job already exists
            existing_job = self.job_repo.get_by_field(
                'external_job_id', 
                job_data['external_job_id']
            )
            
            if existing_job:
                # Update existing job
                update_data = self._prepare_job_update_data(job_data)
                job = self.job_repo.update(existing_job.job_id, update_data)
            else:
                # Create new job
                job_data = self._prepare_job_data(job_data)
                job = self.job_repo.create(job_data)
            
            if not job:
                return None
            
            # Process technology requirements
            if process_tech_requirements and job_data.get('description_cleaned'):
                await self._process_tech_requirements(job)
            
            # Calculate and update data quality score
            self._calculate_data_quality_score(job)
            
            return job
            
        except Exception as e:
            logger.error(f"Error processing job: {e}")
            return None
    
    async def _process_tech_requirements(self, job: Job) -> None:
        """
        Process and store technology requirements for a job.
        
        Args:
            job: Job record to process
        """
        try:
            if not job.description_cleaned:
                return
            
            # Get available technologies
            available_techs = self.tech_stack_repo.get_multi(limit=1000)
            tech_data = [
                {
                    'tech_id': tech.tech_id,
                    'technology_name': tech.technology_name,
                    'normalized_name': tech.normalized_name,
                    'aliases': tech.aliases
                }
                for tech in available_techs
            ]
            
            # Detect technologies
            detection_result = self.tech_detector.detect_technologies(
                job_description=job.description_cleaned,
                available_techs=tech_data,
                confidence_threshold=0.4
            )
            
            # Store detected tech requirements
            for match in detection_result.matches:
                requirement_data = {
                    'requirement_type': match.requirement_type,
                    'confidence_score': match.confidence,
                    'years_experience': match.years_experience,
                    'proficiency_level': match.proficiency_level,
                    'context_snippet': match.context[:500],  # Limit context length
                    'position_in_description': match.position,
                    'detection_method': 'ml_hybrid',
                    'detection_confidence': match.confidence
                }
                
                self.job_tech_req_repo.create_or_update_requirement(
                    job_id=job.job_id,
                    tech_id=match.tech_id,
                    requirement_data=requirement_data
                )
            
            # Update job tech counts
            self.job_repo.update(job.job_id, {
                'required_tech_count': len([m for m in detection_result.matches if m.requirement_type == 'required']),
                'preferred_tech_count': len([m for m in detection_result.matches if m.requirement_type in ['preferred', 'nice-to-have']])
            })
            
            logger.debug(f"Processed {len(detection_result.matches)} tech requirements for job {job.job_id}")
            
        except Exception as e:
            logger.error(f"Error processing tech requirements for job {job.job_id}: {e}")
    
    def _prepare_job_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare job data for database insertion."""
        # Remove any None values and prepare for storage
        prepared_data = {}
        
        for key, value in job_data.items():
            if value is not None:
                prepared_data[key] = value
        
        # Set collection timestamp
        prepared_data['collected_at'] = datetime.now()
        prepared_data['last_updated'] = datetime.now()
        prepared_data['processing_status'] = 'pending'
        
        # Clean text fields
        if 'description_cleaned' in prepared_data:
            from src.utils.text_processing import clean_html
            prepared_data['description_cleaned'] = clean_html(prepared_data['description_cleaned'])
        
        # Calculate word count
        if 'description_cleaned' in prepared_data:
            prepared_data['word_count'] = len(prepared_data['description_cleaned'].split())
        
        return prepared_data
    
    def _prepare_job_update_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare job data for updating existing record."""
        # Only update specific fields
        update_fields = [
            'title', 'description_raw', 'description_cleaned', 'summary',
            'location', 'city', 'salary_min', 'salary_max', 'posted_date',
            'expires_date', 'job_url', 'application_url', 'is_active',
            'last_seen_date', 'raw_data'
        ]
        
        update_data = {}
        for field in update_fields:
            if field in job_data and job_data[field] is not None:
                update_data[field] = job_data[field]
        
        update_data['last_updated'] = datetime.now()
        update_data['last_seen_date'] = datetime.now()
        
        return update_data
    
    def _calculate_data_quality_score(self, job: Job) -> None:
        """Calculate and update data quality score for a job."""
        try:
            score = 0.0
            total_weight = 0.0
            
            # Title (weight: 0.2)
            if job.title and len(job.title.strip()) > 3:
                score += 0.2
            total_weight += 0.2
            
            # Description (weight: 0.3)
            if job.description_cleaned and len(job.description_cleaned.strip()) > 100:
                score += 0.3
            total_weight += 0.3
            
            # Company (weight: 0.15)
            if job.company_id:
                score += 0.15
            total_weight += 0.15
            
            # Location (weight: 0.1)
            if job.location and len(job.location.strip()) > 0:
                score += 0.1
            total_weight += 0.1
            
            # Salary (weight: 0.1)
            if job.salary_min or job.salary_max:
                score += 0.1
            total_weight += 0.1
            
            # Posted date (weight: 0.1)
            if job.posted_date:
                score += 0.1
            total_weight += 0.1
            
            # Job URL (weight: 0.05)
            if job.job_url:
                score += 0.05
            total_weight += 0.05
            
            # Normalize score
            if total_weight > 0:
                final_score = score / total_weight
            else:
                final_score = 0.0
            
            # Update job record
            self.job_repo.update(job.job_id, {
                'data_quality_score': final_score,
                'processing_status': 'processed'
            })
            
        except Exception as e:
            logger.error(f"Error calculating data quality score for job {job.job_id}: {e}")
    
    def get_scraping_statistics(self) -> Dict[str, Any]:
        """
        Get overall scraping statistics.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        try:
            stats = {}
            
            # Get data source statistics
            sources = self.data_source_repo.get_active_sources()
            for source in sources:
                source_stats = {
                    'total_jobs_collected': source.total_jobs_collected,
                    'success_rate': float(source.success_rate or 0),
                    'last_scraped_at': source.last_scraped_at,
                    'is_healthy': source.is_healthy
                }
                stats[source.source_name] = source_stats
            
            # Get overall job counts
            total_jobs = self.job_repo.count({'is_active': True})
            total_companies = self.company_repo.count()
            total_tech_stacks = self.tech_stack_repo.count()
            
            stats['totals'] = {
                'jobs': total_jobs,
                'companies': total_companies,
                'tech_stacks': total_tech_stacks
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting scraping statistics: {e}")
            return {}

