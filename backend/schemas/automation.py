"""
Automation schemas for auto-bump, auto-follow, auto-messages, etc.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AutomationType(str, Enum):
    """Types of automation actions"""
    BUMP = "bump"  # Repost listing to top
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"
    FAVORITE = "favorite"
    MESSAGE = "message"
    PRICE_DROP = "price_drop"


class AutomationStatus(str, Enum):
    """Status of automation jobs"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class BumpConfig(BaseModel):
    """Configuration for auto-bump feature"""
    enabled: bool = True
    interval_hours: int = Field(default=12, ge=1, le=48)  # Bump every X hours
    randomize_delay: bool = True  # Add random delay to avoid detection
    max_delay_minutes: int = Field(default=30, ge=0, le=120)
    target_listings: List[str] = Field(default_factory=list)  # Empty = all active listings
    rotate_listings: bool = True  # Rotate which listings get bumped first
    skip_recent: int = Field(default=6, ge=0)  # Skip if bumped in last X hours


class FollowConfig(BaseModel):
    """Configuration for auto-follow/unfollow"""
    enabled: bool = True
    daily_limit: int = Field(default=50, ge=1, le=200)  # Max follows per day
    unfollow_after_days: int = Field(default=7, ge=1, le=30)
    target_followers_of: List[str] = Field(default_factory=list)  # Follow followers of these users
    target_categories: List[str] = Field(default_factory=list)  # Follow sellers in these categories
    target_brands: List[str] = Field(default_factory=list)  # Follow sellers of these brands
    min_listings: int = Field(default=5, ge=0)  # Only follow users with X+ listings
    blacklist: List[str] = Field(default_factory=list)  # User IDs to never follow


class MessageTemplate(BaseModel):
    """Template for auto-messages"""
    id: str
    name: str
    trigger: str  # "like", "follow", "message_received"
    template: str  # With variables like {{username}}, {{item_title}}, {{price}}
    delay_minutes: int = Field(default=0, ge=0, le=1440)  # Delay before sending
    enabled: bool = True


class MessageConfig(BaseModel):
    """Configuration for auto-messages"""
    enabled: bool = True
    templates: List[MessageTemplate] = Field(default_factory=list)
    daily_limit: int = Field(default=100, ge=1, le=500)
    personalize: bool = True  # Use user's name, item details
    blacklist: List[str] = Field(default_factory=list)


class FavoriteConfig(BaseModel):
    """Configuration for auto-favorites"""
    enabled: bool = True
    target_own_listings: bool = True  # Favorite your own listings
    target_similar: bool = True  # Favorite similar items to build network
    daily_limit: int = Field(default=30, ge=1, le=100)


class AutomationRule(BaseModel):
    """Automation rule configuration"""
    id: str
    user_id: str
    type: AutomationType
    config: Dict[str, Any]  # Specific config based on type
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None


class AutomationJob(BaseModel):
    """Individual automation job execution"""
    id: str
    rule_id: str
    type: AutomationType
    status: AutomationStatus
    target_id: Optional[str] = None  # Listing ID, user ID, etc.
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class AutomationSummary(BaseModel):
    """Summary of automation activities"""
    total_rules: int
    active_rules: int
    jobs_today: int
    jobs_successful: int
    jobs_failed: int
    next_scheduled: Optional[datetime] = None
    recent_jobs: List[AutomationJob] = []
