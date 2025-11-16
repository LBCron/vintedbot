"""API routes for intelligent scheduling"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from typing import List
from datetime import datetime, timedelta
from backend.services.scheduler_service import SchedulerService
from backend.core.database import get_db_pool
from backend.core.auth import get_current_user  # ✅ FIXED: Moved from backend.security.auth
from backend.core.rate_limiter import limiter, AI_RATE_LIMIT, BATCH_RATE_LIMIT, ANALYTICS_RATE_LIMIT
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/scheduling", tags=["scheduling"])


class ScheduleRequest(BaseModel):
    draft_id: str = Field(..., max_length=100)
    scheduled_time: datetime

    @field_validator('scheduled_time')
    @classmethod
    def validate_scheduled_time(cls, v):
        # Must be in the future
        if v < datetime.now():
            raise ValueError('Scheduled time must be in the future')
        # Not more than 1 year ahead
        if v > datetime.now() + timedelta(days=365):
            raise ValueError('Cannot schedule more than 1 year ahead')
        return v


class BulkScheduleRequest(BaseModel):
    draft_ids: List[str] = Field(..., min_length=1, max_length=50, description="Max 50 items per batch")
    strategy: str = Field(..., pattern="^(optimal|spread|burst)$")

    @field_validator('draft_ids')
    @classmethod
    def validate_draft_ids(cls, v):
        if not v:
            raise ValueError('draft_ids cannot be empty')
        if len(v) > 50:
            raise ValueError('Cannot schedule more than 50 items at once')
        for draft_id in v:
            if not draft_id or len(draft_id) > 100:
                raise ValueError('Invalid draft_id')
        return v


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
@limiter.limit(AI_RATE_LIMIT)
async def get_optimal_times(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """Get ML-recommended best publication times"""
    service = SchedulerService()
    return await service.get_optimal_times(current_user["id"], db)


@router.post("/bulk-schedule")
@limiter.limit(BATCH_RATE_LIMIT)
async def bulk_schedule(
    request: Request,
    body: BulkScheduleRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """Schedule multiple drafts using ML strategy"""
    service = SchedulerService()
    return await service.auto_schedule_bulk(
        body.draft_ids,
        body.strategy,
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
