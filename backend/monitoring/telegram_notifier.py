"""
Telegram Notifier
Envoie des notifications Telegram quand des changements sont détectés sur Vinted
"""
import os
import json
from typing import Dict, Any, Optional
import requests
from loguru import logger


class TelegramNotifier:
    """Send Telegram notifications"""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

        if not self.bot_token or not self.chat_id:
            logger.warning("[WARN] Telegram credentials not configured")

    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message to Telegram

        Args:
            message: Message text (supports HTML or Markdown)
            parse_mode: "HTML" or "Markdown"

        Returns:
            True if sent successfully
        """
        if not self.bot_token or not self.chat_id:
            logger.error("[ERROR] Telegram not configured")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info("[OK] Telegram notification sent")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Failed to send Telegram notification: {e}")
            return False

    def send_photo(self, photo_path: str, caption: str = "") -> bool:
        """
        Send a photo to Telegram

        Args:
            photo_path: Filesystem path to the photo
            caption: Text to send with the photo

        Returns:
            True if sent successfully
        """
        if not self.bot_token or not self.chat_id:
            logger.error("[ERROR] Telegram not configured")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
            with open(photo_path, "rb") as photo_file:
                payload = {"chat_id": self.chat_id, "caption": caption}
                files = {"photo": photo_file}
                
                response = requests.post(url, data=payload, files=files, timeout=30)
                response.raise_for_status()

            logger.info("[OK] Telegram photo sent")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Failed to send Telegram photo: {e}")
            return False

    def send_monitoring_alert(self, results: Dict[str, Any]) -> bool:
        """
        Send monitoring alert to Telegram

        Args:
            results: Monitoring results dictionary

        Returns:
            True if sent successfully
        """
        status = results.get("status", "unknown")
        changes = results.get("changes_detected", [])
        failed_tests = [t for t in results.get("tests", []) if t["status"] == "failed"]

        # Build message
        if status == "critical":
            emoji = "🚨"
            title = "ALERTE CRITIQUE - Vinted Bot"
        elif status == "warning":
            emoji = "[WARN]"
            title = "AVERTISSEMENT - Vinted Bot"
        else:
            emoji = "[OK]"
            title = "Vinted Bot - Tout fonctionne"

        message = f"{emoji} <b>{title}</b>\n\n"
        message += f"📅 <b>Date:</b> {results.get('timestamp', 'N/A')}\n"
        message += f"📊 <b>Status:</b> {status.upper()}\n\n"

        if changes:
            message += f"<b>[SEARCH] Changements détectés ({len(changes)}):</b>\n"
            for i, change in enumerate(changes[:5], 1):  # Limit to 5 changes
                severity = change.get("severity", "unknown")
                msg = change.get("message", "Unknown")
                message += f"{i}. [{severity.upper()}] {msg}\n"

            if len(changes) > 5:
                message += f"\n... et {len(changes) - 5} autres changements\n"

        if failed_tests:
            message += f"\n<b>[ERROR] Tests échoués ({len(failed_tests)}):</b>\n"
            for test in failed_tests[:3]:  # Limit to 3 tests
                test_name = test.get("name", "unknown")
                error = test.get("error", test.get("message", "Unknown error"))
                message += f"• {test_name}: {error}\n"

        # Add action items
        if status == "critical":
            message += "\n<b>🔧 Actions requises:</b>\n"
            message += "1. Vérifier les changements détectés\n"
            message += "2. Mettre à jour les sélecteurs si nécessaire\n"
            message += "3. Tester manuellement le bot\n"
        elif status == "warning":
            message += "\n<b>💡 Recommandations:</b>\n"
            message += "• Vérifier les changements non-critiques\n"
            message += "• Surveiller les prochains rapports\n"

        # Add view details link (if you have a dashboard)
        # message += f"\n<a href='https://your-dashboard.com/monitoring'>📊 Voir les détails</a>"

        return self.send_message(message)

    def send_custom_alert(
        self,
        title: str,
        message: str,
        severity: str = "info"
    ) -> bool:
        """
        Send custom alert

        Args:
            title: Alert title
            message: Alert message
            severity: "critical", "warning", or "info"

        Returns:
            True if sent successfully
        """
        emoji_map = {
            "critical": "🚨",
            "warning": "[WARN]",
            "info": "[INFO]"
        }

        emoji = emoji_map.get(severity, "📢")
        full_message = f"{emoji} <b>{title}</b>\n\n{message}"

        return self.send_message(full_message)

    def test_connection(self) -> bool:
        """
        Test Telegram connection

        Returns:
            True if connection successful
        """
        return self.send_custom_alert(
            "Test Connection",
            "Telegram notifications are working! 🎉",
            "info"
        )


def send_monitoring_notification(results: Dict[str, Any]) -> bool:
    """
    Helper function to send monitoring notification

    Args:
        results: Monitoring results

    Returns:
        True if sent successfully
    """
    notifier = TelegramNotifier()
    return notifier.send_monitoring_alert(results)


if __name__ == "__main__":
    # Test notification
    notifier = TelegramNotifier()

    if notifier.test_connection():
        print("[OK] Telegram connection successful!")

        # Test with sample monitoring data
        sample_results = {
            "timestamp": "2025-01-15T08:00:00",
            "status": "warning",
            "tests": [
                {"name": "form_selectors", "status": "passed"},
                {"name": "button_selectors", "status": "failed", "error": "Publish button not found"}
            ],
            "changes_detected": [
                {
                    "test": "button_selectors",
                    "message": "Button selector missing: publish",
                    "severity": "high"
                }
            ]
        }

        notifier.send_monitoring_alert(sample_results)
    else:
        print("[ERROR] Telegram connection failed. Check your credentials.")
