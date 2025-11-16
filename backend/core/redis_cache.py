"""
Redis Cache for Production
High-performance caching layer for expensive operations
"""
import os
import json
import redis.asyncio as aioredis
from typing import Any, Optional, Callable
from functools import wraps
from loguru import logger


class RedisCache:
    """
    Production-ready Redis cache with automatic connection management
    """

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.enabled = os.getenv("REDIS_ENABLED", "true").lower() == "true"

    async def connect(self):
        """Connect to Redis server"""
        if not self.enabled:
            logger.warning("Redis cache is disabled")
            return

        if self.redis is None:
            try:
                self.redis = await aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                await self.redis.ping()
                logger.info(f"✅ Connected to Redis at {self.redis_url}")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Redis: {e}")
                self.redis = None
                self.enabled = False

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.enabled or not self.redis:
            return None

        try:
            value = await self.redis.get(key)
            if value:
                # Try to deserialize JSON
                try:
                    return json.loads(value)
                except:
                    # Return as string if not JSON
                    return value
            return None
        except Exception as e:
            logger.warning(f"Redis GET failed for key '{key}': {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300
    ) -> bool:
        """
        Set value in cache with TTL

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default: 5 minutes)

        Returns:
            True if successful
        """
        if not self.enabled or not self.redis:
            return False

        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            else:
                serialized = str(value)

            await self.redis.set(key, serialized, ex=ttl)
            return True
        except Exception as e:
            logger.warning(f"Redis SET failed for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        if not self.enabled or not self.redis:
            return False

        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis DELETE failed for key '{key}': {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern

        Args:
            pattern: Redis pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis:
            return 0

        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Deleted {len(keys)} keys matching '{pattern}'")
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Redis CLEAR_PATTERN failed for '{pattern}': {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.enabled or not self.redis:
            return False

        try:
            return await self.redis.exists(key) > 0
        except:
            return False

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")


# Global cache instance
cache = RedisCache()


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results in Redis

    Usage:
        @cached(ttl=600, key_prefix="analytics")
        async def get_analytics(user_id: str):
            # Expensive calculation
            return result

    Args:
        ttl: Time to live in seconds
        key_prefix: Optional prefix for cache key

    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function name and arguments
            cache_key_parts = [key_prefix, func.__name__] if key_prefix else [func.__name__]

            # Add args to key
            for arg in args:
                cache_key_parts.append(str(arg))

            # Add kwargs to key (sorted for consistency)
            for k in sorted(kwargs.keys()):
                cache_key_parts.append(f"{k}={kwargs[k]}")

            cache_key = ":".join(cache_key_parts)

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value

            # Cache miss - call function
            logger.debug(f"Cache MISS: {cache_key}")
            result = await func(*args, **kwargs)

            # Store in cache
            await cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


def invalidate_cache_on_update(key_pattern: str):
    """
    Decorator to invalidate cache when data is updated

    Usage:
        @invalidate_cache_on_update("analytics:*")
        async def update_user_data(user_id: str):
            # Update logic
            pass

    Args:
        key_pattern: Pattern of keys to invalidate

    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # Invalidate cache after successful execution
            deleted = await cache.clear_pattern(key_pattern)
            if deleted > 0:
                logger.info(f"Invalidated {deleted} cache keys matching '{key_pattern}'")

            return result

        return wrapper
    return decorator
