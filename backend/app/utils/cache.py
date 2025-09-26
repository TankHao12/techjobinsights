"""
Simple in-memory caching utility for API endpoints.

This module provides TTL-based caching to reduce database load for frequently
accessed analytics endpoints.

Usage:
    from app.utils.cache import cached_query
    
    @cached_query(ttl=300)  # Cache for 5 minutes
    def expensive_query():
        return db.query(...).all()
"""

from functools import wraps
from typing import Any, Callable, Optional
from cachetools import TTLCache
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

# Global cache instances with different TTL values
# Short cache (5 minutes) - for frequently changing data
SHORT_CACHE = TTLCache(maxsize=100, ttl=300)

# Medium cache (15 minutes) - for moderately stable data
MEDIUM_CACHE = TTLCache(maxsize=200, ttl=900)

# Long cache (1 hour) - for stable data
LONG_CACHE = TTLCache(maxsize=500, ttl=3600)


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Generate a unique cache key based on function name and arguments.
    
    Args:
        func_name: Name of the function being cached
        args: Positional arguments
        kwargs: Keyword arguments
        
    Returns:
        MD5 hash of the serialized function call
    """
    # Create a dictionary of all arguments
    key_data = {
        'func': func_name,
        'args': str(args),
        'kwargs': str(sorted(kwargs.items()))
    }
    
    # Serialize and hash
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached_query(
    ttl: int = 300,
    cache_instance: Optional[TTLCache] = None
) -> Callable:
    """
    Decorator to cache function results with time-to-live.
    
    Args:
        ttl: Time to live in seconds (default: 300 = 5 minutes)
        cache_instance: Specific cache instance to use (optional)
        
    Returns:
        Decorated function with caching
        
    Example:
        @cached_query(ttl=600)  # Cache for 10 minutes
        def get_popular_skills(db, limit=20):
            return db.query(...).all()
    """
    def decorator(func: Callable) -> Callable:
        # Select cache instance based on TTL if not provided
        nonlocal cache_instance
        if cache_instance is None:
            if ttl <= 300:
                cache_instance = SHORT_CACHE
            elif ttl <= 900:
                cache_instance = MEDIUM_CACHE
            else:
                cache_instance = LONG_CACHE
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            cache_key = _generate_cache_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            if cache_key in cache_instance:
                logger.debug(f"Cache HIT for {func.__name__}")
                return cache_instance[cache_key]
            
            # Execute function and cache result
            logger.debug(f"Cache MISS for {func.__name__}")
            result = func(*args, **kwargs)
            cache_instance[cache_key] = result
            
            return result
        
        return wrapper
    return decorator


def clear_cache(cache_type: str = 'all') -> int:
    """
    Clear cache(s) manually.
    
    Args:
        cache_type: Type of cache to clear ('short', 'medium', 'long', 'all')
        
    Returns:
        Number of items cleared
    """
    cleared = 0
    
    if cache_type in ('short', 'all'):
        cleared += len(SHORT_CACHE)
        SHORT_CACHE.clear()
        
    if cache_type in ('medium', 'all'):
        cleared += len(MEDIUM_CACHE)
        MEDIUM_CACHE.clear()
        
    if cache_type in ('long', 'all'):
        cleared += len(LONG_CACHE)
        LONG_CACHE.clear()
    
    logger.info(f"Cleared {cleared} items from {cache_type} cache(s)")
    return cleared


def get_cache_stats() -> dict:
    """
    Get statistics about current cache usage.
    
    Returns:
        Dictionary with cache statistics
    """
    return {
        'short_cache': {
            'size': len(SHORT_CACHE),
            'maxsize': SHORT_CACHE.maxsize,
            'ttl': SHORT_CACHE.ttl
        },
        'medium_cache': {
            'size': len(MEDIUM_CACHE),
            'maxsize': MEDIUM_CACHE.maxsize,
            'ttl': MEDIUM_CACHE.ttl
        },
        'long_cache': {
            'size': len(LONG_CACHE),
            'maxsize': LONG_CACHE.maxsize,
            'ttl': LONG_CACHE.ttl
        }
    }

