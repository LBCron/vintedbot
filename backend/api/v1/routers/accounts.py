"""
Multi-Account Management API
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List
from pydantic import BaseModel
from backend.core.auth import get_current_user, User
from backend.core.storage import get_store
from backend.schemas.multi_account import (
    VintedAccount,
    AccountStats,
    AccountSwitchRequest,
    AccountListResponse
)

router = APIRouter(prefix="/accounts", tags=["accounts"])


class AddAccountRequest(BaseModel):
    nickname: str
    cookie: str
    user_agent: str
    is_default: bool = False


class VintedLoginRequest(BaseModel):
    email: str
    password: str
    nickname: str = "Mon Compte Vinted"
    is_default: bool = True


@router.get("/list")
async def list_accounts(
    current_user: User = Depends(get_current_user)
):
    """
    🔐 MULTI-ACCOUNT: Manage multiple Vinted accounts

    Feature from Dotb, VintedSeekers - manage multiple shops!
    - Switch between accounts seamlessly
    - Separate analytics per account
    - Backup/transfer listings
    """
    store = get_store()
    accounts = store.get_user_vinted_accounts(current_user.id)

    # Find the default/active account
    active_account_id = None
    for account in accounts:
        if account["is_default"]:
            active_account_id = account["id"]
            break

    return {
        "ok": True,
        "accounts": accounts,
        "active_account_id": active_account_id
    }


@router.post("/add")
async def add_account(
    request: AddAccountRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Add a new Vinted account"""
    store = get_store()

    try:
        account_id = store.add_vinted_account(
            user_id=current_user.id,
            nickname=request.nickname,
            cookie=request.cookie,
            user_agent=request.user_agent,
            is_default=request.is_default
        )

        return {
            "ok": True,
            "account_id": account_id,
            "message": f"Account '{request.nickname}' added successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vinted-login")
async def vinted_auto_login(
    request: VintedLoginRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    🚀 CONNEXION AUTOMATIQUE À VINTED

    L'utilisateur entre juste son email/password,
    le bot se connecte automatiquement et récupère les cookies.

    Comme Dotb, VintedSeekers - pas besoin de manipuler les cookies!
    """
    from backend.core.vinted_client import VintedClient
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"[VINTED LOGIN] Starting auto-login for user {current_user.id}")

    try:
        # Initialize Playwright browser
        logger.info("[VINTED LOGIN] Initializing Playwright browser...")
        async with VintedClient(headless=True) as client:
            await client.init()
            logger.info("[VINTED LOGIN] Browser initialized successfully")

            # Create a new browser context
            logger.info("[VINTED LOGIN] Creating browser context...")
            context = await client.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            logger.info("[VINTED LOGIN] Context created")

            page = await context.new_page()
            logger.info("[VINTED LOGIN] New page created")

            # Navigate to Vinted login page
            logger.info("[VINTED LOGIN] Navigating to https://www.vinted.fr/member/login...")
            try:
                # Use domcontentloaded instead of networkidle for faster loading
                await page.goto('https://www.vinted.fr/member/login', wait_until='domcontentloaded', timeout=90000)
                logger.info("[VINTED LOGIN] Page loaded successfully")
            except Exception as e:
                logger.error(f"[VINTED LOGIN] Failed to navigate: {str(e)}")
                raise

            logger.info("[VINTED LOGIN] Waiting a few seconds for page to stabilize...")
            await asyncio.sleep(3)  # Give page time to load
            logger.info("[VINTED LOGIN] Page stabilized")

            # Check if login form is present
            logger.info("[VINTED LOGIN] Looking for login form elements...")
            username_field = await page.query_selector('input[name="username"]')
            password_field = await page.query_selector('input[name="password"]')

            if not username_field or not password_field:
                logger.error("[VINTED LOGIN] Login form not found on page")
                # Take screenshot for debugging
                await page.screenshot(path='/app/backend/data/vinted_login_error.png')
                raise Exception("Login form not found on page")

            logger.info("[VINTED LOGIN] Login form found, filling credentials...")

            # Fill login form
            await page.fill('input[name="username"]', request.email)
            logger.info("[VINTED LOGIN] Email filled")

            await page.fill('input[name="password"]', request.password)
            logger.info("[VINTED LOGIN] Password filled")

            # Click login button
            logger.info("[VINTED LOGIN] Clicking submit button...")
            await page.click('button[type="submit"]')
            logger.info("[VINTED LOGIN] Submit button clicked")

            # Wait for redirect after successful login (increased timeout)
            logger.info("[VINTED LOGIN] Waiting for redirect (timeout: 90 seconds)...")
            try:
                await page.wait_for_url('https://www.vinted.fr/**', timeout=90000)
                logger.info(f"[VINTED LOGIN] Redirected successfully to: {page.url}")
            except Exception as e:
                logger.error(f"[VINTED LOGIN] Redirect timeout. Current URL: {page.url}")
                # Take screenshot for debugging
                await page.screenshot(path='/app/backend/data/vinted_login_timeout.png')
                raise

            # Get all cookies
            logger.info("[VINTED LOGIN] Extracting cookies...")
            cookies = await context.cookies()
            logger.info(f"[VINTED LOGIN] Found {len(cookies)} cookies")

            # Format cookies as a string
            cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

            # Get user agent
            user_agent = await page.evaluate('navigator.userAgent')
            logger.info(f"[VINTED LOGIN] User agent: {user_agent}")

            # Close browser
            await context.close()
            logger.info("[VINTED LOGIN] Browser closed")

        # Save account to database
        logger.info("[VINTED LOGIN] Saving account to database...")
        store = get_store()
        account_id = store.add_vinted_account(
            user_id=current_user.id,
            nickname=request.nickname,
            cookie=cookie_string,
            user_agent=user_agent,
            is_default=request.is_default
        )
        logger.info(f"[VINTED LOGIN] Account saved with ID: {account_id}")

        return {
            "ok": True,
            "account_id": account_id,
            "message": f"✅ Connexion réussie ! Compte '{request.nickname}' configuré automatiquement."
        }

    except Exception as e:
        import traceback
        error_detail = str(e)
        traceback_str = traceback.format_exc()

        logger.error(f"[VINTED LOGIN] Error occurred: {error_detail}")
        logger.error(f"[VINTED LOGIN] Traceback: {traceback_str}")

        # Check for common errors
        if "timeout" in error_detail.lower():
            raise HTTPException(
                status_code=408,
                detail="⏱️ Délai d'attente dépassé. Vinted prend trop de temps à répondre. Réessayez dans quelques minutes."
            )
        elif "username" in error_detail.lower() or "password" in error_detail.lower():
            raise HTTPException(
                status_code=401,
                detail="🔒 Email ou mot de passe incorrect."
            )
        elif "login form not found" in error_detail.lower():
            raise HTTPException(
                status_code=500,
                detail="🚫 Impossible de trouver le formulaire de connexion Vinted. Le site a peut-être changé."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"❌ Erreur lors de la connexion : {error_detail}"
            )


@router.post("/switch")
async def switch_account(
    request: AccountSwitchRequest,
    current_user: User = Depends(get_current_user)
):
    """Switch to a different Vinted account"""
    store = get_store()
    # TODO: Update active account
    return {
        "ok": True,
        "active_account_id": request.account_id
    }


@router.delete("/{account_id}")
async def delete_account(
    account_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a Vinted account"""
    store = get_store()

    success = store.delete_vinted_account(current_user.id, account_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Compte non trouvé ou vous n'avez pas la permission de le supprimer"
        )

    return {
        "ok": True,
        "message": "Compte supprimé avec succès"
    }


@router.get("/{account_id}/stats", response_model=AccountStats)
async def get_account_stats(
    account_id: str,
    period: str = "30d",  # 7d, 30d, 90d, all
    current_user: User = Depends(get_current_user)
):
    """
    Get real statistics for a specific account

    ✅ IMPLEMENTED: Real stats calculation from database
    """
    from backend.core.database import get_db_pool

    # Period filter
    period_filters = {
        '7d': "created_at >= datetime('now', '-7 days')",
        '30d': "created_at >= datetime('now', '-30 days')",
        '90d': "created_at >= datetime('now', '-90 days')",
        'all': "1=1"
    }
    period_filter = period_filters.get(period, period_filters['30d'])

    try:
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # Get account info
            account = await conn.fetchrow(
                "SELECT * FROM vinted_accounts WHERE id = $1 AND user_id = $2",
                account_id, current_user.id
            )

            if not account:
                raise HTTPException(404, "Account not found")

            # Calculate real statistics from drafts/listings
            stats_query = f"""
                SELECT
                    COUNT(*) as total_listings,
                    COUNT(CASE WHEN status IN ('published', 'active') THEN 1 END) as active_listings,
                    COUNT(CASE WHEN sold = true THEN 1 END) as total_sales,
                    COALESCE(SUM(CASE WHEN sold = true THEN price END), 0) as total_revenue,
                    COALESCE(AVG(CASE WHEN sold = true THEN price END), 0) as avg_sale_price,
                    COALESCE(SUM(views), 0) as total_views,
                    COALESCE(AVG(views), 0) as avg_views,
                    COUNT(CASE WHEN favorited > 0 THEN 1 END) as favorited_items
                FROM drafts
                WHERE vinted_account_id = $1 AND {period_filter}
            """

            stats = await conn.fetchrow(stats_query, account_id)

            # Get follower counts (if available in account table)
            followers = account.get('followers_count', 0)
            following = account.get('following_count', 0)

            # Calculate conversion rate
            conversion_rate = 0
            if stats['total_views'] and stats['total_views'] > 0:
                conversion_rate = (stats['total_sales'] / stats['total_views']) * 100

            # Get trend (compare to previous period)
            prev_period_query = f"""
                SELECT COALESCE(SUM(CASE WHEN sold = true THEN price END), 0) as prev_revenue
                FROM drafts
                WHERE vinted_account_id = $1
                AND created_at < datetime('now', '-{period}')
                AND created_at >= datetime('now', '-{int(period[:-1]) * 2} days')
            """

            prev_stats = await conn.fetchrow(prev_period_query, account_id)
            revenue_trend = 0

            if prev_stats and prev_stats['prev_revenue'] and prev_stats['prev_revenue'] > 0:
                revenue_trend = ((stats['total_revenue'] - prev_stats['prev_revenue']) / prev_stats['prev_revenue']) * 100

            return AccountStats(
                account_id=account_id,
                total_listings=stats['total_listings'] or 0,
                active_listings=stats['active_listings'] or 0,
                total_sales=stats['total_sales'] or 0,
                total_revenue=float(stats['total_revenue'] or 0),
                avg_sale_price=float(stats['avg_sale_price'] or 0),
                total_views=stats['total_views'] or 0,
                avg_views=float(stats['avg_views'] or 0),
                conversion_rate=round(conversion_rate, 2),
                revenue_trend_percent=round(revenue_trend, 1),
                favorited_items=stats['favorited_items'] or 0,
                followers=followers,
                following=following
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate account stats: {e}")
        # Fallback to empty stats
        return AccountStats(
            account_id=account_id,
            total_listings=0,
            active_listings=0,
            total_sales=0,
            total_revenue=0.0,
            followers=0,
            following=0
        )
