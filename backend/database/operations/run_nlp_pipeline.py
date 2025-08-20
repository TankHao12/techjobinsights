#!/usr/bin/env python3
"""
Run NLP pipeline on unprocessed jobs - Simplified Version

This script uses the integrated DataProcessingPipeline with simplified schema:
- Batch processing
- Statistics tracking
- Error handling
- Posted date passed directly from raw_jobs
- Single extracted_skills JSONB field (no required/preferred split)
- Enum types for employment_type, experience_level, work_arrangement
"""

import sys
import os

# Add backend directory to path (parent of database/)
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.processors.data_pipeline import DataProcessingPipeline
from app.core.logging import get_logger

logger = get_logger(__name__)


def main():
    """Main entry point - optimized for newly scraped data"""
    
    logger.info("=" * 60)
    logger.info("STARTING NLP PIPELINE PROCESSING")
    logger.info("Processing newly scraped jobs (URL checking disabled - not needed)")
    logger.info("=" * 60)

    # Initialize the pipeline
    pipeline = DataProcessingPipeline()

    try:
        # Show current status
        status = pipeline.get_processing_status()
        logger.info("\nCurrent Status:")
        logger.info(f"  Raw jobs: {status['raw_jobs']['unprocessed']} unprocessed / {status['raw_jobs']['total']} total")
        logger.info(f"  Processed jobs: {status['processed_jobs']['total']}")
        logger.info(f"  Tech jobs: {status['processed_jobs']['tech_jobs']} ({status['processed_jobs']['tech_job_rate']}%)")
        logger.info(f"  Pipeline version: {status['pipeline_version']}")
        logger.info("")

        if status['raw_jobs']['unprocessed'] == 0:
            logger.info("No unprocessed jobs to process")
            return

        # Process unprocessed jobs
        logger.info(f"Processing {status['raw_jobs']['unprocessed']} unprocessed jobs...")
        stats = pipeline.process_unprocessed_jobs()

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("NLP PIPELINE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Processed: {stats.processed_jobs}/{stats.total_jobs} jobs")
        logger.info(f"Tech jobs found: {stats.tech_jobs_found}")
        logger.info(f"Jobs with salary: {stats.jobs_with_salary}")
        logger.info(f"Jobs with skills: {stats.jobs_with_skills}")
        
        # URL checking statistics
        if stats.urls_checked > 0:
            logger.info(f"URLs checked: {stats.urls_checked}")
            logger.info(f"URLs accessible: {stats.urls_accessible}")
            logger.info(f"URLs inaccessible: {stats.urls_inaccessible}")
            if stats.url_check_errors > 0:
                logger.info(f"URL check errors: {stats.url_check_errors}")
        
        logger.info(f"Average time per job: {stats.avg_processing_time:.2f}s")
        
        if stats.errors:
            logger.warning(f"Errors encountered: {len(stats.errors)}")
            for error in stats.errors[:5]:  # Show first 5 errors
                logger.warning(f"  - {error}")
        
        logger.info("\nNLP pipeline completed successfully!")

    except KeyboardInterrupt:
        logger.warning("\nProcessing interrupted by user")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
