#!/usr/bin/env python3
"""
STAGE 1: Raw Data Collection Script (FIXED for current app structure)
Bulk collection for initial data gathering
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from datetime import datetime
import argparse
from typing import Optional

from app.core.logging import get_logger
from app.database import SessionLocal, engine
from app.models import RawJob
from app.scrapers.seek_scraper import SeekScraper
from sqlalchemy import func

logger = get_logger(__name__)


class RawDataCollector:
    """Main coordinator for bulk raw data collection"""

    def __init__(self):
        self.scraper = SeekScraper()
        self.db = SessionLocal()
        self.total_collected = 0
        self.total_saved = 0
        self.duplicates_skipped = 0

    def save_job(self, job_data: dict) -> bool:
        """Save a job to database, handling duplicates"""
        try:
            # Check if exists
            existing = self.db.query(RawJob).filter(
                RawJob.url == job_data['url']
            ).first()

            if existing:
                self.duplicates_skipped += 1
                logger.debug(f"Job already exists: {job_data['title'][:50]}")
                return False

            # Create new job (including location)
            raw_job = RawJob(
                title=job_data['title'],
                company=job_data['company'],
                url=job_data['url'],
                full_description=job_data.get('full_description', ''),
                location=job_data.get('location', ''),  # Save scraped location
                posting_date=job_data.get('posting_date', ''),
                search_term=job_data['search_term'],
                scraped_at=datetime.now(),
                processing_version='v1.0-bulk',
                processed=False
            )

            self.db.add(raw_job)
            self.db.commit()
            logger.debug(f"✓ Saved: {job_data['title'][:50]}")
            return True

        except Exception as e:
            logger.error(f"Error saving job: {e}")
            self.db.rollback()
            return False

    def collect_raw_data(
        self,
        search_terms: Optional[list] = None,
        max_pages_per_term: int = 10,
        limit_per_term: Optional[int] = None
    ):
        """Collect raw job data from Seek (bulk collection)"""

        # Use provided search terms or get all from scraper
        terms_to_search = search_terms or self.scraper.get_search_terms()

        logger.info(f"Starting BULK collection for {len(terms_to_search)} search terms")
        logger.info(f"Max pages per term: {max_pages_per_term}")
        if limit_per_term:
            logger.info(f"Limit per term: {limit_per_term}")

        for term_index, search_term in enumerate(terms_to_search, 1):
            logger.info(f"\n[{term_index}/{len(terms_to_search)}] Collecting: '{search_term}'")

            term_count = 0
            jobs_batch = []

            # Collect jobs for this search term
            for page in range(1, max_pages_per_term + 1):
                logger.info(f"  Page {page}/{max_pages_per_term}...")

                # Get search page
                try:
                    url = self.scraper.build_search_url(search_term, page)
                    self.scraper.rate_limit()
                    response = self.scraper.session.get(url, timeout=30)
                    response.raise_for_status()

                    job_cards = self.scraper.extract_job_cards(response.text)

                    if not job_cards:
                        logger.info(f"    No jobs found on page {page}, stopping")
                        break

                    for job_card in job_cards:
                        if limit_per_term and term_count >= limit_per_term:
                            break

                        self.total_collected += 1
                        term_count += 1

                        # Get job URL
                        job_url = job_card.get('url')
                        if not job_url:
                            continue

                        # Get full job details
                        logger.debug(f"    Getting details for job #{term_count}")
                        self.scraper.rate_limit()
                        job_details = self.scraper.extract_job_details(job_url)

                        if job_details and job_details.get('extraction_success'):
                            # Prepare job data (including location from metadata)
                            raw_metadata = job_details.get('raw_metadata', {})
                            job_data = {
                                'title': job_card.get('title'),
                                'company': job_card.get('company'),
                                'url': job_url,
                                'full_description': job_details.get('full_description', ''),
                                'location': raw_metadata.get('location', ''),  # Save scraped location
                                'posting_date': job_card.get('card_posted_date', ''),
                                'search_term': search_term,
                            }

                            # Save immediately
                            if self.save_job(job_data):
                                self.total_saved += 1

                except Exception as e:
                    logger.error(f"  Error on page {page}: {e}")
                    continue

            logger.info(f"  Collected {term_count} jobs for '{search_term}'")

        # Print final statistics
        self.print_statistics()

    def print_statistics(self):
        """Print collection statistics"""
        logger.info("\n" + "=" * 60)
        logger.info("BULK COLLECTION STATISTICS:")
        logger.info(f"Total collected: {self.total_collected}")
        logger.info(f"Total saved: {self.total_saved}")
        logger.info(f"Duplicates skipped: {self.duplicates_skipped}")
        logger.info("=" * 60)

        # Get breakdown by search term
        term_counts = self.db.query(
            RawJob.search_term,
            func.count(RawJob.id).label('count')
        ).group_by(RawJob.search_term).all()

        if term_counts:
            logger.info("\nJobs by search term (top 10):")
            for term, count in sorted(term_counts, key=lambda x: x[1], reverse=True)[:10]:
                logger.info(f"  {term}: {count}")

    def cleanup(self):
        """Clean up resources"""
        if self.db:
            self.db.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Collect raw job data from Seek (Bulk Collection)')

    parser.add_argument(
        '--search-terms',
        nargs='+',
        help='Specific search terms to use (default: use all configured terms)'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=5,
        help='Maximum pages to scrape per search term (default: 5)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum jobs to collect per search term'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode - collect only 5 jobs per term'
    )

    args = parser.parse_args()

    logger.info("Raw Data Collection Starting (BULK MODE)")
    logger.info("=" * 60)

    # Test mode overrides
    if args.test:
        args.limit = 5
        args.max_pages = 1
        logger.info("TEST MODE: Limited to 5 jobs per term")

    # Create collector
    collector = RawDataCollector()

    try:
        # Run collection
        collector.collect_raw_data(
            search_terms=args.search_terms,
            max_pages_per_term=args.max_pages,
            limit_per_term=args.limit
        )

        logger.info("\nBulk collection completed successfully")

    except KeyboardInterrupt:
        logger.warning("\nCollection interrupted by user")
    except Exception as e:
        logger.error(f"Collection failed: {e}", exc_info=True)
    finally:
        collector.cleanup()


if __name__ == "__main__":
    main()