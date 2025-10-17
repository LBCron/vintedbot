"""
Pydantic schemas for bulk photo analysis and draft generation
"""
from typing import List, Optional, Dict, Any, Self
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from backend.schemas.vinted import PublishFlags


class AnalysisResult(BaseModel):
    """Result of AI photo analysis"""
    title: str
    description: str
    price: float
    category: str
    condition: str
    color: str
    brand: Optional[str] = "Non spécifié"
    size: Optional[str] = "Non spécifié"
    confidence: float = Field(ge=0.0, le=1.0)
    fallback: bool = False
    group_index: Optional[int] = None


class DraftItem(BaseModel):
    """Draft listing item"""
    id: str
    title: str
    description: str
    price: float
    category: str
    condition: str
    color: str
    brand: str
    size: str
    photos: List[str]  # URLs or temp_ids
    status: str = "draft"  # draft, ready, published, failed
    confidence: float
    created_at: datetime
    updated_at: datetime
    
    # Analysis metadata
    analysis_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Publication readiness
    flags: Optional[PublishFlags] = None
    missing_fields: List[str] = Field(default_factory=list)


class BulkUploadRequest(BaseModel):
    """Request to start bulk photo analysis"""
    auto_group: bool = True  # Auto-group photos into items
    photos_per_item: int = Field(default=6, ge=1, le=10)
    auto_publish: bool = False  # Auto-publish after analysis
    
    
class BulkUploadResponse(BaseModel):
    """Response from bulk upload"""
    ok: bool
    job_id: str
    total_photos: int
    estimated_items: int
    status: str  # queued, processing, completed, failed
    message: Optional[str] = None


class BulkJobStatus(BaseModel):
    """Status of a bulk analysis job"""
    job_id: str
    status: str  # queued, processing, completed, failed
    total_photos: int
    processed_photos: int
    total_items: int
    completed_items: int
    failed_items: int
    drafts: List[DraftItem]
    errors: List[str] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percent: float = 0.0


class DraftUpdateRequest(BaseModel):
    """Request to update a draft"""
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    condition: Optional[str] = None
    color: Optional[str] = None
    brand: Optional[str] = None
    size: Optional[str] = None
    status: Optional[str] = None


class DraftListResponse(BaseModel):
    """Response for listing drafts"""
    drafts: List[DraftItem]
    total: int
    page: int = 1
    page_size: int = 50


class PhotoCluster(BaseModel):
    """A cluster of photos representing a potential item"""
    cluster_id: str
    photo_paths: List[str]
    photo_count: int
    cluster_type: str  # "main_item", "label", "detail", "merged"
    confidence: float = Field(ge=0.0, le=1.0)
    label_detected: Optional[str] = None  # "care_label", "brand_tag", "size_label", etc.
    merge_target: Optional[str] = None  # cluster_id to merge into


class GroupingPlan(BaseModel):
    """Plan for grouping photos into items (anti-saucisson)"""
    plan_id: str
    total_photos: int
    clusters: List[PhotoCluster]
    estimated_items: int
    single_item_mode: bool
    grouping_reason: str  # Why this grouping was chosen
    created_at: datetime


class GenerateRequest(BaseModel):
    """Request to generate drafts from a plan or photos"""
    plan_id: Optional[str] = None  # Use existing plan
    photo_paths: Optional[List[str]] = None  # Or provide photos directly
    style: str = Field(default="classique", description="Description style")
    auto_grouping: bool = Field(default=True, description="Auto-detect single item mode")
    
    @model_validator(mode="after")
    def check_exactly_one_source(self) -> Self:
        """Ensure exactly one of plan_id or photo_paths is provided"""
        has_plan = self.plan_id is not None
        has_photos = self.photo_paths is not None and len(self.photo_paths) > 0
        
        if not has_plan and not has_photos:
            raise ValueError("Either plan_id or photo_paths must be provided")
        if has_plan and has_photos:
            raise ValueError("Cannot provide both plan_id and photo_paths")
        
        return self
    
    
class GenerateResponse(BaseModel):
    """Response from draft generation"""
    ok: bool
    generated_count: int
    skipped_count: int
    drafts: List[DraftItem]
    errors: List[str] = []
    message: Optional[str] = None


class ValidationError(BaseModel):
    """Validation error details"""
    field: str
    issue: str
    current_value: Any
    expected: str
