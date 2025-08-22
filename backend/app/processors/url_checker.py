"""
URL Checker Utility for NLP Pipeline

This module provides URL accessibility checking functionality that can be
integrated into the data processing pipeline to automatically set is_active
status based on URL availability.
"""

import requests
from typing import Tuple, Optional
from urllib.parse import urlparse
import time
from ..core.logging import get_logger

logger = get_logger(__name__)


class URLChecker:
    """Utility class for checking URL accessibility"""
    
    def __init__(self, timeout: int = 10, max_retries: int = 2):
        """
        Initialize URL checker.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Configure session with headers to avoid bot detection
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def check_url_accessibility(self, url: str) -> Tuple[bool, str, Optional[int]]:
        """
        Check if a URL is accessible and should be marked as active.
        
        Args:
            url: The URL to check
            
        Returns:
            Tuple of (is_accessible, status_message, status_code)
        """
        if not url or not url.strip():
            return False, "Empty URL", None
            
        url = url.strip()
        
        # Validate URL format
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Invalid URL format", None
        except Exception as e:
            return False, f"URL parsing error: {str(e)[:50]}", None
        
        # Try checking the URL with retries
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Checking URL (attempt {attempt + 1}): {url}")
                
                # Use HEAD request first (faster and less bandwidth)
                response = self.session.head(
                    url, 
                    timeout=self.timeout, 
                    allow_redirects=True
                )
                
                return self._evaluate_response(response, url)
                
            except requests.exceptions.Timeout:
                if attempt == self.max_retries:
                    logger.warning(f"URL timeout after {self.max_retries + 1} attempts: {url}")
                    return True, "Timeout - keeping active", None
                time.sleep(1)  # Brief delay before retry
                
            except requests.exceptions.ConnectionError:
                if attempt == self.max_retries:
                    logger.warning(f"Connection error after {self.max_retries + 1} attempts: {url}")
                    return True, "Connection error - keeping active", None
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries:
                    logger.warning(f"Request error after {self.max_retries + 1} attempts for {url}: {e}")
                    return True, f"Request error - keeping active: {str(e)[:50]}", None
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Unexpected error checking {url}: {e}")
                return True, f"Error - keeping active: {str(e)[:50]}", None
        
        return True, "Max retries exceeded - keeping active", None
    
    def _evaluate_response(self, response: requests.Response, original_url: str) -> Tuple[bool, str, int]:
        """
        Evaluate HTTP response to determine if URL should be considered active.
        
        Args:
            response: HTTP response object
            original_url: Original URL that was checked
            
        Returns:
            Tuple of (is_active, status_message, status_code)
        """
        status_code = response.status_code
        
        # Success codes
        if status_code == 200:
            return True, "Active (200 OK)", status_code
        
        # Client error codes that indicate inactive job
        if status_code == 404:
            return False, "Not Found (404)", status_code
        elif status_code == 403:
            return False, "Forbidden (403)", status_code
        elif status_code in [410, 451]:  # Gone, Unavailable for Legal Reasons
            return False, f"Gone ({status_code})", status_code
        
        # Redirect codes - need to check if it's a valid redirect
        elif 300 <= status_code < 400:
            try:
                # Check final destination after redirects
                final_response = self.session.get(
                    original_url, 
                    timeout=self.timeout, 
                    allow_redirects=True
                )
                
                if final_response.status_code == 200:
                    # Check if redirected to a generic page (common for expired jobs)
                    if self._is_generic_redirect(final_response.url, original_url):
                        return False, f"Redirected to generic page ({final_response.url})", status_code
                    return True, f"Active after redirect ({status_code} -> 200)", status_code
                else:
                    return False, f"Redirect failed ({status_code} -> {final_response.status_code})", status_code
                    
            except Exception as e:
                logger.warning(f"Error following redirect for {original_url}: {e}")
                return True, f"Redirect check failed - keeping active ({status_code})", status_code
        
        # Server error codes - assume temporarily unavailable, keep active
        elif 500 <= status_code < 600:
            return True, f"Server error - keeping active ({status_code})", status_code
        
        # Other status codes
        else:
            return False, f"Unexpected status ({status_code})", status_code
    
    def _is_generic_redirect(self, final_url: str, original_url: str) -> bool:
        """
        Check if the final URL appears to be a generic redirect (indicating expired job).
        
        Common patterns for expired job redirects:
        - Redirected to homepage
        - Redirected to search page
        - Redirected to "job not found" page
        """
        try:
            original_domain = urlparse(original_url).netloc.lower()
            final_domain = urlparse(final_url).netloc.lower()
            final_path = urlparse(final_url).path.lower()
            
            # Different domain redirect (suspicious)
            if original_domain != final_domain:
                return True
            
            # Common generic page patterns
            generic_patterns = [
                '/',  # Homepage
                '/jobs',  # Jobs listing
                '/search',  # Search page
                '/not-found',  # Not found page
                '/error',  # Error page
                '/expired',  # Expired page
            ]
            
            # Check if redirected to a generic page
            for pattern in generic_patterns:
                if final_path == pattern or final_path.startswith(pattern + '?'):
                    return True
            
            # If final URL is significantly shorter than original, likely generic
            if len(final_url) < len(original_url) * 0.7:
                return True
                
            return False
            
        except Exception as e:
            logger.warning(f"Error checking generic redirect: {e}")
            return False  # If we can't determine, assume it's valid
    
    def close(self):
        """Close the session"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def check_single_url(url: str, timeout: int = 10) -> Tuple[bool, str, Optional[int]]:
    """
    Convenience function to check a single URL.
    
    Args:
        url: URL to check
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (is_accessible, status_message, status_code)
    """
    with URLChecker(timeout=timeout) as checker:
        return checker.check_url_accessibility(url)







