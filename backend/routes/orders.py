from fastapi import APIRouter

router = APIRouter(prefix="/vinted/orders", tags=["orders"])


@router.get("")
async def get_orders():
    """Get orders (mock)"""
    return {
        "orders": [
            {
                "id": 1,
                "item_id": 123,
                "buyer_name": "Alice Johnson",
                "status": "shipped",
                "tracking_number": "TRACK123456"
            },
            {
                "id": 2,
                "item_id": 789,
                "buyer_name": "Bob Wilson",
                "status": "pending_shipment",
                "tracking_number": None
            }
        ],
        "total": 2
    }


@router.get("/{order_id}")
async def get_order(order_id: int):
    """Get single order (mock)"""
    return {
        "id": order_id,
        "item_id": 123,
        "buyer_name": "Alice Johnson",
        "status": "shipped",
        "tracking_number": "TRACK123456",
        "shipping_address": "123 Main St, City, Country",
        "created_at": "2025-10-13T09:00:00Z"
    }


@router.post("/{order_id}/ship")
async def ship_order(order_id: int, tracking_number: str):
    """Mark order as shipped (mock)"""
    return {
        "success": True,
        "order_id": order_id,
        "status": "shipped",
        "tracking_number": tracking_number
    }
