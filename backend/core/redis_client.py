"""
Redis Client for Caching and Job Queue
Production-ready with connection pooling and automatic retry
"""
import os
import json
import pickle
from typing import Optional, Any, Union
from datetime import timedelta
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError
from backend.utils.logger import logger

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
REDIS_SOCKET_TIMEOUT = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
REDIS_SOCKET_CONNECT_TIMEOUT = int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5"))

# Connection pool
_pool: Optional[ConnectionPool] = None
_client: Optional[redis.Redis] = None


def get_redis_pool() -> ConnectionPool:
    """Get or create Redis connection pool"""
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(
            REDIS_URL,
            max_connections=REDIS_MAX_CONNECTIONS,
            socket_timeout=REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=REDIS_SOCKET_CONNECT_TIMEOUT,
            decode_responses=False,  # We handle encoding ourselves
            retry_on_timeout=True,
            health_check_interval=30,
        )
        logger.info(f"🔴 Redis pool created: {REDIS_MAX_CONNECTIONS} max connections")
    return _pool


async def get_redis() -> redis.Redis:
    """Get Redis client with connection pooling"""
    global _client
    if _client is None:
        pool = get_redis_pool()
        _client = redis.Redis(connection_pool=pool)

        # Test connection
        try:
            await _client.ping()
            logger.info("✅ Redis connection established")
        except ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            logger.warning("⚠️ Running without Redis - performance will be degraded")
            _client = None

    return _client


async def close_redis():
    """Close Redis connections"""
    global _client, _pool
    if _client:
        await _client.close()
        _client = None
    if _pool:
        await _pool.disconnect()
        _pool = None
    logger.info("✅ Redis connections closed")


class RedisCache:
    """Redis cache with automatic serialization and fallback"""

    def __init__(self):
        self.client: Optional[redis.Redis] = None

    async def _ensure_connected(self):
        """Ensure Redis client is connected"""
        if self.client is None:
            self.client = await get_redis()

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        try:
            await self._ensure_connected()
            if self.client is None:
                return default

            value = await self.client.get(key)
            if value is None:
                return default

            # Try to unpickle, fallback to JSON, then raw string
            try:
                return pickle.loads(value)
            except:
                try:
                    return json.loads(value.decode())
                except:
                    return value.decode()

        except RedisError as e:
            logger.warning(f"Redis GET error for {key}: {e}")
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache (any picklable object)
            ttl: Time to live in seconds or timedelta

        Returns:
            True if successful, False otherwise
        """
        try:
            await self._ensure_connected()
            if self.client is None:
                return False

            # Serialize value (prefer pickle for Python objects)
            try:
                serialized = pickle.dumps(value)
            except:
                # Fallback to JSON for non-picklable objects
                serialized = json.dumps(value).encode()

            # Convert timedelta to seconds
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())

            # Set with optional TTL
            if ttl:
                await self.client.setex(key, ttl, serialized)
            else:
                await self.client.set(key, serialized)

            return True

        except RedisError as e:
            logger.warning(f"Redis SET error for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            await self._ensure_connected()
            if self.client is None:
                return False

            await self.client.delete(key)
            return True

        except RedisError as e:
            logger.warning(f"Redis DELETE error for {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            await self._ensure_connected()
            if self.client is None:
                return False

            return await self.client.exists(key) > 0

        except RedisError as e:
            logger.warning(f"Redis EXISTS error for {key}: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        try:
            await self._ensure_connected()
            if self.client is None:
                return None

            return await self.client.incrby(key, amount)

        except RedisError as e:
            logger.warning(f"Redis INCR error for {key}: {e}")
            return None

    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Set expiration on key"""
        try:
            await self._ensure_connected()
            if self.client is None:
                return False

            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())

            return await self.client.expire(key, ttl)

        except RedisError as e:
            logger.warning(f"Redis EXPIRE error for {key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern

        Args:
            pattern: Redis key pattern (e.g., "user:*", "cache:*")

        Returns:
            Number of keys deleted
        """
        try:
            await self._ensure_connected()
            if self.client is None:
                return 0

            keys = []
            async for key in self.client.scan_iter(match=pattern, count=100):
                keys.append(key)

            if keys:
                return await self.client.delete(*keys)
            return 0

        except RedisError as e:
            logger.warning(f"Redis CLEAR_PATTERN error for {pattern}: {e}")
            return 0


# Global cache instance
cache = RedisCache()


# Health check
async def check_redis_health() -> dict:
    """Check Redis connectivity and stats"""
    try:
        client = await get_redis()
        if client is None:
            return {
                "status": "unavailable",
                "message": "Redis not configured"
            }

        # Ping test
        await client.ping()

        # Get stats
        info = await client.info()

        return {
            "status": "healthy",
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "uptime_days": info.get("uptime_in_days", 0),
            "total_commands_processed": info.get("total_commands_processed", 0),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
