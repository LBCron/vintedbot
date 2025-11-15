"""
Caching Strategy for VintedBot

Provides in-memory caching for frequently accessed data
to reduce database queries and improve performance.

In production, replace with Redis for distributed caching.
"""

import time
import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class SimpleCache:
    """
    Simple in-memory cache with TTL support

    For production: Use Redis instead
    """

    def __init__(self):
        self._cache = {}
        self._ttl = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""

        # Check if key exists and not expired
        if key in self._cache:
            if key in self._ttl:
                if time.time() > self._ttl[key]:
                    # Expired, delete
                    del self._cache[key]
                    del self._ttl[key]
                    return None

            return self._cache[key]

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with optional TTL (seconds)"""

        self._cache[key] = value

        if ttl:
            self._ttl[key] = time.time() + ttl

        logger.debug(f"[CACHE] SET: {key} (TTL: {ttl}s)")

    def delete(self, key: str):
        """Delete key from cache"""

        if key in self._cache:
            del self._cache[key]

        if key in self._ttl:
            del self._ttl[key]

        logger.debug(f"[CACHE] DELETE: {key}")

    def clear(self):
        """Clear entire cache"""

        self._cache.clear()
        self._ttl.clear()

        logger.info("[CACHE] CLEARED")

    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""

        keys_to_delete = [k for k in self._cache.keys() if pattern in k]

        for key in keys_to_delete:
            self.delete(key)

        logger.info(f"[CACHE] INVALIDATED: {len(keys_to_delete)} keys matching '{pattern}'")

    def stats(self) -> dict:
        """Get cache statistics"""

        total_keys = len(self._cache)
        expired_keys = sum(1 for k, t in self._ttl.items() if time.time() > t)
        active_keys = total_keys - expired_keys

        return {
            "total_keys": total_keys,
            "active_keys": active_keys,
            "expired_keys": expired_keys
        }


# Global cache instance
cache = SimpleCache()


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results

    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        key_prefix: Prefix for cache key

    Example:
        @cached(ttl=600, key_prefix="user")
        async def get_user(user_id: str):
            return await db.fetch_user(user_id)
    """

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]

            # Add args
            for arg in args:
                key_parts.append(str(arg))

            # Add kwargs
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")

            cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"[CACHE] HIT: {cache_key}")
                return cached_value

            # Cache miss, execute function
            logger.debug(f"[CACHE] MISS: {cache_key}")
            result = await func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Same logic for sync functions
            key_parts = [key_prefix or func.__name__]

            for arg in args:
                key_parts.append(str(arg))

            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")

            cache_key = ":".join(key_parts)

            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"[CACHE] HIT: {cache_key}")
                return cached_value

            logger.debug(f"[CACHE] MISS: {cache_key}")
            result = func(*args, **kwargs)

            cache.set(cache_key, result, ttl)

            return result

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def cache_key(*args, **kwargs) -> str:
    """
    Generate deterministic cache key from arguments

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key string
    """

    key_data = {
        "args": args,
        "kwargs": kwargs
    }

    key_str = json.dumps(key_data, sort_keys=True)
    key_hash = hashlib.md5(key_str.encode()).hexdigest()

    return key_hash


# Cache TTL presets
CACHE_TTL = {
    "short": 60,  # 1 minute
    "medium": 300,  # 5 minutes
    "long": 600,  # 10 minutes
    "hour": 3600,  # 1 hour
    "day": 86400  # 24 hours
}


# Example usage:
"""
from backend.core.cache import cached, cache, CACHE_TTL

# Cache function result for 5 minutes
@cached(ttl=CACHE_TTL["medium"])
async def get_optimal_times(user_id: str):
    # Expensive ML calculation
    return await scheduler_service.get_optimal_times(user_id, db)

# Manual cache operations
cache.set("user:123:settings", {"theme": "dark"}, ttl=CACHE_TTL["hour"])
settings = cache.get("user:123:settings")

# Invalidate cache
cache.delete("user:123:settings")
cache.invalidate_pattern("user:123")  # Invalidate all user 123 keys
"""
