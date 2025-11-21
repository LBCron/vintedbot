"""
Mobile App: Automatic Vinted Authentication
Connects to Vinted using email/password and extracts session cookies
"""
import asyncio
import random
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from loguru import logger
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from backend.core.session import VintedSession
from backend.security.encryption import encrypt_credentials, decrypt_credentials


class VintedAuthResult:
    """Result of Vinted authentication attempt"""

    def __init__(
        self,
        success: bool,
        session: Optional[VintedSession] = None,
        error: Optional[str] = None,
        error_code: Optional[str] = None
    ):
        self.success = success
        self.session = session
        self.error = error
        self.error_code = error_code  # e.g., "INVALID_CREDENTIALS", "CAPTCHA_REQUIRED", "2FA_REQUIRED"

    def to_dict(self) -> Dict[str, Any]:
        result = {
            'success': self.success,
            'error': self.error,
            'error_code': self.error_code
        }

        if self.session:
            result['session'] = {
                'user_agent': self.session.user_agent,
                'vinted_user_id': self.session.vinted_user_id,
                'has_cookies': bool(self.session.cookie)
            }

        return result


class VintedAuthenticator:
    """
    Automatic Vinted Authentication Service

    Features:
    - Email/password login automation
    - Cookie extraction and session management
    - Anti-detection measures
    - Error handling (captcha, 2FA, invalid credentials)
    - Human-like behavior simulation
    """

    # Vinted login URL
    LOGIN_URL = "https://www.vinted.fr/member/login"

    # Anti-detection browser config
    BROWSER_CONFIG = {
        'headless': True,
        'args': [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process'
        ]
    }

    # User agents (rotate for variety)
    USER_AGENTS = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    ]

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def init_browser(self) -> Browser:
        """Initialize Playwright browser"""
        if self.browser:
            return self.browser

        playwright = await async_playwright().start()

        self.browser = await playwright.chromium.launch(**self.BROWSER_CONFIG)

        logger.info("Browser initialized for Vinted authentication")
        return self.browser

    async def create_context(self, user_agent: Optional[str] = None) -> BrowserContext:
        """Create browser context with anti-detection"""
        if not self.browser:
            await self.init_browser()

        # Select random user agent if not provided
        if not user_agent:
            user_agent = random.choice(self.USER_AGENTS)

        # Create context with realistic settings
        self.context = await self.browser.new_context(
            user_agent=user_agent,
            viewport={'width': 375, 'height': 812} if 'iPhone' in user_agent else {'width': 1920, 'height': 1080},
            locale='fr-FR',
            timezone_id='Europe/Paris',
            geolocation={'latitude': 48.8566, 'longitude': 2.3522},  # Paris
            permissions=['geolocation'],
            extra_http_headers={
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
        )

        # Anti-detection: Override navigator properties
        await self.context.add_init_script("""
            // Remove webdriver flag
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Add realistic plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Add realistic languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['fr-FR', 'fr', 'en-US', 'en']
            });
        """)

        logger.debug(f"Created browser context with user agent: {user_agent[:50]}...")
        return self.context

    async def human_delay(self, min_ms: int = 500, max_ms: int = 2000):
        """Human-like random delay"""
        delay_ms = random.randint(min_ms, max_ms)
        await asyncio.sleep(delay_ms / 1000)

    async def human_type(
        self,
        page: Page,
        selector: str,
        text: str,
        clear_first: bool = True
    ):
        """Type like a human (variable speed)"""
        await page.click(selector)
        await self.human_delay(200, 500)

        if clear_first:
            await page.fill(selector, '')
            await self.human_delay(100, 300)

        # Type each character with random delay
        for char in text:
            await page.keyboard.type(char)
            # Variable typing speed: 50-150ms per character
            await asyncio.sleep(random.randint(50, 150) / 1000)

        await self.human_delay(300, 800)

    async def connect_to_vinted(
        self,
        email: str,
        password: str,
        save_credentials: bool = True,
        user_id: Optional[int] = None
    ) -> VintedAuthResult:
        """
        Connect to Vinted account using email/password

        Args:
            email: Vinted email
            password: Vinted password
            save_credentials: Whether to encrypt and save credentials
            user_id: User ID (required if save_credentials=True)

        Returns:
            VintedAuthResult with session or error
        """
        logger.info(f"Attempting Vinted login for {email}...")

        try:
            # Initialize browser
            if not self.context:
                await self.create_context()

            page = await self.context.new_page()

            # Navigate to login page
            logger.debug("Navigating to Vinted login page...")
            await page.goto(self.LOGIN_URL, wait_until='networkidle', timeout=30000)

            # Wait for page to load
            await self.human_delay(2000, 4000)

            # Find and fill email field
            logger.debug("Filling email field...")
            email_selector = 'input[type="email"], input[name="username"], input[id="username"]'

            try:
                await page.wait_for_selector(email_selector, timeout=10000)
            except Exception:
                # Try alternative selectors
                email_selector = '[data-testid="login-email"], [data-test-id="login-email"]'
                await page.wait_for_selector(email_selector, timeout=5000)

            await self.human_type(page, email_selector, email)

            # Fill password field
            logger.debug("Filling password field...")
            password_selector = 'input[type="password"], input[name="password"], input[id="password"]'

            try:
                await page.wait_for_selector(password_selector, timeout=5000)
            except Exception:
                password_selector = '[data-testid="login-password"], [data-test-id="login-password"]'
                await page.wait_for_selector(password_selector, timeout=5000)

            await self.human_type(page, password_selector, password)

            # Pause before clicking submit (humans review before submitting)
            await self.human_delay(1000, 2000)

            # Find and click submit button
            logger.debug("Clicking login button...")
            submit_selector = 'button[type="submit"], button.login, [data-testid="login-submit"]'

            await page.click(submit_selector)

            # Wait for navigation or error
            logger.debug("Waiting for login result...")

            try:
                await page.wait_for_navigation(timeout=15000)
            except Exception as e:
                logger.warning(f"Navigation timeout: {e}")

            # Wait a bit for page to settle
            await self.human_delay(3000, 5000)

            # Check if logged in
            current_url = page.url
            logger.debug(f"Current URL: {current_url}")

            # Success indicators
            if any(indicator in current_url for indicator in ['/member/general', '/inbox', '/items']):
                logger.info("[OK] Login successful!")

                # Extract cookies
                cookies = await self.context.cookies()

                # Find session cookie (usually _vinted_fr_session or similar)
                cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies])

                # Extract user ID from page or cookies
                vinted_user_id = await self._extract_user_id(page, cookies)

                # Get user agent
                user_agent = await page.evaluate('navigator.userAgent')

                # Create session
                session = VintedSession(
                    cookie=cookie_str,
                    user_agent=user_agent,
                    vinted_user_id=vinted_user_id,
                    last_used=datetime.now()
                )

                # Save encrypted credentials if requested
                if save_credentials and user_id:
                    encrypted_creds = encrypt_credentials(email, password, str(user_id))

                    # Store in database (would call storage layer here)
                    from backend.core.storage import get_store
                    store = get_store()

                    # Store session and encrypted credentials
                    # (This would be a new method in storage.py)
                    logger.info(f"Credentials encrypted and session saved for user {user_id}")

                return VintedAuthResult(
                    success=True,
                    session=session
                )

            # Check for specific errors
            page_content = await page.content()

            # Captcha detected
            if 'captcha' in page_content.lower() or 'recaptcha' in page_content.lower():
                logger.warning("Captcha detected")
                return VintedAuthResult(
                    success=False,
                    error="Captcha requis - réessayez dans quelques minutes",
                    error_code="CAPTCHA_REQUIRED"
                )

            # 2FA required
            if '2fa' in page_content.lower() or 'verification' in page_content.lower() or 'code' in current_url.lower():
                logger.warning("2FA required")
                return VintedAuthResult(
                    success=False,
                    error="Authentification à deux facteurs requise",
                    error_code="2FA_REQUIRED"
                )

            # Invalid credentials
            if 'incorrect' in page_content.lower() or 'invalid' in page_content.lower() or current_url == self.LOGIN_URL:
                logger.warning("Invalid credentials")
                return VintedAuthResult(
                    success=False,
                    error="Email ou mot de passe incorrect",
                    error_code="INVALID_CREDENTIALS"
                )

            # Unknown error
            logger.error("Login failed - unknown reason")
            return VintedAuthResult(
                success=False,
                error="Échec de connexion - raison inconnue",
                error_code="UNKNOWN_ERROR"
            )

        except Exception as e:
            logger.error(f"Vinted authentication exception: {e}")
            return VintedAuthResult(
                success=False,
                error=f"Erreur: {str(e)}",
                error_code="EXCEPTION"
            )

        finally:
            # Close page but keep browser/context for reuse
            if page:
                await page.close()

    async def _extract_user_id(self, page: Page, cookies: list) -> Optional[str]:
        """Extract Vinted user ID from page or cookies"""
        try:
            # Try to extract from window object
            user_id = await page.evaluate('''
                () => {
                    if (window.currentUser && window.currentUser.id) {
                        return window.currentUser.id.toString();
                    }
                    return null;
                }
            ''')

            if user_id:
                return user_id

            # Try to find in cookies
            for cookie in cookies:
                if 'user_id' in cookie['name'].lower():
                    return cookie['value']

            logger.warning("Could not extract Vinted user ID")
            return None

        except Exception as e:
            logger.error(f"Failed to extract user ID: {e}")
            return None

    async def close(self):
        """Close browser and context"""
        if self.context:
            await self.context.close()

        if self.browser:
            await self.browser.close()

        logger.info("Browser closed")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.init_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# High-level authentication function
async def authenticate_vinted_account(
    email: str,
    password: str,
    user_id: int,
    save_session: bool = True
) -> VintedAuthResult:
    """
    Authenticate Vinted account (high-level function for API endpoints)

    Args:
        email: Vinted email
        password: Vinted password
        user_id: VintedBot user ID
        save_session: Whether to save session to database

    Returns:
        VintedAuthResult
    """
    async with VintedAuthenticator() as auth:
        result = await auth.connect_to_vinted(
            email=email,
            password=password,
            save_credentials=save_session,
            user_id=user_id
        )

        if result.success and save_session and result.session:
            # Save session to database
            from backend.core.session import save_vinted_session
            save_vinted_session(user_id, result.session)

            logger.info(f"[OK] Vinted account connected and session saved for user {user_id}")

        return result


if __name__ == "__main__":
    # Test authentication
    import sys

    async def test_auth():
        print("Vinted Authentication Test")
        print("=" * 50)

        email = input("Vinted Email: ")
        password = input("Vinted Password: ")

        print("\nAttempting login...")

        async with VintedAuthenticator() as auth:
            result = await auth.connect_to_vinted(email, password, save_credentials=False)

            print("\n" + "=" * 50)
            if result.success:
                print("[OK] LOGIN SUCCESSFUL!")
                print(f"Session: {result.session.cookie[:50]}...")
                print(f"User Agent: {result.session.user_agent}")
                print(f"Vinted User ID: {result.session.vinted_user_id}")
            else:
                print("[ERROR] LOGIN FAILED")
                print(f"Error: {result.error}")
                print(f"Error Code: {result.error_code}")
            print("=" * 50)

    asyncio.run(test_auth())
