from fastapi import APIRouter

router = APIRouter(prefix="/vinted/offers", tags=["offers"])


@router.get("")
async def get_offers():
    """Get offers (mock)"""
    return {
        "offers": [
            {
                "id": 1,
                "item_id": 123,
                "amount": 25.00,
                "status": "pending",
                "buyer_name": "John Doe"
            },
            {
                "id": 2,
                "item_id": 456,
                "amount": 15.00,
                "status": "accepted",
                "buyer_name": "Jane Smith"
            }
        ],
        "total": 2
    }


@router.get("/{offer_id}")
async def get_offer(offer_id: int):
    """Get single offer (mock)"""
    return {
        "id": offer_id,
        "item_id": 123,
        "amount": 25.00,
        "status": "pending",
        "buyer_name": "John Doe",
        "created_at": "2025-10-13T10:00:00Z"
    }
