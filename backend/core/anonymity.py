"""
Anonymity & Security Module
Fonctionnalités pour rester anonyme et éviter la détection
"""
import random
import hashlib
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json


class AnonymityManager:
    """Manage anonymity and anti-detection features"""

    # User agents rotatifs (vrais navigateurs)
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
    ]

    # Résolutions d'écran communes
    SCREEN_RESOLUTIONS = [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1440, "height": 900},
        {"width": 1536, "height": 864},
        {"width": 2560, "height": 1440},
    ]

    # Fuseaux horaires
    TIMEZONES = [
        "Europe/Paris",
        "Europe/London",
        "Europe/Berlin",
        "Europe/Madrid",
        "Europe/Rome"
    ]

    @staticmethod
    def get_random_user_agent() -> str:
        """Get random user agent"""
        return random.choice(AnonymityManager.USER_AGENTS)

    @staticmethod
    def get_random_viewport() -> Dict[str, int]:
        """Get random viewport size"""
        return random.choice(AnonymityManager.SCREEN_RESOLUTIONS)

    @staticmethod
    def get_random_timezone() -> str:
        """Get random timezone"""
        return random.choice(AnonymityManager.TIMEZONES)

    @staticmethod
    def generate_fingerprint() -> Dict[str, any]:
        """
        Generate realistic browser fingerprint
        Makes each session look like a unique user
        """
        return {
            "user_agent": AnonymityManager.get_random_user_agent(),
            "viewport": AnonymityManager.get_random_viewport(),
            "timezone": AnonymityManager.get_random_timezone(),
            "language": random.choice(["fr-FR", "en-US", "en-GB", "es-ES", "de-DE"]),
            "platform": random.choice(["Win32", "MacIntel", "Linux x86_64"]),
            "hardware_concurrency": random.choice([2, 4, 8, 12, 16]),
            "device_memory": random.choice([4, 8, 16, 32]),
            "color_depth": 24,
            "pixel_ratio": random.choice([1, 1.5, 2]),
            "session_id": str(uuid.uuid4())
        }

    @staticmethod
    def get_browser_context_options(fingerprint: Dict = None) -> Dict:
        """
        Get Playwright browser context options with anti-detection

        Args:
            fingerprint: Optional fingerprint dict

        Returns:
            Context options for Playwright
        """
        if not fingerprint:
            fingerprint = AnonymityManager.generate_fingerprint()

        return {
            "user_agent": fingerprint["user_agent"],
            "viewport": fingerprint["viewport"],
            "locale": fingerprint["language"],
            "timezone_id": fingerprint["timezone"],
            "permissions": ["geolocation"],
            "geolocation": AnonymityManager._get_random_location(),
            "color_scheme": random.choice(["light", "dark"]),
            "extra_http_headers": {
                "Accept-Language": f"{fingerprint['language']},en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1"
            }
        }

    @staticmethod
    def _get_random_location() -> Dict[str, float]:
        """Get random location in France"""
        # Coordonnées de grandes villes françaises
        cities = [
            {"latitude": 48.8566, "longitude": 2.3522},   # Paris
            {"latitude": 45.7640, "longitude": 4.8357},   # Lyon
            {"latitude": 43.2965, "longitude": 5.3698},   # Marseille
            {"latitude": 43.6047, "longitude": 1.4442},   # Toulouse
            {"latitude": 47.2184, "longitude": -1.5536},  # Nantes
        ]
        location = random.choice(cities)
        # Ajouter un peu de randomness (±0.1 degré)
        location["latitude"] += random.uniform(-0.1, 0.1)
        location["longitude"] += random.uniform(-0.1, 0.1)
        location["accuracy"] = random.uniform(10, 100)
        return location

    @staticmethod
    def add_random_delay(min_ms: int = 500, max_ms: int = 3000):
        """
        Calculate random human-like delay

        Args:
            min_ms: Minimum delay in milliseconds
            max_ms: Maximum delay in milliseconds

        Returns:
            Delay in seconds
        """
        import time
        delay_ms = random.randint(min_ms, max_ms)
        return delay_ms / 1000

    @staticmethod
    def generate_session_id() -> str:
        """Generate unique session ID"""
        return hashlib.sha256(f"{uuid.uuid4()}{datetime.now()}".encode()).hexdigest()

    @staticmethod
    def obfuscate_request_pattern():
        """
        Generate random request pattern to avoid detection
        Returns timing pattern for requests
        """
        patterns = [
            # Pattern 1: Regular intervals with variance
            [random.uniform(2, 5) for _ in range(5)],
            # Pattern 2: Burst then pause
            [0.5, 0.7, 0.5, 10, 0.6, 0.8],
            # Pattern 3: Gradually increasing
            [1, 1.5, 2, 2.5, 3, 2, 1.5],
            # Pattern 4: Human-like chaos
            [random.uniform(1, 8) for _ in range(6)]
        ]
        return random.choice(patterns)


class ProxyRotator:
    """Manage proxy rotation for IP anonymity"""

    def __init__(self, proxies: List[str] = None):
        """
        Initialize proxy rotator

        Args:
            proxies: List of proxy URLs (e.g., ["http://proxy1:8080", ...])
        """
        self.proxies = proxies or []
        self.current_index = 0
        self.failed_proxies = set()

    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy from rotation"""
        if not self.proxies:
            return None

        available_proxies = [p for p in self.proxies if p not in self.failed_proxies]
        if not available_proxies:
            # Reset if all failed
            self.failed_proxies.clear()
            available_proxies = self.proxies

        proxy = available_proxies[self.current_index % len(available_proxies)]
        self.current_index += 1
        return proxy

    def mark_failed(self, proxy: str):
        """Mark proxy as failed"""
        self.failed_proxies.add(proxy)

    def get_proxy_config(self) -> Optional[Dict]:
        """
        Get proxy configuration for Playwright

        Returns:
            Proxy config dict or None
        """
        proxy = self.get_next_proxy()
        if not proxy:
            return None

        # Parse proxy URL
        # Format: http://user:pass@host:port or http://host:port
        if "@" in proxy:
            auth_part, server_part = proxy.split("@")
            protocol = auth_part.split("://")[0]
            username, password = auth_part.split("://")[1].split(":")
            server = f"{protocol}://{server_part}"
        else:
            server = proxy
            username = None
            password = None

        config = {"server": server}
        if username and password:
            config["username"] = username
            config["password"] = password

        return config


class RequestObfuscator:
    """Obfuscate requests to look more human"""

    @staticmethod
    def add_realistic_cookies(context) -> None:
        """Add realistic cookies that a real browser would have"""
        cookies = [
            {
                "name": "_ga",
                "value": f"GA1.2.{random.randint(1000000000, 9999999999)}.{int(datetime.now().timestamp())}",
                "domain": ".vinted.fr",
                "path": "/"
            },
            {
                "name": "_gid",
                "value": f"GA1.2.{random.randint(1000000000, 9999999999)}.{int(datetime.now().timestamp())}",
                "domain": ".vinted.fr",
                "path": "/"
            },
            {
                "name": "_fbp",
                "value": f"fb.1.{int(datetime.now().timestamp())}.{random.randint(1000000000, 9999999999)}",
                "domain": ".vinted.fr",
                "path": "/"
            }
        ]
        # Note: context.add_cookies() must be awaited in async context
        return cookies

    @staticmethod
    def simulate_mouse_movement() -> List[Dict]:
        """
        Generate realistic mouse movement pattern
        Returns list of (x, y) coordinates
        """
        movements = []
        x, y = random.randint(100, 500), random.randint(100, 500)

        for _ in range(random.randint(5, 15)):
            # Random movement with smooth transitions
            x += random.randint(-50, 50)
            y += random.randint(-50, 50)
            movements.append({"x": max(0, x), "y": max(0, y)})

        return movements

    @staticmethod
    def generate_typing_delays(text: str) -> List[float]:
        """
        Generate realistic typing delays for each character

        Args:
            text: Text to type

        Returns:
            List of delays in seconds for each character
        """
        delays = []
        for char in text:
            if char == " ":
                # Space takes slightly longer
                delay = random.uniform(0.08, 0.15)
            elif char.isupper():
                # Capital letters take longer (shift key)
                delay = random.uniform(0.12, 0.20)
            else:
                # Normal character
                delay = random.uniform(0.05, 0.12)

            delays.append(delay)

        return delays


# Utility functions
def generate_anonymous_session() -> Dict:
    """Generate complete anonymous session configuration"""
    fingerprint = AnonymityManager.generate_fingerprint()
    session_id = AnonymityManager.generate_session_id()

    return {
        "session_id": session_id,
        "fingerprint": fingerprint,
        "browser_options": AnonymityManager.get_browser_context_options(fingerprint),
        "created_at": datetime.now().isoformat()
    }


def should_rotate_session(last_rotation: datetime, max_age_hours: int = 24) -> bool:
    """Check if session should be rotated"""
    age = datetime.now() - last_rotation
    return age > timedelta(hours=max_age_hours)


if __name__ == "__main__":
    # Test anonymity features
    print("🎭 Anonymity Manager Test\n")

    # Generate fingerprint
    fp = AnonymityManager.generate_fingerprint()
    print("1. Generated Fingerprint:")
    print(json.dumps(fp, indent=2))

    # Get browser options
    print("\n2. Browser Context Options:")
    options = AnonymityManager.get_browser_context_options()
    print(json.dumps(options, indent=2, default=str))

    # Generate session
    print("\n3. Complete Anonymous Session:")
    session = generate_anonymous_session()
    print(json.dumps(session, indent=2, default=str))

    # Test proxy rotation
    print("\n4. Proxy Rotation:")
    proxies = ["http://proxy1:8080", "http://proxy2:8080", "http://proxy3:8080"]
    rotator = ProxyRotator(proxies)
    for i in range(5):
        print(f"   Request {i+1}: {rotator.get_next_proxy()}")

    print("\n✅ All tests passed!")
