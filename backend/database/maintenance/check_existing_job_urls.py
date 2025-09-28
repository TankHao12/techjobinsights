#!/usr/bin/env python3
"""
Enhanced script to check URLs for existing processed jobs using the new URL checker utility.

This script:
1. Finds all processed jobs with is_active = True
2. Uses the new URLChecker utility to check URL accessibility
3. Updates is_active = False for jobs with inaccessible URLs
4. Provides detailed reporting and statistics

Usage:
    python scripts/check_existing_job_urls.py [--dry-run] [--limit N] [--batch-size N] [--check-all] [--older-than-days N]
"""

import sys
import os
import argparse
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import time

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.tables import Job
from app.processors.url_checker import URLChecker
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExistingJobURLChecker:
    """Enhanced URL checker for existing processed jobs"""
    
    def __init__(self, dry_run: bool = False, batch_size: int = 20):
        self.dry_run = dry_run
        self.batch_size = batch_size
        
        # Initialize URL checker with same settings as pipeline
        self.url_checker = URLChecker(timeout=10, max_retries=2)
        
        # Statistics
        self.stats = {
            'total_jobs_found': 0,
            'jobs_checked': 0,
            'jobs_kept_active': 0,
            'jobs_marked_inactive': 0,
            'check_errors': 0,
            'start_time': datetime.now()
        }
    
    def find_jobs_to_check(self, db: Session, limit: Optional[int] = None, 
                          check_all: bool = False, older_than_days: Optional[int] = None) -> List[Tuple[int, str, datetime]]:
        """
        Find processed jobs that need URL checking.
        
        Args:
            limit: Maximum number of jobs to check
            check_all: If True, check all active jobs. If False, prioritize older jobs.
            older_than_days: Only check jobs older than N days
            
        Returns:
            List of tuples: (job_id, url, scraped_at)
        """
        query = db.query(
            Job.id,
            Job.original_url,
            Job.scraped_at
        ).filter(
            Job.is_active == True,
            Job.original_url.isnot(None),
            Job.original_url != ''
        )
        
        # Filter by age if specified
        if older_than_days:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
            query = query.filter(Job.scraped_at < cutoff_date)
        elif not check_all:
            # Default: prioritize jobs older than 7 days
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            query = query.filter(Job.scraped_at < cutoff_date)
        
        # Order by scraped_at (oldest first) to prioritize checking older jobs
        query = query.order_by(Job.scraped_at.asc())
        
        if limit:
            query = query.limit(limit)
            
        results = [(r.id, r.original_url, r.scraped_at) for r in query.all()]
        self.stats['total_jobs_found'] = len(results)
        
        logger.info(f"Found {len(results)} jobs to check")
        return results
    
    def check_job_urls(self, db: Session, jobs_to_check: List[Tuple[int, str, datetime]]) -> Dict[str, int]:
        """
        Check URLs for a list of jobs and update their active status.
        
        Returns:
            Dictionary with detailed statistics
        """
        logger.info(f"Starting URL checks for {len(jobs_to_check)} jobs...")
        logger.info(f"Batch size: {self.batch_size}")
        logger.info(f"Dry run: {self.dry_run}")
        
        # Process jobs in batches
        for i in range(0, len(jobs_to_check), self.batch_size):
            batch = jobs_to_check[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(jobs_to_check) + self.batch_size - 1) // self.batch_size
            
            logger.info(f"\\nProcessing batch {batch_num}/{total_batches} ({len(batch)} jobs)")
            
            self._process_batch(db, batch)
            
            # Small delay between batches to be respectful to servers
            if i + self.batch_size < len(jobs_to_check):
                time.sleep(1)
        
        return self.stats
    
    def _process_batch(self, db: Session, batch: List[Tuple[int, str, datetime]]):
        """Process a batch of jobs"""
        
        for job_id, url, scraped_at in batch:
            try:
                logger.debug(f"Checking job {job_id}: {url}")
                
                # Check URL accessibility
                is_accessible, status_message, status_code = self.url_checker.check_url_accessibility(url)
                
                self.stats['jobs_checked'] += 1
                
                # Log result
                age_days = (datetime.utcnow() - scraped_at).days
                status_icon = "✅" if is_accessible else "❌"
                logger.info(f"{status_icon} Job {job_id} ({age_days}d old): {status_message}")
                
                if is_accessible:
                    self.stats['jobs_kept_active'] += 1
                else:
                    # Mark job as inactive
                    if not self.dry_run:
                        job = db.query(Job).filter(Job.id == job_id).first()
                        if job:
                            job.is_active = False
                            logger.info(f"   → Marked job {job_id} as inactive")
                    else:
                        logger.info(f"   → Would mark job {job_id} as inactive (dry run)")
                    
                    self.stats['jobs_marked_inactive'] += 1
                
            except Exception as e:
                logger.error(f"Error checking job {job_id}: {e}")
                self.stats['check_errors'] += 1
        
        # Commit batch changes
        if not self.dry_run:
            try:
                db.commit()
                logger.debug("Batch committed to database")
            except Exception as e:
                logger.error(f"Error committing batch: {e}")
                db.rollback()
    
    def print_summary(self):
        """Print final summary statistics"""
        duration = datetime.now() - self.stats['start_time']
        
        logger.info("\\n" + "=" * 60)
        logger.info("URL CHECKING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total jobs found: {self.stats['total_jobs_found']}")
        logger.info(f"Jobs checked: {self.stats['jobs_checked']}")
        logger.info(f"Jobs kept active: {self.stats['jobs_kept_active']}")
        logger.info(f"Jobs marked inactive: {self.stats['jobs_marked_inactive']}")
        
        if self.stats['check_errors'] > 0:
            logger.warning(f"Check errors: {self.stats['check_errors']}")
        
        logger.info(f"Duration: {duration}")
        
        if self.stats['jobs_checked'] > 0:
            inactive_rate = (self.stats['jobs_marked_inactive'] / self.stats['jobs_checked']) * 100
            logger.info(f"Inactive rate: {inactive_rate:.1f}%")
        
        if self.dry_run:
            logger.info("\\n⚠️  DRY RUN - No changes were made to the database")
        else:
            logger.info("\\n✅ Database updated with URL check results")
    
    def close(self):
        """Clean up resources"""
        if self.url_checker:
            self.url_checker.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Check URLs for existing processed jobs")
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without making changes')
    parser.add_argument('--limit', type=int, 
                       help='Maximum number of jobs to check')
    parser.add_argument('--batch-size', type=int, default=20,
                       help='Number of jobs to process in each batch')
    parser.add_argument('--check-all', action='store_true',
                       help='Check all active jobs (not just older ones)')
    parser.add_argument('--older-than-days', type=int,
                       help='Only check jobs older than N days')
    
    args = parser.parse_args()
    
    logger.info("🔍 STARTING EXISTING JOB URL CHECKING")
    logger.info("=" * 60)
    
    db = SessionLocal()
    checker = ExistingJobURLChecker(
        dry_run=args.dry_run,
        batch_size=args.batch_size
    )
    
    try:
        # Find jobs to check
        jobs_to_check = checker.find_jobs_to_check(
            db, 
            limit=args.limit,
            check_all=args.check_all,
            older_than_days=args.older_than_days
        )
        
        if not jobs_to_check:
            logger.info("No jobs found to check")
            return
        
        # Check URLs and update database
        checker.check_job_urls(db, jobs_to_check)
        
        # Print summary
        checker.print_summary()
        
    except KeyboardInterrupt:
        logger.warning("\\nOperation interrupted by user")
    except Exception as e:
        logger.error(f"Script failed: {e}", exc_info=True)
    finally:
        checker.close()
        db.close()


if __name__ == "__main__":
    main()










