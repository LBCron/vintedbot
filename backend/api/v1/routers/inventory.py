"""
API endpoints for Advanced Inventory Management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional
from pydantic import BaseModel

from backend.inventory.inventory_manager import (
    InventoryManager,
    InventoryItem,
    InventoryStats,
    StockStatus,
    Platform,
    MovementType
)
from backend.core.auth import get_current_user

router = APIRouter(prefix="/inventory", tags=["inventory"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateItemRequest(BaseModel):
    """Request to create inventory item"""
    name: str
    category: str
    cost_price: float
    quantity: int = 1
    brand: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    condition: str = "Bon état"
    location: str = "default"
    notes: Optional[str] = None
    sku: Optional[str] = None


class UpdateQuantityRequest(BaseModel):
    """Request to update quantity"""
    quantity_change: int
    movement_type: str
    notes: Optional[str] = None


class CreateListingRequest(BaseModel):
    """Request to create platform listing"""
    inventory_id: str
    platform: str
    platform_listing_id: str
    listing_price: float
    quantity_listed: int


class InventoryItemResponse(BaseModel):
    """Inventory item response"""
    id: str
    sku: str
    name: str
    category: str
    brand: Optional[str]
    size: Optional[str]
    color: Optional[str]
    condition: str
    cost_price: float
    quantity: int
    status: str
    location: str
    notes: Optional[str]

    class Config:
        from_attributes = True


class InventoryStatsResponse(BaseModel):
    """Inventory statistics response"""
    total_items: int
    total_value: float
    potential_revenue: float
    items_in_stock: int
    items_listed: int
    items_sold: int
    low_stock_count: int
    platforms_active: List[str]
    avg_turnover_days: float


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/items", response_model=InventoryItemResponse)
async def create_inventory_item(
    request: CreateItemRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a new inventory item

    Auto-generates SKU if not provided
    """
    try:
        manager = InventoryManager()
        item = await manager.create_item(
            user_id=current_user['id'],
            name=request.name,
            category=request.category,
            cost_price=request.cost_price,
            quantity=request.quantity,
            brand=request.brand,
            size=request.size,
            color=request.color,
            condition=request.condition,
            location=request.location,
            notes=request.notes,
            sku=request.sku
        )

        return InventoryItemResponse(
            id=item.id,
            sku=item.sku,
            name=item.name,
            category=item.category,
            brand=item.brand,
            size=item.size,
            color=item.color,
            condition=item.condition,
            cost_price=item.cost_price,
            quantity=item.quantity,
            status=item.status.value,
            location=item.location,
            notes=item.notes
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating item: {str(e)}")


@router.get("/items/{item_id}", response_model=InventoryItemResponse)
async def get_inventory_item(
    item_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get inventory item by ID"""
    try:
        manager = InventoryManager()
        item = await manager.get_item(item_id, current_user['id'])

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        return InventoryItemResponse(
            id=item.id,
            sku=item.sku,
            name=item.name,
            category=item.category,
            brand=item.brand,
            size=item.size,
            color=item.color,
            condition=item.condition,
            cost_price=item.cost_price,
            quantity=item.quantity,
            status=item.status.value,
            location=item.location,
            notes=item.notes
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting item: {str(e)}")


@router.patch("/items/{item_id}/quantity", response_model=InventoryItemResponse)
async def update_item_quantity(
    item_id: str,
    request: UpdateQuantityRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Update item quantity

    quantity_change can be positive (add) or negative (remove)
    """
    try:
        manager = InventoryManager()
        item = await manager.update_quantity(
            item_id=item_id,
            user_id=current_user['id'],
            quantity_change=request.quantity_change,
            movement_type=MovementType(request.movement_type),
            notes=request.notes
        )

        return InventoryItemResponse(
            id=item.id,
            sku=item.sku,
            name=item.name,
            category=item.category,
            brand=item.brand,
            size=item.size,
            color=item.color,
            condition=item.condition,
            cost_price=item.cost_price,
            quantity=item.quantity,
            status=item.status.value,
            location=item.location,
            notes=item.notes
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating quantity: {str(e)}")


@router.get("/stats", response_model=InventoryStatsResponse)
async def get_inventory_stats(
    current_user: Dict = Depends(get_current_user)
):
    """Get inventory statistics"""
    try:
        manager = InventoryManager()
        stats = await manager.get_inventory_stats(current_user['id'])

        return InventoryStatsResponse(
            total_items=stats.total_items,
            total_value=stats.total_value,
            potential_revenue=stats.potential_revenue,
            items_in_stock=stats.items_in_stock,
            items_listed=stats.items_listed,
            items_sold=stats.items_sold,
            low_stock_count=stats.low_stock_count,
            platforms_active=stats.platforms_active,
            avg_turnover_days=stats.avg_turnover_days
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@router.get("/search", response_model=List[InventoryItemResponse])
async def search_inventory(
    sku: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    status: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 50,
    current_user: Dict = Depends(get_current_user)
):
    """Search inventory with filters"""
    try:
        manager = InventoryManager()
        items = await manager.search_inventory(
            user_id=current_user['id'],
            sku=sku,
            category=category,
            brand=brand,
            status=StockStatus(status) if status else None,
            location=location,
            limit=limit
        )

        return [
            InventoryItemResponse(
                id=item.id,
                sku=item.sku,
                name=item.name,
                category=item.category,
                brand=item.brand,
                size=item.size,
                color=item.color,
                condition=item.condition,
                cost_price=item.cost_price,
                quantity=item.quantity,
                status=item.status.value,
                location=item.location,
                notes=item.notes
            )
            for item in items
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching inventory: {str(e)}")


@router.post("/listings")
async def create_platform_listing(
    request: CreateListingRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Create a listing on a platform"""
    try:
        manager = InventoryManager()
        listing = await manager.create_platform_listing(
            inventory_id=request.inventory_id,
            user_id=current_user['id'],
            platform=Platform(request.platform),
            platform_listing_id=request.platform_listing_id,
            listing_price=request.listing_price,
            quantity_listed=request.quantity_listed
        )

        return {
            'ok': True,
            'listing_id': listing.id,
            'platform': listing.platform.value,
            'quantity_listed': listing.quantity_listed
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating listing: {str(e)}")


@router.post("/listings/{listing_id}/sold")
async def mark_listing_sold(
    listing_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Mark a platform listing as sold"""
    try:
        manager = InventoryManager()
        result = await manager.mark_listing_sold(
            listing_id=listing_id,
            user_id=current_user['id']
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking sold: {str(e)}")


@router.get("/sku/{sku}/report")
async def get_sku_report(
    sku: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get detailed report for a SKU"""
    try:
        manager = InventoryManager()
        report = await manager.get_sku_report(sku, current_user['id'])

        if not report:
            raise HTTPException(status_code=404, detail="SKU not found")

        return {
            'sku': report.sku,
            'quantity': report.quantity,
            'cost_price': report.cost_price,
            'total_cost': report.total_cost,
            'platforms': report.platforms,
            'movements': [
                {
                    'type': m.movement_type.value,
                    'quantity': m.quantity,
                    'notes': m.notes,
                    'created_at': m.created_at.isoformat()
                }
                for m in report.movements
            ],
            'performance': report.performance
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting SKU report: {str(e)}")


@router.post("/bulk/location")
async def bulk_update_location(
    item_ids: List[str],
    new_location: str,
    current_user: Dict = Depends(get_current_user)
):
    """Bulk update location for multiple items"""
    try:
        manager = InventoryManager()
        updated = await manager.bulk_update_location(
            user_id=current_user['id'],
            item_ids=item_ids,
            new_location=new_location
        )

        return {
            'ok': True,
            'updated_count': updated
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error bulk updating: {str(e)}")
