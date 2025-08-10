"""
TechInsights  - Text Processing Utilities
Common text processing and cleaning functions
"""

import re
from typing import List, Set, Optional
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def clean_html(html_content: str) -> str:
    """
    Clean HTML content and extract plain text.
    
    Args:
        html_content: Raw HTML string
        
    Returns:
        str: Cleaned plain text
    """
    if not html_content:
        return ""
    
    try:
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean it
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
        
    except Exception as e:
        logger.error(f"Error cleaning HTML: {e}")
        return html_content


def normalize_company_name(company_name: str) -> str:
    """
    Normalize company name for deduplication.
    
    Args:
        company_name: Raw company name
        
    Returns:
        str: Normalized company name
    """
    if not company_name:
        return ""
    
    # Convert to lowercase
    normalized = company_name.lower().strip()
    
    # Remove common suffixes
    suffixes = [
        r'\s+(ltd|limited|inc|incorporated|corporation|corp|pty|co|company|llc|plc|nz|limited\.?)\.?\s*$',
        r'\s+(group|holdings|solutions|services|systems|technologies|tech|software)\.?\s*$'
    ]
    
    for suffix_pattern in suffixes:
        normalized = re.sub(suffix_pattern, '', normalized, flags=re.IGNORECASE)
    
    # Remove special characters except spaces and basic punctuation
    normalized = re.sub(r'[^\w\s&.-]', '', normalized)
    
    # Normalize whitespace
    normalized = ' '.join(normalized.split())
    
    return normalized.strip()


def normalize_text(text: str) -> str:
    """
    Normalize text for analysis and comparison.
    
    Args:
        text: Raw text
        
    Returns:
        str: Normalized text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove common punctuation
    text = re.sub(r'[^\w\s+#.-]', ' ', text)
    
    # Normalize common technology name variations
    text = normalize_tech_names(text)
    
    return text.strip()


def normalize_tech_names(text: str) -> str:
    """
    Normalize technology names in text for better matching.
    
    Args:
        text: Text containing technology names
        
    Returns:
        str: Text with normalized technology names
    """
    # Common normalizations for technology names
    normalizations = {
        r'\bjavascript\b': 'javascript',
        r'\bjs\b': 'javascript',
        r'\bnode\.?js\b': 'nodejs',
        r'\breact\.?js\b': 'react',
        r'\bvue\.?js\b': 'vue',
        r'\bangular\.?js\b': 'angular',
        r'\bc#\b': 'csharp',
        r'\bc-sharp\b': 'csharp',
        r'\b\.net\b': 'dotnet',
        r'\bpostgres\b': 'postgresql',
        r'\bpsql\b': 'postgresql',
        r'\bmongo\b': 'mongodb',
        r'\bk8s\b': 'kubernetes',
        r'\baws\b': 'amazon-web-services',
        r'\bgcp\b': 'google-cloud-platform',
        r'\bai/ml\b': 'artificial-intelligence machine-learning',
        r'\bml\b': 'machine-learning',
        r'\bai\b': 'artificial-intelligence'
    }
    
    for pattern, replacement in normalizations.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text


def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text.
    
    Args:
        text: Text to search for emails
        
    Returns:
        List[str]: List of found email addresses
    """
    if not text:
        return []
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    
    # Remove duplicates and return
    return list(set(emails))


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.
    
    Args:
        text: Text to search for URLs
        
    Returns:
        List[str]: List of found URLs
    """
    if not text:
        return []
    
    url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
    urls = re.findall(url_pattern, text)
    
    # Remove duplicates and return
    return list(set(urls))


def extract_phone_numbers(text: str) -> List[str]:
    """
    Extract phone numbers from text (NZ format).
    
    Args:
        text: Text to search for phone numbers
        
    Returns:
        List[str]: List of found phone numbers
    """
    if not text:
        return []
    
    # NZ phone number patterns
    patterns = [
        r'\+64\s*[3-9]\s*\d{3}\s*\d{4}',  # +64 3 xxx xxxx
        r'0[3-9]\s*\d{3}\s*\d{4}',       # 03 xxx xxxx
        r'\(\d{2}\)\s*\d{3}\s*\d{4}',    # (03) xxx xxxx
        r'\d{2}-\d{3}-\d{4}',            # 03-xxx-xxxx
        r'\d{2}\s+\d{3}\s+\d{4}'         # 03 xxx xxxx
    ]
    
    phone_numbers = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        phone_numbers.extend(matches)
    
    # Remove duplicates and return
    return list(set(phone_numbers))


def extract_salary_mentions(text: str) -> List[str]:
    """
    Extract salary mentions from text.
    
    Args:
        text: Text to search for salary information
        
    Returns:
        List[str]: List of found salary mentions
    """
    if not text:
        return []
    
    # Salary patterns
    patterns = [
        r'\$\d{2,3}[,k]\d{3}(?:\s*-\s*\$?\d{2,3}[,k]\d{3})?',  # $80,000 - $100,000
        r'\$\d{2,3}k(?:\s*-\s*\$?\d{2,3}k)?',                   # $80k - $100k
        r'\d{2,3}[,k]\d{3}(?:\s*-\s*\d{2,3}[,k]\d{3})?\s*(?:per\s+)?(?:annum|annually|year|pa)',
        r'\$\d{1,3}(?:\.\d{2})?\s*(?:per\s+)?hour'              # $25.50 per hour
    ]
    
    salary_mentions = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        salary_mentions.extend(matches)
    
    return salary_mentions


def extract_years_experience(text: str) -> Optional[int]:
    """
    Extract years of experience mentioned in text.
    
    Args:
        text: Text to search for experience requirements
        
    Returns:
        Optional[int]: Number of years experience or None if not found
    """
    if not text:
        return None
    
    # Patterns for years of experience
    patterns = [
        r'(\d+)(?:\+)?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)',
        r'(?:minimum|min|at\s+least)\s*(\d+)\s*(?:years?|yrs?)',
        r'(\d+)(?:\+)?\s*(?:years?|yrs?)\s*(?:minimum|min)',
        r'(\d+)-\d+\s*(?:years?|yrs?)',  # Take the minimum from range
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                return int(matches[0])
            except (ValueError, IndexError):
                continue
    
    return None


def extract_education_requirements(text: str) -> List[str]:
    """
    Extract education requirements from text.
    
    Args:
        text: Text to search for education requirements
        
    Returns:
        List[str]: List of education requirements
    """
    if not text:
        return []
    
    education_patterns = [
        r'bachelor(?:\'?s)?\s+(?:degree\s+)?(?:in\s+)?([^,.]+)',
        r'master(?:\'?s)?\s+(?:degree\s+)?(?:in\s+)?([^,.]+)',
        r'phd\s+(?:in\s+)?([^,.]+)',
        r'diploma\s+(?:in\s+)?([^,.]+)',
        r'certificate\s+(?:in\s+)?([^,.]+)',
        r'(?:computer\s+science|cs|engineering|it|information\s+technology)',
        r'(?:relevant\s+)?(?:tertiary|university)\s+(?:qualification|degree)'
    ]
    
    education_requirements = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        education_requirements.extend(matches)
    
    # Clean and deduplicate
    cleaned = []
    for req in education_requirements:
        if isinstance(req, str) and req.strip():
            cleaned.append(req.strip())
    
    return list(set(cleaned))


def count_words(text: str) -> int:
    """
    Count words in text.
    
    Args:
        text: Text to count words in
        
    Returns:
        int: Number of words
    """
    if not text:
        return 0
    
    # Simple word count (split on whitespace)
    words = text.split()
    return len(words)


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        str: Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

