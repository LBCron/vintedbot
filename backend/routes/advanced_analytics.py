"""API routes for advanced analytics with ML"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.services.analytics_ml_service import AnalyticsMLService
from backend.core.database import get_db_pool
from backend.security.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/analytics-ml", tags=["analytics-ml"])


@router.get("/predict-revenue")
async def predict_revenue(
    days_ahead: int = 7,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """Predict revenue for next N days using ML"""
    service = AnalyticsMLService()
    return await service.predict_revenue(current_user["id"], days_ahead, db)


@router.get("/insights")
async def get_smart_insights(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """Get ML-powered actionable insights"""
    service = AnalyticsMLService()
    return await service.generate_insights(current_user["id"], db)


@router.get("/kpis")
async def get_advanced_kpis(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """Get advanced KPIs and metrics"""
    service = AnalyticsMLService()
    return await service.calculate_kpis(current_user["id"], db)
