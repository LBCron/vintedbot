"""API routes for intelligent scheduling"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
from backend.services.scheduler_service import SchedulerService
from backend.core.database import get_db_pool
from backend.security.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/scheduling", tags=["scheduling"])


class ScheduleRequest(BaseModel):
    draft_id: str
    scheduled_time: datetime


class BulkScheduleRequest(BaseModel):
    draft_ids: List[str]
    strategy: str  # 'optimal', 'spread', 'burst'


@router.post("/schedule")
async def schedule_draft(
    request: ScheduleRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """Schedule a single draft for publication"""
    service = SchedulerService()
    return await service.schedule_publication(
        request.draft_id,
        request.scheduled_time,
        current_user["id"],
        db
    )


@router.get("/optimal-times")
async def get_optimal_times(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """Get ML-recommended best publication times"""
    service = SchedulerService()
    return await service.get_optimal_times(current_user["id"], db)


@router.post("/bulk-schedule")
async def bulk_schedule(
    request: BulkScheduleRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """Schedule multiple drafts using ML strategy"""
    service = SchedulerService()
    return await service.auto_schedule_bulk(
        request.draft_ids,
        request.strategy,
        current_user["id"],
        db
    )


@router.get("/calendar")
async def get_scheduled_calendar(
    start_date: datetime,
    end_date: datetime,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """Get scheduled publications for calendar view"""
    service = SchedulerService()
    return await service.get_scheduled_calendar(
        current_user["id"],
        start_date,
        end_date,
        db
    )


@router.delete("/cancel/{schedule_id}")
async def cancel_scheduled(
    schedule_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """Cancel a scheduled publication"""
    service = SchedulerService()
    return await service.cancel_scheduled(schedule_id, current_user["id"], db)
