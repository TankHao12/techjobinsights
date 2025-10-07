#!/usr/bin/env python3
"""
Fix posted dates for existing jobs in the database
Reprocesses raw_jobs.posting_date and updates jobs.posted_date
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime
from app.database import SessionLocal
from app.models import RawJob, Job
from app.processors.nlp_engine import NLPEngine
from app.core.logging import get_logger
from sqlalchemy import func

logger = get_logger(__name__)


def fix_posted_dates():
    """Fix posted dates for all jobs in the database"""
    db = SessionLocal()
    nlp_engine = NLPEngine()
    
    try:
        logger.info("=" * 60)
        logger.info("FIXING POSTED DATES FOR EXISTING JOBS")
        logger.info("=" * 60)
        
        # Get statistics BEFORE
        total_jobs = db.query(func.count(Job.id)).scalar()
        jobs_with_date = db.query(func.count(Job.id)).filter(Job.posted_date.isnot(None)).scalar()
        
        logger.info(f"\nBefore fix:")
        logger.info(f"  Total jobs: {total_jobs}")
        logger.info(f"  Jobs with posted_date: {jobs_with_date} ({jobs_with_date/total_jobs*100:.1f}%)")
        logger.info(f"  Jobs without posted_date: {total_jobs - jobs_with_date}")
        
        # Get all jobs that need fixing
        jobs_to_fix = db.query(Job).join(RawJob).filter(
            Job.posted_date.is_(None)
        ).all()
        
        logger.info(f"\nProcessing {len(jobs_to_fix)} jobs without posted_date...")
        
        updated_count = 0
        failed_count = 0
        no_data_count = 0
        
        for i, job in enumerate(jobs_to_fix, 1):
            try:
                # Get the raw job
                raw_job = db.query(RawJob).filter(RawJob.id == job.raw_job_id).first()
                
                if not raw_job:
                    logger.warning(f"Job {job.id}: No raw_job found")
                    failed_count += 1
                    continue
                
                if not raw_job.posting_date:
                    logger.debug(f"Job {job.id}: No posting_date in raw_jobs")
                    no_data_count += 1
                    continue
                
                # Parse the posting date relative to when it was scraped (for accuracy)
                # Convert scraped_at timestamp to date for reference
                reference_date = raw_job.scraped_at.date() if raw_job.scraped_at else None
                parsed_date = nlp_engine.parse_posted_date(raw_job.posting_date, reference_date=reference_date)
                
                if parsed_date:
                    job.posted_date = parsed_date
                    updated_count += 1
                    
                    if i % 100 == 0:
                        logger.info(f"  Processed {i}/{len(jobs_to_fix)} jobs...")
                        db.commit()
                else:
                    logger.debug(f"Job {job.id}: Could not parse '{raw_job.posting_date}'")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Job {job.id}: Error - {e}")
                failed_count += 1
                continue
        
        # Final commit
        db.commit()
        
        # Get statistics AFTER
        jobs_with_date_after = db.query(func.count(Job.id)).filter(Job.posted_date.isnot(None)).scalar()
        
        logger.info("\n" + "=" * 60)
        logger.info("RESULTS:")
        logger.info("=" * 60)
        logger.info(f"Total jobs processed: {len(jobs_to_fix)}")
        logger.info(f"Successfully updated: {updated_count}")
        logger.info(f"No posting_date in raw_jobs: {no_data_count}")
        logger.info(f"Failed to parse: {failed_count}")
        logger.info(f"\nAfter fix:")
        logger.info(f"  Jobs with posted_date: {jobs_with_date_after} ({jobs_with_date_after/total_jobs*100:.1f}%)")
        logger.info(f"  Jobs without posted_date: {total_jobs - jobs_with_date_after}")
        logger.info(f"  Improvement: +{jobs_with_date_after - jobs_with_date} jobs")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


def check_raw_jobs_posting_dates():
    """Check how many raw_jobs have posting_date populated"""
    db = SessionLocal()
    
    try:
        logger.info("\n" + "=" * 60)
        logger.info("CHECKING RAW_JOBS POSTING_DATE FIELD")
        logger.info("=" * 60)
        
        total_raw = db.query(func.count(RawJob.id)).scalar()
        with_posting_date = db.query(func.count(RawJob.id)).filter(
            RawJob.posting_date.isnot(None),
            RawJob.posting_date != ''
        ).scalar()
        
        logger.info(f"Total raw_jobs: {total_raw}")
        logger.info(f"With posting_date: {with_posting_date} ({with_posting_date/total_raw*100:.1f}%)")
        logger.info(f"Without posting_date: {total_raw - with_posting_date}")
        
        # Show some examples
        logger.info("\nSample posting_date values:")
        samples = db.query(RawJob.posting_date).filter(
            RawJob.posting_date.isnot(None),
            RawJob.posting_date != ''
        ).limit(10).all()
        
        for sample in samples:
            logger.info(f"  - '{sample[0]}'")
            
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix posted dates for existing jobs')
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check raw_jobs posting_date field, do not fix'
    )
    
    args = parser.parse_args()
    
    try:
        if args.check_only:
            check_raw_jobs_posting_dates()
        else:
            check_raw_jobs_posting_dates()
            logger.info("")
            fix_posted_dates()
            
        logger.info("\n✓ Done!")
        
    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)

