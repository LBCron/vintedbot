"""
Analytics API - Dashboard statistics and performance tracking
UNIQUE FEATURE: Not available in any competitor bots!
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime, timedelta
from backend.core.auth import get_current_user, User
from backend.core.storage import get_store
from backend.schemas.analytics import (
    AnalyticsResponse,
    DashboardStats,
    ListingStats,
    PerformanceHeatmap,
    CategoryPerformance
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_dashboard(
    days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_user)
):
    """
    📊 PREMIUM FEATURE: Complete analytics dashboard
    
    Shows:
    - Total views, likes, messages across all listings
    - Performance heatmap (best times to post)
    - Top/bottom performing listings
    - Category performance breakdown
    - Conversion rates
    
    This feature is NOT available in Dotb, VatBot, or any competitor!
    """
    store = get_store()
    user_id = str(current_user.id)
    
    # Get dashboard stats
    stats = store.get_dashboard_stats(user_id, days)
    
    # Get top and bottom performing listings
    top_listings, bottom_listings = store.get_top_bottom_listings(user_id, days, limit=5)
    
    # Get performance heatmap
    heatmap_data = store.get_performance_heatmap(user_id, days)
    
    # Get category performance
    category_data = store.get_category_performance(user_id, days)
    
    # Build DashboardStats
    dashboard = DashboardStats(
        total_listings=stats["total_listings"],
        active_listings=stats["active_listings"],
        total_views=stats["total_views"],
        views_today=stats["views_today"],
        views_week=stats["views_week"],
        total_likes=stats["total_likes"],
        likes_today=stats["likes_today"],
        total_messages=stats["total_messages"],
        avg_conversion_rate=stats["avg_conversion_rate"],
        best_performing=[ListingStats(**listing) for listing in top_listings],
        worst_performing=[ListingStats(**listing) for listing in bottom_listings]
    )
    
    # Build heatmap
    heatmap = [PerformanceHeatmap(**entry) for entry in heatmap_data]
    
    # Build category performance
    by_category = [CategoryPerformance(**cat) for cat in category_data]
    
    return AnalyticsResponse(
        dashboard=dashboard,
        heatmap=heatmap,
        by_category=by_category,
        top_listings=[ListingStats(**listing) for listing in top_listings]
    )


@router.post("/events/view")
async def track_view(
    listing_id: str,
    source: str = "organic",
    current_user: User = Depends(get_current_user)
):
    """Track a view event for analytics"""
    store = get_store()
    
    listing = store.get_listing(listing_id)
    if not listing:
        return {"ok": False, "error": "Listing not found", "listing_id": listing_id}
    
    store.track_analytics_event(
        listing_id=listing_id,
        event_type="view",
        user_id=None,
        source=source
    )
    return {"ok": True, "event": "view", "listing_id": listing_id}


@router.post("/events/like")
async def track_like(
    listing_id: str,
    current_user: User = Depends(get_current_user)
):
    """Track a like/favorite event for analytics"""
    store = get_store()
    
    listing = store.get_listing(listing_id)
    if not listing:
        return {"ok": False, "error": "Listing not found", "listing_id": listing_id}
    
    store.track_analytics_event(
        listing_id=listing_id,
        event_type="like",
        user_id=None,
        source="organic"
    )
    return {"ok": True, "event": "like", "listing_id": listing_id}


@router.post("/events/message")
async def track_message(
    listing_id: str,
    current_user: User = Depends(get_current_user)
):
    """Track a message event for analytics"""
    store = get_store()
    
    listing = store.get_listing(listing_id)
    if not listing:
        return {"ok": False, "error": "Listing not found", "listing_id": listing_id}
    
    store.track_analytics_event(
        listing_id=listing_id,
        event_type="message",
        user_id=None,
        source="organic"
    )
    return {"ok": True, "event": "message", "listing_id": listing_id}


@router.post("/events/sale")
async def track_sale(
    listing_id: str,
    current_user: User = Depends(get_current_user)
):
    """Track a sale event for analytics"""
    store = get_store()
    
    listing = store.get_listing(listing_id)
    if not listing:
        return {"ok": False, "error": "Listing not found", "listing_id": listing_id}
    
    store.track_analytics_event(
        listing_id=listing_id,
        event_type="sale",
        user_id=None,
        source="organic"
    )
    return {"ok": True, "event": "sale", "listing_id": listing_id}
