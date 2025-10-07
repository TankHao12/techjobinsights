#!/usr/bin/env python3
"""
Incremental scraper for new jobs since last scrape
Designed to work with current app structure
"""

import sys
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Set

# Add backend directory to path (parent of database/)
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal, engine
from app.models import RawJob
from app.scrapers.seek_scraper import SeekScraper
from app.core.logging import get_logger
from sqlalchemy import func

logger = get_logger(__name__)

class IncrementalJobScraper:
    """Scrapes only new jobs posted since last scrape"""

    def __init__(self):
        self.scraper = SeekScraper()
        self.db = SessionLocal()
        self.existing_urls = set()
        self.last_scrape_date = None
        self.total_collected = 0
        self.total_saved = 0
        self.duplicates_skipped = 0

    def get_last_scrape_info(self):
        """Get information about last scraping activity"""
        try:
            # Get last scrape date
            latest_scrape = self.db.query(func.max(RawJob.scraped_at)).scalar()

            if latest_scrape:
                self.last_scrape_date = latest_scrape
                days_since = (datetime.now() - latest_scrape).days
                logger.info(f"Last scrape was on: {latest_scrape} ({days_since} days ago)")

                # Load existing URLs from last 7 days to avoid duplicates
                recent_jobs = self.db.query(RawJob.url).filter(
                    RawJob.scraped_at >= datetime.now() - timedelta(days=7)
                ).all()

                self.existing_urls = {job.url for job in recent_jobs}
                logger.info(f"Loaded {len(self.existing_urls)} existing job URLs from last 7 days")
            else:
                logger.info("No previous scraping found - will scrape all available jobs")

        except Exception as e:
            logger.error(f"Error getting scrape info: {e}")

    def is_recent_job(self, posted_text: str, days_threshold: int = None) -> bool:
        """
        Check if job was posted recently

        Args:
            posted_text: Text like 'Listed 2d ago', 'Listed today'
            days_threshold: Max days to consider as recent (default: days since last scrape + 1)
        """
        if not posted_text:
            return True  # Include if we can't determine

        # Calculate threshold based on last scrape
        if days_threshold is None:
            if self.last_scrape_date:
                days_threshold = (datetime.now() - self.last_scrape_date).days + 1
            else:
                days_threshold = 7  # Default to last week

        text = posted_text.lower()

        # Today/yesterday
        if any(word in text for word in ['today', 'yesterday', 'just posted', 'just now']):
            return True

        # Hours ago
        if 'hour' in text or 'h ago' in text or 'hr' in text:
            return True

        # Days ago
        days_match = re.search(r'(\d+)\s*d(?:ays?)?\s*ago', text)
        if days_match:
            days = int(days_match.group(1))
            return days <= days_threshold

        # Default to including it
        return True

    def scrape_search_page(self, search_term: str, page: int) -> List[Dict]:
        """Scrape a single search page and return job cards"""
        try:
            url = self.scraper.build_search_url(search_term, page)
            logger.debug(f"Scraping: {url}")

            self.scraper.rate_limit()
            response = self.scraper.session.get(url, timeout=30)
            response.raise_for_status()

            job_cards = self.scraper.extract_job_cards(response.text)
            return job_cards

        except Exception as e:
            logger.error(f"Error scraping page {page} for '{search_term}': {e}")
            return []

    def scrape_job_details(self, job_card: Dict, search_term: str) -> Dict:
        """Get full details for a job"""
        try:
            job_url = job_card.get('url')
            if not job_url:
                return None

            logger.debug(f"Getting details for: {job_url}")

            self.scraper.rate_limit()
            job_details = self.scraper.extract_job_details(job_url)

            if job_details and job_details.get('extraction_success'):
                # Extract location from metadata
                raw_metadata = job_details.get('raw_metadata', {})
                location = raw_metadata.get('location', '')
                
                # Also check card-level location as fallback
                if not location:
                    location = job_card.get('raw_location', '')

                # Get posted date - prefer detail page over card (more accurate)
                posting_date = raw_metadata.get('posted_date_text', '') or job_card.get('card_posted_date', '')

                return {
                    'title': job_card.get('title'),
                    'company': job_card.get('company'),
                    'url': job_url,
                    'full_description': job_details.get('full_description', ''),
                    'location': location,  # Save location separately for NLP processing
                    'posting_date': posting_date,  # Prefer detail page date over card date
                    'search_term': search_term,
                    'scraped_at': datetime.now(),
                    'processed': False,
                    'processing_version': None
                }
            return None

        except Exception as e:
            logger.error(f"Error getting job details: {e}")
            return None

    def save_job_to_database(self, job_data: Dict) -> bool:
        """Save a single job to the database"""
        try:
            # We've already checked for duplicates before calling this function
            # So we can proceed directly to saving

            # Create RawJob instance
            raw_job = RawJob(
                title=job_data['title'],
                company=job_data['company'],
                url=job_data['url'],
                full_description=job_data['full_description'],
                location=job_data.get('location', ''),  # Save scraped location
                posting_date=job_data['posting_date'],
                search_term=job_data['search_term'],
                scraped_at=job_data['scraped_at'],
                processed=False,
                processing_version=None
            )

            self.db.add(raw_job)
            self.db.commit()
            logger.info(f"✓ Saved new job: {job_data['title']} at {job_data['company']}")
            return True

        except Exception as e:
            logger.error(f"Error saving job: {e}")
            self.db.rollback()
            return False

    def run_incremental_scrape(
        self,
        search_terms: List[str] = None,
        max_pages_per_term: int = 5,
        stop_on_old_jobs: bool = True
    ):
        """
        Run incremental scraping for new jobs

        Args:
            search_terms: List of terms to search (default: use scraper's default)
            max_pages_per_term: Maximum pages to check per search term
            stop_on_old_jobs: Stop scraping a term when hitting old jobs
        """

        # Get last scrape info
        self.get_last_scrape_info()

        # Use provided terms or get all from scraper
        if not search_terms:
            # Get ALL search terms from the scraper for comprehensive coverage
            search_terms = self.scraper.get_search_terms()
            logger.info(f"Using all {len(search_terms)} configured search terms")

            # Or if you want to limit to specific high-priority terms for faster daily runs:
            # search_terms = [
            #     'software engineer',
            #     'software developer',
            #     'python developer',
            #     'full stack developer',
            #     'react developer',
            #     'data engineer',
            #     'devops engineer',
            #     'cloud engineer',
            #     'java developer',
            #     '.net developer'
            # ]

        logger.info("=" * 60)
        logger.info("STARTING INCREMENTAL SCRAPE")
        logger.info(f"Search terms: {len(search_terms)}")
        logger.info(f"Max pages per term: {max_pages_per_term}")
        logger.info(f"Stop on old jobs: {stop_on_old_jobs}")
        logger.info("=" * 60)

        for term_idx, search_term in enumerate(search_terms, 1):
            logger.info(f"\n[{term_idx}/{len(search_terms)}] Searching: '{search_term}'")

            term_new_jobs = 0
            consecutive_old_pages = 0

            for page in range(1, max_pages_per_term + 1):
                logger.info(f"  Page {page}...")

                # Get job cards from this page
                job_cards = self.scrape_search_page(search_term, page)

                if not job_cards:
                    logger.warning(f"  No jobs found on page {page}")
                    break

                page_new_jobs = 0
                page_old_jobs = 0

                for job_card in job_cards:
                    self.total_collected += 1

                    job_url = job_card.get('url')

                    # Skip if we've seen this job before
                    if job_url in self.existing_urls:
                        self.duplicates_skipped += 1
                        page_old_jobs += 1
                        continue

                    # Check if job is recent
                    posted_date = job_card.get('card_posted_date', '')
                    if not self.is_recent_job(posted_date):
                        page_old_jobs += 1
                        if stop_on_old_jobs:
                            continue

                    # Check if job already exists in database BEFORE fetching details
                    # This saves time by not fetching details for duplicates
                    from app.models import RawJob
                    existing_job = self.db.query(RawJob).filter(RawJob.url == job_url).first()
                    if existing_job:
                        self.duplicates_skipped += 1
                        page_old_jobs += 1
                        self.existing_urls.add(job_url)  # Add to cache for future checks
                        logger.debug(f"  Job already in DB, skipping: {job_card.get('title', '')[:50]}")
                        continue

                    # Get full job details only for truly new jobs
                    logger.info(f"  Fetching NEW job: {job_card.get('title', '')[:50]}")
                    job_details = self.scrape_job_details(job_card, search_term)

                    if job_details:
                        # Save to database
                        if self.save_job_to_database(job_details):
                            self.total_saved += 1
                            term_new_jobs += 1
                            page_new_jobs += 1
                            self.existing_urls.add(job_url)
                        else:
                            # This shouldn't happen now since we check above
                            self.duplicates_skipped += 1
                            self.existing_urls.add(job_url)

                logger.info(f"    Found {page_new_jobs} new jobs, {page_old_jobs} old/duplicate jobs")

                # Check if we should stop (hitting too many old jobs)
                if stop_on_old_jobs and page_new_jobs == 0:
                    consecutive_old_pages += 1
                    if consecutive_old_pages >= 2:
                        logger.info(f"  No new jobs for 2 consecutive pages, moving to next term")
                        break
                else:
                    consecutive_old_pages = 0

            logger.info(f"  Total new jobs for '{search_term}': {term_new_jobs}")

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print scraping summary"""
        logger.info("\n" + "=" * 60)
        logger.info("INCREMENTAL SCRAPE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total job cards checked: {self.total_collected}")
        logger.info(f"New jobs saved: {self.total_saved}")
        logger.info(f"Duplicates skipped: {self.duplicates_skipped}")
        logger.info(f"Other jobs skipped: {self.total_collected - self.total_saved - self.duplicates_skipped}")

        if self.last_scrape_date:
            days_covered = (datetime.now() - self.last_scrape_date).days
            logger.info(f"Days covered: {days_covered}")
            if days_covered > 0:
                logger.info(f"Average new jobs per day: {self.total_saved / days_covered:.1f}")

    def cleanup(self):
        """Clean up resources"""
        if self.db:
            self.db.close()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Incremental job scraper')
    parser.add_argument('--terms', nargs='+', help='Search terms to use')
    parser.add_argument('--pages', type=int, default=5, help='Max pages per term')
    parser.add_argument('--no-stop', action='store_true', help="Don't stop on old jobs")

    args = parser.parse_args()

    scraper = IncrementalJobScraper()

    try:
        scraper.run_incremental_scrape(
            search_terms=args.terms,
            max_pages_per_term=args.pages,
            stop_on_old_jobs=not args.no_stop
        )

        logger.info("\nIncremental scrape completed successfully!")

    except KeyboardInterrupt:
        logger.warning("\nScraping interrupted by user")

    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)

    finally:
        scraper.cleanup()


if __name__ == "__main__":
    main()