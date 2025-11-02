"""
Vinted automation client using Playwright.
Handles listing creation, photo uploads, and captcha detection.
"""
import asyncio
import base64
import random
import re
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeout
from backend.core.session import VintedSession


class CaptchaDetected(Exception):
    """Raised when captcha or verification is detected"""
    pass


class VintedClient:
    """Playwright-based Vinted automation client"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
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
        
        playwright = await async_playwright().start()
        
        launch_kwargs = {
            'headless': self.headless,
            'args': ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        }
        
        # Use system Chromium if available (fixes libgbm1 dependency issue on NixOS)
        if chromium_path:
            launch_kwargs['executable_path'] = chromium_path
        
        self.browser = await playwright.chromium.launch(**launch_kwargs)
    
    async def create_context(self, session: VintedSession) -> BrowserContext:
        """
        Create browser context with session cookies
        
        Args:
            session: VintedSession with cookie and user_agent
            
        Returns:
            Browser context
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized. Call init() first.")
        
        # Parse cookies from header string
        cookies = []
        for cookie_str in session.cookie.split(';'):
            cookie_str = cookie_str.strip()
            if '=' in cookie_str:
                name, value = cookie_str.split('=', 1)
                cookies.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.vinted.fr',
                    'path': '/'
                })
        
        self.context = await self.browser.new_context(
            user_agent=session.user_agent,
            viewport={'width': 1280, 'height': 720}
        )
        
        # Add cookies
        await self.context.add_cookies(cookies)
        
        return self.context
    
    async def new_page(self) -> Page:
        """Create new page in context"""
        if not self.context:
            raise RuntimeError("Context not initialized. Call create_context first.")
        
        self.page = await self.context.new_page()
        return self.page
    
    async def close(self):
        """Close browser and context"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def human_delay(self, min_ms: int = 100, max_ms: int = 500):
        """Random human-like delay"""
        await asyncio.sleep(random.randint(min_ms, max_ms) / 1000)
    
    async def detect_challenge(self, page: Page) -> bool:
        """
        Detect if page contains captcha or verification challenge
        
        Args:
            page: Playwright page
            
        Returns:
            True if challenge detected
        """
        # Check for common captcha/verification indicators
        selectors = [
            'iframe[src*="captcha"]',
            'iframe[src*="recaptcha"]',
            'iframe[src*="hcaptcha"]',
            '[id*="captcha"]',
            '[class*="captcha"]',
            '[data-testid*="verification"]',
            'text=Vérification',
            'text=Verify',
            'text=Captcha'
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    print(f"⚠️ Challenge detected: {selector}")
                    return True
            except:
                pass
        
        return False
    
    async def upload_photo(
        self, 
        page: Page, 
        photo_path: str,
        upload_selector: str = 'input[type="file"]'
    ) -> bool:
        """
        Upload photo to Vinted
        
        Args:
            page: Playwright page
            photo_path: Path to photo file
            upload_selector: CSS selector for file input
            
        Returns:
            True if uploaded successfully
        """
        try:
            # Wait for page to be fully loaded
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Check if redirected to login/session page
            current_url = page.url
            if 'session' in current_url or 'login' in current_url or 'member/login' in current_url:
                print(f"⚠️ Redirected to session/login page: {current_url}")
                print("   Session Vinted probablement expirée - veuillez actualiser votre cookie")
                return False
            
            # Wait for file input with longer timeout (15s)
            file_input = await page.wait_for_selector(upload_selector, timeout=15000)
            
            if not file_input:
                print(f"❌ File input not found with selector: {upload_selector}")
                return False
            
            # Upload file
            await file_input.set_input_files(photo_path)
            
            # Human delay
            await self.human_delay(500, 1000)
            
            return True
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            print(f"   Current URL: {page.url}")
            return False
    
    async def fill_listing_form(
        self,
        page: Page,
        title: str,
        price: float,
        description: str,
        brand: Optional[str] = None,
        size: Optional[str] = None,
        condition: Optional[str] = None,
        color: Optional[str] = None,
        category_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fill out Vinted listing form
        
        Args:
            page: Playwright page on /items/new
            title: Item title
            price: Item price
            description: Item description
            brand: Brand name
            size: Size
            condition: Condition
            color: Color
            category_hint: Category hint (e.g. "Homme > Sweats")
            
        Returns:
            Dict with form_filled status and any errors
        """
        result = {'filled': [], 'errors': []}
        
        try:
            # Title
            title_selector = 'input[name="title"], input[placeholder*="Titre"]'
            try:
                await page.fill(title_selector, title)
                await self.human_delay()
                result['filled'].append('title')
            except Exception as e:
                result['errors'].append(f"title: {e}")
            
            # Description
            desc_selector = 'textarea[name="description"], textarea[placeholder*="Description"]'
            try:
                await page.fill(desc_selector, description)
                await self.human_delay()
                result['filled'].append('description')
            except Exception as e:
                result['errors'].append(f"description: {e}")
            
            # Price
            price_selector = 'input[name="price"], input[type="number"]'
            try:
                await page.fill(price_selector, str(price))
                await self.human_delay()
                result['filled'].append('price')
            except Exception as e:
                result['errors'].append(f"price: {e}")
            
            # Brand (if provided)
            if brand:
                brand_selector = 'input[name="brand"], input[placeholder*="Marque"]'
                try:
                    await page.fill(brand_selector, brand)
                    await self.human_delay()
                    result['filled'].append('brand')
                except Exception as e:
                    result['errors'].append(f"brand: {e}")
            
            # Size (if provided)
            if size:
                size_selector = 'select[name="size"], input[name="size"]'
                try:
                    await page.fill(size_selector, size)
                    await self.human_delay()
                    result['filled'].append('size')
                except Exception as e:
                    result['errors'].append(f"size: {e}")
            
            # Condition (if provided)
            if condition:
                condition_selector = 'select[name="condition"], select[name="status"]'
                try:
                    # Try to select by visible text or value
                    await page.select_option(condition_selector, label=condition)
                    await self.human_delay()
                    result['filled'].append('condition')
                except Exception as e:
                    result['errors'].append(f"condition: {e}")
            
            # Color (if provided)
            if color:
                color_selector = 'select[name="color"], input[name="color"]'
                try:
                    await page.fill(color_selector, color)
                    await self.human_delay()
                    result['filled'].append('color')
                except Exception as e:
                    result['errors'].append(f"color: {e}")
            
            return result
            
        except Exception as e:
            result['errors'].append(f"general: {e}")
            return result
    
    async def take_screenshot(self, page: Page, encoding: str = 'base64') -> Optional[str]:
        """
        Take screenshot of current page
        
        Args:
            page: Playwright page
            encoding: 'base64' or 'path'
            
        Returns:
            Screenshot as base64 string or None
        """
        try:
            screenshot_bytes = await page.screenshot(full_page=False)
            if encoding == 'base64':
                return base64.b64encode(screenshot_bytes).decode()
            # For non-base64 encoding, return base64 anyway to match return type
            return base64.b64encode(screenshot_bytes).decode()
        except Exception as e:
            print(f"❌ Screenshot failed: {e}")
            return None
    
    async def click_publish(self, page: Page) -> Tuple[bool, Optional[str]]:
        """
        Click the publish button
        
        Args:
            page: Playwright page
            
        Returns:
            (success, error_message)
        """
        try:
            # Detect challenge before publishing
            if await self.detect_challenge(page):
                raise CaptchaDetected("Challenge/Captcha detected before publish")
            
            # Find publish button (multiple possible selectors)
            publish_selectors = [
                'button:has-text("Publier")',
                'button:has-text("Publish")',
                'button[type="submit"]',
                'button.submit-button'
            ]
            
            for selector in publish_selectors:
                try:
                    button = await page.wait_for_selector(selector, timeout=2000)
                    if button:
                        await button.click()
                        await self.human_delay(1000, 2000)
                        
                        # Check for challenge after click
                        if await self.detect_challenge(page):
                            raise CaptchaDetected("Challenge/Captcha detected after publish click")
                        
                        return (True, None)
                except:
                    continue
            
            return (False, "Publish button not found")
            
        except CaptchaDetected as e:
            return (False, str(e))
        except Exception as e:
            return (False, f"Publish error: {e}")
    
    async def extract_listing_id(self, page: Page) -> Optional[str]:
        """
        Extract listing ID from URL after publish
        
        Args:
            page: Playwright page
            
        Returns:
            Listing ID or None
        """
        try:
            url = page.url
            # Pattern: /items/{listing_id}
            match = re.search(r'/items/(\d+)', url)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            print(f"❌ Extract ID failed: {e}")
            return None
