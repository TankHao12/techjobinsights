"""
TechInsights  - Web Scrapers
Multi-source job scraping modules
"""

from .base_scraper import BaseScraper, ScrapingResult, ScrapingError
from .seek_scraper import SeekScraper
from .scraper_factory import ScraperFactory

__all__ = [
    "BaseScraper",
    "ScrapingResult",
    "ScrapingError",
    "SeekScraper",
    "ScraperFactory"
]

