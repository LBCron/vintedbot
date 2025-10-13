import os
import time
import psutil
from fastapi import APIRouter

router = APIRouter(tags=["health"])

start_time = time.time()


@router.get("/health")
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
            "mock_mode": os.getenv("MOCK_MODE", "true")
        },
        "scheduler_jobs_count": scheduler_jobs_count
    }
