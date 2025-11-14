"""
API endpoints for CRM (Customer Relationship Management)
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional
from pydantic import BaseModel

from backend.crm.crm_manager import (
    CRMManager,
    Customer,
    CustomerStats,
    CustomerSegment,
    InteractionType
)
from backend.core.auth import get_current_user

router = APIRouter(prefix="/crm", tags=["crm"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateCustomerRequest(BaseModel):
    vinted_id: str
    username: str
    email: Optional[str] = None


class RecordPurchaseRequest(BaseModel):
    customer_id: str
    amount: float
    listing_id: str


class BlacklistRequest(BaseModel):
    reason: str


class AddNoteRequest(BaseModel):
    note: str


class CustomerResponse(BaseModel):
    id: str
    vinted_id: str
    username: str
    email: Optional[str]
    segment: str
    total_purchases: int
    total_spent: float
    avg_order_value: float
    is_blacklisted: bool
    blacklist_reason: Optional[str]

    class Config:
        from_attributes = True


class CustomerStatsResponse(BaseModel):
    total_customers: int
    vip_count: int
    loyal_count: int
    new_count: int
    churned_count: int
    blacklisted_count: int
    avg_lifetime_value: float
    repeat_purchase_rate: float


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/customers", response_model=CustomerResponse)
async def create_customer(
    request: CreateCustomerRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Create or update a customer"""
    try:
        manager = CRMManager()
        customer = await manager.create_or_update_customer(
            user_id=current_user['id'],
            vinted_id=request.vinted_id,
            username=request.username,
            email=request.email
        )

        return CustomerResponse(
            id=customer.id,
            vinted_id=customer.vinted_id,
            username=customer.username,
            email=customer.email,
            segment=customer.segment.value,
            total_purchases=customer.total_purchases,
            total_spent=customer.total_spent,
            avg_order_value=customer.avg_order_value,
            is_blacklisted=customer.is_blacklisted,
            blacklist_reason=customer.blacklist_reason
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating customer: {str(e)}")


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get customer by ID"""
    try:
        manager = CRMManager()
        customer = await manager.get_customer(customer_id, current_user['id'])

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        return CustomerResponse(
            id=customer.id,
            vinted_id=customer.vinted_id,
            username=customer.username,
            email=customer.email,
            segment=customer.segment.value,
            total_purchases=customer.total_purchases,
            total_spent=customer.total_spent,
            avg_order_value=customer.avg_order_value,
            is_blacklisted=customer.is_blacklisted,
            blacklist_reason=customer.blacklist_reason
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting customer: {str(e)}")


@router.post("/purchases")
async def record_purchase(
    request: RecordPurchaseRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Record a customer purchase"""
    try:
        manager = CRMManager()
        customer = await manager.record_purchase(
            customer_id=request.customer_id,
            user_id=current_user['id'],
            amount=request.amount,
            listing_id=request.listing_id
        )

        return {
            'ok': True,
            'customer_id': customer.id,
            'new_segment': customer.segment.value,
            'total_purchases': customer.total_purchases,
            'total_spent': customer.total_spent
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording purchase: {str(e)}")


@router.post("/customers/{customer_id}/blacklist")
async def add_to_blacklist(
    customer_id: str,
    request: BlacklistRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Add customer to blacklist"""
    try:
        manager = CRMManager()
        customer = await manager.add_to_blacklist(
            customer_id=customer_id,
            user_id=current_user['id'],
            reason=request.reason
        )

        return {
            'ok': True,
            'customer_id': customer.id,
            'is_blacklisted': customer.is_blacklisted,
            'reason': customer.blacklist_reason
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding to blacklist: {str(e)}")


@router.delete("/customers/{customer_id}/blacklist")
async def remove_from_blacklist(
    customer_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Remove customer from blacklist"""
    try:
        manager = CRMManager()
        customer = await manager.remove_from_blacklist(
            customer_id=customer_id,
            user_id=current_user['id']
        )

        return {
            'ok': True,
            'customer_id': customer.id,
            'is_blacklisted': customer.is_blacklisted
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing from blacklist: {str(e)}")


@router.get("/customers/{customer_id}/interactions")
async def get_customer_interactions(
    customer_id: str,
    limit: int = 20,
    current_user: Dict = Depends(get_current_user)
):
    """Get customer interaction history"""
    try:
        manager = CRMManager()
        interactions = await manager.get_customer_interactions(
            customer_id=customer_id,
            user_id=current_user['id'],
            limit=limit
        )

        return [
            {
                'type': i.interaction_type.value,
                'summary': i.summary,
                'details': i.details,
                'sentiment': i.sentiment,
                'created_at': i.created_at.isoformat()
            }
            for i in interactions
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting interactions: {str(e)}")


@router.get("/segments/{segment}", response_model=List[CustomerResponse])
async def get_customers_by_segment(
    segment: str,
    limit: int = 50,
    current_user: Dict = Depends(get_current_user)
):
    """Get customers in a specific segment"""
    try:
        manager = CRMManager()
        customers = await manager.get_customers_by_segment(
            user_id=current_user['id'],
            segment=CustomerSegment(segment),
            limit=limit
        )

        return [
            CustomerResponse(
                id=c.id,
                vinted_id=c.vinted_id,
                username=c.username,
                email=c.email,
                segment=c.segment.value,
                total_purchases=c.total_purchases,
                total_spent=c.total_spent,
                avg_order_value=c.avg_order_value,
                is_blacklisted=c.is_blacklisted,
                blacklist_reason=c.blacklist_reason
            )
            for c in customers
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting segment: {str(e)}")


@router.get("/stats", response_model=CustomerStatsResponse)
async def get_crm_stats(
    current_user: Dict = Depends(get_current_user)
):
    """Get CRM statistics"""
    try:
        manager = CRMManager()
        stats = await manager.get_crm_stats(current_user['id'])

        return CustomerStatsResponse(
            total_customers=stats.total_customers,
            vip_count=stats.vip_count,
            loyal_count=stats.loyal_count,
            new_count=stats.new_count,
            churned_count=stats.churned_count,
            blacklisted_count=stats.blacklisted_count,
            avg_lifetime_value=stats.avg_lifetime_value,
            repeat_purchase_rate=stats.repeat_purchase_rate
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@router.post("/customers/{customer_id}/notes")
async def add_customer_note(
    customer_id: str,
    request: AddNoteRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Add a note to customer profile"""
    try:
        manager = CRMManager()
        customer = await manager.add_note(
            customer_id=customer_id,
            user_id=current_user['id'],
            note=request.note
        )

        return {
            'ok': True,
            'customer_id': customer.id,
            'notes': customer.notes
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding note: {str(e)}")


@router.get("/search", response_model=List[CustomerResponse])
async def search_customers(
    query: Optional[str] = None,
    segment: Optional[str] = None,
    min_purchases: Optional[int] = None,
    blacklisted_only: bool = False,
    limit: int = 50,
    current_user: Dict = Depends(get_current_user)
):
    """Search customers with filters"""
    try:
        manager = CRMManager()
        customers = await manager.search_customers(
            user_id=current_user['id'],
            query=query,
            segment=CustomerSegment(segment) if segment else None,
            min_purchases=min_purchases,
            blacklisted_only=blacklisted_only,
            limit=limit
        )

        return [
            CustomerResponse(
                id=c.id,
                vinted_id=c.vinted_id,
                username=c.username,
                email=c.email,
                segment=c.segment.value,
                total_purchases=c.total_purchases,
                total_spent=c.total_spent,
                avg_order_value=c.avg_order_value,
                is_blacklisted=c.is_blacklisted,
                blacklist_reason=c.blacklist_reason
            )
            for c in customers
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching customers: {str(e)}")
