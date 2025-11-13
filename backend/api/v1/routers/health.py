from fastapi import APIRouter, Query
from backend.settings import settings
from backend.core.monitoring import get_system_health, get_system_metrics
from backend.core.job_wrapper import get_job_stats
from backend.core.circuit_breaker import get_all_circuit_states

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint (lightweight)"""
    return {
        "status": "ok",
        "api_version": "v1",
        "media_storage": settings.MEDIA_STORAGE,
        "max_uploads": settings.MAX_UPLOADS_PER_REQUEST,
        "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
        "jpeg_quality": settings.JPEG_QUALITY,
        "max_dim_px": settings.MAX_DIM_PX
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """
    Comprehensive health check with all system metrics

    Returns:
        - Overall system health status
        - Database connectivity
        - Disk space
        - Memory usage
        - Circuit breaker states
        - Background job health
        - Storage quotas
    """
    return await get_system_health()


@router.get("/metrics")
async def system_metrics():
    """
    Detailed system metrics endpoint

    Returns:
        - Memory usage (RSS, VMS, percent)
        - CPU usage
        - Disk usage
        - Database size and table counts
        - Uptime
    """
    return await get_system_metrics()


@router.get("/health/jobs")
async def job_health():
    """
    Get health and statistics for background jobs

    Returns:
        - Job execution stats (success/failure counts)
        - Last run times
        - Average execution duration
        - Consecutive failure counts
    """
    return get_job_stats()


@router.get("/health/circuit-breakers")
async def circuit_breaker_status():
    """
    Get status of all circuit breakers

    Returns:
        - Current state (closed/open/half-open)
        - Failure counts
        - Last failure time
        - Recovery timeout
    """
    return {
        "circuit_breakers": get_all_circuit_states()
    }
