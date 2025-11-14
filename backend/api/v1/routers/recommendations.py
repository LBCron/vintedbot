"""
API endpoints for Smart Recommendations Engine
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from pydantic import BaseModel

from backend.recommendations.recommendation_engine import (
    RecommendationEngine,
    SalePrediction,
    OptimizationScore,
    Recommendation,
    RecommendationType,
    Priority
)
from backend.core.auth import get_current_user

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# ============================================================================
# Response Models
# ============================================================================

class SalePredictionResponse(BaseModel):
    """Sale prediction response"""
    listing_id: str
    probability_7d: float
    probability_30d: float
    estimated_days_to_sell: int
    confidence: float
    factors: List[str]

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    """Single recommendation response"""
    type: str
    priority: str
    title: str
    description: str
    action: str
    expected_impact: str
    data: Dict
    confidence: float

    class Config:
        from_attributes = True


class OptimizationScoreResponse(BaseModel):
    """Optimization score response"""
    listing_id: str
    score: float
    photo_score: float
    description_score: float
    pricing_score: float
    timing_score: float
    recommendations: List[RecommendationResponse]


class DashboardInsightsResponse(BaseModel):
    """Dashboard insights response"""
    sell_rate: float
    avg_days_to_sell: int
    active_listings: int
    top_categories: List[str]
    performance_trend: str


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/predict/{listing_id}", response_model=SalePredictionResponse)
async def predict_sale_probability(
    listing_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Predict when a listing will sell

    Returns:
    - Probability of selling in 7 days
    - Probability of selling in 30 days
    - Estimated days to sell
    - Key factors affecting the prediction
    """
    try:
        engine = RecommendationEngine()
        prediction = await engine.predict_sale_probability(
            listing_id=listing_id,
            user_id=current_user['id']
        )

        return SalePredictionResponse(
            listing_id=prediction.listing_id,
            probability_7d=prediction.probability_7d,
            probability_30d=prediction.probability_30d,
            estimated_days_to_sell=prediction.estimated_days_to_sell,
            confidence=prediction.confidence,
            factors=prediction.factors
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting sale: {str(e)}")


@router.get("/optimize/{listing_id}", response_model=OptimizationScoreResponse)
async def get_optimization_recommendations(
    listing_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get comprehensive optimization recommendations for a listing

    Returns:
    - Overall optimization score (0-100)
    - Individual scores for photos, description, pricing, timing
    - Prioritized list of actionable recommendations
    """
    try:
        engine = RecommendationEngine()
        optimization = await engine.get_optimization_recommendations(
            listing_id=listing_id,
            user_id=current_user['id']
        )

        return OptimizationScoreResponse(
            listing_id=optimization.listing_id,
            score=optimization.score,
            photo_score=optimization.photo_score,
            description_score=optimization.description_score,
            pricing_score=optimization.pricing_score,
            timing_score=optimization.timing_score,
            recommendations=[
                RecommendationResponse(
                    type=rec.type.value,
                    priority=rec.priority.value,
                    title=rec.title,
                    description=rec.description,
                    action=rec.action,
                    expected_impact=rec.expected_impact,
                    data=rec.data,
                    confidence=rec.confidence
                )
                for rec in optimization.recommendations
            ]
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting optimization: {str(e)}")


@router.get("/inventory", response_model=List[RecommendationResponse])
async def get_inventory_recommendations(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get inventory management recommendations

    Returns recommendations for:
    - Stale listings to remove or reprice
    - Seasonal opportunities
    - Inventory optimization
    """
    try:
        engine = RecommendationEngine()
        recommendations = await engine.get_inventory_recommendations(
            user_id=current_user['id']
        )

        return [
            RecommendationResponse(
                type=rec.type.value,
                priority=rec.priority.value,
                title=rec.title,
                description=rec.description,
                action=rec.action,
                expected_impact=rec.expected_impact,
                data=rec.data,
                confidence=rec.confidence
            )
            for rec in recommendations
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting inventory recommendations: {str(e)}")


@router.get("/dashboard/insights", response_model=DashboardInsightsResponse)
async def get_dashboard_insights(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get high-level insights for dashboard

    Returns:
    - Overall sell rate
    - Average days to sell
    - Active listings count
    - Top performing categories
    - Performance trend
    """
    try:
        engine = RecommendationEngine()
        insights = await engine.get_dashboard_insights(
            user_id=current_user['id']
        )

        return DashboardInsightsResponse(**insights)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard insights: {str(e)}")


@router.get("/batch/predict", response_model=List[SalePredictionResponse])
async def batch_predict_sale_probability(
    listing_ids: str,  # Comma-separated IDs
    current_user: Dict = Depends(get_current_user)
):
    """
    Predict sale probability for multiple listings

    Query params:
    - listing_ids: Comma-separated listing IDs (e.g., "id1,id2,id3")
    """
    try:
        ids = [id.strip() for id in listing_ids.split(',')]
        engine = RecommendationEngine()

        predictions = []
        for listing_id in ids:
            try:
                prediction = await engine.predict_sale_probability(
                    listing_id=listing_id,
                    user_id=current_user['id']
                )
                predictions.append(SalePredictionResponse(
                    listing_id=prediction.listing_id,
                    probability_7d=prediction.probability_7d,
                    probability_30d=prediction.probability_30d,
                    estimated_days_to_sell=prediction.estimated_days_to_sell,
                    confidence=prediction.confidence,
                    factors=prediction.factors
                ))
            except ValueError:
                # Skip listings that don't exist
                continue

        return predictions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch prediction: {str(e)}")


@router.get("/all", response_model=Dict)
async def get_all_recommendations(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get all recommendations for user (inventory + active listings)

    Convenience endpoint that combines:
    - Inventory recommendations
    - Dashboard insights
    - Top 5 listings that need attention
    """
    try:
        engine = RecommendationEngine()

        # Get inventory recommendations
        inventory_recs = await engine.get_inventory_recommendations(
            user_id=current_user['id']
        )

        # Get dashboard insights
        insights = await engine.get_dashboard_insights(
            user_id=current_user['id']
        )

        # Get active listings that need attention (low optimization score)
        import sqlite3
        conn = sqlite3.connect("/data/vintedbot.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id
            FROM listings
            WHERE user_id = ?
            AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 10
        """, (current_user['id'],))

        active_listings = cursor.fetchall()
        conn.close()

        # Get optimization scores for active listings
        optimizations = []
        for row in active_listings:
            try:
                opt = await engine.get_optimization_recommendations(
                    listing_id=row[0],
                    user_id=current_user['id']
                )
                if opt.score < 70:  # Only include if needs improvement
                    optimizations.append({
                        'listing_id': opt.listing_id,
                        'score': opt.score,
                        'top_recommendation': opt.recommendations[0] if opt.recommendations else None
                    })
            except:
                continue

        # Sort by score (worst first)
        optimizations.sort(key=lambda x: x['score'])

        return {
            'inventory_recommendations': [
                RecommendationResponse(
                    type=rec.type.value,
                    priority=rec.priority.value,
                    title=rec.title,
                    description=rec.description,
                    action=rec.action,
                    expected_impact=rec.expected_impact,
                    data=rec.data,
                    confidence=rec.confidence
                )
                for rec in inventory_recs
            ],
            'insights': DashboardInsightsResponse(**insights),
            'listings_needing_attention': optimizations[:5]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting all recommendations: {str(e)}")
