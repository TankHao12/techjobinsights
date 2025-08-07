"""
TechInsights  - Scraper Factory
Factory class for creating and managing different scrapers
"""

from typing import Dict, Type, Optional, Any
import logging

from .base_scraper import BaseScraper
from .seek_scraper import SeekScraper
from src.core.config import settings

logger = logging.getLogger(__name__)


class ScraperFactory:
    """Factory for creating and managing job scrapers."""
    
    # Registry of available scrapers
    _scrapers: Dict[str, Type[BaseScraper]] = {
        'seek': SeekScraper,
        # Future scrapers can be added here:
        # 'indeed': IndeedScraper,
        # 'trademe': TradeMeScraper,
        # 'linkedin': LinkedInScraper,
    }
    
    @classmethod
    def create_scraper(
        self, 
        source_name: str, 
        **kwargs
    ) -> BaseScraper:
        """
        Create a scraper instance for the specified source.
        
        Args:
            source_name: Name of the job source (e.g., 'seek', 'indeed')
            **kwargs: Additional configuration for the scraper
            
        Returns:
            BaseScraper: Configured scraper instance
            
        Raises:
            ValueError: If source is not supported
        """
        source_name = source_name.lower()
        
        if source_name not in self._scrapers:
            available = ', '.join(self._scrapers.keys())
            raise ValueError(f"Unsupported source '{source_name}'. Available: {available}")
        
        scraper_class = self._scrapers[source_name]
        
        # Get source-specific configuration from settings
        scraper_config = self._get_scraper_config(source_name)
        scraper_config.update(kwargs)
        
        logger.info(f"Creating {source_name} scraper with config: {scraper_config}")
        
        return scraper_class(**scraper_config)
    
    @classmethod
    def get_available_sources(cls) -> list[str]:
        """
        Get list of available scraper sources.
        
        Returns:
            list[str]: List of supported source names
        """
        return list(cls._scrapers.keys())
    
    @classmethod
    def register_scraper(cls, source_name: str, scraper_class: Type[BaseScraper]) -> None:
        """
        Register a new scraper class.
        
        Args:
            source_name: Name of the job source
            scraper_class: Scraper class to register
        """
        cls._scrapers[source_name.lower()] = scraper_class
        logger.info(f"Registered scraper for source: {source_name}")
    
    @classmethod
    def _get_scraper_config(cls, source_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific scraper from settings.
        
        Args:
            source_name: Name of the source
            
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        config = {}
        
        if source_name == 'seek':
            config.update({
                'rate_limit_per_hour': settings.SEEK_RATE_LIMIT,
                'timeout': settings.SCRAPING_TIMEOUT,
                'max_retries': settings.SCRAPING_RETRY_ATTEMPTS
            })
        elif source_name == 'indeed':
            config.update({
                'rate_limit_per_hour': settings.INDEED_RATE_LIMIT,
                'timeout': settings.SCRAPING_TIMEOUT,
                'max_retries': settings.SCRAPING_RETRY_ATTEMPTS
            })
        elif source_name == 'trademe':
            config.update({
                'rate_limit_per_hour': settings.TRADEME_RATE_LIMIT,
                'timeout': settings.SCRAPING_TIMEOUT,
                'max_retries': settings.SCRAPING_RETRY_ATTEMPTS
            })
        
        return config
    
    @classmethod
    def create_all_active_scrapers(cls) -> Dict[str, BaseScraper]:
        """
        Create scrapers for all active sources based on feature flags.
        
        Returns:
            Dict[str, BaseScraper]: Dictionary mapping source names to scraper instances
        """
        active_scrapers = {}
        
        # Check feature flags to determine which scrapers to create
        if settings.COLLECT_SEEK_JOBS:
            active_scrapers['seek'] = cls.create_scraper('seek')
        
        if settings.COLLECT_INDEED_JOBS:
            # active_scrapers['indeed'] = cls.create_scraper('indeed')
            logger.warning("Indeed scraper not yet implemented")
        
        if settings.COLLECT_TRADEME_JOBS:
            # active_scrapers['trademe'] = cls.create_scraper('trademe')
            logger.warning("TradeMe scraper not yet implemented")
        
        if settings.COLLECT_LINKEDIN_JOBS:
            # active_scrapers['linkedin'] = cls.create_scraper('linkedin')
            logger.warning("LinkedIn scraper not yet implemented")
        
        logger.info(f"Created {len(active_scrapers)} active scrapers: {list(active_scrapers.keys())}")
        return active_scrapers

