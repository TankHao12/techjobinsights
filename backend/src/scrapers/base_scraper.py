"""
TechInsights  - Base Scraper
Abstract base class for all job scrapers with common functionality
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Iterator, Union
from datetime import datetime, timedelta
import asyncio
import aiohttp
import logging
import time
import random
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


@dataclass
class ScrapingResult:
    """Result container for scraping operations."""
    
    success: bool
    jobs_found: int = 0
    jobs_processed: int = 0
    jobs_created: int = 0
    jobs_updated: int = 0
    jobs_failed: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.jobs_found == 0:
            return 0.0
        return (self.jobs_processed / self.jobs_found) * 100.0
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        logger.error(f"Scraping error: {error}")
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
        logger.warning(f"Scraping warning: {warning}")


class ScrapingError(Exception):
    """Custom exception for scraping errors."""
    
    def __init__(self, message: str, error_code: str = "SCRAPING_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now()


class RateLimiter:
    """Rate limiter to control request frequency."""
    
    def __init__(self, requests_per_hour: int = 100):
        self.requests_per_hour = requests_per_hour
        self.request_interval = 3600 / requests_per_hour  # seconds between requests
        self.last_request_time = 0.0
        self.request_count = 0
        self.hour_start = time.time()
    
    async def wait_if_needed(self) -> None:
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        
        # Reset counter if an hour has passed
        if current_time - self.hour_start >= 3600:
            self.request_count = 0
            self.hour_start = current_time
        
        # Check if we've exceeded hourly limit
        if self.request_count >= self.requests_per_hour:
            wait_time = 3600 - (current_time - self.hour_start)
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
                await asyncio.sleep(wait_time)
                self.request_count = 0
                self.hour_start = time.time()
        
        # Ensure minimum interval between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_interval:
            wait_time = self.request_interval - time_since_last
            # Add small random delay to avoid being too predictable
            wait_time += random.uniform(0.1, 0.5)
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
        self.request_count += 1


class BaseScraper(ABC):
    """
    Abstract base class for all job scrapers.
    
    Provides common functionality like rate limiting, error handling,
    session management, and data validation.
    """
    
    def __init__(
        self,
        source_name: str,
        base_url: str,
        rate_limit_per_hour: int = 100,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the base scraper.
        
        Args:
            source_name: Name of the data source
            base_url: Base URL for the job site
            rate_limit_per_hour: Maximum requests per hour
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.source_name = source_name
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Rate limiting
        self.rate_limiter = RateLimiter(rate_limit_per_hour)
        
        # User agent rotation
        self.ua = UserAgent()
        
        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Statistics
        self.stats = {
            'requests_made': 0,
            'requests_failed': 0,
            'jobs_scraped': 0,
            'errors_encountered': 0,
            'start_time': None,
            'end_time': None
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def initialize(self) -> None:
        """Initialize the scraper and HTTP session."""
        if self.session is None:
            connector = aiohttp.TCPConnector(
                limit=10,  # Connection pool limit
                limit_per_host=5,
                ttl_dns_cache=300,
                ttl_connection_pool=300
            )
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'User-Agent': self.ua.random}
            )
        
        self.stats['start_time'] = time.time()
        logger.info(f"Initialized {self.source_name} scraper")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None
        
        self.stats['end_time'] = time.time()
        logger.info(f"Cleaned up {self.source_name} scraper")
    
    async def make_request(
        self,
        url: str,
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> aiohttp.ClientResponse:
        """
        Make an HTTP request with rate limiting and retry logic.
        
        Args:
            url: URL to request
            method: HTTP method
            params: Query parameters
            data: Request body data
            headers: Additional headers
            
        Returns:
            aiohttp.ClientResponse: HTTP response
            
        Raises:
            ScrapingError: If request fails after all retries
        """
        if not self.session:
            raise ScrapingError("Scraper not initialized. Use async context manager.")
        
        # Apply rate limiting
        await self.rate_limiter.wait_if_needed()
        
        # Prepare headers
        request_headers = {'User-Agent': self.ua.random}
        if headers:
            request_headers.update(headers)
        
        # Convert relative URLs to absolute
        if not url.startswith(('http://', 'https://')):
            url = urljoin(self.base_url, url)
        
        # Retry logic
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                self.stats['requests_made'] += 1
                
                async with self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    headers=request_headers
                ) as response:
                    
                    # Check for rate limiting response
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limited by server. Waiting {retry_after} seconds...")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    # Raise for HTTP errors
                    response.raise_for_status()
                    
                    logger.debug(f"Successfully requested {url} (attempt {attempt + 1})")
                    return response
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                self.stats['requests_failed'] += 1
                
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Request failed (attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {self.max_retries + 1} attempts: {e}")
        
        # All retries exhausted
        raise ScrapingError(
            f"Failed to request {url} after {self.max_retries + 1} attempts: {last_exception}",
            error_code="REQUEST_FAILED",
            details={'url': url, 'last_exception': str(last_exception)}
        )
    
    async def get_html(self, url: str, **kwargs) -> str:
        """
        Get HTML content from a URL.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for make_request
            
        Returns:
            str: HTML content
        """
        response = await self.make_request(url, **kwargs)
        html = await response.text()
        return html
    
    async def get_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Get JSON content from a URL.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for make_request
            
        Returns:
            Dict[str, Any]: JSON data
        """
        response = await self.make_request(url, **kwargs)
        json_data = await response.json()
        return json_data
    
    def validate_job_data(self, job_data: Dict[str, Any]) -> bool:
        """
        Validate scraped job data.
        
        Args:
            job_data: Raw job data dictionary
            
        Returns:
            bool: True if data is valid
        """
        required_fields = ['external_job_id', 'title', 'source_id']
        
        for field in required_fields:
            if not job_data.get(field):
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate title length
        title = job_data.get('title', '')
        if len(title) < 3 or len(title) > 500:
            logger.warning(f"Invalid title length: {len(title)}")
            return False
        
        return True
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove common HTML entities
        text = (text.replace('&nbsp;', ' ')
                   .replace('&amp;', '&')
                   .replace('&lt;', '<')
                   .replace('&gt;', '>')
                   .replace('&quot;', '"')
                   .replace('&#39;', "'"))
        
        return text.strip()
    
    def extract_salary_range(self, salary_text: str) -> Dict[str, Optional[float]]:
        """
        Extract salary range from text.
        
        Args:
            salary_text: Raw salary text
            
        Returns:
            Dict[str, Optional[float]]: Salary min/max values
        """
        import re
        
        if not salary_text:
            return {'salary_min': None, 'salary_max': None}
        
        # Remove common prefixes and clean up
        salary_text = re.sub(r'^\$?\s*', '', salary_text.lower())
        salary_text = re.sub(r'[,\s]+', '', salary_text)
        
        # Pattern for salary ranges
        range_pattern = r'(\d+)(?:k)?(?:\s*-\s*|\s+to\s+)(\d+)(?:k)?'
        single_pattern = r'(\d+)(?:k)?'
        
        range_match = re.search(range_pattern, salary_text)
        if range_match:
            min_val = float(range_match.group(1))
            max_val = float(range_match.group(2))
            
            # Handle 'k' suffix (thousands)
            if 'k' in salary_text:
                min_val *= 1000
                max_val *= 1000
            
            return {'salary_min': min_val, 'salary_max': max_val}
        
        single_match = re.search(single_pattern, salary_text)
        if single_match:
            value = float(single_match.group(1))
            if 'k' in salary_text:
                value *= 1000
            
            return {'salary_min': value, 'salary_max': value}
        
        return {'salary_min': None, 'salary_max': None}
    
    # ========================================================================
    # ABSTRACT METHODS - Must be implemented by subclasses
    # ========================================================================
    
    @abstractmethod
    async def scrape_jobs(
        self,
        max_pages: int = 10,
        keywords: Optional[str] = None,
        location: Optional[str] = None,
        **kwargs
    ) -> ScrapingResult:
        """
        Scrape jobs from the source.
        
        Args:
            max_pages: Maximum number of pages to scrape
            keywords: Search keywords
            location: Location filter
            **kwargs: Additional scraping parameters
            
        Returns:
            ScrapingResult: Scraping results and metadata
        """
        pass
    
    @abstractmethod
    async def scrape_job_details(self, job_url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape detailed information for a specific job.
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            Optional[Dict[str, Any]]: Detailed job data or None if failed
        """
        pass
    
    @abstractmethod
    def parse_job_listing(self, job_element: Any) -> Optional[Dict[str, Any]]:
        """
        Parse a job listing from HTML element or JSON data.
        
        Args:
            job_element: Job listing element/data
            
        Returns:
            Optional[Dict[str, Any]]: Parsed job data or None if failed
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get scraping statistics.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        stats = self.stats.copy()
        
        if stats['start_time'] and stats['end_time']:
            stats['total_time'] = stats['end_time'] - stats['start_time']
        
        if stats['requests_made'] > 0:
            stats['success_rate'] = (
                (stats['requests_made'] - stats['requests_failed']) / stats['requests_made'] * 100
            )
        
        return stats

