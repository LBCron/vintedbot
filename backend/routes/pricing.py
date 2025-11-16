"""API routes for price optimization"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from backend.services.price_optimizer_service import PriceOptimizerService
from backend.core.database import get_db_pool
from backend.core.auth import get_current_user  # ✅ FIXED: Moved from backend.security.auth
from backend.core.rate_limiter import limiter, AI_RATE_LIMIT, BATCH_RATE_LIMIT
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/pricing", tags=["pricing"])


class PriceAnalyzeRequest(BaseModel):
    draft_id: str = Field(..., max_length=100)
    strategy: str = Field("balanced", pattern="^(quick_sale|balanced|premium|competitive)$")


class BulkOptimizeRequest(BaseModel):
    draft_ids: List[str] = Field(..., min_length=1, max_length=100, description="Max 100 items per batch")
    strategy: str = Field(..., pattern="^(quick_sale|balanced|premium|competitive)$")
    apply: bool = False

    @field_validator('draft_ids')
    @classmethod
    def validate_draft_ids(cls, v):
        if not v:
            raise ValueError('draft_ids cannot be empty')
        if len(v) > 100:
            raise ValueError('Cannot optimize more than 100 items at once')
        # Validate each ID
        for draft_id in v:
            if not draft_id or len(draft_id) > 100:
                raise ValueError('Invalid draft_id')
        return v


class MarketAnalysisRequest(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    brand: str = Field(..., min_length=1, max_length=100)
    condition: str = Field(..., pattern="^(new|like_new|good|fair)$")
    size: Optional[str] = Field(None, max_length=50)


@router.post("/analyze")
@limiter.limit(AI_RATE_LIMIT)
async def analyze_article_price(
    http_request: Request,
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
@limiter.limit(BATCH_RATE_LIMIT)
async def bulk_optimize_prices(
    http_request: Request,
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
@limiter.limit(AI_RATE_LIMIT)
async def get_market_analysis(
    http_request: Request,
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
