"""
Main monitoring script
Runs monitoring tests and sends notifications
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.monitoring.vinted_monitor import run_monitoring
from backend.monitoring.telegram_notifier import TelegramNotifier
from loguru import logger


async def main():
    """Main monitoring function"""
    logger.info("[START] Starting Vinted platform monitoring...")

    # Get credentials from environment
    cookie = os.getenv("VINTED_COOKIE")
    user_agent = os.getenv("VINTED_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    if not cookie:
        logger.error("[ERROR] VINTED_COOKIE environment variable required")
        sys.exit(1)

    # Run monitoring
    try:
        results = await run_monitoring(cookie, user_agent)

        # Send notification
        notifier = TelegramNotifier()

        if results["status"] == "healthy":
            logger.info("[OK] All tests passed - No changes detected")
            # Only send notification if you want daily "all good" messages
            # notifier.send_custom_alert("Vinted Bot Status", "Tous les tests sont passés [OK]", "info")

        elif results["status"] == "warning":
            logger.warning("[WARN] Minor issues detected")
            notifier.send_monitoring_alert(results)

        elif results["status"] == "critical":
            logger.error("🚨 CRITICAL issues detected!")
            notifier.send_monitoring_alert(results)

            # Exit with error code (useful for CI/CD)
            sys.exit(1)

        else:
            logger.error("[ERROR] Monitoring failed")
            notifier.send_custom_alert(
                "Vinted Bot Monitor Error",
                f"Le monitoring a échoué avec le statut: {results['status']}",
                "critical"
            )
            sys.exit(1)

    except Exception as e:
        logger.error(f"[ERROR] Monitoring exception: {e}")

        # Send error notification
        notifier = TelegramNotifier()
        notifier.send_custom_alert(
            "Vinted Bot Monitor Exception",
            f"Une erreur est survenue:\n<code>{str(e)}</code>",
            "critical"
        )
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
