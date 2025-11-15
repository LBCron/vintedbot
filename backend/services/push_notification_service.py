"""
Push Notification Service - Web Push Notifications for VintedBot

Sends push notifications to users for important events:
- Article sold
- New messages
- Publishing scheduled
- Price changes
"""

import os
import json
import logging
from typing import Dict, Optional
from datetime import datetime

try:
    from pywebpush import webpush, WebPushException
    WEBPUSH_AVAILABLE = True
except ImportError:
    WEBPUSH_AVAILABLE = False
    logging.warning("pywebpush not installed - push notifications disabled")

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Service for sending web push notifications"""

    def __init__(self):
        self.vapid_private_key = os.getenv("VAPID_PRIVATE_KEY")
        self.vapid_public_key = os.getenv("VAPID_PUBLIC_KEY")
        self.vapid_claims = {
            "sub": os.getenv("VAPID_EMAIL", "mailto:admin@vintedbot.com")
        }

        if not WEBPUSH_AVAILABLE:
            logger.warning("Push notifications disabled - pywebpush not available")
        elif not self.vapid_private_key or not self.vapid_public_key:
            logger.warning("Push notifications disabled - VAPID keys not configured")

    async def send_notification(
        self,
        subscription_info: Dict,
        title: str,
        message: str,
        url: str = "/",
        icon: str = "/logo192.png",
        badge: str = "/logo72.png"
    ) -> bool:
        """
        Send push notification to a user

        Args:
            subscription_info: Push subscription object from browser
            title: Notification title
            message: Notification message
            url: URL to open when clicked
            icon: Notification icon
            badge: Notification badge

        Returns:
            True if sent successfully, False otherwise
        """

        if not WEBPUSH_AVAILABLE:
            logger.debug(f"Push notification skipped (webpush unavailable): {title}")
            return False

        if not self.vapid_private_key or not self.vapid_public_key:
            logger.debug(f"Push notification skipped (no VAPID keys): {title}")
            return False

        try:
            payload = json.dumps({
                "title": title,
                "message": message,
                "url": url,
                "icon": icon,
                "badge": badge,
                "timestamp": datetime.utcnow().isoformat()
            })

            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims,
                ttl=86400  # 24 hours
            )

            logger.info(f"Push notification sent: {title}")
            return True

        except WebPushException as e:
            logger.error(f"Push notification failed: {e}")

            # If subscription is expired (410), we should remove it
            if e.response and e.response.status_code == 410:
                logger.info("Push subscription expired - should be removed")

            return False

        except Exception as e:
            logger.error(f"Push notification error: {e}")
            return False

    async def notify_article_sold(
        self,
        subscription_info: Dict,
        article_title: str,
        price: float,
        buyer_name: str = "Un acheteur"
    ) -> bool:
        """Notify user when article is sold"""

        return await self.send_notification(
            subscription_info=subscription_info,
            title="🎉 Article vendu !",
            message=f"{article_title} vendu pour {price}€ à {buyer_name}",
            url="/orders",
            icon="/logo192.png"
        )

    async def notify_new_message(
        self,
        subscription_info: Dict,
        buyer_name: str,
        article_title: str,
        message_preview: str = ""
    ) -> bool:
        """Notify user of new message"""

        message = f"{buyer_name} vous a envoyé un message"
        if article_title:
            message += f" concernant '{article_title}'"

        if message_preview:
            message += f": {message_preview[:50]}..."

        return await self.send_notification(
            subscription_info=subscription_info,
            title="💬 Nouveau message",
            message=message,
            url="/messages"
        )

    async def notify_publication_scheduled(
        self,
        subscription_info: Dict,
        article_title: str,
        scheduled_time: datetime
    ) -> bool:
        """Notify user when publication is scheduled"""

        return await self.send_notification(
            subscription_info=subscription_info,
            title="📅 Publication programmée",
            message=f"'{article_title}' sera publié le {scheduled_time.strftime('%d/%m à %H:%M')}",
            url="/scheduling"
        )

    async def notify_publication_complete(
        self,
        subscription_info: Dict,
        article_title: str
    ) -> bool:
        """Notify user when scheduled publication completes"""

        return await self.send_notification(
            subscription_info=subscription_info,
            title="✅ Article publié !",
            message=f"'{article_title}' a été publié sur Vinted",
            url="/drafts"
        )

    async def notify_price_suggestion(
        self,
        subscription_info: Dict,
        article_title: str,
        current_price: float,
        suggested_price: float,
        potential_increase: float
    ) -> bool:
        """Notify user of better price suggestion"""

        percentage = (potential_increase / current_price) * 100

        return await self.send_notification(
            subscription_info=subscription_info,
            title="💰 Optimisation de prix",
            message=f"'{article_title}': {suggested_price}€ (+{percentage:.0f}%) recommandé",
            url="/price-optimizer"
        )

    async def notify_ai_message_generated(
        self,
        subscription_info: Dict,
        buyer_name: str
    ) -> bool:
        """Notify user that AI generated a response"""

        return await self.send_notification(
            subscription_info=subscription_info,
            title="🤖 Réponse IA générée",
            message=f"Réponse automatique envoyée à {buyer_name}",
            url="/messages"
        )

    async def notify_error(
        self,
        subscription_info: Dict,
        error_title: str,
        error_message: str
    ) -> bool:
        """Notify user of an error"""

        return await self.send_notification(
            subscription_info=subscription_info,
            title=f"⚠️ {error_title}",
            message=error_message,
            url="/settings"
        )


# Global instance
push_service = PushNotificationService()
