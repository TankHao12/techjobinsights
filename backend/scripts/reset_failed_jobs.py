#!/usr/bin/env python3
"""
Reset Failed Jobs - Resets processed flag for jobs that failed processing.

This script identifies jobs that were marked as processed but were never
successfully inserted into the jobs table, and resets their processed flag
so they can be reprocessed.

Usage:
    python scripts/reset_failed_jobs.py [--dry-run]

Options:
    --dry-run: Show what would be reset without actually changing data
"""

import sys
import os
import argparse

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database import SessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)


def reset_failed_jobs(dry_run: bool = False) -> None:
    """
    Reset processed flag for jobs that failed processing.
    
    Args:
        dry_run: If True, only show what would be reset without making changes
        
    Returns:
        None
    """
    db = SessionLocal()
    
    try:
        logger.info("=" * 60)
        logger.info("RESET FAILED JOBS")
        logger.info("=" * 60)
        
        # Step 1: Identify failed jobs
        logger.info("\n1. Identifying failed jobs...")
        
        query_failed = text("""
            SELECT COUNT(*) 
            FROM raw_jobs 
            WHERE processed = TRUE 
            AND id NOT IN (
                SELECT raw_job_id 
                FROM jobs 
                WHERE raw_job_id IS NOT NULL
            )
        """)
        
        failed_count = db.execute(query_failed).scalar()
        logger.info(f"   Found {failed_count} failed jobs")
        
        if failed_count == 0:
            logger.info("   No failed jobs to reset!")
            return
        
        # Show sample of failed jobs
        logger.info("\n2. Sample of failed jobs:")
        
        query_sample = text("""
            SELECT id, title, company, processed_at, processing_version
            FROM raw_jobs 
            WHERE processed = TRUE 
            AND id NOT IN (
                SELECT raw_job_id 
                FROM jobs 
                WHERE raw_job_id IS NOT NULL
            )
            ORDER BY id
            LIMIT 5
        """)
        
        samples = db.execute(query_sample).fetchall()
        for job in samples:
            job_id, title, company, processed_at, version = job
            logger.info(f"   Job {job_id}: {title[:50]}... ({company})")
            logger.info(f"            Processed: {processed_at}, Version: {version}")
        
        if failed_count > 5:
            logger.info(f"   ... and {failed_count - 5} more")
        
        # Step 3: Reset processed flags
        if dry_run:
            logger.info("\n3. DRY RUN - No changes made")
            logger.info(f"   Would reset {failed_count} jobs")
        else:
            logger.info(f"\n3. Resetting {failed_count} jobs...")
            
            reset_query = text("""
                UPDATE raw_jobs 
                SET 
                    processed = FALSE, 
                    processed_at = NULL, 
                    processing_version = NULL
                WHERE processed = TRUE 
                AND id NOT IN (
                    SELECT raw_job_id 
                    FROM jobs 
                    WHERE raw_job_id IS NOT NULL
                )
            """)
            
            result = db.execute(reset_query)
            db.commit()
            
            logger.info(f"   ✅ Reset {result.rowcount} jobs successfully")
        
        # Step 4: Show current status
        logger.info("\n4. Current status:")
        
        total_raw = db.execute(text("SELECT COUNT(*) FROM raw_jobs")).scalar()
        processed_raw = db.execute(text("SELECT COUNT(*) FROM raw_jobs WHERE processed = TRUE")).scalar()
        unprocessed_raw = total_raw - processed_raw
        total_jobs = db.execute(text("SELECT COUNT(*) FROM jobs")).scalar()
        
        logger.info(f"   Raw jobs (total):       {total_raw}")
        logger.info(f"   Raw jobs (processed):   {processed_raw}")
        logger.info(f"   Raw jobs (unprocessed): {unprocessed_raw}")
        logger.info(f"   Jobs table (inserted):  {total_jobs}")
        
        logger.info("\n" + "=" * 60)
        if dry_run:
            logger.info("DRY RUN COMPLETE")
            logger.info("Run without --dry-run to actually reset jobs")
        else:
            logger.info("RESET COMPLETE")
            logger.info("You can now run: python database/run_nlp_pipeline.py")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error resetting failed jobs: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Reset failed jobs that were marked as processed but not inserted",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (see what would be reset)
  python scripts/reset_failed_jobs.py --dry-run
  
  # Actually reset failed jobs
  python scripts/reset_failed_jobs.py
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be reset without making changes'
    )
    
    args = parser.parse_args()
    
    try:
        reset_failed_jobs(dry_run=args.dry_run)
    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to reset jobs: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

