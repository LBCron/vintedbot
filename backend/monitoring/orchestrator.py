"""
Monitoring Orchestrator
Orchestre le monitoring, les notifications et l'auto-correction
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.monitoring.vinted_monitor import run_monitoring
from backend.monitoring.telegram_notifier import TelegramNotifier
from backend.monitoring.claude_auto_fix import ClaudeAutoFix
from loguru import logger


class MonitoringOrchestrator:
    """Orchestrate monitoring workflow"""

    def __init__(
        self,
        cookie: str,
        user_agent: str,
        enable_auto_fix: bool = False,
        enable_telegram: bool = True
    ):
        self.cookie = cookie
        self.user_agent = user_agent
        self.enable_auto_fix = enable_auto_fix
        self.enable_telegram = enable_telegram

        self.notifier = TelegramNotifier() if enable_telegram else None
        self.auto_fix = ClaudeAutoFix() if enable_auto_fix else None

    async def run(self) -> int:
        """
        Run complete monitoring workflow

        Returns:
            Exit code (0 = success, 1 = failure)
        """
        logger.info("[START] Starting Vinted Monitoring Orchestrator...")

        try:
            # Step 1: Run monitoring tests
            logger.info("📊 Step 1: Running monitoring tests...")
            results = await run_monitoring(self.cookie, self.user_agent)

            status = results.get("status", "unknown")
            logger.info(f"Monitoring status: {status}")

            # Step 2: Send Telegram notification if enabled
            if self.enable_telegram and self.notifier:
                logger.info("📱 Step 2: Sending Telegram notification...")

                if status in ["warning", "critical"]:
                    self.notifier.send_monitoring_alert(results)
                elif status == "healthy":
                    # Only send "all good" message if you want daily confirmations
                    pass

            # Step 3: Claude auto-analysis if critical and enabled
            if self.enable_auto_fix and self.auto_fix and status == "critical":
                logger.info("🤖 Step 3: Running Claude auto-analysis...")

                try:
                    analysis = self.auto_fix.analyze_monitoring_results(results)

                    if analysis:
                        logger.info("[OK] Claude analysis complete")

                        # Send analysis via Telegram
                        if self.notifier:
                            self._send_analysis_notification(analysis)

                        # Note: Auto-applying fixes is disabled by default for safety
                        # You can enable it by implementing auto_fix.generate_fix_pr()
                        logger.info("💡 Review Claude's suggestions in: backend/monitoring/analyses/")

                except Exception as e:
                    logger.error(f"[ERROR] Claude analysis failed: {e}")
                    if self.notifier:
                        self.notifier.send_custom_alert(
                            "Claude Analysis Error",
                            f"L'analyse Claude a échoué:\n<code>{str(e)}</code>",
                            "warning"
                        )

            # Step 4: Determine exit code
            if status == "healthy":
                logger.info("[OK] All systems operational")
                return 0
            elif status == "warning":
                logger.warning("[WARN] Minor issues detected - review recommended")
                return 0  # Don't fail CI for warnings
            elif status == "critical":
                logger.error("🚨 Critical issues detected - immediate action required")
                return 1  # Fail CI for critical issues
            else:
                logger.error("[ERROR] Monitoring failed")
                return 1

        except Exception as e:
            logger.error(f"[ERROR] Orchestrator exception: {e}")

            if self.notifier:
                self.notifier.send_custom_alert(
                    "Monitoring System Error",
                    f"Le système de monitoring a rencontré une erreur:\n<code>{str(e)}</code>",
                    "critical"
                )

            return 1

    def _send_analysis_notification(self, analysis: dict):
        """Send Claude analysis via Telegram"""
        if not self.notifier:
            return

        suggestions = analysis.get("suggestions", {})
        severity = suggestions.get("severity", "unknown")
        analysis_text = suggestions.get("analysis", "No analysis available")
        fixes = suggestions.get("fixes", [])

        message = f"🤖 <b>Analyse Claude - Auto-Fix</b>\n\n"
        message += f"<b>Sévérité:</b> {severity.upper()}\n\n"

        # Add analysis summary
        message += f"<b>Analyse:</b>\n{analysis_text[:500]}"  # Limit to 500 chars
        if len(analysis_text) > 500:
            message += "...\n"

        # Add fixes count
        if fixes:
            message += f"\n\n<b>🔧 Corrections suggérées:</b> {len(fixes)}\n"
            for i, fix in enumerate(fixes[:3], 1):  # Show first 3 fixes
                message += f"{i}. {fix.get('function', 'N/A')}: {fix.get('issue', 'N/A')[:100]}\n"

        message += f"\n📁 Détails complets dans: <code>backend/monitoring/analyses/</code>"

        self.notifier.send_message(message)


async def main():
    """Main entry point"""
    # Get configuration
    cookie = os.getenv("VINTED_COOKIE")
    user_agent = os.getenv("VINTED_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    enable_auto_fix = os.getenv("ENABLE_CLAUDE_AUTO_FIX", "false").lower() == "true"
    enable_telegram = os.getenv("ENABLE_TELEGRAM", "true").lower() == "true"

    if not cookie:
        logger.error("[ERROR] VINTED_COOKIE environment variable required")
        sys.exit(1)

    # Run orchestrator
    orchestrator = MonitoringOrchestrator(
        cookie=cookie,
        user_agent=user_agent,
        enable_auto_fix=enable_auto_fix,
        enable_telegram=enable_telegram
    )

    exit_code = await orchestrator.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
