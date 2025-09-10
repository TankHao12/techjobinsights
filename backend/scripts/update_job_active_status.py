#!/usr/bin/env python3
"""
Script to update is_active status for jobs based on URL availability.

This script:
1. Finds all jobs with is_active = True
2. Checks if their URLs are still accessible
3. Updates is_active = False for jobs with inactive URLs
4. Provides detailed reporting on job status changes

The is_active column is used to:
- Filter jobs in API responses (only show active jobs by default)
- Calculate statistics (active vs inactive job counts)
- Maintain data quality (hide expired job postings)

Usage:
    python scripts/update_job_active_status.py [--dry-run] [--limit N] [--batch-size N] [--check-all]
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import argparse
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import time
import requests
from urllib.parse import urlparse

from app.database import get_db
from app.models.tables import Job, RawJob
from app.core.logging import get_logger

logger = get_logger(__name__)

class JobActiveStatusUpdater:
    """Handles updating is_active status for jobs"""
    
    def __init__(self, dry_run: bool = False, batch_size: int = 20):
        self.dry_run = dry_run
        self.batch_size = batch_size
        
        # Configure session for URL checking
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Statistics
        self.stats = {
            'total_active_jobs': 0,
            'urls_checked': 0,
            'urls_still_active': 0,
            'urls_inactive': 0,
            'urls_error': 0,
            'jobs_deactivated': 0,
            'jobs_kept_active': 0
        }
    
    def find_active_jobs(self, db: Session, limit: Optional[int] = None, check_all: bool = False) -> List[Tuple[int, str, datetime]]:
        """
        Find jobs that are currently marked as active.
        
        Args:
            check_all: If True, check all active jobs. If False, prioritize older jobs.
            
        Returns:
            List of tuples: (job_id, url, scraped_at)
        """
        query = db.query(
            Job.id,
            Job.original_url,
            Job.scraped_at
        ).filter(
            Job.is_active == True,
            Job.original_url.isnot(None)
        )
        
        if not check_all:
            # Prioritize jobs older than 7 days for checking
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            query = query.filter(Job.scraped_at < cutoff_date)
        
        # Order by scraped_at (oldest first) to prioritize checking older jobs
        query = query.order_by(Job.scraped_at.asc())
        
        if limit:
            query = query.limit(limit)
            
        results = [(r.id, r.original_url, r.scraped_at) for r in query.all()]
        self.stats['total_active_jobs'] = len(results)
        
        return results
    
    def check_url_status(self, url: str) -> Tuple[bool, str]:
        """
        Check if a job URL is still active.
        
        Returns:
            Tuple of (is_active, status_message)
        """
        try:
            logger.debug(f"Checking URL: {url}")
            
            # Make HEAD request first (faster)
            response = self.session.head(url, timeout=10, allow_redirects=True)
            
            # Check status codes
            if response.status_code == 200:
                return True, "Active (200 OK)"
            elif response.status_code == 404:
                return False, "Not Found (404)"
            elif response.status_code == 403:
                return False, "Forbidden (403)"
            elif response.status_code in [410, 451]:  # Gone, Unavailable for Legal Reasons
                return False, f"Gone ({response.status_code})"
            elif 300 <= response.status_code < 400:
                # Follow redirects and check final destination
                final_response = self.session.get(url, timeout=10, allow_redirects=True)
                if final_response.status_code == 200:
                    # Check if redirected to a generic page (common for expired jobs)
                    if self._is_generic_redirect(final_response.url, url):
                        return False, f"Redirected to generic page ({final_response.url})"
                    return True, f"Active after redirect ({response.status_code} -> 200)"
                else:
                    return False, f"Redirect failed ({response.status_code} -> {final_response.status_code})"
            elif 500 <= response.status_code < 600:
                # Server errors - assume temporarily unavailable, keep active
                return True, f"Server error - keeping active ({response.status_code})"
            else:
                return False, f"Unexpected status ({response.status_code})"
                
        except requests.exceptions.Timeout:
            return True, "Timeout - keeping active"
        except requests.exceptions.ConnectionError:
            return True, "Connection error - keeping active"
        except requests.exceptions.RequestException as e:
            return True, f"Request error - keeping active ({str(e)[:50]})"
        except Exception as e:
            logger.error(f"Unexpected error checking {url}: {e}")
            return True, f"Error - keeping active ({str(e)[:50]})"
    
    def _is_generic_redirect(self, final_url: str, original_url: str) -> bool:
        """
        Check if the final URL appears to be a generic redirect (indicating expired job).
        
        Common patterns for expired Seek jobs:
        - Redirected to search page
        - Redirected to homepage
        - URL structure completely different
        """
        try:
            original_parsed = urlparse(original_url)
            final_parsed = urlparse(final_url)
            
            # If redirected to a different domain, likely expired
            if original_parsed.netloc != final_parsed.netloc:
                return True
            
            # Check for common Seek redirect patterns
            if 'seek.co.nz' in final_parsed.netloc:
                final_path = final_parsed.path.lower()
                
                # Redirected to search or homepage
                if final_path in ['/', '/jobs', '/jobs/', '']:
                    return True
                
                # Redirected to search results
                if '/jobs?' in final_path or 'search' in final_path:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def update_job_status(self, db: Session, job_id: int, is_active: bool, status_message: str) -> bool:
        """Update job's is_active status"""
        try:
            if self.dry_run:
                action = "deactivate" if not is_active else "keep active"
                logger.info(f"[DRY RUN] Would {action} job {job_id}: {status_message}")
                return True
            
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                old_status = job.is_active
                job.is_active = is_active
                db.commit()
                
                if old_status != is_active:
                    action = "deactivated" if not is_active else "reactivated"
                    logger.info(f"Job {job_id} {action}: {status_message}")
                else:
                    logger.debug(f"Job {job_id} status unchanged: {status_message}")
                
                return True
            else:
                logger.error(f"Job {job_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")
            db.rollback()
            return False
    
    def process_batch(self, db: Session, jobs_batch: List[Tuple[int, str, datetime]]) -> None:
        """Process a batch of jobs"""
        logger.info(f"Processing batch of {len(jobs_batch)} jobs...")
        
        for job_id, url, scraped_at in jobs_batch:
            self.stats['urls_checked'] += 1
            
            # Check URL status
            is_active, status_message = self.check_url_status(url)
            
            # Update statistics
            if is_active:
                self.stats['urls_still_active'] += 1
                self.stats['jobs_kept_active'] += 1
            else:
                self.stats['urls_inactive'] += 1
            
            # Update job status
            if self.update_job_status(db, job_id, is_active, status_message):
                if not is_active:
                    self.stats['jobs_deactivated'] += 1
            
            # Rate limiting - be respectful to the server
            time.sleep(0.5)
    
    def run(self, limit: Optional[int] = None, check_all: bool = False) -> None:
        """Run the active status update process"""
        logger.info("=" * 80)
        logger.info("STARTING JOB ACTIVE STATUS UPDATE")
        logger.info("=" * 80)
        
        if self.dry_run:
            logger.info("*** DRY RUN MODE - NO CHANGES WILL BE MADE ***")
        
        if check_all:
            logger.info("Checking ALL active jobs (including recent ones)")
        else:
            logger.info("Checking active jobs older than 7 days")
        
        db = next(get_db())
        
        try:
            # Find active jobs to check
            jobs_to_check = self.find_active_jobs(db, limit, check_all)
            
            logger.info(f"Found {self.stats['total_active_jobs']} active jobs to check")
            
            if not jobs_to_check:
                logger.info("No jobs need status checking. Exiting.")
                return
            
            # Process in batches
            for i in range(0, len(jobs_to_check), self.batch_size):
                batch = jobs_to_check[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                total_batches = (len(jobs_to_check) + self.batch_size - 1) // self.batch_size
                
                logger.info(f"\n--- Batch {batch_num}/{total_batches} ---")
                self.process_batch(db, batch)
                
                # Longer delay between batches to be respectful
                if i + self.batch_size < len(jobs_to_check):
                    logger.info("Waiting 3 seconds between batches...")
                    time.sleep(3)
            
            # Print final statistics
            self.print_statistics()
            
        except Exception as e:
            logger.error(f"Error during status update process: {e}")
            raise
        finally:
            db.close()
    
    def print_statistics(self) -> None:
        """Print processing statistics"""
        logger.info("\n" + "=" * 80)
        logger.info("JOB ACTIVE STATUS UPDATE COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total active jobs found: {self.stats['total_active_jobs']}")
        logger.info(f"URLs checked: {self.stats['urls_checked']}")
        logger.info(f"URLs still active: {self.stats['urls_still_active']}")
        logger.info(f"URLs inactive: {self.stats['urls_inactive']}")
        logger.info(f"Jobs deactivated: {self.stats['jobs_deactivated']}")
        logger.info(f"Jobs kept active: {self.stats['jobs_kept_active']}")
        
        if self.stats['urls_checked'] > 0:
            active_rate = (self.stats['urls_still_active'] / self.stats['urls_checked']) * 100
            logger.info(f"Active rate: {active_rate:.1f}%")
        
        logger.info("\nNote: Jobs with server errors or connection issues are kept active")
        logger.info("to avoid false negatives due to temporary issues.")

def main():
    parser = argparse.ArgumentParser(description='Update job active status based on URL availability')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--limit', type=int, help='Limit number of jobs to check')
    parser.add_argument('--batch-size', type=int, default=20, help='Number of jobs to process per batch')
    parser.add_argument('--check-all', action='store_true', help='Check all active jobs (not just old ones)')
    
    args = parser.parse_args()
    
    updater = JobActiveStatusUpdater(
        dry_run=args.dry_run,
        batch_size=args.batch_size
    )
    
    updater.run(limit=args.limit, check_all=args.check_all)

if __name__ == "__main__":
    main()
