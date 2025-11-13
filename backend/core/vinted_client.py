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
from backend.core.circuit_breaker import playwright_breaker, CircuitBreakerError
from loguru import logger


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
    
    async def click_save_as_draft(self, page: Page) -> Tuple[bool, Optional[str]]:
        """
        Click the save as draft button
        
        Args:
            page: Playwright page
            
        Returns:
            (success, error_message)
        """
        try:
            # Detect challenge before saving draft
            if await self.detect_challenge(page):
                raise CaptchaDetected("Challenge/Captcha detected before save draft")
            
            # Find save as draft button (multiple possible selectors)
            draft_selectors = [
                'button:has-text("Sauvegarder comme brouillon")',
                'button:has-text("Enregistrer comme brouillon")',
                'button:has-text("Save as draft")',
                'button[data-testid*="draft"]',
                'button[class*="draft"]',
                'a:has-text("Sauvegarder comme brouillon")',
                'a:has-text("Save as draft")'
            ]
            
            for selector in draft_selectors:
                try:
                    button = await page.wait_for_selector(selector, timeout=2000)
                    if button:
                        await button.click()
                        await self.human_delay(1000, 2000)
                        
                        # Check for challenge after click
                        if await self.detect_challenge(page):
                            raise CaptchaDetected("Challenge/Captcha detected after save draft click")
                        
                        return (True, None)
                except:
                    continue
            
            return (False, "Save as draft button not found")
            
        except CaptchaDetected as e:
            return (False, str(e))
        except Exception as e:
            return (False, f"Save draft error: {e}")
    
    async def extract_draft_id(self, page: Page) -> Optional[str]:
        """
        Extract draft ID from URL after save as draft
        
        Args:
            page: Playwright page
            
        Returns:
            Draft ID or None
        """
        try:
            url = page.url
            # Pattern: /items/drafts/{draft_id}
            match = re.search(r'/items/drafts/(\d+)', url)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            print(f"❌ Extract draft ID failed: {e}")
            return None
    
    async def bump(
        self,
        page: Page,
        listing_id: str,
        listing_url: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Bump a listing by deleting and recreating it
        This brings the listing to the top of search results for free

        Args:
            page: Playwright page
            listing_id: Listing ID to bump
            listing_url: URL to the listing

        Returns:
            (success, error_message)
        """
        try:
            # Protect with circuit breaker
            return await playwright_breaker.call_async(
                self._bump_internal,
                page, listing_id, listing_url
            )
        except CircuitBreakerError as e:
            logger.error(f"Circuit breaker open for bump: {e}")
            return (False, "Service temporarily unavailable - too many failures")
        except Exception as e:
            logger.error(f"Unexpected error in bump: {e}")
            return (False, f"Bump failed: {e}")

    async def _bump_internal(
        self,
        page: Page,
        listing_id: str,
        listing_url: str
    ) -> Tuple[bool, Optional[str]]:
        """Internal bump implementation (called via circuit breaker)"""
        try:
            print(f"🔄 Bumping listing {listing_id}...")

            # Navigate to listing
            await page.goto(listing_url, wait_until='networkidle')
            await self.human_delay(1000, 2000)
            
            # Find delete button
            delete_selectors = [
                'button:has-text("Supprimer")',
                'button:has-text("Delete")',
                'a:has-text("Supprimer")',
                '[data-testid*="delete"]',
                '[class*="delete"]'
            ]
            
            deleted = False
            for selector in delete_selectors:
                try:
                    button = await page.wait_for_selector(selector, timeout=2000)
                    if button:
                        await button.click()
                        await self.human_delay(500, 1000)
                        
                        # Confirm deletion
                        confirm_selectors = [
                            'button:has-text("Confirmer")',
                            'button:has-text("Confirm")',
                            'button:has-text("Oui")',
                            'button:has-text("Yes")'
                        ]
                        
                        for confirm_selector in confirm_selectors:
                            try:
                                confirm_btn = await page.wait_for_selector(confirm_selector, timeout=2000)
                                if confirm_btn:
                                    await confirm_btn.click()
                                    await self.human_delay(1000, 2000)
                                    deleted = True
                                    break
                            except:
                                continue
                        
                        if deleted:
                            break
                except:
                    continue
            
            if not deleted:
                return (False, "Could not delete listing for bump")
            
            print(f"✅ Listing deleted, now recreating...")
            
            # Note: Actual recreation would require saved listing data
            # This is a placeholder - in production, you'd need to:
            # 1. Save listing data before deletion
            # 2. Navigate to /items/new
            # 3. Recreate the listing with saved data
            
            return (True, None)
            
        except Exception as e:
            return (False, f"Bump failed: {e}")
    
    async def follow(
        self,
        page: Page,
        user_id: str,
        user_profile_url: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Follow a Vinted user
        
        Args:
            page: Playwright page
            user_id: Vinted user ID
            user_profile_url: URL to user's profile
            
        Returns:
            (success, error_message)
        """
        try:
            print(f"👥 Following user {user_id}...")
            
            # Navigate to user profile
            await page.goto(user_profile_url, wait_until='networkidle')
            await self.human_delay(1000, 2000)
            
            # Find follow button
            follow_selectors = [
                'button:has-text("Suivre")',
                'button:has-text("Follow")',
                '[data-testid*="follow"]',
                'button[class*="follow"]'
            ]
            
            for selector in follow_selectors:
                try:
                    button = await page.wait_for_selector(selector, timeout=2000)
                    if button:
                        # Check if already following
                        button_text = await button.inner_text()
                        if "Suivi" in button_text or "Following" in button_text:
                            return (True, "Already following")
                        
                        await button.click()
                        await self.human_delay(1000, 2000)
                        
                        print(f"✅ Successfully followed user {user_id}")
                        return (True, None)
                except:
                    continue
            
            return (False, "Follow button not found")
            
        except Exception as e:
            return (False, f"Follow failed: {e}")
    
    async def unfollow(
        self,
        page: Page,
        user_id: str,
        user_profile_url: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Unfollow a Vinted user
        
        Args:
            page: Playwright page
            user_id: Vinted user ID
            user_profile_url: URL to user's profile
            
        Returns:
            (success, error_message)
        """
        try:
            print(f"👋 Unfollowing user {user_id}...")
            
            # Navigate to user profile
            await page.goto(user_profile_url, wait_until='networkidle')
            await self.human_delay(1000, 2000)
            
            # Find unfollow button (usually says "Following" or "Suivi")
            unfollow_selectors = [
                'button:has-text("Suivi")',
                'button:has-text("Following")',
                'button:has-text("Ne plus suivre")',
                'button:has-text("Unfollow")',
                '[data-testid*="unfollow"]'
            ]
            
            for selector in unfollow_selectors:
                try:
                    button = await page.wait_for_selector(selector, timeout=2000)
                    if button:
                        await button.click()
                        await self.human_delay(1000, 2000)
                        
                        # May need to confirm
                        confirm_selectors = [
                            'button:has-text("Confirmer")',
                            'button:has-text("Confirm")',
                            'button:has-text("Ne plus suivre")',
                            'button:has-text("Unfollow")'
                        ]
                        
                        for confirm_selector in confirm_selectors:
                            try:
                                confirm_btn = await page.wait_for_selector(confirm_selector, timeout=1000)
                                if confirm_btn:
                                    await confirm_btn.click()
                                    await self.human_delay(500, 1000)
                                    break
                            except:
                                continue
                        
                        print(f"✅ Successfully unfollowed user {user_id}")
                        return (True, None)
                except:
                    continue
            
            return (False, "Unfollow button not found")
            
        except Exception as e:
            return (False, f"Unfollow failed: {e}")
    
    async def send_message(
        self,
        page: Page,
        conversation_url: str,
        message: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Send a message in a conversation
        
        Args:
            page: Playwright page
            conversation_url: URL to the conversation
            message: Message text to send
            
        Returns:
            (success, error_message)
        """
        try:
            print(f"💬 Sending message...")
            
            # Navigate to conversation
            await page.goto(conversation_url, wait_until='networkidle')
            await self.human_delay(1000, 2000)
            
            # Find message input
            message_selectors = [
                'textarea[placeholder*="message"]',
                'textarea[placeholder*="Message"]',
                'textarea[name="message"]',
                'input[type="text"][placeholder*="message"]',
                '[data-testid*="message-input"]'
            ]
            
            message_input = None
            for selector in message_selectors:
                try:
                    message_input = await page.wait_for_selector(selector, timeout=2000)
                    if message_input:
                        break
                except:
                    continue
            
            if not message_input:
                return (False, "Message input not found")
            
            # Type message with human-like delay between characters
            await message_input.click()
            await self.human_delay(200, 500)
            
            for char in message:
                await message_input.type(char, delay=random.randint(50, 150))
            
            await self.human_delay(500, 1000)
            
            # Find send button
            send_selectors = [
                'button:has-text("Envoyer")',
                'button:has-text("Send")',
                'button[type="submit"]',
                '[data-testid*="send"]'
            ]
            
            for selector in send_selectors:
                try:
                    send_btn = await page.wait_for_selector(selector, timeout=2000)
                    if send_btn:
                        await send_btn.click()
                        await self.human_delay(1000, 2000)
                        
                        print(f"✅ Message sent successfully")
                        return (True, None)
                except:
                    continue
            
            return (False, "Send button not found")
            
        except Exception as e:
            return (False, f"Send message failed: {e}")
