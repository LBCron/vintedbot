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
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a specific account"""
    # TODO: Calculate stats from listings/analytics tables
    return AccountStats(
        account_id=account_id,
        total_listings=0,
        active_listings=0,
        total_sales=0,
        total_revenue=0.0,
        followers=0,
        following=0
    )
