"""
Test script to validate monitoring setup
Vérifie que tout est correctement configuré
"""
import os
import sys
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

def print_status(check_name: str, passed: bool, message: str = ""):
    """Print colored status"""
    if passed:
        print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} {check_name}")
        if message:
            print(f"  {Fore.CYAN}{message}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗{Style.RESET_ALL} {check_name}")
        if message:
            print(f"  {Fore.YELLOW}{message}{Style.RESET_ALL}")

def main():
    """Run setup validation"""
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[SEARCH] Vinted Monitoring - Setup Validation{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

    all_passed = True

    # Check 1: Python version
    print(f"{Fore.BLUE}1. Checking Python version...{Style.RESET_ALL}")
    python_version = sys.version_info
    if python_version >= (3, 9):
        print_status("Python version", True, f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print_status("Python version", False, f"Python 3.9+ required (found {python_version.major}.{python_version.minor})")
        all_passed = False

    # Check 2: Required modules
    print(f"\n{Fore.BLUE}2. Checking required modules...{Style.RESET_ALL}")

    required_modules = [
        ("playwright", "playwright"),
        ("loguru", "loguru"),
        ("anthropic", "anthropic"),
        ("requests", "requests"),
        ("dotenv", "python-dotenv")
    ]

    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
            print_status(f"{package_name}", True)
        except ImportError:
            print_status(f"{package_name}", False, f"Install with: pip install {package_name}")
            all_passed = False

    # Check 3: Playwright browsers
    print(f"\n{Fore.BLUE}3. Checking Playwright browsers...{Style.RESET_ALL}")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                print_status("Chromium browser", True)
            except Exception as e:
                print_status("Chromium browser", False, "Install with: playwright install chromium")
                all_passed = False
    except Exception as e:
        print_status("Playwright", False, str(e))
        all_passed = False

    # Check 4: Environment variables
    print(f"\n{Fore.BLUE}4. Checking environment variables...{Style.RESET_ALL}")

    # Try to load .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass

    # Check VINTED_COOKIE (required)
    cookie = os.getenv("VINTED_COOKIE")
    if cookie and len(cookie) > 50:
        print_status("VINTED_COOKIE", True, "Configured")
    else:
        print_status("VINTED_COOKIE", False, "Required - Get from browser DevTools")
        all_passed = False

    # Check TELEGRAM (optional)
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat = os.getenv("TELEGRAM_CHAT_ID")
    if telegram_token and telegram_chat:
        print_status("Telegram", True, "Bot token and chat ID configured")
    else:
        print_status("Telegram", False, "Optional - Configure for notifications")

    # Check ANTHROPIC_API_KEY (optional)
    claude_key = os.getenv("ANTHROPIC_API_KEY")
    if claude_key:
        print_status("Claude API", True, "API key configured")
    else:
        print_status("Claude API", False, "Optional - Configure for auto-fix suggestions")

    # Check 5: Directory structure
    print(f"\n{Fore.BLUE}5. Checking directory structure...{Style.RESET_ALL}")

    base_dir = Path("backend/monitoring")
    required_files = [
        "vinted_monitor.py",
        "telegram_notifier.py",
        "claude_auto_fix.py",
        "orchestrator.py",
        "run_monitor.py",
        "README.md"
    ]

    for filename in required_files:
        filepath = base_dir / filename
        if filepath.exists():
            print_status(filename, True)
        else:
            print_status(filename, False, f"File not found: {filepath}")
            all_passed = False

    # Check snapshots directory
    snapshot_dir = Path("backend/monitoring/snapshots")
    if not snapshot_dir.exists():
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        print_status("snapshots/", True, "Created")
    else:
        print_status("snapshots/", True, "Exists")

    # Check analyses directory
    analyses_dir = Path("backend/monitoring/analyses")
    if not analyses_dir.exists():
        analyses_dir.mkdir(parents=True, exist_ok=True)
        print_status("analyses/", True, "Created")
    else:
        print_status("analyses/", True, "Exists")

    # Check 6: GitHub Actions workflow
    print(f"\n{Fore.BLUE}6. Checking GitHub Actions workflow...{Style.RESET_ALL}")
    workflow_file = Path(".github/workflows/vinted-monitor.yml")
    if workflow_file.exists():
        print_status("vinted-monitor.yml", True, "Workflow configured")
    else:
        print_status("vinted-monitor.yml", False, "Workflow file not found")
        all_passed = False

    # Summary
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    if all_passed:
        print(f"{Fore.GREEN}[OK] All checks passed!{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}Next steps:{Style.RESET_ALL}")
        print(f"  1. Test monitoring: {Fore.WHITE}python backend/monitoring/run_monitor.py{Style.RESET_ALL}")
        print(f"  2. Test Telegram: {Fore.WHITE}python backend/monitoring/telegram_notifier.py{Style.RESET_ALL}")
        print(f"  3. Configure GitHub Secrets for automatic monitoring")
        return 0
    else:
        print(f"{Fore.RED}✗ Some checks failed{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Please fix the issues above before proceeding{Style.RESET_ALL}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        sys.exit(1)
