from fastapi import APIRouter
from typing import List
from backend.models.schemas import Draft, Item, ItemStatus
from backend.services.ai import ai_service
from backend.models.db import db
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/bonus", tags=["Bonus Features"])


@router.get("/test/photoset", response_model=List[Draft])
async def generate_test_photoset():
    test_urls = [
        "https://example.com/photo1.jpg",
        "https://example.com/photo2.jpg",
        "https://example.com/photo3.jpg",
        "https://example.com/photo4.jpg",
        "https://example.com/photo5.jpg"
    ]
    
    drafts = []
    for url in test_urls:
        draft = ai_service.generate_listing([url])
        drafts.append(draft)
    
    return drafts


@router.get("/recommendations", response_model=List[Item])
async def get_recommendations():
    items = db.get_all()
    
    recommendations = []
    for item in items:
        if item.status == ItemStatus.LISTED:
            days_since_creation = (datetime.now() - item.created_at).days if isinstance(item.created_at, datetime) else 0
            
            if days_since_creation > 14:
                recommendations.append(item)
            elif item.estimated_sale_score and item.estimated_sale_score < 50:
                recommendations.append(item)
    
    return recommendations[:10]


@router.post("/simulate/multi-price")
async def simulate_multiple_prices(prices: List[float], min_price: float = 10.0, days: int = 30):
    from backend.services.pricing import pricing_service
    
    results = {}
    for price in prices:
        trajectory = pricing_service.simulate_price_trajectory(price, min_price, days)
        results[f"price_{price}"] = [{"day": r.day, "price": r.price} for r in trajectory]
    
    return results
