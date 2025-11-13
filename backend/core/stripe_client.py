"""
Stripe Integration for VintedBot SaaS
Handles subscription billing, customer portal, webhooks
"""
import os
import stripe
from dotenv import load_dotenv
from typing import Optional, Dict, Any

load_dotenv()

# Stripe Configuration with validation
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Validate Stripe configuration at startup
if not stripe.api_key or stripe.api_key == "":
    import sys
    print("WARNING: STRIPE_SECRET_KEY not set - Stripe features disabled")
    print("   Set STRIPE_SECRET_KEY to enable subscriptions")

if not STRIPE_WEBHOOK_SECRET:
    import sys
    print("WARNING: STRIPE_WEBHOOK_SECRET not set - webhooks will fail")

# Pricing Configuration (monthly prices in cents)
PRICING_PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "price_id": None,
        "quotas": {
            "drafts": 50,
            "publications_month": 10,
            "ai_analyses_month": 20,
            "photos_storage_mb": 500
        }
    },
    "starter": {
        "name": "Starter",
        "price": 1900,  # 19€/month
        "price_id": os.getenv("STRIPE_STARTER_PRICE_ID"),
        "quotas": {
            "drafts": 500,
            "publications_month": 100,
            "ai_analyses_month": 200,
            "photos_storage_mb": 5000
        }
    },
    "pro": {
        "name": "Pro",
        "price": 4900,  # 49€/month
        "price_id": os.getenv("STRIPE_PRO_PRICE_ID"),
        "quotas": {
            "drafts": 2000,
            "publications_month": 500,
            "ai_analyses_month": 1000,
            "photos_storage_mb": 20000
        }
    },
    "scale": {
        "name": "Scale",
        "price": 9900,  # 99€/month
        "price_id": os.getenv("STRIPE_SCALE_PRICE_ID"),
        "quotas": {
            "drafts": 10000,
            "publications_month": 2500,
            "ai_analyses_month": 5000,
            "photos_storage_mb": 100000
        }
    }
}

# Validate price IDs for paid plans (after PRICING_PLANS is defined)
for plan_key in ["starter", "pro", "scale"]:
    price_id = PRICING_PLANS[plan_key]["price_id"]
    if not price_id:
        import sys
        print(f"WARNING: STRIPE_{plan_key.upper()}_PRICE_ID not set - {plan_key} plan unavailable")


def create_checkout_session(
    user_id: int,
    user_email: str,
    plan: str,
    success_url: str,
    cancel_url: str,
    existing_customer_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a Stripe checkout session for subscription
    
    Args:
        user_id: Internal user ID
        user_email: User's email
        plan: Plan name (starter, pro, scale)
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if user cancels
        existing_customer_id: Existing Stripe customer ID to reuse
        
    Returns:
        {
            "id": "cs_...",
            "url": "https://checkout.stripe.com/...",
            "customer": "cus_..."
        }
    """
    if not stripe.api_key:
        raise ValueError("Stripe is not configured. Please contact support.")
    
    if plan not in PRICING_PLANS or plan == "free":
        raise ValueError(f"Invalid plan: {plan}")
    
    plan_config = PRICING_PLANS[plan]
    price_id = plan_config["price_id"]
    
    if not price_id:
        raise ValueError(f"Stripe price ID not configured for plan: {plan}")
    
    # Reuse existing customer or create new one
    if existing_customer_id:
        customer_id = existing_customer_id
    else:
        customer = stripe.Customer.create(
            email=user_email,
            metadata={"user_id": str(user_id)}
        )
        customer_id = customer.id
    
    # Create checkout session
    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{
            "price": price_id,
            "quantity": 1
        }],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": str(user_id),
            "plan": plan
        }
    )
    
    return {
        "id": session.id,
        "url": session.url,
        "customer": customer_id
    }


def create_customer_portal_session(
    customer_id: str,
    return_url: str
) -> Dict[str, str]:
    """
    Create a Stripe customer portal session for subscription management
    
    Args:
        customer_id: Stripe customer ID
        return_url: URL to redirect after portal session
        
    Returns:
        {"url": "https://billing.stripe.com/..."}
    """
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url
    )
    
    return {"url": session.url}


def verify_webhook_signature(payload: bytes, signature: str) -> Optional[stripe.Event]:
    """
    Verify Stripe webhook signature and return event
    
    Args:
        payload: Raw request body
        signature: Stripe-Signature header value
        
    Returns:
        stripe.Event or None if verification fails or webhook secret not configured
    """
    if not STRIPE_WEBHOOK_SECRET:
        return None
    
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, STRIPE_WEBHOOK_SECRET
        )
        return event
    except stripe.error.SignatureVerificationError:
        return None
    except Exception:
        return None


def get_plan_quotas(plan: str) -> Dict[str, int]:
    """Get quota limits for a plan"""
    if plan not in PRICING_PLANS:
        plan = "free"
    return PRICING_PLANS[plan]["quotas"]
