"""
Complete Data Processing Pipeline for Tech Jobs Insights NZ
Transforms raw scraped job data into structured insights using NLP
"""

import os
import sys
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import text

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ..core.logging import get_logger
from ..database import SessionLocal
from ..models.tables import RawJob, Job, Company, Location, Category
from .nlp_engine import NLPEngine
from .url_checker import URLChecker

logger = get_logger(__name__)

@dataclass
class ProcessingStats:
    """Statistics for a processing run"""
    total_jobs: int = 0
    processed_jobs: int = 0
    tech_jobs_found: int = 0
    jobs_with_salary: int = 0
    jobs_with_skills: int = 0
    # URL checking statistics
    urls_checked: int = 0
    urls_accessible: int = 0
    urls_inaccessible: int = 0
    url_check_errors: int = 0
    avg_processing_time: float = 0.0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class DataProcessingPipeline:
    """Complete data processing pipeline for job insights extraction"""

    def __init__(self, enable_url_checking: bool = False):
        self.nlp_engine = NLPEngine()
        self.processing_version = "v2.4.0-comprehensive-skill-fixes"  # Fixed R, Scala, Rust, SQL, Go false positives

        # Processing configuration
        self.batch_size = 50  # Process jobs in batches
        self.min_tech_confidence = 0.25  # Minimum confidence for detailed processing (lowered to reduce false negatives)
        
        # URL checking configuration (disabled by default - redundant for newly scraped data)
        self.enable_url_checking = enable_url_checking
        self.url_check_timeout = 10  # seconds
        self.url_check_max_retries = 2
        
        # Initialize URL checker if enabled (mainly for testing or special cases)
        self.url_checker = URLChecker(
            timeout=self.url_check_timeout,
            max_retries=self.url_check_max_retries
        ) if enable_url_checking else None

        logger.info("Data Processing Pipeline initialized")
        logger.info(f"NLP Engine: {'spaCy Available' if hasattr(self.nlp_engine, 'nlp') and self.nlp_engine.nlp else 'spaCy Not Available'}")
        logger.info(f"Processing Version: {self.processing_version}")
        
        if self.enable_url_checking:
            logger.info("⚠️  URL Checking: ENABLED (Note: May be redundant for newly scraped data)")
        else:
            logger.info("✅ URL Checking: DISABLED (Recommended - newly scraped URLs are already accessible)")
            logger.info("💡 Use 'python scripts/check_existing_job_urls.py' to check older job URLs")

    def process_unprocessed_jobs(self, batch_size: Optional[int] = None) -> ProcessingStats:
        """Process unprocessed raw jobs (optionally limited to batch_size)"""

        db = SessionLocal()
        stats = ProcessingStats()

        try:
            # Get unprocessed raw jobs (including NULL values)
            query = db.query(RawJob).filter(
                (RawJob.processed == False) | (RawJob.processed == None)
            )
            if batch_size:
                query = query.limit(batch_size)
            unprocessed_jobs = query.all()

            stats.total_jobs = len(unprocessed_jobs)
            logger.info(f"Found {stats.total_jobs} unprocessed jobs")

            if stats.total_jobs == 0:
                logger.info("No unprocessed jobs found")
                return stats

            # Process jobs in batches
            total_processing_time = 0.0

            for i in range(0, len(unprocessed_jobs), self.batch_size):
                batch = unprocessed_jobs[i:i + self.batch_size]
                batch_stats = self._process_batch(db, batch)

                # Accumulate statistics
                stats.processed_jobs += batch_stats.processed_jobs
                stats.tech_jobs_found += batch_stats.tech_jobs_found
                stats.jobs_with_salary += batch_stats.jobs_with_salary
                stats.jobs_with_skills += batch_stats.jobs_with_skills
                total_processing_time += batch_stats.avg_processing_time * len(batch)
                stats.errors.extend(batch_stats.errors)

                logger.info(f"Processed batch {i//self.batch_size + 1}/{(len(unprocessed_jobs) + self.batch_size - 1)//self.batch_size}")

            stats.avg_processing_time = total_processing_time / stats.total_jobs if stats.total_jobs > 0 else 0.0

            # Commit all changes
            db.commit()

            logger.info(f"Processing complete:")
            logger.info(f"Total jobs: {stats.total_jobs}")
            logger.info(f"Processed: {stats.processed_jobs}")
            logger.info(f"Tech jobs: {stats.tech_jobs_found}")
            logger.info(f"With salary: {stats.jobs_with_salary}")
            logger.info(f"With skills: {stats.jobs_with_skills}")
            logger.info(f"Avg time/job: {stats.avg_processing_time:.2f}s")
            logger.info(f"Errors: {len(stats.errors)}")

        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}")
            db.rollback()
            raise
        finally:
            db.close()
            # Clean up URL checker
            if self.url_checker:
                self.url_checker.close()

        return stats

    def _process_batch(self, db: Session, batch: List[RawJob]) -> ProcessingStats:
        """Process a batch of raw jobs"""

        batch_stats = ProcessingStats()
        start_time = time.time()

        for raw_job in batch:
            try:
                # Process individual job
                processed_job = self._process_single_job(raw_job)

                if processed_job:
                    # Insert processed job into database
                    self._insert_processed_job(db, processed_job, raw_job)

                    # Update statistics
                    batch_stats.processed_jobs += 1
                    if processed_job['is_tech_job']:
                        batch_stats.tech_jobs_found += 1
                    if processed_job['salary_min'] is not None:
                        batch_stats.jobs_with_salary += 1
                    if processed_job['extracted_skills']:
                        batch_stats.jobs_with_skills += 1
                    
                    # URL checking statistics
                    if self.enable_url_checking and 'url_check_status' in processed_job:
                        batch_stats.urls_checked += 1
                        if processed_job['is_active']:
                            batch_stats.urls_accessible += 1
                        else:
                            batch_stats.urls_inaccessible += 1

                    # Mark raw job as processed
                    raw_job.processed = True
                    raw_job.processed_at = datetime.now()
                    raw_job.processing_version = self.processing_version

            except Exception as e:
                error_msg = f"Error processing job {raw_job.id}: {str(e)}"
                logger.warning(error_msg)
                logger.debug(f"Full error details for job {raw_job.id}:", exc_info=True)
                batch_stats.errors.append(error_msg)
                
                # CRITICAL: Rollback the transaction to recover from error state
                db.rollback()

                # Still mark as processed to avoid reprocessing
                try:
                    raw_job.processed = True
                    raw_job.processed_at = datetime.now()
                    raw_job.processing_version = f"{self.processing_version}-error"
                    db.commit()
                except Exception as commit_error:
                    logger.error(f"Failed to mark job {raw_job.id} as processed: {commit_error}")
                    db.rollback()

        batch_processing_time = time.time() - start_time
        batch_stats.avg_processing_time = batch_processing_time / len(batch)

        return batch_stats

    def _process_single_job(self, raw_job: RawJob) -> Optional[Dict[str, Any]]:
        """
        Process a single raw job using NLP
        
        Changes in simplified version:
        - Posted date passed directly from raw_jobs (no NLP parsing)
        - Removed skill categorization (required vs preferred)
        - Removed remote_friendly calculation (derived from work_arrangement)
        - Returns enum values for employment_type, experience_level, work_arrangement
        - Extracts location using NLP from raw_job.location or description
        """

        if not raw_job.full_description:
            logger.warning(f"Job {raw_job.id} has no description, skipping")
            return None

        try:
            # Extract all information using NLP
            job_data = {
                'raw_job_id': raw_job.id,
                'title': raw_job.title,
                'description': raw_job.full_description,
                'original_url': raw_job.url,
                'found_via_search_term': raw_job.search_term,
                'scraped_at': raw_job.scraped_at,
                'processing_version': self.processing_version,
                'processed_at': datetime.now(),
                'is_active': True  # Default to active, will be updated by URL check
            }

            # Parse posted_date from raw_jobs using scraped_at as reference
            if raw_job.posting_date:
                # Use scraped_at as reference date for accurate historical parsing
                reference_date = raw_job.scraped_at.date() if raw_job.scraped_at else None
                parsed_date = self.nlp_engine.parse_posted_date(
                    raw_job.posting_date,
                    reference_date=reference_date
                )
                job_data['posted_date'] = parsed_date

            # 1. Tech Job Classification
            is_tech, tech_confidence = self.nlp_engine.is_tech_job(
                raw_job.title, raw_job.full_description
            )
            job_data['is_tech_job'] = is_tech
            job_data['tech_confidence_score'] = round(tech_confidence, 2)

            # Initialize all fields with default values (for non-tech jobs)
            job_data['extracted_skills'] = {}
            job_data['salary_min'] = None
            job_data['salary_max'] = None
            job_data['salary_currency'] = 'NZD'
            job_data['salary_period'] = None
            job_data['salary_raw_text'] = None
            job_data['salary_confidence_score'] = 0.0
            job_data['employment_type'] = None
            job_data['experience_level'] = None
            job_data['work_arrangement'] = None
            job_data['location_info'] = None

            # Only process further if it's likely a tech job
            if tech_confidence < self.min_tech_confidence:
                logger.debug(f"Job {raw_job.id} has low tech confidence ({tech_confidence:.2f}), skipping detailed processing")
                return job_data

            # 2. Location Extraction (NLP-based)
            location_info = self.nlp_engine.extract_location(
                location_text=raw_job.location,
                description=raw_job.full_description
            )
            job_data['location_info'] = location_info  # Store for use in _insert_processed_job

            # 3. Skills Extraction (single JSONB field, grouped by category)
            skills = self.nlp_engine.extract_skills(raw_job.full_description)
            job_data['extracted_skills'] = skills

            # 4. Salary Information
            salary_info = self.nlp_engine.extract_salary_info(raw_job.full_description)
            job_data['salary_min'] = salary_info.get('min_salary')
            job_data['salary_max'] = salary_info.get('max_salary')
            job_data['salary_currency'] = salary_info.get('currency', 'NZD')
            job_data['salary_period'] = salary_info.get('period')
            job_data['salary_raw_text'] = salary_info.get('raw_text')
            job_data['salary_confidence_score'] = round(salary_info.get('confidence_score', 0.0), 2)

            # 5. Employment Details (returns enum values)
            job_data['employment_type'] = self.nlp_engine.extract_employment_type(raw_job.full_description)
            job_data['experience_level'] = self.nlp_engine.extract_experience_level(
                raw_job.title, raw_job.full_description
            )
            job_data['work_arrangement'] = self.nlp_engine.extract_work_arrangement(raw_job.full_description)

            # 6. URL Accessibility Check (if enabled)
            if self.enable_url_checking and self.url_checker and raw_job.url:
                is_accessible, status_message, status_code = self.url_checker.check_url_accessibility(raw_job.url)
                job_data['is_active'] = is_accessible
                job_data['url_check_status'] = status_message
                job_data['url_status_code'] = status_code
                
                logger.debug(f"URL check for job {raw_job.id}: {status_message}")
                
                if not is_accessible:
                    logger.info(f"Job {raw_job.id} marked as inactive due to URL: {status_message}")

            return job_data

        except Exception as e:
            logger.error(f"Error processing job {raw_job.id}: {e}")
            raise

    def _get_or_create_company(self, db: Session, company_name: str) -> int:
        """Get or create a company record and return its ID"""
        if not company_name or company_name.strip() == '':
            return None
            
        # Normalize company name
        normalized_name = company_name.strip().lower()
        
        # Check if company exists
        company = db.query(Company).filter(Company.normalized_name == normalized_name).first()
        
        if company:
            return company.id
        
        # Create new company
        new_company = Company(
            name=company_name.strip(),
            normalized_name=normalized_name
        )
        db.add(new_company)
        db.flush()
        logger.debug(f"Created new company: {company_name}")
        return new_company.id

    def _get_or_create_location(self, db: Session, location_info: Dict[str, Optional[str]]) -> int:
        """
        Get or create location record from NLP-extracted location info.
        
        Args:
            location_info: Dict with keys city, region, country, raw_location
            
        Returns:
            Location ID or None if no valid location found
        """
        if not location_info or not location_info.get('city'):
            return None
        
        city = location_info.get('city')
        region = location_info.get('region')
        country = location_info.get('country', 'New Zealand')
        
        # Check if location exists by city
        location = db.query(Location).filter(Location.city == city).first()
        
        if location:
            # Update region if we have better info
            if region and not location.region:
                location.region = region
                db.flush()
            return location.id
        
        # Create new location with full details
        new_location = Location(
            city=city,
            region=region,
            country=country
        )
        db.add(new_location)
        db.flush()
        logger.debug(f"Created new location: {city}, {region}, {country}")
        return new_location.id

    def _get_category_for_job(self, db: Session, title: str, skills: dict) -> int:
        """
        Determine category based on job title and skills.
        
        Uses existing categories from database (seeded data).
        Categories are matched by priority order to avoid duplicates.
        
        Args:
            db: Database session
            title: Job title
            skills: Extracted skills dictionary
            
        Returns:
            Category ID or None if no match found
        """
        if not title:
            return None
        
        title_lower = title.lower()
        
        # Category mapping with keywords (ordered by priority)
        # Note: These names MUST match the seeded category names in database/init.py
        # Updated with improved keyword matching based on analysis of "Other Tech Roles"
        category_keywords = {
            'Software Development': [
                # Core development roles
                'software', 'developer', 'programmer', 'engineer', 'full stack', 'backend', 'frontend', 'web developer',
                # Leadership and architecture roles
                'tech lead', 'technical lead', 'solution architect', 'technology architect', 'senior solution architect',
                'software architect', 'principal engineer', 'staff engineer', 'engineering manager', 'development lead',
                'technical architect', 'systems architect', 'application architect'
            ],
            'Data & Analytics': [
                'data', 'analyst', 'analytics', 'scientist', 'ml', 'machine learning', 'ai', 'artificial intelligence', 'data engineer',
                'business intelligence', 'bi analyst', 'data analyst', 'reporting analyst', 'insights analyst'
            ],
            'DevOps & Infrastructure': [
                'devops', 'cloud', 'infrastructure', 'platform', 'sre', 'reliability', 'kubernetes', 'docker', 'aws', 'azure',
                'automation', 'automation technician', 'systems administrator', 'network', 'infrastructure engineer',
                'cloud engineer', 'platform engineer', 'site reliability'
            ],
            'Security': [
                'security', 'cybersecurity', 'infosec', 'penetration', 'ethical hacking', 'security analyst',
                'information security', 'security engineer', 'security consultant'
            ],
            'QA & Testing': [
                'qa', 'test', 'quality assurance', 'automation tester', 'test engineer', 'testing',
                'quality engineer', 'test analyst', 'automation engineer'
            ],
            'Product Management': [
                'product manager', 'product owner', 'product lead',
                'product specialist', 'digital product', 'product consultant', 'product analyst',
                'business analyst', 'product marketing', 'product strategy'
            ],
            'Project Management': [
                'project manager', 'scrum master', 'agile coach', 'program manager',
                'delivery manager', 'projects delivery', 'project lead', 'program lead',
                'implementation manager', 'project coordinator', 'delivery lead'
            ],
            'UI/UX Design': [
                'ui', 'ux', 'design', 'user experience', 'interface', 'designer', 'figma',
                'visual designer', 'interaction designer', 'user interface', 'graphic designer'
            ],
            'Mobile Development': [
                'mobile', 'ios', 'android', 'react native', 'flutter', 'swift', 'kotlin',
                'mobile developer', 'app developer', 'mobile engineer'
            ],
            'Database Administration': [
                'database', 'dba', 'database administrator', 'sql server',
                'database engineer', 'sql developer', 'database analyst'
            ],
            'Support & IT': [
                'support', 'helpdesk', 'technical support', 'it support', 'service desk',
                'technical consultant', 'it consultant', 'systems analyst', 'business systems',
                'technical specialist', 'it specialist', 'consultant', 'implementation consultant'
            ],
        }
        
        # Find matching category (first match wins - order matters!)
        matched_category_name = None
        for category_name, keywords in category_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                matched_category_name = category_name
                break
        
        # Default to "Other Tech Roles" if no match
        if not matched_category_name:
            matched_category_name = 'Other Tech Roles'
        
        # Look up existing category (DO NOT create new ones)
        category = db.query(Category).filter(Category.name == matched_category_name).first()
        
        if category:
            return category.id
        
        # If category doesn't exist, log warning and use "Other Tech Roles" as fallback
        logger.warning(f"Category '{matched_category_name}' not found in database, using 'Other Tech Roles' fallback")
        fallback_category = db.query(Category).filter(Category.name == 'Other Tech Roles').first()
        
        if fallback_category:
            return fallback_category.id
        
        # Last resort: return None (should never happen if seed data is loaded)
        logger.error("No categories found in database! Run: python database/init.py --seed-data")
        return None


    def _insert_processed_job(self, db: Session, job_data: Dict[str, Any], raw_job: RawJob):
        """Insert processed job data into the jobs table using SQLAlchemy ORM"""

        try:
            # Check if job already exists by URL
            existing_job = db.query(Job).filter(Job.original_url == job_data.get('original_url')).first()
            if existing_job:
                logger.debug(f"Job with URL {job_data.get('original_url')} already exists (ID: {existing_job.id})")
                return existing_job.id

            # Get or create foreign key records
            company_id = self._get_or_create_company(db, raw_job.company)
            
            # Get or create location from NLP-extracted location info
            location_info = job_data.get('location_info')
            location_id = self._get_or_create_location(db, location_info) if location_info else None
            
            # Determine category based on title and skills
            category_id = self._get_category_for_job(db, job_data.get('title'), job_data.get('extracted_skills'))

            # Create Job instance with all foreign keys populated
            job = Job(
                raw_job_id=job_data.get('raw_job_id'),
                title=job_data.get('title'),
                company_id=company_id,
                location_id=location_id,
                category_id=category_id,
                description=job_data.get('description'),
                posted_date=job_data.get('posted_date'),
                scraped_at=job_data.get('scraped_at'),
                is_tech_job=job_data.get('is_tech_job'),
                tech_confidence_score=job_data.get('tech_confidence_score'),
                employment_type=job_data.get('employment_type'),
                experience_level=job_data.get('experience_level'),
                work_arrangement=job_data.get('work_arrangement'),
                extracted_skills=job_data.get('extracted_skills'),
                salary_min=job_data.get('salary_min'),
                salary_max=job_data.get('salary_max'),
                salary_currency=job_data.get('salary_currency', 'NZD'),
                salary_period=job_data.get('salary_period'),
                salary_raw_text=job_data.get('salary_raw_text'),
                salary_confidence_score=job_data.get('salary_confidence_score'),
                processed_at=job_data.get('processed_at'),
                processing_version=job_data.get('processing_version'),
                original_url=job_data.get('original_url'),
                found_via_search_term=job_data.get('found_via_search_term')
            )

            # Add and commit
            db.add(job)
            db.flush()  # Flush to get the ID

            logger.debug(f"Inserted processed job {raw_job.id} as job {job.id}")
            return job.id

        except Exception as e:
            logger.error(f"Failed to insert job {raw_job.id}: {e}")
            raise

    def reprocess_jobs(self, force_reprocess: bool = False) -> ProcessingStats:
        """Reprocess existing jobs (useful for version upgrades)"""

        db = SessionLocal()
        stats = ProcessingStats()

        try:
            if force_reprocess:
                # Reset all jobs to unprocessed
                db.execute(text("UPDATE raw_jobs SET processed = FALSE"))
                db.execute(text("DELETE FROM jobs"))  # Clear existing processed jobs
                db.commit()
                logger.info("Reset all jobs for reprocessing")

            # Process unprocessed jobs
            stats = self.process_unprocessed_jobs()

        except Exception as e:
            logger.error(f"Reprocessing failed: {e}")
            db.rollback()
            raise
        finally:
            db.close()

        return stats

    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status and statistics"""

        db = SessionLocal()

        try:
            status = {}

            # Raw jobs status
            total_raw = db.execute(text("SELECT COUNT(*) FROM raw_jobs")).scalar()
            processed_raw = db.execute(text("SELECT COUNT(*) FROM raw_jobs WHERE processed = TRUE")).scalar()
            unprocessed_raw = total_raw - processed_raw

            # Processed jobs status
            total_processed = db.execute(text("SELECT COUNT(*) FROM jobs")).scalar()
            tech_jobs = db.execute(text("SELECT COUNT(*) FROM jobs WHERE is_tech_job = TRUE")).scalar()
            jobs_with_salary = db.execute(text("SELECT COUNT(*) FROM jobs WHERE salary_min IS NOT NULL")).scalar()
            jobs_with_skills = db.execute(text("SELECT COUNT(*) FROM jobs WHERE extracted_skills != '{}'")).scalar()

            # Processing versions
            versions = db.execute(text("""
                SELECT processing_version, COUNT(*) as count
                FROM raw_jobs
                WHERE processed = TRUE
                GROUP BY processing_version
                ORDER BY count DESC
            """)).fetchall()

            status = {
                'raw_jobs': {
                    'total': total_raw,
                    'processed': processed_raw,
                    'unprocessed': unprocessed_raw,
                    'processing_rate': round(processed_raw / total_raw * 100, 1) if total_raw > 0 else 0
                },
                'processed_jobs': {
                    'total': total_processed,
                    'tech_jobs': tech_jobs,
                    'tech_job_rate': round(tech_jobs / total_processed * 100, 1) if total_processed > 0 else 0,
                    'jobs_with_salary': jobs_with_salary,
                    'salary_extraction_rate': round(jobs_with_salary / total_processed * 100, 1) if total_processed > 0 else 0,
                    'jobs_with_skills': jobs_with_skills,
                    'skills_extraction_rate': round(jobs_with_skills / total_processed * 100, 1) if total_processed > 0 else 0
                },
                'processing_versions': [{'version': v[0], 'count': v[1]} for v in versions],
                'pipeline_version': self.processing_version,
                'nlp_engine_status': 'spaCy Available' if hasattr(self.nlp_engine, 'nlp') and self.nlp_engine.nlp else 'spaCy Not Available'
            }

            return status

        finally:
            db.close()

    def process_specific_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Process a specific raw job by ID (useful for testing)"""

        db = SessionLocal()

        try:
            raw_job = db.query(RawJob).filter(RawJob.id == job_id).first()

            if not raw_job:
                logger.error(f"Raw job {job_id} not found")
                return None

            logger.info(f"Processing specific job {job_id}: {raw_job.title}")

            # Process the job
            processed_job = self._process_single_job(raw_job)

            if processed_job:
                # Delete existing processed job if it exists
                db.execute(text("DELETE FROM jobs WHERE raw_job_id = :job_id"), {'job_id': job_id})

                # Insert new processed job
                self._insert_processed_job(db, processed_job, raw_job)

                # Mark raw job as processed
                raw_job.processed = True
                raw_job.processed_at = datetime.now()
                raw_job.processing_version = self.processing_version

                db.commit()

                logger.info(f"Successfully processed job {job_id}")
                return processed_job
            else:
                logger.warning(f"Job {job_id} was not processed (low quality/confidence)")
                return None

        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
            db.rollback()
            raise
        finally:
            db.close()


def main():
    """Main function for running the pipeline"""

    print("Tech Jobs Insights - Data Processing Pipeline")
    print("=" * 60)

    pipeline = DataProcessingPipeline()

    try:
        # Show current status
        status = pipeline.get_processing_status()
        print(f"Current Status:")
        print(f" Raw jobs: {status['raw_jobs']['unprocessed']} unprocessed / {status['raw_jobs']['total']} total")
        print(f" Processed jobs: {status['processed_jobs']['total']}")
        print(f" Tech jobs: {status['processed_jobs']['tech_jobs']} ({status['processed_jobs']['tech_job_rate']}%)")
        print(f" Pipeline version: {status['pipeline_version']}")
        print()

        if status['raw_jobs']['unprocessed'] > 0:
            print(f"Processing {status['raw_jobs']['unprocessed']} unprocessed jobs...")

            # Process unprocessed jobs
            stats = pipeline.process_unprocessed_jobs()

            print(f"Processing completed!")
            print(f" Processed: {stats.processed_jobs}/{stats.total_jobs}")
            print(f" Tech jobs found: {stats.tech_jobs_found}")
            print(f" Jobs with salary: {stats.jobs_with_salary}")
            print(f" Jobs with skills: {stats.jobs_with_skills}")
            print(f" Average time per job: {stats.avg_processing_time:.2f}s")
            if stats.errors:
                print(f" Errors: {len(stats.errors)}")
        else:
            print("All jobs are already processed!")

    except Exception as e:
        print(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()
