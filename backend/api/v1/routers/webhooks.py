"""
Webhooks API Router
Manage external webhooks (Zapier, Make, custom integrations)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict
from loguru import logger

from backend.core.auth import get_current_user
from backend.services.webhook_service import webhook_service
from backend.models.user import User


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# Request/Response Models
class CreateWebhookRequest(BaseModel):
    url: HttpUrl
    events: Optional[List[str]] = None  # None = subscribe to all events
    secret: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


class WebhookResponse(BaseModel):
    id: str
    url: str
    events: Optional[List[str]]
    active: bool
    created_at: str
    last_triggered: Optional[str] = None
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0


class TestWebhookRequest(BaseModel):
    url: HttpUrl
    headers: Optional[Dict[str, str]] = None


@router.get("/events")
async def get_available_events():
    """
    Get list of available webhook events

    Returns:
        List of supported events
    """
    events = [
        {
            "name": "listing.created",
            "description": "Triggered when a new listing is created"
        },
        {
            "name": "listing.sold",
            "description": "Triggered when a listing is sold"
        },
        {
            "name": "message.received",
            "description": "Triggered when a message is received"
        },
        {
            "name": "account.connected",
            "description": "Triggered when a Vinted account is connected"
        },
        {
            "name": "automation.completed",
            "description": "Triggered when an automation task completes"
        }
    ]

    return {"events": events}


@router.post("", response_model=WebhookResponse)
async def create_webhook(
    request: CreateWebhookRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new webhook

    Args:
        request: Webhook configuration
        current_user: Authenticated user

    Returns:
        Created webhook
    """
    # Validate events
    valid_events = [
        "listing.created",
        "listing.sold",
        "message.received",
        "account.connected",
        "automation.completed"
    ]

    if request.events:
        for event in request.events:
            if event not in valid_events:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid event: {event}"
                )

    # Create webhook
    webhook_id = await webhook_service.register_webhook(
        user_id=str(current_user.id),
        url=str(request.url),
        events=request.events,
        secret=request.secret,
        headers=request.headers
    )

    if not webhook_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create webhook"
        )

    # Get created webhook
    webhooks = await webhook_service.get_user_webhooks(str(current_user.id))
    webhook = next((w for w in webhooks if w['id'] == webhook_id), None)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook created but not found"
        )

    return WebhookResponse(
        id=webhook['id'],
        url=webhook['url'],
        events=webhook.get('events'),
        active=webhook['active'],
        created_at=webhook['created_at'].isoformat(),
        last_triggered=webhook['last_triggered'].isoformat() if webhook.get('last_triggered') else None,
        total_calls=webhook.get('total_calls', 0),
        successful_calls=webhook.get('successful_calls', 0),
        failed_calls=webhook.get('failed_calls', 0)
    )


@router.get("", response_model=List[WebhookResponse])
async def list_webhooks(
    current_user: User = Depends(get_current_user)
):
    """
    Get all webhooks for current user

    Returns:
        List of webhooks
    """
    webhooks = await webhook_service.get_user_webhooks(str(current_user.id))

    return [
        WebhookResponse(
            id=webhook['id'],
            url=webhook['url'],
            events=webhook.get('events'),
            active=webhook['active'],
            created_at=webhook['created_at'].isoformat(),
            last_triggered=webhook['last_triggered'].isoformat() if webhook.get('last_triggered') else None,
            total_calls=webhook.get('total_calls', 0),
            successful_calls=webhook.get('successful_calls', 0),
            failed_calls=webhook.get('failed_calls', 0)
        )
        for webhook in webhooks
    ]


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a webhook

    Args:
        webhook_id: Webhook ID
        current_user: Authenticated user

    Returns:
        Success message
    """
    success = await webhook_service.delete_webhook(
        webhook_id=webhook_id,
        user_id=str(current_user.id)
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found or already deleted"
        )

    return {
        "success": True,
        "message": "Webhook deleted successfully"
    }


@router.post("/test")
async def test_webhook(
    request: TestWebhookRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Test a webhook URL

    Args:
        request: Test webhook request
        current_user: Authenticated user

    Returns:
        Test result
    """
    result = await webhook_service.test_webhook(
        url=str(request.url),
        headers=request.headers
    )

    return result


@router.get("/stats")
async def get_webhook_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get webhook statistics for current user

    Returns:
        Webhook statistics
    """
    webhooks = await webhook_service.get_user_webhooks(str(current_user.id))

    total_webhooks = len(webhooks)
    active_webhooks = sum(1 for w in webhooks if w['active'])
    total_calls = sum(w.get('total_calls', 0) for w in webhooks)
    successful_calls = sum(w.get('successful_calls', 0) for w in webhooks)
    failed_calls = sum(w.get('failed_calls', 0) for w in webhooks)

    success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0

    return {
        "total_webhooks": total_webhooks,
        "active_webhooks": active_webhooks,
        "total_calls": total_calls,
        "successful_calls": successful_calls,
        "failed_calls": failed_calls,
        "success_rate": round(success_rate, 2)
    }
