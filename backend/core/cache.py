"""
Redis Caching Layer
Performance optimization for frequently accessed data

Caches:
- User sessions
- API responses
- ML predictions
- Market data

SECURITY FIX Bug #59: Added retry logic for Redis connections
"""
import os
import json
import redis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from redis.exceptions import (
    ConnectionError,
    TimeoutError,
    BusyLoadingError,
    ResponseError
)
from typing import Optional, Any
from loguru import logger
from functools import wraps
import hashlib


class CacheService:
    """
    Redis caching service for performance optimization

    Features:
    - Automatic serialization/deserialization
    - TTL support
    - Cache invalidation
    - Hit/miss tracking
    """

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.enabled = os.getenv("ENABLE_CACHE", "true").lower() == "true"
        self.client: Optional[redis.Redis] = None

        if self.enabled:
            self._connect()


    def _connect(self):
        """
        Connect to Redis with retry logic

        SECURITY FIX Bug #59: Exponential backoff retry for resilience
        Retries 3 times with delays: 0.5s, 1s, 2s
        """
        try:
            # Configure retry with exponential backoff
            retry_policy = Retry(ExponentialBackoff(), 3)

            self.client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,  # Ping every 30s to keep connection alive
                retry=retry_policy,
                retry_on_timeout=True,
                retry_on_error=[ConnectionError, TimeoutError, BusyLoadingError]
            )

            # Test connection with retry
            self.client.ping()
            logger.info("✅ Redis cache connected with retry policy (3 retries, exponential backoff)")

        except (ConnectionError, TimeoutError, ResponseError) as e:
            logger.warning(f"⚠️ Redis connection failed after retries: {e} - Caching disabled")
            self.enabled = False
            self.client = None
        except Exception as e:
            logger.error(f"❌ Unexpected Redis error: {e} - Caching disabled")
            self.enabled = False
            self.client = None


    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Returns None if not found or error
        """
        if not self.enabled or not self.client:
            return None

        try:
            value = self.client.get(key)

            if value:
                logger.debug(f"✅ Cache HIT: {key}")
                return json.loads(value)
            else:
                logger.debug(f"❌ Cache MISS: {key}")
                return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None


    def set(self, key: str, value: Any, ttl: int = 3600):
        """
        Set value in cache with TTL (seconds)

        Default TTL: 1 hour
        """
        if not self.enabled or not self.client:
            return False

        try:
            serialized = json.dumps(value)
            self.client.setex(key, ttl, serialized)
            logger.debug(f"✅ Cache SET: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False


    def delete(self, key: str):
        """Delete key from cache"""
        if not self.enabled or not self.client:
            return False

        try:
            self.client.delete(key)
            logger.debug(f"✅ Cache DELETE: {key}")
            return True

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False


    def clear_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        if not self.enabled or not self.client:
            return False

        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
                logger.info(f"✅ Cache CLEAR: {len(keys)} keys matching {pattern}")
            return True

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False


    def cache_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from arguments

        Uses MD5 hash for consistent keys
        """
        key_data = f"{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()


# Singleton instance
cache_service = CacheService()


def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator for caching function results

    Usage:
        @cached(ttl=3600, key_prefix="ml_prediction")
        async def predict_price(category, brand):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{cache_service.cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            cache_service.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


# Cache configuration
CACHE_TTL = {
    "session": 3600,  # 1 hour
    "api_response": 300,  # 5 minutes
    "ml_prediction": 86400,  # 24 hours
    "market_data": 3600,  # 1 hour
    "user_profile": 600,  # 10 minutes
}


# Helper functions
async def cache_user_session(user_id: int, session_data: dict):
    """Cache user session"""
    key = f"session:user:{user_id}"
    cache_service.set(key, session_data, CACHE_TTL["session"])


async def get_user_session(user_id: int) -> Optional[dict]:
    """Get cached user session"""
    key = f"session:user:{user_id}"
    return cache_service.get(key)


async def invalidate_user_cache(user_id: int):
    """Invalidate all cache for a user"""
    cache_service.clear_pattern(f"*:user:{user_id}:*")
    cache_service.delete(f"session:user:{user_id}")
