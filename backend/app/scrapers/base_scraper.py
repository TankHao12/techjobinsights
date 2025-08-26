"""
Abstract base scraper class for raw data collection
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Generator
import time
import random
import requests
from datetime import datetime
import logging

from ..core.config import settings
from ..core.logging import get_logger, PerformanceLogger

class BaseScraper(ABC):
    """Abstract base class for all scrapers"""

    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"scraper.{name}")
        self.session = self._create_session()
        self.processed_urls = set()

    def _create_session(self) -> requests.Session:
        """Create configured requests session"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        return session

    def rate_limit(self) -> None:
        """Intelligent rate limiting"""
        delay = random.uniform(
            settings.SCRAPING_DELAY_MIN,
            settings.SCRAPING_DELAY_MAX
        )
        time.sleep(delay)

    @abstractmethod
    def get_search_terms(self) -> List[str]:
        """Get list of search terms to scrape"""
        pass

    @abstractmethod
    def build_search_url(self, search_term: str, page: int) -> str:
        """Build search URL for given term and page"""
        pass

    @abstractmethod
    def extract_job_cards(self, html_content: str) -> List[Dict]:
        """Extract job cards from search page HTML"""
        pass

    @abstractmethod
    def extract_job_details(self, job_url: str) -> Dict:
        """Extract detailed job information from job page"""
        pass

    def scrape_search_page(self, search_term: str, page: int) -> List[Dict]:
        """Scrape a single search page"""
        url = self.build_search_url(search_term, page)

        try:
            with PerformanceLogger(self.logger, f"scraping page {page} for '{search_term}'"):
                response = self.session.get(url, timeout=settings.SCRAPING_TIMEOUT)
                response.raise_for_status()

                job_cards = self.extract_job_cards(response.text)
                self.logger.info(f"Found {len(job_cards)} job cards on page {page}")

                return job_cards

        except Exception as e:
            self.logger.error(f"Failed to scrape page {page} for '{search_term}': {e}")
            return []

    def scrape_job_details(self, job_card: Dict, search_term: str = None) -> Optional[Dict]:
        """Scrape detailed job information"""
        job_url = job_card.get('url')
        if not job_url or job_url in self.processed_urls:
            return None

        self.processed_urls.add(job_url)

        try:
            with PerformanceLogger(self.logger, f"scraping job details"):
                job_details = self.extract_job_details(job_url)

                # Combine card and detail data
                raw_job = {
                    **job_card,
                    **job_details,
                    'scraped_at': datetime.now(),
                    'scraper_name': self.name
                }
                
                # Add search term if provided
                if search_term:
                    raw_job['search_term'] = search_term

                return raw_job

        except Exception as e:
            self.logger.error(f"Failed to scrape job details from {job_url}: {e}")
            return None

    def scrape_search_term(
        self,
        search_term: str,
        max_pages: int = 10,
        max_consecutive_empty: int = 3
    ) -> Generator[Dict, None, None]:
        """Scrape all pages for a search term"""

        self.logger.info(f"Starting scrape for '{search_term}' (max {max_pages} pages)")

        consecutive_empty = 0

        for page in range(1, max_pages + 1):
            if consecutive_empty >= max_consecutive_empty:
                self.logger.info(f"Stopping after {consecutive_empty} consecutive empty pages")
                break

            job_cards = self.scrape_search_page(search_term, page)

            if not job_cards:
                consecutive_empty += 1
                continue
            else:
                consecutive_empty = 0

            # Process each job card
            for job_card in job_cards:
                self.rate_limit()

                raw_job = self.scrape_job_details(job_card, search_term)
                if raw_job:
                    yield raw_job

            self.logger.info(f"Completed page {page} for '{search_term}'")

    def scrape_all(self, max_pages_per_term: int = 10) -> Generator[Dict, None, None]:
        """Scrape all search terms"""

        search_terms = self.get_search_terms()
        self.logger.info(f"Starting full scrape: {len(search_terms)} terms x {max_pages_per_term} pages")

        for term_index, search_term in enumerate(search_terms, 1):
            self.logger.info(f"[{term_index}/{len(search_terms)}] Processing '{search_term}'")

            term_jobs = list(self.scrape_search_term(search_term, max_pages_per_term))
            self.logger.info(f"Collected {len(term_jobs)} jobs for '{search_term}'")

            for job in term_jobs:
                yield job

        self.logger.info(f"Scraping complete!")