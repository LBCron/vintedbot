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
    
    logger.info(f"📋 Publish job {job.job_id} queued (mode: {data.mode})")
    
    return {
        "job_id": job.job_id,
        "status": job.status,
        "mode": job.mode,
        "created_at": job.created_at
    }


@router.get("/queue")
async def list_jobs(limit: int = 50, offset: int = 0):
    """List all publish jobs"""
    with get_db_session() as db:
        jobs = db.exec(
            select(PublishJob)
            .order_by(PublishJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        
        return {
            "jobs": [
                {
                    "job_id": j.job_id,
                    "item_id": j.item_id,
                    "session_id": j.session_id,
                    "mode": j.mode,
                    "status": j.status,
                    "schedule_at": j.schedule_at,
                    "created_at": j.created_at,
                    "updated_at": j.updated_at
                }
                for j in jobs
            ],
            "total": len(jobs)
        }


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
    
    logger.info(f"❌ Job {job_id} cancelled")
    
    return {
        "success": True,
        "job_id": job_id,
        "status": "cancelled"
    }
