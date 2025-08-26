"""
Seek.co.nz scraper implementation - optimized for speed (1 sec/job)
"""
from typing import Dict, List
from bs4 import BeautifulSoup
import re
from datetime import datetime

from .base_scraper import BaseScraper
from ..core.logging import get_logger

logger = get_logger(__name__)

class SeekScraper(BaseScraper):
    """Optimized Seek.co.nz scraper for raw data collection"""

    def __init__(self):
        super().__init__("seek_nz")
        self.base_url = "https://www.seek.co.nz"

    def get_search_terms(self) -> List[str]:
        """Comprehensive tech search terms"""
        return [
            # Core development roles
            'software engineer', 'software developer', 'full stack developer',
            'python developer', 'javascript developer', 'web developer',
            'react developer', 'java developer', 'c# developer', '.net developer',
            'node developer', 'angular developer', 'vue developer',

            # Specialized roles
            'data scientist', 'data engineer', 'data analyst',
            'devops engineer', 'cloud engineer', 'platform engineer',
            'mobile developer', 'ios developer', 'android developer',
            'qa engineer', 'test engineer', 'automation engineer',

            # Leadership and architecture
            'technical lead', 'tech lead', 'solution architect', 'software architect',
            'engineering manager', 'product manager',

            # Emerging tech
            'ai engineer', 'machine learning engineer', 'ml engineer',
            'blockchain developer', 'cybersecurity engineer',
            'embedded software engineer', 'firmware engineer'
        ]

    def build_search_url(self, search_term: str, page: int) -> str:
        """Build Seek search URL"""
        encoded_term = search_term.replace(' ', '%20')
        return f"{self.base_url}/jobs?keywords={encoded_term}&where=New%20Zealand&page={page}"

    def extract_job_cards(self, html_content: str) -> List[Dict]:
        """Extract ALL job cards (normal + premium) from search page"""

        soup = BeautifulSoup(html_content, 'html.parser')

        # Get BOTH normal and premium job cards (captures all 22 jobs)
        normal_jobs = soup.find_all('article', attrs={'data-automation': 'normalJob'})
        premium_jobs = soup.find_all('article', attrs={'data-automation': 'premiumJob'})
        job_cards = normal_jobs + premium_jobs

        cards = []

        for position, card in enumerate(job_cards, 1):
            try:
                # Extract basic card information
                title_elem = card.find('a', attrs={'data-automation': 'jobTitle'})
                if not title_elem:
                    continue

                title = self._clean_text(title_elem.get_text(strip=True))
                job_url = title_elem.get('href')
                if job_url and not job_url.startswith('http'):
                    job_url = self.base_url + job_url

                # Company
                company_elem = card.find('a', attrs={'data-automation': 'jobCompany'})
                company = self._clean_text(company_elem.get_text(strip=True)) if company_elem else 'Unknown'

                # Card summary/description
                summary_elem = card.find('span', attrs={'data-automation': 'jobShortDescription'})
                card_summary = self._clean_text(summary_elem.get_text(strip=True)) if summary_elem else ''

                # Card type
                card_type = card.get('data-automation', 'unknown')

                # Raw location (from card)
                location_elem = card.find('a', attrs={'data-automation': 'jobLocation'}) or \
                              card.find('span', attrs={'data-automation': 'jobLocation'})
                raw_location = self._clean_text(location_elem.get_text(strip=True)) if location_elem else ''

                # Raw salary (from card if available)
                salary_elem = card.find('span', attrs={'data-automation': 'jobSalary'})
                raw_salary = self._clean_text(salary_elem.get_text(strip=True)) if salary_elem else ''

                # Posted date - updated selectors for current Seek.co.nz structure
                posted_date = ''

                # Look for date text patterns in the card
                card_text = card.get_text()
                
                # Enhanced patterns to match current Seek date formats
                date_patterns = [
                    r'Listed\s+(twenty|thirty|forty|fifty|sixty)\s+(one|two|three|four|five|six|seven|eight|nine)\s+hours?\s+ago',
                    r'Listed\s+(\d+)\s*hours?\s*ago',
                    r'Listed\s+(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|twenty\s+one|twenty\s+two|twenty\s+three|twenty\s+four|twenty\s+five)\s+days?\s*ago',
                    r'Listed\s+(\d+)\s*days?\s*ago',
                    r'Listed\s+(one|two|three|four)\s+weeks?\s*ago',
                    r'Listed\s+(\d+)\s*weeks?\s*ago',
                    r'Listed\s+(one|two|three|four|five|six)\s+months?\s*ago',
                    r'Listed\s+(\d+)\s*months?\s*ago',
                    r'Listed\s+today',
                    r'Listed\s+yesterday',
                    r'just\s+posted',
                    r'\d+h\s+ago',
                    r'\d+d\s+ago',
                    r'\d+w\s+ago',
                    r'\d+m\s+ago'
                ]
                
                for pattern in date_patterns:
                    matches = re.findall(pattern, card_text, re.IGNORECASE)
                    if matches:
                        # Get the full match including the pattern
                        full_matches = re.findall(pattern.replace(r'\s+', r'\s+'), card_text, re.IGNORECASE)
                        if full_matches:
                            posted_date = full_matches[0] if isinstance(full_matches[0], str) else ' '.join(full_matches[0])
                            break
                
                # If no pattern matched, try broader search
                if not posted_date:
                    broader_matches = re.findall(r'(?:Listed\s+)?(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty)\s*(?:hours?|days?|weeks?|months?)\s*ago|today|yesterday|just\s*posted|\d+[hdwm]\s*ago', card_text, re.IGNORECASE)
                    if broader_matches:
                        posted_date = broader_matches[0]

                card_data = {
                    'title': title,
                    'company': company,
                    'card_summary': card_summary,
                    'url': job_url,
                    'card_type': card_type,
                    'card_position': position,
                    'raw_location_text': raw_location,
                    'raw_salary_text': raw_salary,
                    'card_posted_date': posted_date
                }

                cards.append(card_data)

            except Exception as e:
                self.logger.warning(f"Failed to extract card data: {e}")
                continue

        return cards

    def extract_job_details(self, job_url: str) -> Dict:
        """Extract detailed job information - optimized for speed"""

        start_time = datetime.now()

        try:
            response = self.session.get(job_url, timeout=20)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract full job description (primary content)
            full_description = self._extract_full_description(soup)

            # Extract additional metadata with fallbacks
            raw_metadata = self._extract_raw_metadata(soup)

            # Calculate processing metrics
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            return {
                'full_description': full_description,
                'raw_metadata': raw_metadata,
                'html_size_bytes': len(response.content),
                'extraction_success': True,
                'scraping_duration_ms': duration_ms
            }

        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.logger.error(f"Failed to extract job details from {job_url}: {e}")

            return {
                'full_description': '',
                'raw_metadata': {},
                'html_size_bytes': 0,
                'extraction_success': False,
                'scraping_duration_ms': duration_ms,
                'extraction_errors': {'error': str(e)}
            }

    def _extract_full_description(self, soup: BeautifulSoup) -> str:
        """Extract the complete job description"""

        # Try multiple selectors for job description
        description_selectors = [
            '[data-automation="jobAdDetails"]',
            '[data-automation="jobDescription"]',
            '.job-description',
            '[data-testid="job-details-content"]'
        ]

        for selector in description_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                # Get text with line breaks preserved
                text = desc_elem.get_text(separator='\n', strip=True)
                return self._clean_text(text)

        # Fallback: get the largest text block
        all_text_elements = soup.find_all(['p', 'div', 'span'],
                                        text=True,
                                        string=lambda text: text and len(text.strip()) > 50)

        if all_text_elements:
            longest = max(all_text_elements, key=lambda x: len(x.get_text()))
            return self._clean_text(longest.get_text(strip=True))

        return ''

    def _extract_raw_metadata(self, soup: BeautifulSoup) -> Dict:
        """Extract all available metadata for post-processing"""

        metadata = {}

        # Salary information
        salary_selectors = [
            '[data-automation="jobSalary"]',
            '.salary',
            '[data-testid="job-salary"]'
        ]
        for selector in salary_selectors:
            elem = soup.select_one(selector)
            if elem:
                metadata['salary_text'] = self._clean_text(elem.get_text(strip=True))
                break

        # Job type / employment type
        type_selectors = [
            '[data-automation="jobWorkType"]',
            '[data-automation="jobType"]',
            '.work-type'
        ]
        for selector in type_selectors:
            elem = soup.select_one(selector)
            if elem:
                metadata['job_type'] = self._clean_text(elem.get_text(strip=True))
                break

        # Location (detailed) - updated with correct job detail page selector
        location_selectors = [
            '[data-automation="job-detail-location"]',  # Primary selector for job detail pages
            '[data-automation="jobLocation"]',          # Fallback for search cards
            '[data-automation="jobSuburb"]',            # Legacy selector
            '.location'                                 # Generic fallback
        ]
        for selector in location_selectors:
            elem = soup.select_one(selector)
            if elem:
                metadata['location'] = self._clean_text(elem.get_text(strip=True))
                break

        # Posted date - updated for current Seek.co.nz structure
        posted_date_text = ''

        # Get the full page text for pattern matching
        page_text = soup.get_text()
        
        # Enhanced patterns for detail page (matches "Posted 23h ago", "Posted 2d ago", etc.)
        detail_date_patterns = [
            r'Posted\s+(\d+)\s*hours?\s*ago',
            r'Posted\s+(\d+)h\s*ago',
            r'Posted\s+(\d+)\s*days?\s*ago', 
            r'Posted\s+(\d+)d\s*ago',
            r'Posted\s+(\d+)\s*weeks?\s*ago',
            r'Posted\s+(\d+)w\s*ago',
            r'Posted\s+(\d+)\s*months?\s*ago',
            r'Posted\s+(\d+)m\s*ago',
            r'Posted\s+today',
            r'Posted\s+yesterday',
            r'Listed\s+(\d+)\s*hours?\s*ago',
            r'Listed\s+(\d+)h\s*ago',
            r'Listed\s+(\d+)\s*days?\s*ago',
            r'Listed\s+(\d+)d\s*ago',
            r'Listed\s+(\d+)\s*weeks?\s*ago',
            r'Listed\s+(\d+)w\s*ago',
            r'Listed\s+today',
            r'Listed\s+yesterday'
        ]
        
        for pattern in detail_date_patterns:
            matches = re.search(pattern, page_text, re.IGNORECASE)
            if matches:
                posted_date_text = matches.group(0)
                break
        
        # Broader fallback if specific patterns don't match
        if not posted_date_text:
            broader_matches = re.search(r'(?:Posted|Listed)\s+(?:\d+\s*(?:hours?|days?|weeks?|months?)\s*ago|\d+[hdwm]\s*ago|today|yesterday)', page_text, re.IGNORECASE)
            if broader_matches:
                posted_date_text = broader_matches.group(0)

        if posted_date_text:
            metadata['posted_date_text'] = posted_date_text

        # Company information
        company_info_elem = soup.select_one('[data-automation="jobCompany"]')
        if company_info_elem:
            metadata['company_info'] = self._clean_text(company_info_elem.get_text(strip=True))

        # Work arrangement (remote/hybrid/onsite)
        arrangement_keywords = ['remote', 'hybrid', 'onsite', 'work from home', 'wfh']
        description_text = soup.get_text().lower()
        for keyword in arrangement_keywords:
            if keyword in description_text:
                metadata['work_arrangement_hints'] = metadata.get('work_arrangement_hints', [])
                metadata['work_arrangement_hints'].append(keyword)

        return metadata

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for storage"""
        if not text:
            return ""

        try:
            # Handle encoding issues
            cleaned = text.encode('utf-8', errors='ignore').decode('utf-8')

            # Normalize whitespace
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()

            # Remove excessive punctuation
            cleaned = re.sub(r'[^\w\s\.,!?;:()\-$%/\\]', '', cleaned)

            return cleaned

        except Exception:
            return ""