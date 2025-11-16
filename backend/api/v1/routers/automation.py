"""
Automation API - Auto-bump, auto-follow, auto-messages, etc.
WITH REAL PLAYWRIGHT EXECUTION
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import uuid
import os
import asyncio
import random
import time
from backend.core.auth import get_current_user, User
from backend.core.storage import get_store
from backend.core.vinted_client import VintedClient, CaptchaDetected
from backend.core.vinted_api_client import VintedAPIClient
from backend.core.session import SessionVault
from backend.schemas.automation import (
    AutomationRule,
    AutomationJob,
    AutomationStatus,
    BumpConfig,
    FollowConfig,
    MessageConfig,
    FavoriteConfig,
    AutomationSummary,
    AutomationType
)

router = APIRouter(prefix="/automation", tags=["automation"])

# Initialize session vault
vault = SessionVault(
    key=os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"),
    storage_path="backend/data/session.enc"
)


# Helper function for anti-detection delays
async def human_delay(min_ms: int = 500, max_ms: int = 2000):
    """Random human-like delay"""
    await asyncio.sleep(random.randint(min_ms, max_ms) / 1000)


@router.get("/rules", response_model=List[AutomationRule])
async def list_automation_rules(
    current_user: User = Depends(get_current_user)
):
    """List all automation rules for current user"""
    store = get_store()
    user_id = str(current_user.id)
    
    rules = store.get_automation_rules(user_id)
    
    return [
        AutomationRule(
            id=rule["id"],
            user_id=rule["user_id"],
            type=AutomationType(rule["type"]),
            config=rule["config"],
            enabled=rule["enabled"],
            created_at=datetime.fromisoformat(rule["created_at"]),
            last_run=datetime.fromisoformat(rule["last_run"]) if rule["last_run"] else None,
            next_run=datetime.fromisoformat(rule["next_run"]) if rule["next_run"] else None
        )
        for rule in rules
    ]


@router.post("/bump/config")
async def configure_auto_bump(
    config: BumpConfig,
    current_user: User = Depends(get_current_user)
):
    """
    🔄 AUTO-BUMP: Automatically repost listings to top
    
    Feature from Dotb, VatBot - saves money vs Vinted's paid bumps!
    - Rotates listings intelligently
    - Randomized delays to avoid detection
    - Configurable intervals
    """
    store = get_store()
    user_id = str(current_user.id)
    
    # Create or update bump rule
    rule_id = f"bump_{user_id}_{uuid.uuid4().hex[:8]}"
    
    store.save_automation_rule(
        rule_id=rule_id,
        user_id=user_id,
        rule_type="bump",
        config=config.model_dump(),
        enabled=config.enabled
    )
    
    return {
        "ok": True,
        "message": "Auto-bump configured successfully",
        "rule_id": rule_id,
        "config": config.model_dump()
    }


@router.post("/follow/config")
async def configure_auto_follow(
    config: FollowConfig,
    current_user: User = Depends(get_current_user)
):
    """
    👥 AUTO-FOLLOW: Automated follower growth
    
    Feature from VatBot - ~10% follow-back rate!
    - Target specific categories/brands
    - Smart filtering (min listings, blacklist)
    - Auto-unfollow after X days
    - Daily limits to avoid detection
    """
    store = get_store()
    user_id = str(current_user.id)
    
    # Create or update follow rule
    rule_id = f"follow_{user_id}_{uuid.uuid4().hex[:8]}"
    
    store.save_automation_rule(
        rule_id=rule_id,
        user_id=user_id,
        rule_type="follow",
        config=config.model_dump(),
        enabled=config.enabled
    )
    
    return {
        "ok": True,
        "message": "Auto-follow configured successfully",
        "rule_id": rule_id,
        "config": config.model_dump()
    }


@router.post("/messages/config")
async def configure_auto_messages(
    config: MessageConfig,
    current_user: User = Depends(get_current_user)
):
    """
    💬 AUTO-MESSAGES: Send automatic offers to likers
    
    Feature from Dotb, Sales Bot - increase conversion!
    - Personalized templates with variables
    - Trigger on likes, follows, messages
    - Human-like delays
    - Blacklist support
    """
    store = get_store()
    user_id = str(current_user.id)
    
    # Create or update message rule
    rule_id = f"message_{user_id}_{uuid.uuid4().hex[:8]}"
    
    store.save_automation_rule(
        rule_id=rule_id,
        user_id=user_id,
        rule_type="message",
        config=config.model_dump(),
        enabled=config.enabled
    )
    
    # Save message templates separately
    with store.get_connection() as conn:
        cursor = conn.cursor()
        for template in config.templates:
            cursor.execute("""
                INSERT OR REPLACE INTO message_templates 
                (id, user_id, name, trigger, template, delay_minutes, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                template.id,
                user_id,
                template.name,
                template.trigger,
                template.template,
                template.delay_minutes,
                1 if template.enabled else 0
            ))
        conn.commit()
    
    return {
        "ok": True,
        "message": "Auto-messages configured successfully",
        "rule_id": rule_id,
        "config": config.model_dump()
    }


@router.get("/summary", response_model=AutomationSummary)
async def get_automation_summary(
    current_user: User = Depends(get_current_user)
):
    """Get summary of all automation activities"""
    store = get_store()
    user_id = str(current_user.id)
    
    summary = store.get_automation_summary(user_id, days=1)
    
    return AutomationSummary(
        total_rules=summary["total_rules"],
        active_rules=summary["active_rules"],
        jobs_today=summary["jobs_today"],
        jobs_successful=summary["jobs_successful"],
        jobs_failed=summary["jobs_failed"],
        next_scheduled=None,
        recent_jobs=[
            AutomationJob(
                id=job["id"],
                rule_id=job["rule_id"],
                type=AutomationType(job["type"]),
                status=AutomationStatus(job["status"]),
                target_id=job["target_id"],
                result=job["result"],
                error=job["error"],
                started_at=datetime.fromisoformat(job["started_at"]),
                completed_at=datetime.fromisoformat(job["completed_at"]) if job["completed_at"] else None
            )
            for job in summary["recent_jobs"]
        ]
    )


@router.post("/bump/execute")
async def execute_bump_now(
    listing_ids: List[str],
    current_user: User = Depends(get_current_user)
):
    """
    🚀 INSTANT BUMP: Manually trigger REAL bump for specific listings
    Uses HTTP API (10x faster than Playwright!)
    """
    store = get_store()
    user_id = str(current_user.id)

    # Get Vinted session
    session = vault.load_session()
    if not session:
        raise HTTPException(status_code=401, detail="No Vinted session found. Please authenticate first.")

    bumped_listings = []
    failed_listings = []

    # Initialize HTTP API client (much faster than Playwright!)
    async with VintedAPIClient(session) as client:
        for listing_id in listing_ids:
            job_id = f"bump_{listing_id}_{uuid.uuid4().hex[:8]}"

            # Create job in DB
            store.log_automation_job(
                job_id=job_id,
                rule_id="manual_bump",
                job_type="bump",
                status="running",
                target_id=listing_id
            )

            try:
                # Execute REAL bump via HTTP API
                print(f"🔄 Executing REAL bump for listing {listing_id} via HTTP API...")
                success, error_msg = await client.bump_item(listing_id)

                # Anti-detection delay (shorter because HTTP is faster)
                await human_delay(500, 1500)

                if success:
                    # Update job as completed
                    store.update_automation_job(
                        job_id=job_id,
                        status="completed",
                        result={"listing_id": listing_id, "method": "http_api", "bumped": True}
                    )

                    # Track analytics event
                    store.track_analytics_event(
                        listing_id=listing_id,
                        event_type="bump",
                        user_id=user_id,
                        source="manual"
                    )
                    
                    bumped_listings.append(listing_id)
                    print(f"✅ Successfully bumped listing {listing_id}")
                else:
                    # Update job as failed
                    store.update_automation_job(
                        job_id=job_id,
                        status="failed",
                        error=error_msg or "Unknown error"
                    )
                    failed_listings.append(listing_id)
                    print(f"❌ Failed to bump listing {listing_id}: {error_msg}")
                    
            except Exception as e:
                print(f"❌ Exception bumping listing {listing_id}: {e}")
                store.update_automation_job(
                    job_id=job_id,
                    status="failed",
                    error=str(e)
                )
                failed_listings.append(listing_id)

    return {
        "ok": True,
        "bumped": len(bumped_listings),
        "failed": len(failed_listings),
        "listing_ids": bumped_listings,
        "failed_ids": failed_listings
    }


@router.post("/follow/execute")
async def execute_follow_now(
    vinted_user_ids: List[str],
    current_user: User = Depends(get_current_user)
):
    """
    👥 INSTANT FOLLOW: Manually trigger REAL follow for specific users
    Uses HTTP API (10x faster than Playwright!)
    """
    store = get_store()
    user_id = str(current_user.id)

    # Get Vinted session
    session = vault.load_session()
    if not session:
        raise HTTPException(status_code=401, detail="No Vinted session found. Please authenticate first.")

    followed_users = []
    failed_users = []

    # Initialize HTTP API client
    async with VintedAPIClient(session) as client:
        for vinted_user_id in vinted_user_ids:
            # Check if already following
            if store.is_following(user_id, vinted_user_id):
                print(f"⏭️ Already following user {vinted_user_id}, skipping...")
                continue

            job_id = f"follow_{vinted_user_id}_{uuid.uuid4().hex[:8]}"

            # Create job in DB
            store.log_automation_job(
                job_id=job_id,
                rule_id="manual_follow",
                job_type="follow",
                status="running",
                target_id=vinted_user_id
            )

            try:
                # Execute REAL follow via HTTP API
                print(f"👥 Executing REAL follow for user {vinted_user_id} via HTTP API...")
                success, error_msg = await client.follow_user(vinted_user_id)

                # Anti-detection delay (shorter for HTTP)
                await human_delay(500, 1500)

                if success:
                    # Update job as completed
                    store.update_automation_job(
                        job_id=job_id,
                        status="completed",
                        result={"vinted_user_id": vinted_user_id, "method": "http_api", "followed": True}
                    )

                    # Track in follows table
                    store.track_follow(
                        user_id=user_id,
                        vinted_user_id=vinted_user_id,
                        source="manual"
                    )

                    followed_users.append(vinted_user_id)
                    print(f"✅ Successfully followed user {vinted_user_id}")
                else:
                    # Update job as failed
                    store.update_automation_job(
                        job_id=job_id,
                        status="failed",
                        error=error_msg or "Unknown error"
                    )
                    failed_users.append(vinted_user_id)
                    print(f"❌ Failed to follow user {vinted_user_id}: {error_msg}")

            except Exception as e:
                print(f"❌ Exception following user {vinted_user_id}: {e}")
                store.update_automation_job(
                    job_id=job_id,
                    status="failed",
                    error=str(e)
                )
                failed_users.append(vinted_user_id)

    return {
        "ok": True,
        "followed": len(followed_users),
        "failed": len(failed_users),
        "user_ids": followed_users,
        "failed_ids": failed_users
    }


@router.post("/unfollow/execute")
async def execute_unfollow_now(
    vinted_user_ids: List[str],
    current_user: User = Depends(get_current_user)
):
    """
    👋 INSTANT UNFOLLOW: Manually trigger REAL unfollow for specific users
    Uses HTTP API (10x faster than Playwright!)
    """
    store = get_store()
    user_id = str(current_user.id)

    # Get Vinted session
    session = vault.load_session()
    if not session:
        raise HTTPException(status_code=401, detail="No Vinted session found. Please authenticate first.")

    unfollowed_users = []
    failed_users = []

    # Initialize HTTP API client
    async with VintedAPIClient(session) as client:
        for vinted_user_id in vinted_user_ids:
            job_id = f"unfollow_{vinted_user_id}_{uuid.uuid4().hex[:8]}"

            # Create job in DB
            store.log_automation_job(
                job_id=job_id,
                rule_id="manual_unfollow",
                job_type="unfollow",
                status="running",
                target_id=vinted_user_id
            )

            try:
                # Execute REAL unfollow via HTTP API
                print(f"👋 Executing REAL unfollow for user {vinted_user_id} via HTTP API...")
                success, error_msg = await client.unfollow_user(vinted_user_id)

                # Anti-detection delay (shorter for HTTP)
                await human_delay(500, 1500)

                if success:
                    # Update job as completed
                    store.update_automation_job(
                        job_id=job_id,
                        status="completed",
                        result={"vinted_user_id": vinted_user_id, "method": "http_api", "unfollowed": True}
                    )

                    # Track unfollow in DB
                    store.track_unfollow(
                        user_id=user_id,
                        vinted_user_id=vinted_user_id
                    )

                    unfollowed_users.append(vinted_user_id)
                    print(f"✅ Successfully unfollowed user {vinted_user_id}")
                else:
                    # Update job as failed
                    store.update_automation_job(
                        job_id=job_id,
                        status="failed",
                        error=error_msg or "Unknown error"
                    )
                    failed_users.append(vinted_user_id)
                    print(f"❌ Failed to unfollow user {vinted_user_id}: {error_msg}")

            except Exception as e:
                print(f"❌ Exception unfollowing user {vinted_user_id}: {e}")
                store.update_automation_job(
                    job_id=job_id,
                    status="failed",
                    error=str(e)
                )
                failed_users.append(vinted_user_id)

    return {
        "ok": True,
        "unfollowed": len(unfollowed_users),
        "failed": len(failed_users),
        "user_ids": unfollowed_users,
        "failed_ids": failed_users
    }


class SendMessageRequest(BaseModel):
    """Request model for sending messages"""
    conversation_id: str
    message: Optional[str] = None
    template_id: Optional[str] = None
    variables: Optional[dict] = None  # For template variable replacement


@router.post("/messages/send")
async def send_message(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user)
):
    """
    💬 SEND MESSAGE: Send a message to a conversation
    Uses HTTP API with typing simulation (10x faster than Playwright!)

    Supports:
    - Direct message sending
    - Template-based messages with variable replacement
    - Human-like typing simulation
    """
    store = get_store()
    user_id = str(current_user.id)

    # Get Vinted session
    session = vault.load_session()
    if not session:
        raise HTTPException(status_code=401, detail="No Vinted session found. Please authenticate first.")

    # Determine message to send
    message_text = request.message

    if request.template_id and not message_text:
        # Load template from DB
        with store.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT template FROM message_templates
                WHERE id = ? AND user_id = ? AND enabled = 1
            """, (request.template_id, user_id))
            row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Template not found or disabled")

        message_text = row["template"]

        # Replace variables in template
        if request.variables:
            for key, value in request.variables.items():
                message_text = message_text.replace(f"{{{{{key}}}}}", str(value))

    if not message_text:
        raise HTTPException(status_code=400, detail="Either message or template_id must be provided")

    job_id = f"message_{request.conversation_id}_{uuid.uuid4().hex[:8]}"

    # Create job in DB
    store.log_automation_job(
        job_id=job_id,
        rule_id="manual_message",
        job_type="message",
        status="running",
        target_id=request.conversation_id
    )

    try:
        # Initialize HTTP API client
        async with VintedAPIClient(session) as client:
            # Execute REAL message send via HTTP API (with typing simulation)
            print(f"💬 Executing REAL message send to conversation {request.conversation_id} via HTTP API...")
            success, error_msg = await client.send_message(
                request.conversation_id,
                message_text,
                simulate_typing=True  # Simulates human typing for anti-detection
            )

            if success:
                # Update job as completed
                store.update_automation_job(
                    job_id=job_id,
                    status="completed",
                    result={
                        "conversation_id": request.conversation_id,
                        "method": "http_api",
                        "message_sent": True,
                        "message_length": len(message_text)
                    }
                )

                print(f"✅ Successfully sent message to conversation {request.conversation_id}")

                return {
                    "ok": True,
                    "conversation_id": request.conversation_id,
                    "message_sent": True,
                    "job_id": job_id
                }
            else:
                # Update job as failed
                store.update_automation_job(
                    job_id=job_id,
                    status="failed",
                    error=error_msg or "Unknown error"
                )

                print(f"❌ Failed to send message: {error_msg}")

                return {
                    "ok": False,
                    "error": error_msg or "Failed to send message",
                    "job_id": job_id
                }
    
    except Exception as e:
        print(f"❌ Exception sending message: {e}")
        store.update_automation_job(
            job_id=job_id,
            status="failed",
            error=str(e)
        )
        
        if 'client' in locals():
            await client.close()
        
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/follows/pending-unfollow")
async def get_pending_unfollows(
    days_since_follow: int = 7,
    current_user: User = Depends(get_current_user)
):
    """
    Get list of users that should be unfollowed (followed X days ago, didn't follow back)
    """
    store = get_store()
    user_id = str(current_user.id)
    
    pending_unfollows = store.get_follows_to_unfollow(user_id, days_since_follow)
    
    return {
        "ok": True,
        "count": len(pending_unfollows),
        "vinted_user_ids": pending_unfollows,
        "days_since_follow": days_since_follow
    }


# Upselling configuration model
class UpsellConfig(BaseModel):
    """Configuration for bulk upselling messages (Dotb feature)"""
    enabled: bool
    trigger: str = "order_completed"  # When to send: order_completed, order_delivered
    delay_days: int = 3  # Days after trigger
    message_template: str
    max_items_to_suggest: int = 3  # Number of similar items to suggest
    daily_limit: int = 20  # Max upsell messages per day
    exclude_categories: List[str] = []  # Don't upsell these categories


@router.post("/upsell/config")
async def configure_upselling(
    config: UpsellConfig,
    current_user: User = Depends(get_current_user)
):
    """
    Configure bulk upselling messages (Dotb feature)

    Automatically suggest similar items to buyers after a successful sale.
    Increases revenue by promoting your other products.

    Template variables available:
    - {buyer_name}: Buyer's name
    - {item_title}: Original item purchased
    - {similar_items}: List of similar items (auto-generated)
    - {your_shop}: Your shop name

    Example:
    "Hi {buyer_name}! Thanks for buying {item_title}!
     Check out these similar items you might like: {similar_items}"
    """
    store = get_store()
    user_id = str(current_user.id)

    # Create or update upsell rule
    rule_id = f"upsell_{user_id}_{uuid.uuid4().hex[:8]}"

    store.save_automation_rule(
        rule_id=rule_id,
        user_id=user_id,
        rule_type="upsell",
        config=config.model_dump(),
        enabled=config.enabled
    )

    return {
        "ok": True,
        "message": "Upselling configuration saved",
        "rule_id": rule_id,
        "config": config.model_dump()
    }


@router.post("/upsell/execute")
async def execute_upselling(
    order_ids: List[str],
    current_user: User = Depends(get_current_user)
):
    """
    Manually execute upselling for specific orders

    Sends upsell messages to buyers of completed orders,
    suggesting similar items they might be interested in.
    """
    try:
        results = {
            "success": [],
            "failed": [],
            "total": len(order_ids)
        }

        # Get user's session
        session_data = vault.get_session(str(current_user.id))
        if not session_data:
            raise HTTPException(status_code=400, detail="No Vinted session found. Please configure your Vinted cookie first.")

        # ✅ IMPLEMENTED: Real upselling with UpsellingService
        from backend.services.upselling_service import UpsellingService

        upselling_service = UpsellingService()

        for order_id in order_ids:
            try:
                # Get order details from store
                store = get_store()
                order = store.get_order(order_id)

                if not order:
                    results["failed"].append({
                        "order_id": order_id,
                        "error": "Order not found"
                    })
                    continue

                # Get sold item ID and buyer name
                sold_item_id = order.get("item_id")
                buyer_name = order.get("buyer_name")

                if not sold_item_id:
                    results["failed"].append({
                        "order_id": order_id,
                        "error": "No item ID in order"
                    })
                    continue

                # Execute upselling workflow
                upsell_result = await upselling_service.execute_upselling(
                    sold_item_id=sold_item_id,
                    user_id=str(current_user.id),
                    buyer_name=buyer_name,
                    auto_send=False  # Don't auto-send, return message for review
                )

                if upsell_result["success"]:
                    results["success"].append({
                        "order_id": order_id,
                        "message": upsell_result["message"],
                        "similar_items_count": len(upsell_result["similar_items"]),
                        "message_sent": upsell_result["auto_sent"]
                    })
                    print(f"[UPSELL] Generated upsell for order {order_id}: {len(upsell_result['similar_items'])} items suggested")
                else:
                    results["failed"].append({
                        "order_id": order_id,
                        "error": upsell_result.get("message", "Upselling failed")
                    })

            except Exception as e:
                results["failed"].append({
                    "order_id": order_id,
                    "error": str(e)
                })

        return {
            "ok": True,
            "message": f"Upselling executed for {len(results['success'])} orders",
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Upselling failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upselling failed: {str(e)}")


@router.get("/upsell/templates")
async def get_upsell_templates(current_user: User = Depends(get_current_user)):
    """
    Get predefined upselling message templates

    Returns ready-to-use templates for different scenarios
    """
    templates = [
        {
            "id": "friendly",
            "name": "Message Amical",
            "template": "Salut ! J'ai vu que tu as liké {item_title} 😊 Il est encore dispo si ça t'intéresse ! N'hésite pas si tu as des questions",
            "delay_days": 0,
            "is_default": True
        },
        {
            "id": "casual",
            "name": "Style Décontracté",
            "template": "Hey ! Tu craques sur {item_title} ? Je peux te faire un bon prix si tu veux 👍 Dis-moi !",
            "delay_days": 0,
            "is_default": False
        },
        {
            "id": "quick",
            "name": "Réponse Rapide",
            "template": "Hello ! Merci pour ton message 😊 Il est en super état, porté 2-3 fois max. Des questions ?",
            "delay_days": 0,
            "is_default": False
        },
        {
            "id": "enthusiastic",
            "name": "Enthousiaste",
            "template": "Salut ! Yes il est encore là ! Tu veux d'autres photos ou des infos ? Je suis dispo ✨",
            "delay_days": 0,
            "is_default": False
        },
        {
            "id": "helpful",
            "name": "Serviable",
            "template": "Coucou ! Contente que ça te plaise 😊 Je peux répondre à toutes tes questions si besoin !",
            "delay_days": 0,
            "is_default": False
        },
        {
            "id": "price_nego",
            "name": "Négociation Prix",
            "template": "Hey ! Je peux descendre un peu le prix si ça peut t'aider 😊 Fais-moi une offre !",
            "delay_days": 0,
            "is_default": False
        },
        {
            "id": "condition",
            "name": "État Article",
            "template": "Salut ! Il est nickel, vraiment en super état 👌 Tu veux plus de photos ?",
            "delay_days": 0,
            "is_default": False
        },
        {
            "id": "available",
            "name": "Disponibilité",
            "template": "Hello ! Oui il est toujours dispo 😊 Je peux te l'envoyer rapidement si tu veux",
            "delay_days": 0,
            "is_default": False
        }
    ]

    return {
        "templates": templates,
        "total": len(templates)
    }


@router.post("/messages/suggest")
async def suggest_reply(
    message_context: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Generate natural French reply suggestions based on context

    Analyzes the incoming message and generates 3 natural, contextual responses
    """
    import random

    incoming_message = message_context.get("message", "").lower()
    item_title = message_context.get("item_title", "l'article")
    item_price = message_context.get("item_price", "")

    suggestions = []

    # Detect message type and generate appropriate responses
    if any(word in incoming_message for word in ["état", "etat", "condition", "usure", "porté"]):
        suggestions = [
            f"Salut ! Il est nickel, porté 2-3 fois max 😊 Aucun défaut visible",
            f"Hello ! Il est en super état, vraiment comme neuf 👌",
            f"Hey ! Il est impeccable, aucun soucis niveau état ✨"
        ]

    elif any(word in incoming_message for word in ["prix", "prix", "combien", "réduction", "reduction", "offre"]):
        suggestions = [
            f"Hey ! Je peux te faire {item_price}€ si ça te va 😊",
            f"Salut ! Fais-moi une offre, on s'arrange toujours 👍",
            f"Hello ! Le prix est négociable, dis-moi ce que tu proposes !"
        ]

    elif any(word in incoming_message for word in ["disponible", "dispo", "encore", "vendu"]):
        suggestions = [
            f"Salut ! Oui il est toujours dispo 😊",
            f"Hey ! Yes il est encore là, tu le veux ? 👍",
            f"Hello ! Il est bien disponible, je peux te l'envoyer rapidement ✨"
        ]

    elif any(word in incoming_message for word in ["photo", "photos", "voir", "image"]):
        suggestions = [
            f"Bien sûr ! Je t'envoie d'autres photos tout de suite 📸",
            f"Pas de souci ! Tu veux des photos de quel côté ? 😊",
            f"Oui carrément ! Je te fais ça dans 5 min 👍"
        ]

    elif any(word in incoming_message for word in ["taille", "mesure", "dimension"]):
        suggestions = [
            f"C'est une taille M, je te donne les mesures si tu veux 📏",
            f"Hello ! C'est du M, ça correspond bien aux tailles standards 😊",
            f"C'est un M, je peux te donner les dimensions exactes si besoin !"
        ]

    elif any(word in incoming_message for word in ["merci", "intéressé", "interesse", "prends", "achète"]):
        suggestions = [
            f"Super ! Je te fais un colis nickel 😊",
            f"Cool ! Je t'envoie ça rapidement 📦",
            f"Top ! Merci à toi, je prépare ton colis ✨"
        ]

    else:
        # Generic friendly responses
        suggestions = [
            f"Salut ! Merci pour ton message 😊 {item_title} est encore dispo !",
            f"Hello ! N'hésite pas si tu as des questions sur {item_title} 👍",
            f"Hey ! Je suis là si tu veux plus d'infos ✨"
        ]

    # Shuffle and return 3 suggestions
    random.shuffle(suggestions)

    return {
        "suggestions": suggestions[:3],
        "context_detected": "price" if "prix" in incoming_message else "condition" if "état" in incoming_message else "availability" if "dispo" in incoming_message else "general"
    }
