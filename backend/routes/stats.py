from fastapi import APIRouter
import time
from backend.models.schemas import StatsResponse, HealthResponse
from backend.models.db import db
from backend.services.stats import stats_service
from backend.jobs.scheduler import get_scheduler_jobs_count

router = APIRouter(tags=["Stats"])

start_time = time.time()


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    items = db.get_all()
    return stats_service.calculate_stats(items)


@router.get("/health", response_model=HealthResponse)
async def get_health():
    uptime = time.time() - start_time
    return HealthResponse(
        status="healthy",
        uptime_seconds=round(uptime, 2),
        version="1.0.0",
        scheduler_jobs=get_scheduler_jobs_count()
    )
