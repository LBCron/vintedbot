"""
Comprehensive Test Suite for VintedBot
Tests all critical functionality
"""
import pytest
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.vinted_client import VintedClient
from backend.core.session import VintedSession
from backend.core.anonymity import AnonymityManager
from backend.core.proxy_manager import ProxyManager
from backend.monitoring.vinted_monitor import VintedMonitor


class TestAnonymity:
    """Test anonymity features"""

    def test_generate_fingerprint(self):
        """Test fingerprint generation"""
        fp = AnonymityManager.generate_fingerprint()

        assert fp is not None
        assert 'user_agent' in fp
        assert 'viewport' in fp
        assert 'timezone' in fp
        assert fp['viewport']['width'] > 0
        assert fp['viewport']['height'] > 0

    def test_get_random_user_agent(self):
        """Test user agent randomization"""
        ua1 = AnonymityManager.get_random_user_agent()
        ua2 = AnonymityManager.get_random_user_agent()

        assert ua1 is not None
        assert len(ua1) > 50
        # Should be able to get different UAs (not deterministic but likely)

    def test_browser_context_options(self):
        """Test browser context generation"""
        options = AnonymityManager.get_browser_context_options()

        assert 'user_agent' in options
        assert 'viewport' in options
        assert 'timezone_id' in options
        assert 'geolocation' in options


class TestProxyManager:
    """Test proxy management"""

    def test_proxy_manager_init(self):
        """Test proxy manager initialization"""
        manager = ProxyManager()
        assert manager is not None

    def test_add_proxy(self):
        """Test adding proxy"""
        manager = ProxyManager("backend/tests/test_proxies.json")
        manager.add_proxy("test.proxy.com", 8080, "http", country="FR")

        assert len(manager.proxies) > 0
        assert manager.proxies[0]['host'] == "test.proxy.com"

    def test_get_next_proxy(self):
        """Test proxy rotation"""
        manager = ProxyManager("backend/tests/test_proxies.json")
        manager.add_proxy("proxy1.test", 8080, "http")
        manager.add_proxy("proxy2.test", 8080, "http")

        proxy1 = manager.get_next_proxy()
        proxy2 = manager.get_next_proxy()

        assert proxy1 is not None
        assert proxy2 is not None
        # Should rotate
        assert proxy1['host'] != proxy2['host'] or manager.current_index > 1


@pytest.mark.asyncio
class TestVintedClient:
    """Test Vinted client functionality"""

    async def test_client_init(self):
        """Test client initialization"""
        async with VintedClient(headless=True) as client:
            assert client.browser is not None

    async def test_human_delay(self):
        """Test human delay generation"""
        client = VintedClient(headless=True)
        await client.init()

        import time
        start = time.time()
        await client.human_delay(100, 200)
        elapsed = (time.time() - start) * 1000

        assert 90 < elapsed < 250  # Allow some margin

        await client.close()


class TestMonitoring:
    """Test monitoring system"""

    def test_monitor_init(self):
        """Test monitor initialization"""
        monitor = VintedMonitor(
            cookie="test_cookie",
            user_agent="test_ua"
        )
        assert monitor is not None
        assert monitor.results is not None

    @pytest.mark.asyncio
    async def test_monitoring_structure(self):
        """Test monitoring results structure"""
        # This would need real cookie to actually run
        # For now, just test the structure
        monitor = VintedMonitor(
            cookie="test",
            user_agent="test"
        )

        assert 'timestamp' in monitor.results
        assert 'status' in monitor.results
        assert 'tests' in monitor.results
        assert 'changes_detected' in monitor.results


class TestBackup:
    """Test backup system"""

    def test_backup_manager_init(self):
        """Test backup manager initialization"""
        from backend.core.auto_backup import BackupManager

        manager = BackupManager(
            backup_dir="backend/tests/test_backups",
            retention_days=7
        )
        assert manager is not None
        assert manager.backup_dir.exists()

    def test_list_backups(self):
        """Test listing backups"""
        from backend.core.auto_backup import BackupManager

        manager = BackupManager("backend/tests/test_backups")
        backups = manager.list_backups()
        assert isinstance(backups, list)


def test_environment_setup():
    """Test that environment is properly configured"""
    import os

    # Check Python version
    assert sys.version_info >= (3, 9)

    # Check key modules are importable
    import playwright
    import loguru
    import anthropic

    assert True


@pytest.mark.asyncio
async def test_async_operations():
    """Test async operations work correctly"""
    async def dummy_async():
        await asyncio.sleep(0.1)
        return True

    result = await dummy_async()
    assert result is True


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
