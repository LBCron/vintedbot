import os
import time
import psutil
from fastapi import APIRouter
from backend.settings import settings

router = APIRouter(tags=["health"])

start_time = time.time()


@router.get("/health")
@router.options("/health")
async def health_check():
    """Enhanced health check endpoint"""
    process = psutil.Process()
    memory_info = process.memory_info()
    
    # Get scheduler jobs count if available
    scheduler_jobs_count = 0
    try:
        from backend.jobs import scheduler
        if scheduler:
            scheduler_jobs_count = len(scheduler.get_jobs())
    except:
        pass
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "uptime_seconds": int(time.time() - start_time),
        "process": {
            "pid": os.getpid(),
            "mem_mb": round(memory_info.rss / 1024 / 1024, 2)
        },
        "config": {
            "port": 5000,
            "openai_enabled": bool(os.getenv("OPENAI_API_KEY")),
            "allowed_origins": os.getenv("ALLOWED_ORIGINS", "*"),
            "mock_mode": settings.MOCK_MODE
        },
        "scheduler_jobs_count": scheduler_jobs_count
    }


@router.get("/ready")
@router.options("/ready")
async def readiness_check():
    """Readiness check endpoint for Lovable.dev frontend"""
    return {
        "status": "ready",
        "timestamp": int(time.time())
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
