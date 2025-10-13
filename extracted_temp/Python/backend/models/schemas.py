from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ItemStatus(str, Enum):
    DRAFT = "draft"
    LISTED = "listed"
    SOLD = "sold"
    ARCHIVED = "archived"


class Condition(str, Enum):
    NEW_WITH_TAGS = "new_with_tags"
    NEW_WITHOUT_TAGS = "new_without_tags"
    VERY_GOOD = "very_good"
    GOOD = "good"
    SATISFACTORY = "satisfactory"


class PriceSuggestion(BaseModel):
    min: float = Field(..., description="Minimum price threshold")
    max: float = Field(..., description="Maximum price")
    target: float = Field(..., description="Target selling price")
    justification: str = Field(..., description="Reasoning for price range")


class PriceHistory(BaseModel):
    date: datetime
    old_price: float
    new_price: float
    reason: str = "automatic_drop"


class Item(BaseModel):
    id: str
    title: str
    description: str
    brand: Optional[str] = None
    category: Optional[str] = None
    size: Optional[str] = None
    condition: Optional[Condition] = None
    price: float
    price_suggestion: Optional[PriceSuggestion] = None
    price_history: List[PriceHistory] = []
    keywords: List[str] = []
    image_urls: List[str] = []
    image_hash: Optional[str] = None
    status: ItemStatus = ItemStatus.DRAFT
    possible_duplicate: bool = False
    estimated_sale_score: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Draft(BaseModel):
    title: str
    description: str
    brand: Optional[str] = None
    category_guess: Optional[str] = None
    condition: Optional[Condition] = None
    size_guess: Optional[str] = None
    keywords: List[str] = []
    price_suggestion: PriceSuggestion
    image_urls: List[str] = []
    possible_duplicate: bool = False
    estimated_sale_score: Optional[int] = None


class PhotoIngestRequest(BaseModel):
    urls: Optional[List[str]] = []


class PriceSimulation(BaseModel):
    initial_price: float
    min_price: float
    days: int = 30


class SimulationResult(BaseModel):
    day: int
    price: float
    drop_percentage: float = 0.0


class StatsResponse(BaseModel):
    total_items: int
    total_value: float
    avg_price: float
    top_brands: List[str]
    duplicates_detected: int
    avg_days_since_creation: float


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    version: str
    scheduler_jobs: int
