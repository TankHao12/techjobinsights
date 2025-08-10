"""
TechInsights  - Utilities
Common utility functions and helpers
"""

from .text_processing import (
    clean_html,
    normalize_company_name,
    extract_emails,
    extract_urls,
    normalize_text
)
from .tech_detection import TechStackDetector

__all__ = [
    "clean_html",
    "normalize_company_name",
    "extract_emails",
    "extract_urls",
    "normalize_text",
    "TechStackDetector"
]

