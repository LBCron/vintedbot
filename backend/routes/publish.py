from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from backend.db import queue_publish_job, get_publish_job, get_db_session, update_job_status
from backend.models import PublishJob, JobStatus
from backend.utils.logger import logger
from sqlmodel import select

router = APIRouter(prefix="/vinted/publish", tags=["publish"])


class QueueJobRequest(BaseModel):
    item_id: int
    session_id: int
    mode: str = "manual"
    schedule_at: Optional[datetime] = None


@router.post("/queue")
async def queue_job(data: QueueJobRequest):
    """Queue a new publish job"""
    job = queue_publish_job(
        item_id=data.item_id,
        session_id=data.session_id,
        mode=data.mode,
        schedule_at=data.schedule_at
    )
    
    logger.info(f"[INFO] Publish job {job.job_id} queued (mode: {data.mode})")
    
    return {
        "job_id": job.job_id,
        "status": job.status,
        "mode": job.mode,
        "created_at": job.created_at
    }


@router.get("/queue")
async def list_jobs(limit: int = 50, offset: int = 0):
    """
    List all publish jobs - LOVABLE FORMAT
    
    Returns array of jobs with format:
    [{job_id, item_id, status, mode, scheduled_at, logs, screenshot}, ...]
    """
    with get_db_session() as db:
        jobs = db.exec(
            select(PublishJob)
            .order_by(PublishJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        
        # Return LOVABLE FORMAT: direct array, not wrapped in {"jobs": ...}
        return [
            {
                "job_id": j.job_id,
                "item_id": j.item_id or 0,  # Ensure not None
                "status": str(j.status.value if hasattr(j.status, 'value') else j.status),
                "mode": str(j.mode.value if hasattr(j.mode, 'value') else j.mode),
                "scheduled_at": j.schedule_at.isoformat() + "Z" if j.schedule_at else None,
                "logs": "\n".join([log.get('message', str(log)) for log in j.logs]) if j.logs else None,
                "screenshot": j.screenshot_path if j.screenshot_path else None
            }
            for j in jobs
        ]


@router.get("/queue/{job_id}")
async def get_job_status(job_id: str):
    """Get job status with logs and screenshot"""
    job = get_publish_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.job_id,
        "item_id": job.item_id,
        "session_id": job.session_id,
        "mode": job.mode,
        "status": job.status,
        "logs": job.logs,
        "screenshot_path": job.screenshot_path,
        "schedule_at": job.schedule_at,
        "created_at": job.created_at,
        "updated_at": job.updated_at
    }


@router.post("/queue/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a publish job"""
    job = get_publish_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status in [JobStatus.completed, JobStatus.cancelled]:
        raise HTTPException(status_code=400, detail="Job already completed or cancelled")
    
    update_job_status(job_id, JobStatus.cancelled)
    
    logger.info(f"[ERROR] Job {job_id} cancelled")
    
    return {
        "success": True,
        "job_id": job_id,
        "status": "cancelled"
    }


@router.post("/queue/{job_id}/retry")
async def retry_job(job_id: str):
    """Retry a failed publish job"""
    job = get_publish_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status not in [JobStatus.failed, JobStatus.cancelled]:
        raise HTTPException(status_code=400, detail="Only failed or cancelled jobs can be retried")
    
    update_job_status(job_id, JobStatus.queued)
    
    logger.info(f"[PROCESS] Job {job_id} queued for retry")
    
    return {
        "success": True,
        "job_id": job_id,
        "status": "queued"
    }


@router.post("/queue/{job_id}/run")
async def run_job(job_id: str):
    """Manually trigger a queued job"""
    job = get_publish_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.queued:
        raise HTTPException(status_code=400, detail="Only queued jobs can be run manually")
    
    update_job_status(job_id, JobStatus.running)
    
    logger.info(f"▶️ Job {job_id} started manually")
    
    return {
        "success": True,
        "job_id": job_id,
        "status": "processing"
    }


@router.post("/queue/{job_id}/pause")
async def pause_job(job_id: str):
    """Pause a processing job"""
    job = get_publish_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.running:
        raise HTTPException(status_code=400, detail="Only running jobs can be paused")
    
    update_job_status(job_id, JobStatus.queued)
    
    logger.info(f"⏸️ Job {job_id} paused")
    
    return {
        "success": True,
        "job_id": job_id,
        "status": "queued"
    }


@router.delete("/queue/{job_id}")
async def delete_job(job_id: str):
    """Delete a publish job"""
    from backend.db import get_db_session
    
    job = get_publish_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    with get_db_session() as db:
        db.delete(job)
        db.commit()
    
    logger.info(f"🗑️ Job {job_id} deleted")
    
    return {
        "success": True,
        "job_id": job_id,
        "message": "Job deleted"
    }
