"""
TechInsights  - Seek NZ Scraper
Specialized scraper for Seek New Zealand job postings
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Iterator
from urllib.parse import urljoin, parse_qs, urlparse
import json
import logging
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, ScrapingResult, ScrapingError
from src.models.job import ExperienceLevel, EmploymentType, RemoteWorkOption

logger = logging.getLogger(__name__)


class SeekScraper(BaseScraper):
    """
    Scraper for Seek New Zealand job postings.
    
    Features:
    - Respects robots.txt and rate limits
    - Scrapes both job listings and detailed job pages
    - Handles pagination automatically
    - Extracts comprehensive job information
    - Built-in error handling and retry logic
    """
    
    # Seek NZ specific configuration
    SEEK_BASE_URL = "https://www.seek.co.nz"
    SEEK_SEARCH_URL = "https://www.seek.co.nz/jobs"
    SEEK_API_URL = "https://www.seek.co.nz/api/jobsearch/v5/search"
    
    # IT-related classification ID for Seek NZ
    IT_CLASSIFICATION_ID = "6281"  # Information & Communication Technology
    
    # Experience level mapping
    EXPERIENCE_LEVEL_MAP = {
        'entry': ExperienceLevel.ENTRY,
        'junior': ExperienceLevel.JUNIOR,
        'mid': ExperienceLevel.MID,
        'senior': ExperienceLevel.SENIOR,
        'lead': ExperienceLevel.LEAD,
        'principal': ExperienceLevel.PRINCIPAL,
        'executive': ExperienceLevel.EXECUTIVE,
        'graduate': ExperienceLevel.ENTRY,
        'intern': ExperienceLevel.ENTRY
    }
    
    # Employment type mapping
    EMPLOYMENT_TYPE_MAP = {
        'full time': EmploymentType.FULL_TIME,
        'part time': EmploymentType.PART_TIME,
        'contract': EmploymentType.CONTRACT,
        'temporary': EmploymentType.TEMPORARY,
        'casual': EmploymentType.CASUAL,
        'internship': EmploymentType.INTERNSHIP
    }
    
    def __init__(self, rate_limit_per_hour: int = 100, **kwargs):
        """
        Initialize Seek scraper.
        
        Args:
            rate_limit_per_hour: Requests per hour limit
            **kwargs: Additional scraper configuration
        """
        super().__init__(
            source_name="seek",
            base_url=self.SEEK_BASE_URL,
            rate_limit_per_hour=rate_limit_per_hour,
            **kwargs
        )
        
        # Seek-specific headers
        self.default_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-NZ,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
    
    async def scrape_jobs(
        self,
        max_pages: int = 10,
        keywords: Optional[str] = None,
        location: Optional[str] = None,
        include_job_details: bool = True,
        **kwargs
    ) -> ScrapingResult:
        """
        Scrape IT jobs from Seek NZ.
        
        Args:
            max_pages: Maximum number of pages to scrape
            keywords: Additional search keywords
            location: Location filter (e.g., "Auckland", "Wellington")
            include_job_details: Whether to fetch detailed job information
            **kwargs: Additional search parameters
            
        Returns:
            ScrapingResult: Comprehensive scraping results
        """
        result = ScrapingResult(success=False)
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting Seek NZ job scraping (max_pages={max_pages})")
            
            # Build search parameters
            search_params = self._build_search_params(
                keywords=keywords,
                location=location,
                **kwargs
            )
            
            jobs_data = []
            current_page = 1
            
            while current_page <= max_pages:
                try:
                    logger.info(f"Scraping page {current_page} of {max_pages}")
                    
                    # Update page parameter
                    search_params['page'] = current_page
                    
                    # Fetch job listings page
                    page_jobs = await self._scrape_jobs_page(search_params)
                    
                    if not page_jobs:
                        logger.info("No more jobs found, stopping pagination")
                        break
                    
                    result.jobs_found += len(page_jobs)
                    
                    # Process each job listing
                    for job_data in page_jobs:
                        try:
                            # Enhance with detailed information if requested
                            if include_job_details and job_data.get('job_url'):
                                detailed_data = await self.scrape_job_details(job_data['job_url'])
                                if detailed_data:
                                    job_data.update(detailed_data)
                            
                            # Validate and clean job data
                            if self.validate_job_data(job_data):
                                jobs_data.append(job_data)
                                result.jobs_processed += 1
                            else:
                                result.jobs_failed += 1
                                result.add_warning(f"Invalid job data for ID: {job_data.get('external_job_id')}")
                        
                        except Exception as e:
                            result.jobs_failed += 1
                            result.add_error(f"Error processing job: {e}")
                    
                    current_page += 1
                    
                    # Small delay between pages
                    await asyncio.sleep(1.0)
                    
                except Exception as e:
                    result.add_error(f"Error scraping page {current_page}: {e}")
                    break
            
            # Store results in metadata
            result.metadata = {
                'source': 'seek_nz',
                'search_params': search_params,
                'jobs_data': jobs_data,
                'pages_scraped': current_page - 1
            }
            
            result.success = result.jobs_processed > 0
            result.processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Seek scraping completed: {result.jobs_processed}/{result.jobs_found} jobs processed "
                f"in {result.processing_time:.1f}s"
            )
            
            return result
            
        except Exception as e:
            result.add_error(f"Fatal error during Seek scraping: {e}")
            result.processing_time = (datetime.now() - start_time).total_seconds()
            return result
    
    async def _scrape_jobs_page(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scrape a single page of job listings.
        
        Args:
            search_params: Search parameters for the API
            
        Returns:
            List[Dict[str, Any]]: List of job data dictionaries
        """
        try:
            # Try API endpoint first
            try:
                return await self._scrape_via_api(search_params)
            except Exception as api_error:
                logger.warning(f"API scraping failed: {api_error}. Falling back to HTML scraping.")
                return await self._scrape_via_html(search_params)
                
        except Exception as e:
            logger.error(f"Failed to scrape jobs page: {e}")
            return []
    
    async def _scrape_via_api(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scrape jobs using Seek's API endpoint.
        
        Args:
            search_params: API search parameters
            
        Returns:
            List[Dict[str, Any]]: List of job data
        """
        try:
            # Convert HTML search params to API params
            api_params = {
                'siteKey': 'NZ-Main',
                'sourcesystem': 'houston',
                'userqueryid': None,
                'userid': None,
                'usersessionid': None,
                'eventCaptureSessionId': None,
                'where': search_params.get('where', ''),
                'page': search_params.get('page', 1),
                'seekSelectAllPages': 'true',
                'classification': self.IT_CLASSIFICATION_ID,
                'pageSize': 22,  # Seek's default page size
            }
            
            if search_params.get('keywords'):
                api_params['keywords'] = search_params['keywords']
            
            headers = self.default_headers.copy()
            headers['Referer'] = self.SEEK_SEARCH_URL
            
            response_data = await self.get_json(
                self.SEEK_API_URL,
                params=api_params,
                headers=headers
            )
            
            jobs = []
            job_listings = response_data.get('data', {}).get('jobs', [])
            
            for job_item in job_listings:
                job_data = self._parse_api_job(job_item)
                if job_data:
                    jobs.append(job_data)
            
            logger.debug(f"Scraped {len(jobs)} jobs via API")
            return jobs
            
        except Exception as e:
            logger.error(f"API scraping error: {e}")
            raise
    
    async def _scrape_via_html(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scrape jobs by parsing HTML search results.
        
        Args:
            search_params: Search parameters
            
        Returns:
            List[Dict[str, Any]]: List of job data
        """
        try:
            # Build search URL
            search_url = self._build_search_url(search_params)
            
            html = await self.get_html(search_url)
            soup = BeautifulSoup(html, 'html.parser')
            
            jobs = []
            
            # Find job listing containers
            job_cards = soup.find_all('article', {'data-automation': 'normalJob'})
            
            for job_card in job_cards:
                job_data = self.parse_job_listing(job_card)
                if job_data:
                    jobs.append(job_data)
            
            logger.debug(f"Scraped {len(jobs)} jobs via HTML")
            return jobs
            
        except Exception as e:
            logger.error(f"HTML scraping error: {e}")
            raise
    
    def _parse_api_job(self, job_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse job data from API response.
        
        Args:
            job_item: Job item from API response
            
        Returns:
            Optional[Dict[str, Any]]: Parsed job data
        """
        try:
            job_id = job_item.get('id')
            if not job_id:
                return None
            
            # Basic job information
            job_data = {
                'external_job_id': str(job_id),
                'source_id': 1,  # Seek source ID (should be configurable)
                'title': self.clean_text(job_item.get('title', '')),
                'job_url': urljoin(self.SEEK_BASE_URL, f"/job/{job_id}"),
                'posted_date': self._parse_date(job_item.get('listingDate')),
                'location': self._extract_location(job_item.get('location', {})),
                'company_name': job_item.get('advertiser', {}).get('description', ''),
                'summary': self.clean_text(job_item.get('teaser', '')),
                'is_featured': job_item.get('isPremium', False),
                'raw_data': job_item
            }
            
            # Extract salary information
            salary_info = self._extract_salary_from_api(job_item)
            job_data.update(salary_info)
            
            # Extract employment type and work arrangement
            job_data.update(self._extract_employment_info_from_api(job_item))
            
            return job_data
            
        except Exception as e:
            logger.error(f"Error parsing API job: {e}")
            return None
    
    def parse_job_listing(self, job_element: Any) -> Optional[Dict[str, Any]]:
        """
        Parse job listing from HTML element.
        
        Args:
            job_element: BeautifulSoup job element
            
        Returns:
            Optional[Dict[str, Any]]: Parsed job data
        """
        try:
            # Extract job ID from data attributes or URL
            job_id = None
            job_link = job_element.find('a', {'data-automation': 'jobTitle'})
            
            if job_link and job_link.get('href'):
                href = job_link['href']
                job_id_match = re.search(r'/job/(\d+)', href)
                if job_id_match:
                    job_id = job_id_match.group(1)
            
            if not job_id:
                return None
            
            # Basic job information
            title_element = job_element.find('a', {'data-automation': 'jobTitle'})
            title = title_element.get_text(strip=True) if title_element else ""
            
            company_element = job_element.find('a', {'data-automation': 'jobCompany'})
            company_name = company_element.get_text(strip=True) if company_element else ""
            
            location_element = job_element.find('a', {'data-automation': 'jobLocation'})
            location = location_element.get_text(strip=True) if location_element else ""
            
            summary_element = job_element.find('span', {'data-automation': 'jobShortDescription'})
            summary = summary_element.get_text(strip=True) if summary_element else ""
            
            job_data = {
                'external_job_id': job_id,
                'source_id': 1,  # Seek source ID
                'title': self.clean_text(title),
                'company_name': self.clean_text(company_name),
                'location': self.clean_text(location),
                'summary': self.clean_text(summary),
                'job_url': urljoin(self.SEEK_BASE_URL, job_link['href']) if job_link else None,
                'posted_date': self._extract_posted_date(job_element),
                'is_featured': 'premium' in job_element.get('class', [])
            }
            
            # Extract salary if available
            salary_info = self._extract_salary_from_html(job_element)
            job_data.update(salary_info)
            
            return job_data
            
        except Exception as e:
            logger.error(f"Error parsing job listing: {e}")
            return None
    
    async def scrape_job_details(self, job_url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape detailed information from a job posting page.
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            Optional[Dict[str, Any]]: Detailed job information
        """
        try:
            html = await self.get_html(job_url)
            soup = BeautifulSoup(html, 'html.parser')
            
            details = {}
            
            # Extract full job description
            description_element = soup.find('div', {'data-automation': 'jobAdDetails'})
            if description_element:
                # Get raw HTML description
                details['description_raw'] = str(description_element)
                
                # Get cleaned text description
                description_text = description_element.get_text(separator=' ', strip=True)
                details['description_cleaned'] = self.clean_text(description_text)
                details['word_count'] = len(description_text.split())
            
            # Extract additional job metadata
            details.update(self._extract_job_metadata(soup))
            
            # Extract company information
            company_info = self._extract_company_info(soup)
            if company_info:
                details.update(company_info)
            
            # Extract application URL
            apply_button = soup.find('a', {'data-automation': 'job-detail-apply'})
            if apply_button and apply_button.get('href'):
                details['application_url'] = urljoin(self.SEEK_BASE_URL, apply_button['href'])
            
            return details
            
        except Exception as e:
            logger.error(f"Error scraping job details from {job_url}: {e}")
            return None
    
    def _build_search_params(
        self,
        keywords: Optional[str] = None,
        location: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build search parameters for Seek job search."""
        params = {
            'classification': self.IT_CLASSIFICATION_ID,
            'page': 1,
            'sortmode': 'ListedDate',  # Sort by newest first
            'where': location or 'All New Zealand'
        }
        
        if keywords:
            # Combine with IT-specific keywords
            it_keywords = f"{keywords} OR software OR developer OR programmer OR IT OR technology"
            params['keywords'] = it_keywords
        else:
            # Default IT-related keywords
            params['keywords'] = 'software OR developer OR programmer OR IT OR technology OR engineer'
        
        # Add any additional parameters
        params.update(kwargs)
        
        return params
    
    def _build_search_url(self, search_params: Dict[str, Any]) -> str:
        """Build search URL from parameters."""
        base_url = self.SEEK_SEARCH_URL
        
        # Convert params to query string
        query_parts = []
        for key, value in search_params.items():
            if value is not None:
                query_parts.append(f"{key}={value}")
        
        if query_parts:
            return f"{base_url}?{'&'.join(query_parts)}"
        
        return base_url
    
    def _parse_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_string:
            return None
        
        try:
            # Handle ISO format
            if 'T' in date_string:
                return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            
            # Handle relative dates
            if 'day' in date_string.lower():
                days_match = re.search(r'(\d+)', date_string)
                if days_match:
                    days_ago = int(days_match.group(1))
                    return datetime.now() - timedelta(days=days_ago)
            
            # Handle "today", "yesterday" etc.
            if 'today' in date_string.lower():
                return datetime.now()
            elif 'yesterday' in date_string.lower():
                return datetime.now() - timedelta(days=1)
            
        except Exception as e:
            logger.warning(f"Could not parse date '{date_string}': {e}")
        
        return None
    
    def _extract_location(self, location_data: Dict[str, Any]) -> str:
        """Extract location string from location data."""
        if isinstance(location_data, str):
            return location_data
        
        if isinstance(location_data, dict):
            area = location_data.get('area', '')
            suburb = location_data.get('suburb', '')
            
            if suburb and area:
                return f"{suburb}, {area}"
            elif area:
                return area
            elif suburb:
                return suburb
        
        return ""
    
    def _extract_salary_from_api(self, job_item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract salary information from API job item."""
        salary_info = {
            'salary_min': None,
            'salary_max': None,
            'salary_currency': 'NZD',
            'salary_period': 'annually'
        }
        
        salary_data = job_item.get('salary')
        if salary_data and isinstance(salary_data, dict):
            salary_info['salary_min'] = salary_data.get('min')
            salary_info['salary_max'] = salary_data.get('max')
            
            # Determine period from the salary text
            salary_text = salary_data.get('label', '').lower()
            if 'hour' in salary_text:
                salary_info['salary_period'] = 'hourly'
            elif 'day' in salary_text:
                salary_info['salary_period'] = 'daily'
            elif 'week' in salary_text:
                salary_info['salary_period'] = 'weekly'
            elif 'month' in salary_text:
                salary_info['salary_period'] = 'monthly'
        
        return salary_info
    
    def _extract_salary_from_html(self, job_element: Any) -> Dict[str, Any]:
        """Extract salary information from HTML job element."""
        salary_element = job_element.find('span', {'data-automation': 'jobSalary'})
        
        if salary_element:
            salary_text = salary_element.get_text(strip=True)
            salary_data = self.extract_salary_range(salary_text)
            salary_data['salary_currency'] = 'NZD'
            salary_data['salary_period'] = 'annually'  # Default for Seek NZ
            return salary_data
        
        return {'salary_min': None, 'salary_max': None, 'salary_currency': 'NZD'}
    
    def _extract_employment_info_from_api(self, job_item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract employment type and work arrangement from API data."""
        info = {}
        
        # Employment type
        work_type = job_item.get('workType', '').lower()
        if work_type in self.EMPLOYMENT_TYPE_MAP:
            info['employment_type'] = self.EMPLOYMENT_TYPE_MAP[work_type]
        
        # Remote work detection
        job_title = job_item.get('title', '').lower()
        job_summary = job_item.get('teaser', '').lower()
        
        if any(term in job_title + job_summary for term in ['remote', 'work from home', 'wfh']):
            info['is_remote_friendly'] = True
            if 'hybrid' in job_title + job_summary:
                info['remote_work_option'] = RemoteWorkOption.HYBRID
            else:
                info['remote_work_option'] = RemoteWorkOption.REMOTE
        
        return info
    
    def _extract_posted_date(self, job_element: Any) -> Optional[datetime]:
        """Extract posted date from job element."""
        date_element = job_element.find('span', {'data-automation': 'jobListingDate'})
        if date_element:
            date_text = date_element.get_text(strip=True)
            return self._parse_date(date_text)
        return None
    
    def _extract_job_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract additional metadata from job detail page."""
        metadata = {}
        
        # Look for structured data
        structured_data = soup.find('script', {'type': 'application/ld+json'})
        if structured_data:
            try:
                data = json.loads(structured_data.string)
                if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                    metadata.update(self._parse_structured_job_data(data))
            except json.JSONDecodeError:
                pass
        
        # Extract experience level from title or description
        title = soup.find('h1', {'data-automation': 'job-detail-title'})
        if title:
            title_text = title.get_text().lower()
            for keyword, level in self.EXPERIENCE_LEVEL_MAP.items():
                if keyword in title_text:
                    metadata['experience_level'] = level
                    break
        
        return metadata
    
    def _parse_structured_job_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse structured job data (JSON-LD)."""
        parsed = {}
        
        # Employment type
        employment_type = data.get('employmentType', '')
        if employment_type.lower() in self.EMPLOYMENT_TYPE_MAP:
            parsed['employment_type'] = self.EMPLOYMENT_TYPE_MAP[employment_type.lower()]
        
        # Date posted
        date_posted = data.get('datePosted')
        if date_posted:
            parsed['posted_date'] = self._parse_date(date_posted)
        
        # Valid through (expiry date)
        valid_through = data.get('validThrough')
        if valid_through:
            parsed['expires_date'] = self._parse_date(valid_through)
        
        # Salary information
        salary = data.get('baseSalary', {})
        if isinstance(salary, dict):
            value = salary.get('value', {})
            if isinstance(value, dict):
                parsed['salary_min'] = value.get('minValue')
                parsed['salary_max'] = value.get('maxValue')
                parsed['salary_currency'] = salary.get('currency', 'NZD')
        
        return parsed
    
    def _extract_company_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract company information from job page."""
        company_info = {}
        
        # Company name
        company_element = soup.find('span', {'data-automation': 'advertiser-name'})
        if company_element:
            company_info['company_name'] = self.clean_text(company_element.get_text())
        
        # Company description/profile link
        company_link = soup.find('a', {'data-automation': 'company-link'})
        if company_link and company_link.get('href'):
            company_info['company_url'] = urljoin(self.SEEK_BASE_URL, company_link['href'])
        
        return company_info

