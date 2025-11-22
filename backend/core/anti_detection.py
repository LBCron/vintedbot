"""
Advanced Anti-Detection System for Vinted Automation
Implements sophisticated techniques to avoid bot detection
"""
import random
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
from backend.utils.logger import logger

# ============================================================================
# TIMING & DELAYS
# ============================================================================

class HumanBehavior:
    """Simulate human-like behavior patterns"""

    @staticmethod
    def random_delay(min_sec: float = 1.0, max_sec: float = 3.0) -> float:
        """
        Generate random delay that follows human patterns

        Humans don't use uniform random delays - they have patterns:
        - Most actions are quick (1-2 sec)
        - Occasional longer pauses (thinking)
        - Very rare instant actions
        """
        # 70% quick actions (1-2 sec)
        # 25% medium pauses (2-4 sec)
        # 5% long pauses (4-8 sec)
        roll = random.random()

        if roll < 0.70:
            # Quick action
            return random.uniform(min_sec, min_sec + 1.0)
        elif roll < 0.95:
            # Medium pause
            return random.uniform(min_sec + 1.0, max_sec)
        else:
            # Long pause (thinking)
            return random.uniform(max_sec, max_sec * 2)

    @staticmethod
    async def human_delay(min_sec: float = 1.0, max_sec: float = 3.0):
        """Async human-like delay"""
        delay = HumanBehavior.random_delay(min_sec, max_sec)
        await asyncio.sleep(delay)

    @staticmethod
    def typing_delay_per_char() -> float:
        """
        Human typing speed varies between 50-150ms per character

        Fast typers: 50-80ms
        Average: 80-120ms
        Slow typers: 120-150ms
        """
        # Pick a "personality" for this session
        personality = random.random()

        if personality < 0.2:
            # Fast typer (20%)
            return random.uniform(0.05, 0.08)
        elif personality < 0.7:
            # Average typer (50%)
            return random.uniform(0.08, 0.12)
        else:
            # Slow typer (30%)
            return random.uniform(0.12, 0.15)

    @staticmethod
    async def human_typing(text: str, page) -> None:
        """
        Type text with human-like delays

        Args:
            text: Text to type
            page: Playwright page object
        """
        base_delay = HumanBehavior.typing_delay_per_char()

        for char in text:
            await page.keyboard.type(char)

            # Add variation to each keystroke
            variation = random.uniform(0.8, 1.2)
            delay = base_delay * variation

            # Occasional longer pauses (thinking, backspace, etc.)
            if random.random() < 0.05:  # 5% chance
                delay *= random.uniform(2, 5)

            await asyncio.sleep(delay)


# ============================================================================
# BROWSER FINGERPRINTING
# ============================================================================

class BrowserFingerprint:
    """Generate realistic browser fingerprints to avoid detection"""

    # Real user agents (rotated)
    USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",

        # Chrome on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",

        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",

        # Firefox on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",

        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]

    # Screen resolutions (common ones)
    SCREEN_RESOLUTIONS = [
        {"width": 1920, "height": 1080},  # Full HD (most common)
        {"width": 1366, "height": 768},   # Laptop
        {"width": 2560, "height": 1440},  # 2K
        {"width": 1536, "height": 864},   # Laptop
        {"width": 1440, "height": 900},   # Old laptop
    ]

    # Timezones (Europe)
    TIMEZONES = [
        "Europe/Paris",
        "Europe/London",
        "Europe/Berlin",
        "Europe/Madrid",
        "Europe/Rome",
    ]

    # Languages
    LANGUAGES = [
        "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "en-US,en;q=0.9",
        "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
    ]

    @classmethod
    def generate(cls) -> Dict[str, Any]:
        """Generate complete browser fingerprint"""
        resolution = random.choice(cls.SCREEN_RESOLUTIONS)

        return {
            "user_agent": random.choice(cls.USER_AGENTS),
            "viewport": resolution,
            "screen": resolution,
            "timezone_id": random.choice(cls.TIMEZONES),
            "locale": random.choice(cls.LANGUAGES).split(",")[0],
            "accept_language": random.choice(cls.LANGUAGES),
        }

    @classmethod
    async def apply_to_context(cls, context, fingerprint: Optional[Dict] = None):
        """
        Apply fingerprint to Playwright context

        Args:
            context: Playwright browser context
            fingerprint: Optional pre-generated fingerprint
        """
        if fingerprint is None:
            fingerprint = cls.generate()

        # Note: viewport is already set during context creation in vinted_client.py
        # No need to set it again here as BrowserContext doesn't have set_viewport_size()

        # Set timezone
        await context.add_init_script(f"""
            // Override timezone
            Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {{
                value: function() {{
                    return {{ timeZone: '{fingerprint["timezone_id"]}' }};
                }}
            }});
        """)

        # Anti-detection: Hide webdriver property
        await context.add_init_script("""
            // Hide webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Override plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['fr-FR', 'fr', 'en-US', 'en']
            });

            // Chrome-specific
            window.chrome = { runtime: {} };

            // Permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        logger.info(f"Applied fingerprint: {fingerprint['user_agent'][:50]}...")


# ============================================================================
# PATTERN ROTATION
# ============================================================================

class ActionRotator:
    """Rotate action patterns to avoid predictable behavior"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.action_history: list = []
        self.last_action_time: Dict[str, datetime] = {}

    def should_skip_action(self, action_type: str, min_interval_hours: int = 1) -> bool:
        """
        Check if action should be skipped to avoid patterns

        Args:
            action_type: Type of action (bump, follow, message)
            min_interval_hours: Minimum hours between same action

        Returns:
            True if should skip, False otherwise
        """
        last_time = self.last_action_time.get(action_type)

        if last_time:
            elapsed = datetime.utcnow() - last_time
            if elapsed < timedelta(hours=min_interval_hours):
                logger.info(f"Skipping {action_type} - too soon (last: {elapsed.seconds//60}min ago)")
                return True

        return False

    def record_action(self, action_type: str):
        """Record action execution"""
        self.last_action_time[action_type] = datetime.utcnow()
        self.action_history.append({
            "type": action_type,
            "timestamp": datetime.utcnow()
        })

        # Keep only last 100 actions
        if len(self.action_history) > 100:
            self.action_history = self.action_history[-100:]

    def get_smart_delay(self, action_type: str) -> float:
        """
        Calculate smart delay based on action history

        Users who just did many actions should wait longer
        """
        # Count recent actions (last hour)
        recent_cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_actions = [
            a for a in self.action_history
            if a["timestamp"] > recent_cutoff and a["type"] == action_type
        ]

        # Base delay: 60-180 seconds
        base_delay = random.uniform(60, 180)

        # Add penalty for frequent actions
        penalty = len(recent_actions) * random.uniform(30, 60)

        total_delay = base_delay + penalty

        logger.info(
            f"Smart delay for {action_type}: {total_delay:.0f}s "
            f"(recent actions: {len(recent_actions)})"
        )

        return total_delay


# ============================================================================
# SELECTOR ROTATION
# ============================================================================

class SelectorRotator:
    """Rotate selectors to handle dynamic changes"""

    # Multiple selectors for same element (in priority order)
    SELECTORS = {
        "login_button": [
            "[data-testid='login-button']",
            "button:has-text('Se connecter')",
            "button:has-text('Login')",
            ".auth__button--login",
            "a[href*='login']",
        ],
        "price_input": [
            "[data-testid='price-input']",
            "input[name='price']",
            "input[placeholder*='prix']",
            "input[type='number']",
        ],
        "title_input": [
            "[data-testid='title-input']",
            "input[name='title']",
            "input[placeholder*='titre']",
            "#item-title",
        ],
    }

    @classmethod
    async def find_element(cls, page, element_name: str, timeout: int = 5000):
        """
        Try multiple selectors until one works

        Args:
            page: Playwright page
            element_name: Element name from SELECTORS dict
            timeout: Timeout per selector

        Returns:
            Locator object or None
        """
        selectors = cls.SELECTORS.get(element_name, [])

        for selector in selectors:
            try:
                locator = page.locator(selector)
                await locator.wait_for(state="visible", timeout=timeout)
                logger.info(f"Found {element_name} using: {selector}")
                return locator
            except Exception:
                continue

        logger.warning(f"Could not find {element_name} with any selector")
        return None


# ============================================================================
# PROXY ROTATION (Optional)
# ============================================================================

class ProxyRotator:
    """Rotate proxies for distributed requests (if proxies are configured)"""

    def __init__(self, proxy_list: list = None):
        self.proxies = proxy_list or []
        self.current_index = 0

    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy in rotation"""
        if not self.proxies:
            return None

        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
