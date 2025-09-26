"""
Utilities module for Tech Jobs Insights NZ API.

This module contains utility functions and helpers used across the application.
"""

from app.utils.cache import (
    cached_query,
    clear_cache,
    get_cache_stats,
    SHORT_CACHE,
    MEDIUM_CACHE,
    LONG_CACHE
)

__all__ = [
    'cached_query',
    'clear_cache',
    'get_cache_stats',
    'SHORT_CACHE',
    'MEDIUM_CACHE',
    'LONG_CACHE'
]

