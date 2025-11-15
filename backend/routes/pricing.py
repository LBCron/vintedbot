"""API routes for price optimization"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from backend.services.price_optimizer_service import PriceOptimizerService
from backend.core.database import get_db_pool
from backend.security.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/pricing", tags=["pricing"])


class PriceAnalyzeRequest(BaseModel):
    draft_id: str
    strategy: str = "balanced"  # quick_sale, balanced, premium, competitive


class BulkOptimizeRequest(BaseModel):
    draft_ids: List[str]
    strategy: str
    apply: bool = False


class MarketAnalysisRequest(BaseModel):
    category: str
    brand: str
    condition: str
    size: Optional[str] = None


@router.post("/analyze")
async def analyze_article_price(
    request: PriceAnalyzeRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """Analyze and suggest optimal price for an article"""
    async with db.acquire() as conn:
        article = await conn.fetchrow(
            "SELECT * FROM drafts WHERE id = $1 AND user_id = $2",
            request.draft_id,
            current_user["id"]
        )

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

    service = PriceOptimizerService()
    return await service.suggest_optimal_price(dict(article), request.strategy)


@router.post("/bulk-optimize")
async def bulk_optimize_prices(
    request: BulkOptimizeRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_pool)
):
    """Optimize prices for multiple drafts"""
    service = PriceOptimizerService()
    results = await service.bulk_optimize_prices(
        request.draft_ids,
        request.strategy,
        request.apply,
        current_user["id"],
        db
    )

    return {
        "results": results,
        "total_items": len(results),
        "applied": request.apply
    }


@router.post("/market-analysis")
async def get_market_analysis(
    request: MarketAnalysisRequest
):
    """Get market price analysis for similar items"""
    service = PriceOptimizerService()
    return await service.analyze_market_prices(
        request.category,
        request.brand,
        request.condition,
        request.size
    )
