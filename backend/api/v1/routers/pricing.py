"""
Pricing API Endpoints
AI-powered pricing recommendations and dynamic pricing
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from backend.core.auth import get_current_user, User
from backend.pricing.pricing_engine import PricingEngine, PricingStrategy
from loguru import logger

router = APIRouter(prefix="/pricing", tags=["pricing"])
pricing_engine = PricingEngine()


class PriceRecommendationRequest(BaseModel):
    brand: str
    category: str
    condition: str
    original_price: Optional[float] = None
    strategy: str = "match_market"  # quick_sale, maximize_profit, match_market, dynamic


class DynamicPricingRequest(BaseModel):
    item_id: str
    min_acceptable_price: float
    adjustment_frequency_days: int = 7


@router.post("/recommend")
async def get_price_recommendation(
    request: PriceRecommendationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered price recommendation

    Analyzes market data, brand premium, condition, and demand
    to provide optimal pricing strategy.

    Returns:
        - min_price: Minimum viable price
        - optimal_price: Recommended price for best results
        - max_price: Maximum reasonable price
        - confidence: low/medium/high
        - reasoning: Explanation of pricing logic
        - market_average: Average market price
        - competitor_prices: Sample competitor prices
        - demand_score: 0-100 demand rating
        - estimated_days_to_sell: Predicted time to sell
    """
    try:
        # Map string strategy to enum
        strategy_map = {
            'quick_sale': PricingStrategy.QUICK_SALE,
            'maximize_profit': PricingStrategy.MAXIMIZE_PROFIT,
            'match_market': PricingStrategy.MATCH_MARKET,
            'dynamic': PricingStrategy.DYNAMIC
        }

        strategy = strategy_map.get(request.strategy, PricingStrategy.MATCH_MARKET)

        logger.info(f"💰 Price recommendation requested by {current_user.email}")

        recommendation = await pricing_engine.get_price_recommendation(
            brand=request.brand,
            category=request.category,
            condition=request.condition,
            original_price=request.original_price,
            strategy=strategy,
            user_id=current_user.user_id
        )

        return {
            'ok': True,
            'recommendation': recommendation.to_dict()
        }

    except Exception as e:
        logger.error(f"❌ Price recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies")
async def get_pricing_strategies(current_user: User = Depends(get_current_user)):
    """
    Get available pricing strategies

    Returns list of pricing strategies with descriptions.
    """
    strategies = [
        {
            'id': 'quick_sale',
            'name': 'Vente Rapide',
            'description': 'Prix compétitif pour vente en moins de 7 jours',
            'typical_discount': '15%',
            'best_for': 'Articles en stock depuis longtemps, besoin de cash rapide'
        },
        {
            'id': 'maximize_profit',
            'name': 'Maximiser le Profit',
            'description': 'Prix optimal pour maximiser vos marges',
            'typical_discount': '0-5%',
            'best_for': 'Articles rares, marques premium, pas pressé de vendre'
        },
        {
            'id': 'match_market',
            'name': 'S\'aligner sur le Marché',
            'description': 'Prix similaire à la concurrence',
            'typical_discount': '5-10%',
            'best_for': 'Stratégie équilibrée, bon compromis vitesse/profit'
        },
        {
            'id': 'dynamic',
            'name': 'Prix Dynamique (Auto)',
            'description': 'Ajustement automatique selon la demande',
            'typical_discount': 'Variable',
            'best_for': 'Laisser l\'IA gérer le pricing'
        }
    ]

    return {
        'ok': True,
        'strategies': strategies
    }


@router.post("/dynamic/enable")
async def enable_dynamic_pricing(
    request: DynamicPricingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Enable dynamic pricing for an item

    Auto-adjusts price based on performance:
    - Many views, no likes → price too high
    - Many likes, no sale → reduce slightly
    - No engagement → significant reduction needed
    """
    try:
        result = await pricing_engine.enable_dynamic_pricing(
            item_id=request.item_id,
            min_acceptable_price=request.min_acceptable_price,
            adjustment_frequency_days=request.adjustment_frequency_days
        )

        return {
            'ok': True,
            'message': 'Dynamic pricing enabled',
            **result
        }

    except Exception as e:
        logger.error(f"❌ Failed to enable dynamic pricing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/analysis")
async def analyze_market(
    category: str,
    brand: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze market for a category/brand

    Returns:
    - Average price
    - Price range (min/max)
    - Number of active listings
    - Recent sales data
    - Demand trend
    """
    # TODO: Implement market analysis with Vinted scraping
    return {
        'ok': True,
        'category': category,
        'brand': brand,
        'market_data': {
            'average_price': 25.50,
            'min_price': 12.00,
            'max_price': 45.00,
            'active_listings': 150,
            'recent_sales': 12,
            'demand_trend': 'increasing'
        },
        'note': 'Market analysis coming soon with real Vinted data'
    }


@router.get("/competitors/{item_id}")
async def get_competitor_prices(
    item_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get competitor prices for similar items

    Scrapes Vinted for similar items and returns pricing data.
    """
    # TODO: Implement competitor tracking
    return {
        'ok': True,
        'item_id': item_id,
        'competitors': [
            {'seller': 'user123', 'price': 22.00, 'condition': 'Très bon état'},
            {'seller': 'user456', 'price': 25.00, 'condition': 'Bon état'},
            {'seller': 'user789', 'price': 20.00, 'condition': 'Satisfaisant'}
        ],
        'note': 'Real-time competitor tracking coming soon'
    }
