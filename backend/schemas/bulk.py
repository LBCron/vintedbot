"""
Pydantic schemas for bulk photo analysis and draft generation
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


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
