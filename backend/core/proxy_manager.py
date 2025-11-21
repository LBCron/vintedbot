"""
Advanced Proxy & VPN Management
Gère les proxies, VPN, et rotation d'IP pour rester anonyme
"""
import asyncio
import aiohttp
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger
import json
from pathlib import Path


class ProxyManager:
    """Advanced proxy management with health checks and rotation"""

    def __init__(self, proxy_file: str = "backend/data/proxies.json"):
        self.proxy_file = Path(proxy_file)
        self.proxies: List[Dict] = []
        self.current_index = 0
        self.failed_count = {}
        self.last_check = {}
        self.load_proxies()

    def load_proxies(self):
        """Load proxies from file"""
        if self.proxy_file.exists():
            try:
                with open(self.proxy_file, 'r') as f:
                    self.proxies = json.load(f)
                logger.info(f"[OK] Loaded {len(self.proxies)} proxies")
            except Exception as e:
                logger.error(f"[ERROR] Failed to load proxies: {e}")
                self.proxies = []
        else:
            logger.warning("[WARN] No proxy file found - running without proxies")
            self.proxies = []

    def save_proxies(self):
        """Save proxies to file"""
        try:
            self.proxy_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.proxy_file, 'w') as f:
                json.dump(self.proxies, f, indent=2)
        except Exception as e:
            logger.error(f"[ERROR] Failed to save proxies: {e}")

    def add_proxy(
        self,
        host: str,
        port: int,
        protocol: str = "http",
        username: Optional[str] = None,
        password: Optional[str] = None,
        country: Optional[str] = None
    ):
        """Add new proxy"""
        proxy = {
            "host": host,
            "port": port,
            "protocol": protocol,
            "username": username,
            "password": password,
            "country": country,
            "status": "active",
            "added_at": datetime.now().isoformat()
        }
        self.proxies.append(proxy)
        self.save_proxies()
        logger.info(f"[OK] Added proxy: {host}:{port}")

    def get_next_proxy(self, country: Optional[str] = None) -> Optional[Dict]:
        """Get next working proxy"""
        if not self.proxies:
            return None

        # Filter by country if specified
        available = [p for p in self.proxies if p["status"] == "active"]
        if country:
            available = [p for p in available if p.get("country") == country]

        if not available:
            logger.warning("[WARN] No available proxies")
            return None

        # Get next in rotation
        proxy = available[self.current_index % len(available)]
        self.current_index += 1

        return proxy

    def get_random_proxy(self, country: Optional[str] = None) -> Optional[Dict]:
        """Get random proxy"""
        available = [p for p in self.proxies if p["status"] == "active"]
        if country:
            available = [p for p in available if p.get("country") == country]

        if not available:
            return None

        return random.choice(available)

    def mark_failed(self, proxy: Dict):
        """Mark proxy as failed"""
        proxy_id = f"{proxy['host']}:{proxy['port']}"
        self.failed_count[proxy_id] = self.failed_count.get(proxy_id, 0) + 1

        # Disable after 3 failures
        if self.failed_count[proxy_id] >= 3:
            for p in self.proxies:
                if p['host'] == proxy['host'] and p['port'] == proxy['port']:
                    p['status'] = 'failed'
                    logger.warning(f"[WARN] Proxy disabled: {proxy_id}")
                    break
            self.save_proxies()

    async def check_proxy(self, proxy: Dict) -> bool:
        """Check if proxy is working"""
        proxy_url = self.format_proxy_url(proxy)
        test_url = "https://api.ipify.org?format=json"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    test_url,
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"[OK] Proxy working: {proxy['host']} (IP: {data.get('ip')})")
                        return True
                    return False
        except Exception as e:
            logger.error(f"[ERROR] Proxy check failed: {proxy['host']} - {e}")
            return False

    async def check_all_proxies(self):
        """Check all proxies health"""
        logger.info("[SEARCH] Checking all proxies...")
        tasks = [self.check_proxy(proxy) for proxy in self.proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for proxy, result in zip(self.proxies, results):
            if isinstance(result, bool):
                proxy['status'] = 'active' if result else 'failed'
                proxy['last_check'] = datetime.now().isoformat()

        self.save_proxies()
        active_count = sum(1 for p in self.proxies if p['status'] == 'active')
        logger.info(f"[OK] Health check complete: {active_count}/{len(self.proxies)} proxies active")

    @staticmethod
    def format_proxy_url(proxy: Dict) -> str:
        """Format proxy as URL"""
        auth = ""
        if proxy.get("username") and proxy.get("password"):
            auth = f"{proxy['username']}:{proxy['password']}@"

        return f"{proxy['protocol']}://{auth}{proxy['host']}:{proxy['port']}"

    def get_playwright_proxy_config(self, proxy: Dict = None) -> Optional[Dict]:
        """
        Get proxy config for Playwright

        Args:
            proxy: Proxy dict (if None, gets next proxy)

        Returns:
            Playwright proxy config
        """
        if proxy is None:
            proxy = self.get_next_proxy()

        if not proxy:
            return None

        config = {
            "server": f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}"
        }

        if proxy.get("username") and proxy.get("password"):
            config["username"] = proxy["username"]
            config["password"] = proxy["password"]

        return config


class VPNManager:
    """
    VPN Management (for local VPN installations)
    Requires OpenVPN or WireGuard installed
    """

    def __init__(self, config_dir: str = "backend/data/vpn_configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.current_vpn = None

    def list_vpn_configs(self) -> List[str]:
        """List available VPN configurations"""
        configs = []
        for file in self.config_dir.glob("*.ovpn"):
            configs.append(file.stem)
        return configs

    async def connect_vpn(self, config_name: str) -> bool:
        """
        Connect to VPN (OpenVPN)
        NOTE: Requires sudo/admin privileges

        Args:
            config_name: Name of VPN config file (without .ovpn)

        Returns:
            True if connected
        """
        config_file = self.config_dir / f"{config_name}.ovpn"
        if not config_file.exists():
            logger.error(f"[ERROR] VPN config not found: {config_name}")
            return False

        try:
            # This is a simplified example
            # In production, you'd use subprocess to call openvpn
            logger.info(f"🔐 Connecting to VPN: {config_name}")
            # proc = await asyncio.create_subprocess_exec(
            #     "openvpn", "--config", str(config_file),
            #     stdout=asyncio.subprocess.PIPE,
            #     stderr=asyncio.subprocess.PIPE
            # )
            # self.current_vpn = proc
            logger.warning("[WARN] VPN connection requires manual setup with OpenVPN/WireGuard")
            return False
        except Exception as e:
            logger.error(f"[ERROR] VPN connection failed: {e}")
            return False

    async def disconnect_vpn(self):
        """Disconnect current VPN"""
        if self.current_vpn:
            logger.info("🔐 Disconnecting VPN...")
            # self.current_vpn.terminate()
            # await self.current_vpn.wait()
            self.current_vpn = None


class IPRotator:
    """
    Smart IP rotation combining proxies and VPN
    """

    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.vpn_manager = VPNManager()
        self.rotation_strategy = "proxy"  # "proxy", "vpn", or "both"
        self.rotation_interval = 50  # Rotate every N requests
        self.request_count = 0

    async def get_current_ip(self) -> Optional[str]:
        """Get current public IP"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.ipify.org?format=json") as response:
                    data = await response.json()
                    return data.get("ip")
        except Exception as e:
            logger.error(f"[ERROR] Failed to get IP: {e}")
            return None

    def should_rotate(self) -> bool:
        """Check if IP should be rotated"""
        self.request_count += 1
        return self.request_count % self.rotation_interval == 0

    async def rotate_ip(self):
        """Rotate IP address"""
        if self.rotation_strategy == "proxy":
            logger.info("[PROCESS] Rotating proxy...")
            new_proxy = self.proxy_manager.get_next_proxy()
            if new_proxy:
                logger.info(f"[OK] Switched to proxy: {new_proxy['host']}")
            return new_proxy

        elif self.rotation_strategy == "vpn":
            logger.info("[PROCESS] Rotating VPN...")
            # VPN rotation logic here
            pass

        elif self.rotation_strategy == "both":
            # Rotate both proxy and VPN
            pass

    def get_playwright_config(self) -> Dict:
        """Get current Playwright proxy config"""
        if self.rotation_strategy in ["proxy", "both"]:
            proxy_config = self.proxy_manager.get_playwright_proxy_config()
            if proxy_config:
                return {"proxy": proxy_config}
        return {}


# Example proxies.json structure for reference
EXAMPLE_PROXIES = [
    {
        "host": "proxy.example.com",
        "port": 8080,
        "protocol": "http",
        "username": "user",
        "password": "pass",
        "country": "FR",
        "status": "active",
        "added_at": "2025-01-15T10:00:00"
    }
]


if __name__ == "__main__":
    # Test proxy manager
    async def test():
        manager = ProxyManager()

        # Add example proxies (you need to add real ones)
        # manager.add_proxy("proxy1.example.com", 8080, "http", country="FR")

        # Check all proxies
        # await manager.check_all_proxies()

        # Get next proxy
        proxy = manager.get_next_proxy()
        if proxy:
            print(f"[OK] Current proxy: {proxy['host']}:{proxy['port']}")
        else:
            print("[WARN] No proxies configured")

        # Test IP rotator
        rotator = IPRotator()
        current_ip = await rotator.get_current_ip()
        print(f"📍 Current IP: {current_ip}")

    asyncio.run(test())
