"""
Pydantic schemas for Vinted API endpoints
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SessionRequest(BaseModel):
    """Request to save Vinted session"""
    cookie: str = Field(..., alias="cookie_value", description="Complete Cookie header value")
    user_agent: str = Field(..., description="User-Agent string")
    expires_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True  # Accept both 'cookie' and 'cookie_value'


class SessionResponse(BaseModel):
    """Response after saving session - LOVABLE FORMAT"""
    session_id: int
    valid: bool
    created_at: str
    note: Optional[str] = None


class AuthCheckResponse(BaseModel):
    """Response for auth check"""
    authenticated: bool
    username: Optional[str] = None
    user_id: Optional[str] = None


class PhotoUploadResponse(BaseModel):
    """Response after photo upload"""
    ok: bool
    photo: Dict[str, str] = Field(
        ..., 
        description="Photo metadata with temp_id and url"
    )


class PriceSuggestion(BaseModel):
    """AI price suggestion with min/target/max"""
    min: float = Field(..., gt=0)
    target: float = Field(..., gt=0)
    max: float = Field(..., gt=0)


class PublishFlags(BaseModel):
    """Publication readiness flags"""
    publish_ready: bool = Field(default=False, description="True if all validations passed")
    ai_validated: bool = Field(default=False)
    photos_validated: bool = Field(default=False)


class ListingPrepareRequest(BaseModel):
    """Request to prepare a listing (draft)"""
    title: str = Field(..., min_length=1, max_length=160)
    price: float = Field(..., gt=0)
    description: str
    brand: Optional[str] = None
    size: Optional[str] = None
    condition: Optional[str] = None
    color: Optional[str] = None
    category_hint: Optional[str] = None
    photos: List[str] = Field(default=[], description="List of photo temp_ids or URLs")
    
    # AI-enriched fields for validation
    hashtags: Optional[List[str]] = Field(default=None, description="3-5 hashtags for better visibility")
    price_suggestion: Optional[PriceSuggestion] = None
    flags: Optional[PublishFlags] = None
    
    dry_run: bool = Field(default=False, description="If true, don't actually prepare")


class ListingPrepareResponse(BaseModel):
    """Response after preparing listing"""
    ok: bool
    dry_run: bool
    confirm_token: Optional[str] = None
    preview_url: Optional[str] = None
    screenshot_b64: Optional[str] = None
    draft_context: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None


class ListingPublishRequest(BaseModel):
    """Request to publish a prepared listing"""
    confirm_token: str = Field(..., description="Token from prepare endpoint")
    dry_run: bool = Field(default=False, description="If false, actually publish")


class ListingPublishResponse(BaseModel):
    """Response after publishing"""
    ok: bool
    dry_run: bool
    listing_id: Optional[str] = None
    listing_url: Optional[str] = None
    needs_manual: Optional[bool] = None
    reason: Optional[str] = None


class PublishJob(BaseModel):
    """Publish job in queue - LOVABLE FORMAT"""
    job_id: str
    item_id: int | str
    status: str = Field(..., description="queued | processing | success | failed | blocked")
    mode: str = Field(..., description="manual | automated")
    scheduled_at: Optional[str] = None
    logs: Optional[str] = None
    screenshot: Optional[str] = None
