
import os
import requests
from loguru import logger

def send_discord_webhook(feedback_text: str):
    """
    Sends a feedback message to a Discord webhook.

    Args:
        feedback_text: The text of the feedback from the user.
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("DISCORD_WEBHOOK_URL is not set. Skipping feedback notification.")
        return

    try:
        payload = {
            "embeds": [
                {
                    "title": "New Bot Feedback Received! [START]",
                    "description": feedback_text,
                    "color": 5814783, # Hex color #58b9ff
                    "footer": {
                        "text": f"VintedBot Feedback System"
                    }
                }
            ]
        }
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Successfully sent feedback to Discord.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send feedback to Discord: {e}")

