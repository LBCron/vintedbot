"""
VintedBot Human Simulator
Simulates a real user testing the entire application
"""
import asyncio
import random
import time
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

@dataclass
class TestResult:
    """Result of a single test"""
    test_name: str
    status: str  # 'pass', 'fail', 'warning'
    duration: float
    screenshot_path: Optional[str] = None
    error_message: Optional[str] = None
    details: Optional[Dict] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class Bug:
    """A bug found during testing"""
    type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    issue: str
    screenshot: Optional[str] = None
    how_to_reproduce: Optional[str] = None
    suggested_fix: Optional[str] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class Improvement:
    """An improvement suggestion"""
    type: str
    severity: str
    issue: str
    suggestion: str
    business_impact: Optional[str] = None
    implementation_effort: Optional[str] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


class HumanSimulator:
    """Simulates a real human user testing the application"""

    def __init__(self, base_url: str = "http://localhost:5174", headless: bool = False):
        self.base_url = base_url
        self.headless = headless
        self.results: List[TestResult] = []
        self.bugs: List[Bug] = []
        self.improvements: List[Improvement] = []
        self.test_email = f"test_{random.randint(10000, 99999)}@example.com"
        self.test_password = "SecureTest123!@#"

        # Create directories
        Path("test-results/screenshots").mkdir(parents=True, exist_ok=True)

    async def run_complete_simulation(self):
        """Run complete user simulation"""
        print("🤖 SIMULATION UTILISATEUR HUMAIN VINTEDBOT")
        print("=" * 70)
        print(f"Base URL: {self.base_url}")
        print(f"Test Email: {self.test_email}")
        print(f"Headless: {self.headless}")
        print("=" * 70)

        start_time = time.time()

        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=self.headless,
                slow_mo=50 if not self.headless else 0  # Slow down for visibility
            )

            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='fr-FR',
                timezone_id='Europe/Paris'
            )

            page = await context.new_page()

            # Enable console logging
            page.on("console", lambda msg: print(f"  [CONSOLE {msg.type}] {msg.text}"))
            page.on("pageerror", lambda exc: self.add_bug("critical", "javascript", f"Uncaught exception: {exc}"))

            try:
                # Test suite
                await self.test_homepage_first_visit(page)
                await self.test_signup_flow(page)
                await self.test_dashboard_overview(page)
                await self.test_upload_and_ai_draft(page)
                await self.test_language_switch(page)
                await self.test_performance_metrics(page)
                await self.test_mobile_responsive(context)
                await self.test_accessibility(page)

            except Exception as e:
                print(f"\n❌ Fatal error during simulation: {e}")
                await self.take_screenshot(page, "fatal_error")

            finally:
                await browser.close()

        total_duration = time.time() - start_time

        # Generate report
        await self.generate_report(total_duration)

        print(f"\n{'=' * 70}")
        print(f"✅ SIMULATION TERMINÉE EN {total_duration:.2f}s")
        print(f"{'=' * 70}")
        print(f"Tests: {len(self.results)}")
        print(f"Bugs: {len(self.bugs)} ({len([b for b in self.bugs if b.severity == 'critical'])} critical)")
        print(f"Improvements: {len(self.improvements)}")
        print(f"\n📄 Rapport: test-results/report.html")
        print(f"📊 JSON: test-results/report.json")

    # =============================================================================
    # TEST SCENARIOS
    # =============================================================================

    async def test_homepage_first_visit(self, page: Page):
        """Test: First-time visitor landing on homepage"""
        test_name = "Homepage - First Visit"
        start = time.time()

        try:
            print(f"\n🔍 TEST: {test_name}")

            # Navigate to homepage
            response = await page.goto(self.base_url, wait_until='domcontentloaded')
            load_time = time.time() - start

            # Check HTTP status
            if response.status != 200:
                self.add_bug("high", "server", f"Homepage returns HTTP {response.status}")

            # Check load time
            if load_time > 3:
                self.add_improvement(
                    "performance",
                    "medium",
                    f"Homepage loads in {load_time:.2f}s (target: <3s)",
                    "Optimize bundle size, enable code splitting, lazy load images",
                    "5% conversion improvement",
                    "2 days"
                )

            await self.human_delay()

            # Check for logo
            logo_count = await page.locator('img[alt*="logo" i], [data-testid="logo"], .logo').count()
            if logo_count == 0:
                self.add_bug("medium", "branding", "No visible logo on homepage", await self.take_screenshot(page, "no-logo"))

            # Check for call-to-action
            cta = page.locator('button, a').filter(has_text=re.compile(r'sign up|get started|commencer|inscription', re.I))
            if await cta.count() == 0:
                self.add_bug("high", "conversion", "No clear CTA button on homepage", await self.take_screenshot(page, "no-cta"))

            # Check page title
            title = await page.title()
            if not title or len(title) < 10:
                self.add_improvement("seo", "low", f"Page title too short: '{title}'", "Add descriptive SEO title")

            # Scroll behavior
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await self.human_delay(500)

            self.add_result(test_name, "pass", time.time() - start, details={'load_time': load_time, 'status': response.status})
            print(f"  ✅ Homepage OK ({load_time:.2f}s)")

        except Exception as e:
            await self.handle_test_error(page, test_name, e, start)

    async def test_signup_flow(self, page: Page):
        """Test: User signup process"""
        test_name = "User Signup Flow"
        start = time.time()

        try:
            print(f"\n🔍 TEST: {test_name}")

            # Find and click signup button
            signup_buttons = page.locator('a, button').filter(has_text=re.compile(r'sign up|register|inscription', re.I))

            if await signup_buttons.count() == 0:
                self.add_bug("critical", "navigation", "No signup button found", await self.take_screenshot(page, "no-signup-button"))
                raise Exception("Cannot proceed without signup button")

            await signup_buttons.first.click()
            await self.human_delay()

            # Wait for signup form
            try:
                await page.wait_for_url('**/register', timeout=5000)
            except:
                # Maybe different URL
                current_url = page.url
                if 'register' not in current_url.lower() and 'signup' not in current_url.lower():
                    self.add_bug("medium", "navigation", f"Signup redirects to unexpected URL: {current_url}")

            # Test validation - invalid email
            email_input = page.locator('input[type="email"], input[name="email"]').first
            password_input = page.locator('input[type="password"], input[name="password"]').first

            if await email_input.count() == 0 or await password_input.count() == 0:
                self.add_bug("critical", "form", "Email or password input not found", await self.take_screenshot(page, "missing-form-fields"))
                raise Exception("Form fields missing")

            # Test 1: Invalid email
            await email_input.fill("not-an-email")
            await password_input.fill(self.test_password)

            submit_button = page.locator('button[type="submit"]').first
            await submit_button.click()
            await self.human_delay(1000)

            # Check for error message
            error_visible = await page.locator('text=/invalid.*email|email.*invalid/i').count() > 0
            if not error_visible:
                self.add_bug("medium", "validation", "No error message for invalid email format")

            # Test 2: Valid signup
            await email_input.fill(self.test_email)
            await password_input.fill(self.test_password)

            # Fill name if exists
            name_input = page.locator('input[name="name"], input[placeholder*="name" i]')
            if await name_input.count() > 0:
                await name_input.first.fill("Test User")

            await submit_button.click()
            await self.human_delay(3000)  # Wait for signup to complete

            # Check redirect
            current_url = page.url
            expected_redirects = ['/dashboard', '/upload', '/home']
            redirected_correctly = any(path in current_url for path in expected_redirects)

            if not redirected_correctly:
                self.add_bug("high", "flow", f"Signup doesn't redirect to dashboard (current: {current_url})", await self.take_screenshot(page, "wrong-signup-redirect"))

            # Check for welcome message or confirmation
            welcome_msg = await page.locator('text=/welcome|bienvenue|success/i').count()
            if welcome_msg == 0:
                self.add_improvement("ux", "low", "No welcome message after signup", "Add toast notification to confirm successful signup")

            self.add_result(test_name, "pass", time.time() - start, details={'email': self.test_email})
            print(f"  ✅ Signup successful: {self.test_email}")

        except Exception as e:
            await self.handle_test_error(page, test_name, e, start)

    async def test_dashboard_overview(self, page: Page):
        """Test: Dashboard overview and navigation"""
        test_name = "Dashboard Overview"
        start = time.time()

        try:
            print(f"\n🔍 TEST: {test_name}")

            # Ensure we're on dashboard
            if '/dashboard' not in page.url and '/home' not in page.url:
                await page.goto(f"{self.base_url}/dashboard")
                await self.human_delay()

            # Check for navigation menu
            nav_items = ['Upload', 'Drafts', 'Analytics', 'Settings']
            for item in nav_items:
                nav_link = page.locator(f'a, button').filter(has_text=re.compile(item, re.I))
                if await nav_link.count() == 0:
                    self.add_improvement("navigation", "medium", f"No '{item}' link in navigation", "Add clear navigation to all key features")

            # Check for empty state or data
            page_text = await page.inner_text('body')
            if 'no draft' in page_text.lower() or 'aucun brouillon' in page_text.lower():
                print("  ℹ️  Dashboard shows empty state (expected for new user)")
            else:
                print("  ℹ️  Dashboard shows existing data")

            self.add_result(test_name, "pass", time.time() - start)
            print(f"  ✅ Dashboard OK")

        except Exception as e:
            await self.handle_test_error(page, test_name, e, start)

    async def test_upload_and_ai_draft(self, page: Page):
        """Test: Upload images and AI draft creation"""
        test_name = "Upload & AI Draft Creation"
        start = time.time()

        try:
            print(f"\n🔍 TEST: {test_name}")

            # Navigate to upload page
            upload_link = page.locator('a, button').filter(has_text=re.compile(r'upload|télécharger', re.I)).first
            if await upload_link.count() > 0:
                await upload_link.click()
                await self.human_delay()

            # Check we're on upload page
            if '/upload' not in page.url:
                await page.goto(f"{self.base_url}/upload")
                await self.human_delay()

            # Look for file input
            file_input = page.locator('input[type="file"]').first

            if await file_input.count() == 0:
                self.add_bug("critical", "upload", "No file input found on upload page", await self.take_screenshot(page, "no-file-input"))
                raise Exception("Cannot test upload without file input")

            # Create dummy test image files (since we may not have fixtures)
            # In real scenario, we'd use actual image files
            print("  ⚠️  Skipping actual file upload (requires test fixtures)")
            self.add_improvement("testing", "low", "Add test image fixtures for automated testing", "Create fixtures folder with sample product images")

            self.add_result(test_name, "warning", time.time() - start, details={'note': 'Requires test fixtures'})
            print(f"  ⚠️  Upload test incomplete (needs fixtures)")

        except Exception as e:
            await self.handle_test_error(page, test_name, e, start)

    async def test_language_switch(self, page: Page):
        """Test: Language switching functionality"""
        test_name = "Language Switch"
        start = time.time()

        try:
            print(f"\n🔍 TEST: {test_name}")

            # Look for language selector
            lang_selectors = page.locator('[data-testid="language-selector"], button').filter(has_text=re.compile(r'EN|FR|language|langue', re.I))

            if await lang_selectors.count() == 0:
                self.add_improvement("i18n", "medium", "No visible language selector", "Add language switcher to navbar")
                self.add_result(test_name, "warning", time.time() - start, details={'note': 'No language selector found'})
                print("  ⚠️  No language selector found")
                return

            # Test language switch
            await lang_selectors.first.click()
            await self.human_delay()

            # Check if content changed
            page_text_before = await page.inner_text('body')

            # Click language option
            en_option = page.locator('text=/english|anglais|EN/i').first
            if await en_option.count() > 0:
                await en_option.click()
                await self.human_delay(1000)

                page_text_after = await page.inner_text('body')

                # Very basic check - text should be different
                if page_text_before == page_text_after:
                    self.add_bug("medium", "i18n", "Language switch doesn't change content", await self.take_screenshot(page, "lang-no-change"))
                else:
                    print("  ✅ Language switched successfully")

            self.add_result(test_name, "pass", time.time() - start)

        except Exception as e:
            await self.handle_test_error(page, test_name, e, start)

    async def test_performance_metrics(self, page: Page):
        """Test: Performance metrics"""
        test_name = "Performance Metrics"
        start = time.time()

        try:
            print(f"\n🔍 TEST: {test_name}")

            # Get performance metrics
            metrics = await page.evaluate("""() => {
                const perfData = window.performance.timing;
                const dns = perfData.domainLookupEnd - perfData.domainLookupStart;
                const tcp = perfData.connectEnd - perfData.connectStart;
                const ttfb = perfData.responseStart - perfData.requestStart;
                const load = perfData.loadEventEnd - perfData.navigationStart;

                return {
                    dns: dns,
                    tcp: tcp,
                    ttfb: ttfb,
                    total: load
                };
            }""")

            print(f"  📊 Metrics:")
            print(f"     DNS: {metrics['dns']}ms")
            print(f"     TCP: {metrics['tcp']}ms")
            print(f"     TTFB: {metrics['ttfb']}ms")
            print(f"     Total: {metrics['total']}ms")

            if metrics['ttfb'] > 1000:
                self.add_improvement("performance", "high", f"Time to First Byte is {metrics['ttfb']}ms (target: <500ms)", "Optimize server response time, add caching")

            if metrics['total'] > 5000:
                self.add_improvement("performance", "medium", f"Total page load is {metrics['total']}ms (target: <3000ms)", "Optimize assets, enable CDN")

            self.add_result(test_name, "pass", time.time() - start, details=metrics)
            print(f"  ✅ Performance metrics captured")

        except Exception as e:
            await self.handle_test_error(page, test_name, e, start)

    async def test_mobile_responsive(self, context: BrowserContext):
        """Test: Mobile responsive design"""
        test_name = "Mobile Responsive"
        start = time.time()

        try:
            print(f"\n🔍 TEST: {test_name}")

            # Create mobile page
            mobile_page = await context.new_page()
            await mobile_page.set_viewport_size({"width": 375, "height": 667})  # iPhone SE

            # Navigate to homepage
            await mobile_page.goto(self.base_url)
            await self.human_delay()

            # Check if navigation is hidden/hamburger
            nav_elements = await mobile_page.locator('nav a').count()

            # Take screenshot
            await self.take_screenshot(mobile_page, "mobile_view")

            # Check for common mobile issues
            body_width = await mobile_page.evaluate("document.body.scrollWidth")
            viewport_width = 375

            if body_width > viewport_width * 1.1:  # 10% tolerance
                self.add_bug("medium", "responsive", f"Horizontal scroll on mobile (width: {body_width}px > {viewport_width}px)", "mobile_view")

            await mobile_page.close()

            self.add_result(test_name, "pass", time.time() - start)
            print(f"  ✅ Mobile responsive check done")

        except Exception as e:
            print(f"  ❌ Mobile test error: {e}")
            self.add_result(test_name, "fail", time.time() - start, error_message=str(e))

    async def test_accessibility(self, page: Page):
        """Test: Basic accessibility checks"""
        test_name = "Accessibility"
        start = time.time()

        try:
            print(f"\n🔍 TEST: {test_name}")

            # Check for alt text on images
            images_without_alt = await page.locator('img:not([alt])').count()
            if images_without_alt > 0:
                self.add_bug("medium", "a11y", f"{images_without_alt} images missing alt text", "Add descriptive alt text to all images")

            # Check for proper heading hierarchy
            h1_count = await page.locator('h1').count()
            if h1_count == 0:
                self.add_bug("medium", "seo", "No H1 heading on page", "Add H1 heading for SEO and accessibility")
            elif h1_count > 1:
                self.add_improvement("seo", "low", f"Multiple H1 headings ({h1_count}) on page", "Use single H1, organize with H2-H6")

            # Check for form labels
            inputs_without_labels = await page.evaluate("""() => {
                const inputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"]');
                let count = 0;
                inputs.forEach(input => {
                    if (!input.labels || input.labels.length === 0) {
                        if (!input.getAttribute('aria-label') && !input.getAttribute('placeholder')) {
                            count++;
                        }
                    }
                });
                return count;
            }""")

            if inputs_without_labels > 0:
                self.add_bug("medium", "a11y", f"{inputs_without_labels} form inputs missing labels", "Add proper labels or aria-label attributes")

            self.add_result(test_name, "pass", time.time() - start)
            print(f"  ✅ Accessibility check done")

        except Exception as e:
            await self.handle_test_error(page, test_name, e, start)

    # =============================================================================
    # HELPERS
    # =============================================================================

    async def human_delay(self, ms: int = None):
        """Simulate human delay"""
        if ms is None:
            ms = random.randint(300, 1500)
        await asyncio.sleep(ms / 1000)

    async def take_screenshot(self, page: Page, name: str) -> str:
        """Take screenshot"""
        timestamp = int(time.time())
        safe_name = name.replace(" ", "_").replace("/", "_")
        path = f"test-results/screenshots/{safe_name}_{timestamp}.png"
        try:
            await page.screenshot(path=path, full_page=True)
            return path
        except Exception as e:
            print(f"  ⚠️  Screenshot failed: {e}")
            return None

    def add_result(self, test_name: str, status: str, duration: float, screenshot_path: str = None, error_message: str = None, details: Dict = None):
        """Add test result"""
        self.results.append(TestResult(
            test_name=test_name,
            status=status,
            duration=duration,
            screenshot_path=screenshot_path,
            error_message=error_message,
            details=details
        ))

    def add_bug(self, severity: str, bug_type: str, issue: str, screenshot: str = None, how_to_reproduce: str = None, suggested_fix: str = None):
        """Add bug"""
        self.bugs.append(Bug(
            type=bug_type,
            severity=severity,
            issue=issue,
            screenshot=screenshot,
            how_to_reproduce=how_to_reproduce,
            suggested_fix=suggested_fix
        ))

    def add_improvement(self, imp_type: str, severity: str, issue: str, suggestion: str, business_impact: str = None, implementation_effort: str = None):
        """Add improvement"""
        self.improvements.append(Improvement(
            type=imp_type,
            severity=severity,
            issue=issue,
            suggestion=suggestion,
            business_impact=business_impact,
            implementation_effort=implementation_effort
        ))

    async def handle_test_error(self, page: Page, test_name: str, error: Exception, start_time: float):
        """Handle test error"""
        screenshot = await self.take_screenshot(page, f"error_{test_name.replace(' ', '_')}")

        self.add_result(
            test_name=test_name,
            status="fail",
            duration=time.time() - start_time,
            screenshot_path=screenshot,
            error_message=str(error)
        )

        self.add_bug(
            severity="critical",
            bug_type="crash",
            issue=f"{test_name} failed: {str(error)}",
            screenshot=screenshot
        )

        print(f"  ❌ {test_name} FAILED: {error}")

    async def generate_report(self, total_duration: float):
        """Generate HTML and JSON report"""

        # Calculate stats
        total_tests = len(self.results)
        passed = len([r for r in self.results if r.status == 'pass'])
        failed = len([r for r in self.results if r.status == 'fail'])
        warnings = len([r for r in self.results if r.status == 'warning'])

        critical_bugs = len([b for b in self.bugs if b.severity == 'critical'])
        high_bugs = len([b for b in self.bugs if b.severity == 'high'])
        medium_bugs = len([b for b in self.bugs if b.severity == 'medium'])

        # Generate HTML
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VintedBot Test Report - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
        .header h1 {{ font-size: 36px; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .stat-card {{ background: white; border-radius: 10px; padding: 25px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }}
        .stat-number {{ font-size: 48px; font-weight: bold; margin-bottom: 5px; }}
        .stat-label {{ color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }}
        .pass {{ color: #10b981; }}
        .fail {{ color: #ef4444; }}
        .warning {{ color: #f59e0b; }}
        .section {{ background: white; border-radius: 10px; padding: 30px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }}
        .section h2 {{ font-size: 24px; margin-bottom: 20px; color: #1f2937; }}
        .bug-card, .improvement-card {{ padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid; }}
        .bug-card.critical {{ border-color: #ef4444; background: #fef2f2; }}
        .bug-card.high {{ border-color: #f59e0b; background: #fffbeb; }}
        .bug-card.medium {{ border-color: #3b82f6; background: #eff6ff; }}
        .bug-card.low {{ border-color: #6b7280; background: #f9fafb; }}
        .improvement-card {{ border-color: #10b981; background: #f0fdf4; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        .badge.critical {{ background: #ef4444; color: white; }}
        .badge.high {{ background: #f59e0b; color: white; }}
        .badge.medium {{ background: #3b82f6; color: white; }}
        .badge.low {{ background: #6b7280; color: white; }}
        .screenshot {{ max-width: 100%; border-radius: 8px; margin-top: 10px; cursor: pointer; border: 2px solid #e5e7eb; }}
        .screenshot:hover {{ border-color: #667eea; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        th {{ background: #f9fafb; font-weight: 600; color: #374151; }}
        tr:hover {{ background: #f9fafb; }}
        .status-pass {{ color: #10b981; font-weight: 600; }}
        .status-fail {{ color: #ef4444; font-weight: 600; }}
        .status-warning {{ color: #f59e0b; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 VintedBot - Test Report</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')} | Duration: {total_duration:.2f}s</p>
        </div>

        <div class="summary">
            <div class="stat-card">
                <div class="stat-number pass">{passed}</div>
                <div class="stat-label">Tests Passed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number fail">{failed}</div>
                <div class="stat-label">Tests Failed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number warning">{warnings}</div>
                <div class="stat-label">Warnings</div>
            </div>
            <div class="stat-card">
                <div class="stat-number fail">{critical_bugs + high_bugs}</div>
                <div class="stat-label">Critical/High Bugs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(self.bugs)}</div>
                <div class="stat-label">Total Bugs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(self.improvements)}</div>
                <div class="stat-label">Improvements</div>
            </div>
        </div>

        <div class="section">
            <h2>🔴 Bugs Found ({len(self.bugs)})</h2>
            {self._format_bugs_html()}
        </div>

        <div class="section">
            <h2>💡 Improvements Suggested ({len(self.improvements)})</h2>
            {self._format_improvements_html()}
        </div>

        <div class="section">
            <h2>📊 Test Results ({total_tests})</h2>
            {self._format_results_html()}
        </div>
    </div>
</body>
</html>"""

        # Save HTML
        with open('test-results/report.html', 'w', encoding='utf-8') as f:
            f.write(html)

        # Save JSON
        json_data = {
            'generated_at': datetime.now().isoformat(),
            'duration': total_duration,
            'summary': {
                'total_tests': total_tests,
                'passed': passed,
                'failed': failed,
                'warnings': warnings,
                'bugs_found': len(self.bugs),
                'critical_bugs': critical_bugs,
                'high_bugs': high_bugs,
                'medium_bugs': medium_bugs,
                'improvements': len(self.improvements)
            },
            'bugs': [b.to_dict() for b in self.bugs],
            'improvements': [i.to_dict() for i in self.improvements],
            'test_results': [r.to_dict() for r in self.results]
        }

        with open('test-results/report.json', 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)

    def _format_bugs_html(self) -> str:
        if not self.bugs:
            return '<p style="color: #10b981; font-size: 18px;">✅ No bugs found!</p>'

        html = ''
        for bug in sorted(self.bugs, key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[x.severity]):
            screenshot_html = ''
            if bug.screenshot:
                screenshot_html = f'<img src="{bug.screenshot}" class="screenshot" alt="Bug screenshot">'

            html += f'''
            <div class="bug-card {bug.severity}">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                    <span class="badge {bug.severity}">{bug.severity}</span>
                    <span style="color: #6b7280; font-size: 14px;">{bug.type}</span>
                </div>
                <p style="font-size: 16px; font-weight: 500; margin-bottom: 8px;">{bug.issue}</p>
                {screenshot_html}
            </div>
            '''
        return html

    def _format_improvements_html(self) -> str:
        if not self.improvements:
            return '<p style="color: #6b7280;">No improvements suggested.</p>'

        html = ''
        for imp in self.improvements:
            html += f'''
            <div class="improvement-card">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                    <span class="badge {imp.severity}">{imp.severity}</span>
                    <span style="color: #6b7280; font-size: 14px;">{imp.type}</span>
                </div>
                <p style="font-size: 16px; font-weight: 500; margin-bottom: 5px;">{imp.issue}</p>
                <p style="color: #059669; margin-bottom: 5px;">💡 Suggestion: {imp.suggestion}</p>
                {f'<p style="color: #6b7280; font-size: 14px;">Impact: {imp.business_impact}</p>' if imp.business_impact else ''}
            </div>
            '''
        return html

    def _format_results_html(self) -> str:
        if not self.results:
            return '<p>No tests run.</p>'

        html = '<table><thead><tr><th>Test Name</th><th>Status</th><th>Duration</th><th>Details</th></tr></thead><tbody>'

        for result in self.results:
            status_class = f'status-{result.status}'
            details = result.details if result.details else {}
            details_str = ', '.join([f'{k}: {v}' for k, v in details.items()]) if details else '-'

            html += f'''
            <tr>
                <td>{result.test_name}</td>
                <td class="{status_class}">{result.status.upper()}</td>
                <td>{result.duration:.2f}s</td>
                <td>{details_str}</td>
            </tr>
            '''

        html += '</tbody></table>'
        return html


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    import sys

    headless = '--headless' in sys.argv
    base_url = "http://localhost:5174"

    # Check if custom URL provided
    for arg in sys.argv:
        if arg.startswith('--url='):
            base_url = arg.split('=')[1]

    simulator = HumanSimulator(base_url=base_url, headless=headless)
    asyncio.run(simulator.run_complete_simulation())
