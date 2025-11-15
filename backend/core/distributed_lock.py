"""
Distributed Locking with Redis

Prevents duplicate cron job execution across multiple server instances.

Critical for:
- Scheduled publications (prevent double-posting)
- Price drops (prevent multiple price updates)
- Auto-bump (prevent spam bumps)
- Cleanup jobs (prevent race conditions)
"""
import asyncio
import logging
import time
import uuid
from typing import Optional
from contextlib import asynccontextmanager
import redis.asyncio as redis
import os

logger = logging.getLogger(__name__)


class DistributedLock:
    """
    Redis-based distributed lock with automatic expiration

    Usage:
        async with DistributedLock("cron:scheduled_publisher"):
            # Only ONE server will execute this block
            await publish_scheduled_items()
    """

    def __init__(
        self,
        lock_name: str,
        timeout: int = 300,  # 5 minutes default
        retry_delay: float = 1.0,
        max_retries: int = 0,  # Don't wait by default for cron jobs
    ):
        """
        Initialize distributed lock

        Args:
            lock_name: Unique name for this lock
            timeout: Lock expiration in seconds (prevents deadlocks)
            retry_delay: Delay between lock acquisition retries
            max_retries: Max attempts to acquire lock (0 = fail immediately)
        """
        self.lock_name = f"lock:{lock_name}"
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.lock_value = str(uuid.uuid4())  # Unique ID for this lock instance
        self._redis: Optional[redis.Redis] = None

    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection"""
        if self._redis is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self._redis = await redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
            )
        return self._redis

    async def acquire(self) -> bool:
        """
        Acquire the distributed lock

        Returns:
            True if lock acquired, False otherwise
        """
        r = await self._get_redis()
        attempt = 0

        while attempt <= self.max_retries:
            try:
                # Try to set lock with NX (only if not exists) and EX (expiration)
                acquired = await r.set(
                    self.lock_name,
                    self.lock_value,
                    nx=True,  # Only set if key doesn't exist
                    ex=self.timeout,  # Expire after timeout seconds
                )

                if acquired:
                    logger.info(f"✅ Lock acquired: {self.lock_name} (expires in {self.timeout}s)")
                    return True

                # Lock already held by another instance
                if attempt < self.max_retries:
                    logger.debug(f"🔒 Lock busy: {self.lock_name}, retry {attempt + 1}/{self.max_retries}")
                    await asyncio.sleep(self.retry_delay)
                    attempt += 1
                else:
                    logger.warning(f"❌ Failed to acquire lock: {self.lock_name} (already held)")
                    return False

            except Exception as e:
                logger.error(f"❌ Lock acquisition error: {e}")
                return False

        return False

    async def release(self):
        """
        Release the distributed lock (only if we own it)

        Uses Lua script to ensure atomicity
        """
        r = await self._get_redis()

        # Lua script to ensure we only delete our own lock
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        try:
            result = await r.eval(lua_script, 1, self.lock_name, self.lock_value)
            if result:
                logger.info(f"✅ Lock released: {self.lock_name}")
            else:
                logger.warning(f"⚠️ Lock not released (expired or not owned): {self.lock_name}")
        except Exception as e:
            logger.error(f"❌ Lock release error: {e}")

    async def extend(self, additional_time: int):
        """
        Extend lock expiration time

        Args:
            additional_time: Additional seconds to add to expiration
        """
        r = await self._get_redis()

        # Lua script to extend only if we own the lock
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("expire", KEYS[1], ARGV[2])
        else
            return 0
        end
        """

        try:
            result = await r.eval(
                lua_script,
                1,
                self.lock_name,
                self.lock_value,
                additional_time,
            )
            if result:
                logger.debug(f"Lock extended: {self.lock_name} (+{additional_time}s)")
            return bool(result)
        except Exception as e:
            logger.error(f"❌ Lock extend error: {e}")
            return False

    async def __aenter__(self):
        """Async context manager entry"""
        acquired = await self.acquire()
        if not acquired:
            raise LockAcquisitionError(f"Could not acquire lock: {self.lock_name}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.release()
        if self._redis:
            await self._redis.close()


class LockAcquisitionError(Exception):
    """Raised when lock cannot be acquired"""
    pass


@asynccontextmanager
async def distributed_lock(
    lock_name: str,
    timeout: int = 300,
    fail_silently: bool = True,
):
    """
    Convenient context manager for distributed locks

    Args:
        lock_name: Unique lock identifier
        timeout: Lock expiration in seconds
        fail_silently: If True, skip execution if lock can't be acquired
                      If False, raise LockAcquisitionError

    Usage:
        async with distributed_lock("cron:publish"):
            await publish_scheduled_items()
    """
    lock = DistributedLock(lock_name, timeout=timeout, max_retries=0)

    try:
        acquired = await lock.acquire()
        if not acquired:
            if fail_silently:
                logger.info(f"⏭️ Skipping execution (lock held): {lock_name}")
                yield False  # Signal that we didn't get the lock
                return
            else:
                raise LockAcquisitionError(f"Could not acquire lock: {lock_name}")

        yield True  # Signal that we got the lock
    finally:
        await lock.release()
        if lock._redis:
            await lock._redis.close()
