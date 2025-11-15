"""
Comprehensive Health Checks

Provides detailed health status for all system components:
- Database connectivity
- Redis connectivity
- External APIs (OpenAI)
- Disk space
- Memory usage
"""
import asyncio
import psutil
import time
from typing import Dict, List
import os


class HealthCheckService:
    """Comprehensive health check system"""

    def __init__(self):
        self.checks: Dict[str, callable] = {
            "database": self.check_database,
            "redis": self.check_redis,
            "openai": self.check_openai,
            "disk": self.check_disk_space,
            "memory": self.check_memory
        }

    async def check_all(self) -> Dict:
        """Run all health checks"""
        start_time = time.time()

        results = {}
        overall_healthy = True

        for name, check_func in self.checks.items():
            try:
                result = await check_func()
                results[name] = result

                if not result.get("healthy", False):
                    overall_healthy = False

            except Exception as e:
                results[name] = {
                    "healthy": False,
                    "error": str(e),
                    "status": "ERROR"
                }
                overall_healthy = False

        duration = time.time() - start_time

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": time.time(),
            "duration_ms": round(duration * 1000, 2),
            "checks": results
        }

    async def check_database(self) -> Dict:
        """Check PostgreSQL database connectivity"""
        try:
            from core.database import get_db_pool

            pool = await get_db_pool()

            if not pool:
                return {
                    "healthy": False,
                    "status": "NOT_INITIALIZED",
                    "message": "Database pool not initialized"
                }

            # Try simple query
            async with pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")

                pool_size = pool.get_size()
                pool_free = pool.get_idle_size()

                return {
                    "healthy": True,
                    "status": "OK",
                    "pool_size": pool_size,
                    "pool_free": pool_free,
                    "pool_used": pool_size - pool_free
                }

        except Exception as e:
            return {
                "healthy": False,
                "status": "ERROR",
                "error": str(e)
            }

    async def check_redis(self) -> Dict:
        """Check Redis connectivity"""
        try:
            import redis
            from core.config import settings

            r = redis.from_url(settings.REDIS_URL or "redis://localhost:6379/0")

            # Ping Redis
            r.ping()

            # Get memory info
            info = r.info("memory")

            return {
                "healthy": True,
                "status": "OK",
                "memory_used_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                "memory_peak_mb": round(info.get("used_memory_peak", 0) / 1024 / 1024, 2)
            }

        except Exception as e:
            return {
                "healthy": False,
                "status": "ERROR",
                "error": str(e)
            }

    async def check_openai(self) -> Dict:
        """Check OpenAI API connectivity"""
        try:
            import os
            from openai import AsyncOpenAI

            api_key = os.getenv("OPENAI_API_KEY")

            if not api_key:
                return {
                    "healthy": False,
                    "status": "NOT_CONFIGURED",
                    "message": "OpenAI API key not set"
                }

            # Try to list models (lightweight request)
            client = AsyncOpenAI(api_key=api_key)

            try:
                models = await asyncio.wait_for(
                    client.models.list(),
                    timeout=5.0
                )

                return {
                    "healthy": True,
                    "status": "OK",
                    "models_available": len(models.data) if models else 0
                }

            except asyncio.TimeoutError:
                return {
                    "healthy": False,
                    "status": "TIMEOUT",
                    "message": "OpenAI API request timed out"
                }

        except Exception as e:
            return {
                "healthy": False,
                "status": "ERROR",
                "error": str(e)
            }

    async def check_disk_space(self) -> Dict:
        """Check disk space availability"""
        try:
            # Get disk usage for current directory
            usage = psutil.disk_usage('/')

            percent_used = usage.percent
            free_gb = usage.free / (1024 ** 3)

            # Healthy if < 90% used AND > 1GB free
            healthy = percent_used < 90 and free_gb > 1

            return {
                "healthy": healthy,
                "status": "OK" if healthy else "WARNING",
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "used_gb": round(usage.used / (1024 ** 3), 2),
                "free_gb": round(free_gb, 2),
                "percent_used": percent_used
            }

        except Exception as e:
            return {
                "healthy": False,
                "status": "ERROR",
                "error": str(e)
            }

    async def check_memory(self) -> Dict:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()

            percent_used = memory.percent
            available_gb = memory.available / (1024 ** 3)

            # Healthy if < 90% used
            healthy = percent_used < 90

            return {
                "healthy": healthy,
                "status": "OK" if healthy else "WARNING",
                "total_gb": round(memory.total / (1024 ** 3), 2),
                "used_gb": round(memory.used / (1024 ** 3), 2),
                "available_gb": round(available_gb, 2),
                "percent_used": percent_used
            }

        except Exception as e:
            return {
                "healthy": False,
                "status": "ERROR",
                "error": str(e)
            }

    async def liveness_check(self) -> Dict:
        """Minimal liveness check (is the service running?)"""
        return {
            "status": "alive",
            "timestamp": time.time()
        }

    async def readiness_check(self) -> Dict:
        """Readiness check (is the service ready to handle requests?)"""
        # Check critical dependencies
        db_check = await self.check_database()
        redis_check = await self.check_redis()

        ready = db_check.get("healthy", False) and redis_check.get("healthy", False)

        return {
            "status": "ready" if ready else "not_ready",
            "timestamp": time.time(),
            "database": db_check.get("status"),
            "redis": redis_check.get("status")
        }


# Global instance
health_service = HealthCheckService()
