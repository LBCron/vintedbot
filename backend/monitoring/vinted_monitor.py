"""
Vinted Platform Monitor
Détecte automatiquement les changements dans la plateforme Vinted qui pourraient casser le bot
"""
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from playwright.async_api import async_playwright, Browser, Page
from loguru import logger
import hashlib

from backend.core.vinted_client import VintedClient
from backend.core.session import VintedSession


class VintedMonitor:
    """Monitor Vinted platform for changes"""

    def __init__(self, cookie: str, user_agent: str):
        self.cookie = cookie
        self.user_agent = user_agent
        self.results: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "status": "unknown",
            "tests": [],
            "changes_detected": [],
            "errors": []
        }
        self.snapshot_dir = Path("backend/monitoring/snapshots")
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all monitoring tests"""
        logger.info("[SEARCH] Starting Vinted platform monitoring...")

        try:
            async with VintedClient(headless=True) as client:
                session = VintedSession(
                    cookie=self.cookie,
                    user_agent=self.user_agent
                )
                await client.create_context(session)
                page = await client.new_page()

                # Test 1: Page structure
                await self._test_page_structure(page, client)

                # Test 2: Form selectors
                await self._test_form_selectors(page, client)

                # Test 3: Button selectors
                await self._test_button_selectors(page, client)

                # Test 4: Session validity
                await self._test_session_validity(page, client)

                # Test 5: Upload functionality
                await self._test_upload_functionality(page, client)

            # Analyze results
            self._analyze_results()

        except Exception as e:
            logger.error(f"[ERROR] Monitoring failed: {e}")
            self.results["status"] = "error"
            self.results["errors"].append(str(e))

        # Save results
        self._save_results()

        return self.results

    async def _test_page_structure(self, page: Page, client: VintedClient):
        """Test if key pages load correctly"""
        test_name = "page_structure"
        logger.info(f"Testing {test_name}...")

        try:
            # Test new item page
            await page.goto("https://www.vinted.fr/items/new", wait_until='networkidle', timeout=15000)

            # Take snapshot of page structure
            page_hash = await self._snapshot_page_structure(page, "items_new")

            # Check if structure changed
            previous_hash = self._load_previous_hash("items_new")
            if previous_hash and previous_hash != page_hash:
                self.results["changes_detected"].append({
                    "test": test_name,
                    "message": "Page structure changed on /items/new",
                    "severity": "high",
                    "details": {
                        "previous_hash": previous_hash,
                        "current_hash": page_hash
                    }
                })

            self.results["tests"].append({
                "name": test_name,
                "status": "passed",
                "url": page.url
            })

        except Exception as e:
            logger.error(f"[ERROR] {test_name} failed: {e}")
            self.results["tests"].append({
                "name": test_name,
                "status": "failed",
                "error": str(e)
            })

    async def _test_form_selectors(self, page: Page, client: VintedClient):
        """Test if form selectors still exist"""
        test_name = "form_selectors"
        logger.info(f"Testing {test_name}...")

        selectors_to_test = {
            "title": ['input[name="title"]', 'input[placeholder*="Titre"]'],
            "description": ['textarea[name="description"]', 'textarea[placeholder*="Description"]'],
            "price": ['input[name="price"]', 'input[type="number"]'],
            "brand": ['input[name="brand"]', 'input[placeholder*="Marque"]'],
            "file_upload": ['input[type="file"]']
        }

        try:
            await page.goto("https://www.vinted.fr/items/new", wait_until='networkidle', timeout=15000)

            missing_selectors = []
            for field, selectors in selectors_to_test.items():
                found = False
                for selector in selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            found = True
                            break
                    except:
                        pass

                if not found:
                    missing_selectors.append({
                        "field": field,
                        "selectors": selectors
                    })
                    self.results["changes_detected"].append({
                        "test": test_name,
                        "message": f"Form selector missing: {field}",
                        "severity": "critical",
                        "details": {
                            "field": field,
                            "tested_selectors": selectors
                        }
                    })

            self.results["tests"].append({
                "name": test_name,
                "status": "passed" if not missing_selectors else "failed",
                "missing_selectors": missing_selectors
            })

        except Exception as e:
            logger.error(f"[ERROR] {test_name} failed: {e}")
            self.results["tests"].append({
                "name": test_name,
                "status": "failed",
                "error": str(e)
            })

    async def _test_button_selectors(self, page: Page, client: VintedClient):
        """Test if button selectors still exist"""
        test_name = "button_selectors"
        logger.info(f"Testing {test_name}...")

        button_selectors = {
            "publish": [
                'button:has-text("Publier")',
                'button:has-text("Publish")',
                'button[type="submit"]'
            ],
            "draft": [
                'button:has-text("Sauvegarder comme brouillon")',
                'button:has-text("Save as draft")'
            ]
        }

        try:
            await page.goto("https://www.vinted.fr/items/new", wait_until='networkidle', timeout=15000)

            missing_buttons = []
            for button_name, selectors in button_selectors.items():
                found = False
                for selector in selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            found = True
                            break
                    except:
                        pass

                if not found:
                    missing_buttons.append({
                        "button": button_name,
                        "selectors": selectors
                    })
                    self.results["changes_detected"].append({
                        "test": test_name,
                        "message": f"Button selector missing: {button_name}",
                        "severity": "high",
                        "details": {
                            "button": button_name,
                            "tested_selectors": selectors
                        }
                    })

            self.results["tests"].append({
                "name": test_name,
                "status": "passed" if not missing_buttons else "failed",
                "missing_buttons": missing_buttons
            })

        except Exception as e:
            logger.error(f"[ERROR] {test_name} failed: {e}")
            self.results["tests"].append({
                "name": test_name,
                "status": "failed",
                "error": str(e)
            })

    async def _test_session_validity(self, page: Page, client: VintedClient):
        """Test if session is still valid"""
        test_name = "session_validity"
        logger.info(f"Testing {test_name}...")

        try:
            await page.goto("https://www.vinted.fr/items/new", wait_until='networkidle', timeout=15000)

            current_url = page.url

            # Check if redirected to login
            if 'session' in current_url or 'login' in current_url or 'member/login' in current_url:
                self.results["changes_detected"].append({
                    "test": test_name,
                    "message": "Session expired - cookie needs to be updated",
                    "severity": "critical",
                    "details": {
                        "redirected_to": current_url
                    }
                })
                self.results["tests"].append({
                    "name": test_name,
                    "status": "failed",
                    "message": "Session expired"
                })
            else:
                self.results["tests"].append({
                    "name": test_name,
                    "status": "passed"
                })

        except Exception as e:
            logger.error(f"[ERROR] {test_name} failed: {e}")
            self.results["tests"].append({
                "name": test_name,
                "status": "failed",
                "error": str(e)
            })

    async def _test_upload_functionality(self, page: Page, client: VintedClient):
        """Test if file upload still works"""
        test_name = "upload_functionality"
        logger.info(f"Testing {test_name}...")

        try:
            await page.goto("https://www.vinted.fr/items/new", wait_until='networkidle', timeout=15000)

            # Check if file input exists and is functional
            file_input = await page.query_selector('input[type="file"]')

            if not file_input:
                self.results["changes_detected"].append({
                    "test": test_name,
                    "message": "File upload input not found",
                    "severity": "critical",
                    "details": {}
                })
                self.results["tests"].append({
                    "name": test_name,
                    "status": "failed",
                    "message": "File input not found"
                })
            else:
                # Check if input accepts files
                is_visible = await file_input.is_visible()
                is_enabled = await file_input.is_enabled()

                self.results["tests"].append({
                    "name": test_name,
                    "status": "passed",
                    "details": {
                        "visible": is_visible,
                        "enabled": is_enabled
                    }
                })

        except Exception as e:
            logger.error(f"[ERROR] {test_name} failed: {e}")
            self.results["tests"].append({
                "name": test_name,
                "status": "failed",
                "error": str(e)
            })

    async def _snapshot_page_structure(self, page: Page, page_name: str) -> str:
        """Take snapshot of page structure and return hash"""
        try:
            # Get page content
            content = await page.content()

            # Extract key structural elements (simplified)
            # In production, you'd want more sophisticated analysis
            structure = {
                "forms": len(await page.query_selector_all("form")),
                "inputs": len(await page.query_selector_all("input")),
                "buttons": len(await page.query_selector_all("button")),
                "textareas": len(await page.query_selector_all("textarea"))
            }

            # Create hash
            structure_str = json.dumps(structure, sort_keys=True)
            page_hash = hashlib.md5(structure_str.encode()).hexdigest()

            # Save snapshot
            snapshot_file = self.snapshot_dir / f"{page_name}_latest.json"
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "hash": page_hash,
                    "structure": structure
                }, f, indent=2)

            return page_hash

        except Exception as e:
            logger.error(f"Failed to snapshot page structure: {e}")
            return ""

    def _load_previous_hash(self, page_name: str) -> Optional[str]:
        """Load previous page structure hash"""
        try:
            snapshot_file = self.snapshot_dir / f"{page_name}_latest.json"
            if snapshot_file.exists():
                with open(snapshot_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("hash")
            return None
        except:
            return None

    def _analyze_results(self):
        """Analyze test results and set overall status"""
        failed_tests = [t for t in self.results["tests"] if t["status"] == "failed"]
        changes = self.results["changes_detected"]

        if failed_tests or changes:
            # Check severity
            critical_changes = [c for c in changes if c.get("severity") == "critical"]
            if critical_changes:
                self.results["status"] = "critical"
            else:
                self.results["status"] = "warning"
        else:
            self.results["status"] = "healthy"

        logger.info(f"[OK] Monitoring complete. Status: {self.results['status']}")

    def _save_results(self):
        """Save monitoring results"""
        results_file = self.snapshot_dir / f"monitor_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        # Also save as latest
        latest_file = self.snapshot_dir / "monitor_results_latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        logger.info(f"📝 Results saved to {results_file}")


async def run_monitoring(cookie: str, user_agent: str) -> Dict[str, Any]:
    """Run monitoring and return results"""
    monitor = VintedMonitor(cookie, user_agent)
    return await monitor.run_all_tests()


if __name__ == "__main__":
    # Test locally
    import sys

    cookie = os.getenv("VINTED_COOKIE", "")
    user_agent = os.getenv("VINTED_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    if not cookie:
        print("[ERROR] VINTED_COOKIE environment variable required")
        sys.exit(1)

    results = asyncio.run(run_monitoring(cookie, user_agent))

    print(json.dumps(results, indent=2, ensure_ascii=False))

    # Exit with error code if critical issues found
    if results["status"] == "critical":
        sys.exit(1)
