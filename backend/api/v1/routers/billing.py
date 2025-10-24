"""
Billing Router - Stripe Integration
Handles subscription checkout, customer portal, webhooks
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging

from backend.core.auth import get_current_user, User
from backend.core.storage import get_storage
from backend.core.stripe_client import (
    create_checkout_session,
    create_customer_portal_session,
    verify_webhook_signature,
    get_plan_quotas,
    PRICING_PLANS
)

router = APIRouter(prefix="/billing", tags=["Billing"])
logger = logging.getLogger(__name__)


class CheckoutRequest(BaseModel):
    plan: str  # starter, pro, scale
    success_url: str
    cancel_url: str


class PortalRequest(BaseModel):
    return_url: str


@router.get("/plans")
async def get_pricing_plans():
    """Get available pricing plans"""
    return {
        "plans": {
            plan_key: {
                "name": plan_data["name"],
                "price_cents": plan_data["price"],
                "price_eur": plan_data["price"] / 100,
                "quotas": plan_data["quotas"]
            }
            for plan_key, plan_data in PRICING_PLANS.items()
        }
    }


@router.post("/checkout")
async def create_checkout(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create Stripe checkout session for subscription upgrade
    """
    try:
        # Get user's existing Stripe customer ID if available
        storage = get_storage()
        user_data = storage.get_user_by_id(current_user.id)
        existing_customer_id = user_data.get("stripe_customer_id") if user_data else None
        
        session = create_checkout_session(
            user_id=current_user.id,
            user_email=current_user.email,
            plan=request.plan,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            existing_customer_id=existing_customer_id
        )
        
        # Store customer_id in database
        storage = get_storage()
        storage.update_user_stripe_customer(current_user.id, session["customer"])
        
        return {
            "checkout_url": session["url"],
            "session_id": session["id"]
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/portal")
async def create_portal(
    request: PortalRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create Stripe customer portal session for subscription management
    """
    storage = get_storage()
    user = storage.get_user_by_id(current_user.id)
    
    if not user or not user.get("stripe_customer_id"):
        raise HTTPException(
            status_code=400,
            detail="No active subscription found. Please subscribe first."
        )
    
    try:
        portal = create_customer_portal_session(
            customer_id=user["stripe_customer_id"],
            return_url=request.return_url
        )
        
        return {"portal_url": portal["url"]}
    
    except Exception as e:
        logger.error(f"Portal creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature")
):
    """
    Handle Stripe webhooks for subscription events
    
    Events handled:
    - checkout.session.completed: Subscription created
    - customer.subscription.updated: Plan changed
    - customer.subscription.deleted: Subscription cancelled
    """
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")
    
    # Get raw body for signature verification
    payload = await request.body()
    
    # Verify webhook signature
    event = verify_webhook_signature(payload, stripe_signature)
    if not event:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    storage = get_storage()
    event_type = event["type"]
    
    try:
        if event_type == "checkout.session.completed":
            # Subscription created
            session = event["data"]["object"]
            user_id = int(session["metadata"]["user_id"])
            plan = session["metadata"]["plan"]
            customer_id = session["customer"]
            subscription_id = session.get("subscription")
            
            # Update user subscription
            storage.update_user_subscription(
                user_id=user_id,
                plan=plan,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id
            )
            
            # Update quotas
            quotas = get_plan_quotas(plan)
            storage.update_user_quotas(user_id, quotas)
            
            logger.info(f"✅ Subscription created: user={user_id}, plan={plan}")
        
        elif event_type == "customer.subscription.updated":
            # Plan changed or subscription updated
            subscription = event["data"]["object"]
            customer_id = subscription["customer"]
            
            # Find user by customer_id
            user = storage.get_user_by_stripe_customer(customer_id)
            if user:
                # Determine new plan from price_id
                price_id = subscription["items"]["data"][0]["price"]["id"]
                new_plan = None
                for plan_key, plan_data in PRICING_PLANS.items():
                    if plan_data.get("price_id") == price_id:
                        new_plan = plan_key
                        break
                
                if new_plan:
                    storage.update_user_subscription(
                        user_id=user["id"],
                        plan=new_plan,
                        stripe_subscription_id=subscription["id"]
                    )
                    
                    quotas = get_plan_quotas(new_plan)
                    storage.update_user_quotas(user["id"], quotas)
                    
                    logger.info(f"✅ Subscription updated: user={user['id']}, plan={new_plan}")
        
        elif event_type == "customer.subscription.deleted":
            # Subscription cancelled
            subscription = event["data"]["object"]
            customer_id = subscription["customer"]
            
            user = storage.get_user_by_stripe_customer(customer_id)
            if user:
                # Downgrade to free plan
                storage.update_user_subscription(
                    user_id=user["id"],
                    plan="free",
                    stripe_subscription_id=None
                )
                
                quotas = get_plan_quotas("free")
                storage.update_user_quotas(user["id"], quotas)
                
                logger.info(f"✅ Subscription cancelled: user={user['id']} → free plan")
        
        return JSONResponse({"status": "success"})
    
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
