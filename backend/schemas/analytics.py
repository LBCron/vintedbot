"""
Analytics schemas for tracking listing performance and user statistics
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ListingView(BaseModel):
    """Single view event"""
    listing_id: str
    user_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "organic"  # organic, search, profile, bump


class ListingLike(BaseModel):
    """Single like/favorite event"""
    listing_id: str
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ListingStats(BaseModel):
    """Statistics for a single listing"""
    listing_id: str
    title: str
    price: float
    category: Optional[str] = None
    views_total: int = 0
    views_today: int = 0
    views_week: int = 0
    likes_total: int = 0
    likes_today: int = 0
    messages_total: int = 0
    conversion_rate: float = 0.0  # messages / views
    days_active: int = 0
    last_bump: Optional[datetime] = None
    performance_score: float = 0.0  # 0-100 based on views, likes, messages


class DashboardStats(BaseModel):
    """Overall dashboard statistics"""
    total_listings: int
    active_listings: int
    total_views: int
    views_today: int
    views_week: int
    total_likes: int
    likes_today: int
    total_messages: int
    avg_conversion_rate: float
    best_performing: List[ListingStats] = []
    worst_performing: List[ListingStats] = []


class PerformanceHeatmap(BaseModel):
    """Heatmap data for best posting times"""
    day_of_week: int  # 0=Monday, 6=Sunday
    hour: int  # 0-23
    views: int
    likes: int
    messages: int
    performance_score: float


class CategoryPerformance(BaseModel):
    """Performance metrics by category"""
    category: str
    listings_count: int
    avg_views: float
    avg_likes: float
    avg_price: float
    conversion_rate: float
    avg_days_to_sell: Optional[float] = None


class AnalyticsResponse(BaseModel):
    """Complete analytics dashboard response"""
    dashboard: DashboardStats
    heatmap: List[PerformanceHeatmap] = []
    by_category: List[CategoryPerformance] = []
    top_listings: List[ListingStats] = []
