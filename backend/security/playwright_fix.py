"""
PLAYWRIGHT MEMORY LEAK FIX

Critical memory leak: playwright instance never closed
This causes累积 memory consumption and process leaks

Apply this fix to backend/core/vinted_client.py
"""

FIXED_CODE = '''
class VintedClient:
    """Playwright-based Vinted automation client"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None  # ✅ FIXED: Store playwright instance

    async def __aenter__(self):
        """Async context manager entry"""
        await self.init()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def init(self):
        """Initialize browser and context"""
        import subprocess

        # Get Chromium path from Nix (fix for Replit NixOS)
        try:
            chromium_path = subprocess.check_output(['which', 'chromium']).decode().strip()
        except:
            chromium_path = None  # Fallback to Playwright's bundled browser

        # ✅ FIXED: Store playwright instance for proper cleanup
        self.playwright = await async_playwright().start()

        # Extended Chromium args for better performance and anti-detection
        launch_kwargs = {
            'headless': self.headless,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',  # Hide automation
                '--disable-features=IsolateOrigins,site-per-process',  # Performance
                '--disable-web-security',  # Allow cross-origin
                '--disable-features=VizDisplayCompositor',  # Better stability
                '--disable-gpu',  # GPU not needed in headless
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-infobars',
                '--window-size=1280,720',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-background-timer-throttling',
                '--disable-hang-monitor',
                '--disable-prompt-on-repost',
                '--disable-sync',
                '--disable-translate',
                '--metrics-recording-only',
                '--mute-audio',
                '--safebrowsing-disable-auto-update',
                '--password-store=basic',
                '--use-mock-keychain',
                '--disable-extensions',
                '--disable-plugins',
            ],
            'timeout': 60000,  # 60 seconds browser launch timeout
        }

        # Use system Chromium if available (fixes libgbm1 dependency issue on NixOS)
        if chromium_path:
            launch_kwargs['executable_path'] = chromium_path

        self.browser = await self.playwright.chromium.launch(**launch_kwargs)

    async def close(self):
        """
        ✅ FIXED: Close all resources including playwright instance
        """
        try:
            if self.page:
                await self.page.close()
                self.page = None
        except Exception as e:
            logger.warning(f"Error closing page: {e}")

        try:
            if self.context:
                await self.context.close()
                self.context = None
        except Exception as e:
            logger.warning(f"Error closing context: {e}")

        try:
            if self.browser:
                await self.browser.close()
                self.browser = None
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")

        # ✅ FIXED: Stop playwright instance to free resources
        try:
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                logger.debug("✅ Playwright instance stopped")
        except Exception as e:
            logger.warning(f"Error stopping playwright: {e}")
'''

print("Apply this fix to backend/core/vinted_client.py")
print("Changes needed:")
print("1. Add self.playwright = None in __init__")
print("2. Change 'playwright = await async_playwright().start()' to 'self.playwright = await async_playwright().start()'")
print("3. In close() method, add playwright cleanup:")
print("   if self.playwright:")
print("       await self.playwright.stop()")
print("       self.playwright = None")
