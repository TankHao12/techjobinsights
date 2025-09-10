#!/usr/bin/env python3
"""
Reset processed flag for jobs that exist in raw_jobs but not in jobs table.

This script:
1. Identifies jobs in raw_jobs that don't have corresponding entries in jobs table
2. Resets their processed flag to FALSE
3. Clears processed_at and processing_version
4. Allows them to be reprocessed by the NLP pipeline

Usage:
    python scripts/reset_unprocessed_jobs.py [--dry-run] [--confirm]
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import argparse
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from app.database import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)

def get_current_status(db: Session) -> dict:
    """Get current status of raw_jobs and jobs tables"""
    # Total raw jobs
    total_raw_jobs = db.execute(text("SELECT COUNT(*) FROM raw_jobs")).scalar()
    
    # Processed raw jobs
    processed_raw_jobs = db.execute(text("SELECT COUNT(*) FROM raw_jobs WHERE processed = true")).scalar()
    
    # Unprocessed raw jobs
    unprocessed_raw_jobs = db.execute(text("SELECT COUNT(*) FROM raw_jobs WHERE processed = false OR processed IS NULL")).scalar()
    
    # Jobs in jobs table
    jobs_in_jobs_table = db.execute(text("SELECT COUNT(*) FROM jobs")).scalar()
    
    # Jobs that are processed but missing from jobs table
    processed_but_missing = db.execute(text("""
        SELECT COUNT(*) 
        FROM raw_jobs rj 
        LEFT JOIN jobs j ON rj.id = j.raw_job_id 
        WHERE rj.processed = true AND j.id IS NULL
    """)).scalar()
    
    return {
        'total_raw_jobs': total_raw_jobs,
        'processed_raw_jobs': processed_raw_jobs,
        'unprocessed_raw_jobs': unprocessed_raw_jobs,
        'jobs_in_jobs_table': jobs_in_jobs_table,
        'processed_but_missing': processed_but_missing
    }

def reset_unprocessed_jobs(db: Session, dry_run: bool = False) -> int:
    """
    Reset processed flag for jobs that don't exist in jobs table.
    
    Returns:
        Number of jobs that were reset
    """
    if dry_run:
        logger.info("*** DRY RUN MODE - NO CHANGES WILL BE MADE ***")
    
    # Count jobs that will be reset
    count_query = text("""
        SELECT COUNT(*) 
        FROM raw_jobs 
        WHERE id NOT IN (
            SELECT DISTINCT raw_job_id 
            FROM jobs 
            WHERE raw_job_id IS NOT NULL
        )
    """)
    
    jobs_to_reset = db.execute(count_query).scalar()
    logger.info(f"Jobs to reset: {jobs_to_reset}")
    
    if jobs_to_reset == 0:
        logger.info("No jobs need to be reset - all raw jobs have corresponding jobs entries")
        return 0
    
    if dry_run:
        logger.info(f"[DRY RUN] Would reset {jobs_to_reset} jobs")
        return jobs_to_reset
    
    # Reset the jobs
    reset_query = text("""
        UPDATE raw_jobs 
        SET 
            processed = false,
            processed_at = NULL,
            processing_version = NULL
        WHERE id NOT IN (
            SELECT DISTINCT raw_job_id 
            FROM jobs 
            WHERE raw_job_id IS NOT NULL
        )
    """)
    
    result = db.execute(reset_query)
    db.commit()
    
    logger.info(f"Successfully reset {result.rowcount} jobs")
    return result.rowcount

def main():
    parser = argparse.ArgumentParser(description='Reset processed flag for missing jobs')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--confirm', action='store_true', help='Confirm the operation (required for actual changes)')
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.confirm:
        logger.error("You must use --dry-run to preview changes or --confirm to make actual changes")
        return
    
    logger.info("=" * 80)
    logger.info("RESET UNPROCESSED JOBS")
    logger.info("=" * 80)
    
    db = next(get_db())
    
    try:
        # Get current status
        status = get_current_status(db)
        
        logger.info("Current Status:")
        logger.info(f"  Total raw jobs: {status['total_raw_jobs']}")
        logger.info(f"  Processed raw jobs: {status['processed_raw_jobs']}")
        logger.info(f"  Unprocessed raw jobs: {status['unprocessed_raw_jobs']}")
        logger.info(f"  Jobs in jobs table: {status['jobs_in_jobs_table']}")
        logger.info(f"  Processed but missing: {status['processed_but_missing']}")
        
        if status['processed_but_missing'] == 0:
            logger.info("No jobs need to be reset - all processed raw jobs have corresponding jobs entries")
            return
        
        # Reset the jobs
        reset_count = reset_unprocessed_jobs(db, dry_run=args.dry_run)
        
        if not args.dry_run:
            # Show updated status
            updated_status = get_current_status(db)
            logger.info("\nUpdated Status:")
            logger.info(f"  Total raw jobs: {updated_status['total_raw_jobs']}")
            logger.info(f"  Processed raw jobs: {updated_status['processed_raw_jobs']}")
            logger.info(f"  Unprocessed raw jobs: {updated_status['unprocessed_raw_jobs']}")
            logger.info(f"  Jobs in jobs table: {updated_status['jobs_in_jobs_table']}")
            logger.info(f"  Processed but missing: {updated_status['processed_but_missing']}")
            
            logger.info(f"\n✅ Successfully reset {reset_count} jobs for reprocessing")
            logger.info("You can now run the NLP pipeline to reprocess these jobs:")
            logger.info("  python database/run_nlp_pipeline.py")
        
    except Exception as e:
        logger.error(f"Error during reset: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
