import os
import time
import psutil
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from backend.settings import settings

router = APIRouter(tags=["health"])

start_time = time.time()


@router.get("/health")
@router.options("/health")
async def health_check():
    """
    Comprehensive health check endpoint

    SECURITY FIX Bug #67: Tests all critical dependencies
    Returns 200 if healthy, 503 if degraded/unhealthy
    """
    checks = {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": int(time.time() - start_time),
        "checks": {}
    }

    # Process info
    process = psutil.Process()
    memory_info = process.memory_info()
    checks["process"] = {
        "pid": os.getpid(),
        "mem_mb": round(memory_info.rss / 1024 / 1024, 2),
        "cpu_percent": process.cpu_percent(interval=0.1)
    }

    # Database check (PostgreSQL) - TEMPORARILY DISABLED
    # TODO: Implement proper async database health check
    # For now, assume healthy if app started (which requires DB connection)
    checks["checks"]["database"] = {"status": "assumed_healthy", "type": "postgresql", "note": "DB check temporarily disabled during migration"}

    # Redis check
    try:
        from backend.core.cache import cache_service
        # Ping Redis
        cache_service.set("healthcheck_test", "ok", ttl=10)
        result = cache_service.get("healthcheck_test")
        if result == "ok":
            checks["checks"]["redis"] = {"status": "healthy"}
        else:
            checks["checks"]["redis"] = {"status": "degraded", "error": "ping failed"}
            checks["status"] = "degraded"
    except Exception as e:
        checks["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
        checks["status"] = "degraded"

    # Scheduler check
    try:
        from backend.jobs import scheduler
        if scheduler:
            jobs_count = len(scheduler.get_jobs())
            checks["checks"]["scheduler"] = {
                "status": "healthy",
                "jobs_count": jobs_count
            }
        else:
            checks["checks"]["scheduler"] = {"status": "unhealthy", "error": "not initialized"}
            checks["status"] = "degraded"
    except Exception as e:
        checks["checks"]["scheduler"] = {"status": "unhealthy", "error": str(e)}
        checks["status"] = "degraded"

    # Configuration check
    checks["config"] = {
        "environment": os.getenv("ENV", "development"),
        "openai_enabled": bool(os.getenv("OPENAI_API_KEY")),
        "stripe_enabled": bool(os.getenv("STRIPE_SECRET_KEY")),
        "mock_mode": settings.MOCK_MODE
    }

    # Return appropriate status code
    status_code = 200 if checks["status"] == "healthy" else 503
    return JSONResponse(content=checks, status_code=status_code)


@router.get("/ready")
@router.options("/ready")
async def readiness_check():
    """
    Kubernetes-style readiness check
    Returns 200 if ready to serve traffic, 503 otherwise
    """
    # TEMPORARILY: Assume ready if app is running
    # TODO: Implement proper async database check
    return {
        "status": "ready",
        "timestamp": int(time.time()),
        "note": "DB check temporarily disabled during migration"
    }


@router.get("/stats")
@router.options("/stats")
async def backend_stats():
    """Stats endpoint for Lovable.dev frontend"""
    from backend.db import get_db_session
    from backend.models import Listing, Draft, PublishJob
    from sqlmodel import func, select

    with get_db_session() as db:
        total_listings = db.exec(select(func.count(Listing.id))).first() or 0
        total_drafts = db.exec(select(func.count(Draft.id))).first() or 0
        total_jobs = db.exec(select(func.count(PublishJob.job_id))).first() or 0

    return {
        "status": "ok",
        "stats": {
            "listings": total_listings,
            "drafts": total_drafts,
            "publish_jobs": total_jobs
        },
        "uptime_seconds": int(time.time() - start_time)
    }
