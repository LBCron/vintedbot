"""
Multi-account management schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VintedAccount(BaseModel):
    """Vinted account configuration"""
    id: str
    user_id: str  # Backend user who owns this account
    nickname: str  # Friendly name (e.g., "Main Account", "Kids Clothes")
    vinted_username: Optional[str] = None
    vinted_user_id: Optional[str] = None
    cookie: str  # Encrypted session cookie
    user_agent: str
    is_active: bool = True
    is_default: bool = False
    last_used: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AccountStats(BaseModel):
    """Statistics for a Vinted account"""
    account_id: str
    total_listings: int
    active_listings: int
    total_sales: int
    total_revenue: float
    followers: int
    following: int


class AccountSwitchRequest(BaseModel):
    """Request to switch active account"""
    account_id: str


class AccountListResponse(BaseModel):
    """List of user's Vinted accounts"""
    accounts: List[VintedAccount]
    active_account_id: Optional[str] = None
