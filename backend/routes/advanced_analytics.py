"""API routes for advanced analytics with ML"""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from backend.services.analytics_ml_service import AnalyticsMLService
from backend.core.database import get_db_pool
from backend.core.auth import get_current_user  # ✅ FIXED: Moved from backend.security.auth
from backend.core.rate_limiter import limiter, AI_RATE_LIMIT, ANALYTICS_RATE_LIMIT
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/analytics-ml", tags=["analytics-ml"])


@router.get("/predict-revenue")
@limiter.limit(AI_RATE_LIMIT)
async def predict_revenue(
    http_request: Request,
    days_ahead: int = 7,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """Predict revenue for next N days using ML"""
    service = AnalyticsMLService()
    return await service.predict_revenue(current_user["id"], days_ahead, db)


@router.get("/insights")
@limiter.limit(AI_RATE_LIMIT)
async def get_smart_insights(
    http_request: Request,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """Get ML-powered actionable insights"""
    service = AnalyticsMLService()
    return await service.generate_insights(current_user["id"], db)


@router.get("/kpis")
@limiter.limit(ANALYTICS_RATE_LIMIT)
async def get_advanced_kpis(
    http_request: Request,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """Get advanced KPIs and metrics"""
    service = AnalyticsMLService()
    return await service.calculate_kpis(current_user["id"], db)
