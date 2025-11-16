"""
Webhook Service
Sends events to external services (Zapier, Make, custom webhooks)
"""
import httpx
import json
from typing import Dict, List, Optional
from loguru import logger
from datetime import datetime


class WebhookService:
    """
    Service for sending webhook events to external services

    Supported events:
    - listing.created
    - listing.sold
    - message.received
    - account.connected
    - automation.completed
    """

    def __init__(self):
        self.timeout = httpx.Timeout(10.0)
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def send_webhook(
        self,
        url: str,
        event: str,
        data: Dict,
        headers: Optional[Dict] = None
    ) -> bool:
        """
        Send webhook to external URL

        Args:
            url: Webhook URL
            event: Event type (e.g., "listing.created")
            data: Event data
            headers: Optional custom headers

        Returns:
            True if successful
        """
        if not url:
            return False

        payload = {
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        request_headers = {
            "Content-Type": "application/json",
            "User-Agent": "VintedBot-Webhook/1.0"
        }

        if headers:
            request_headers.update(headers)

        try:
            response = await self.client.post(
                url,
                json=payload,
                headers=request_headers
            )

            if response.status_code in [200, 201, 202, 204]:
                logger.info(f"✅ Webhook sent: {event} to {url}")
                return True
            else:
                logger.warning(f"⚠️ Webhook failed: {event} to {url} - Status {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Webhook error: {event} to {url} - {e}")
            return False

    async def send_user_webhooks(
        self,
        user_id: str,
        event: str,
        data: Dict
    ) -> int:
        """
        Send webhooks to all registered URLs for a user

        Args:
            user_id: User ID
            event: Event type
            data: Event data

        Returns:
            Number of successful webhooks
        """
        from backend.core.database import get_db_pool

        try:
            pool = await get_db_pool()

            async with pool.acquire() as conn:
                # Get all active webhooks for user
                webhooks = await conn.fetch("""
                    SELECT id, url, events, headers, secret
                    FROM webhooks
                    WHERE user_id = $1 AND active = true
                """, user_id)

                if not webhooks:
                    return 0

                successful = 0

                for webhook in webhooks:
                    # Check if webhook is subscribed to this event
                    subscribed_events = webhook.get('events', [])
                    if subscribed_events and event not in subscribed_events:
                        continue

                    url = webhook.get('url')
                    headers = webhook.get('headers', {})
                    secret = webhook.get('secret')

                    # Add signature header if secret is set
                    if secret:
                        import hmac
                        import hashlib

                        # Create signature
                        payload_str = json.dumps(data)
                        signature = hmac.new(
                            secret.encode(),
                            payload_str.encode(),
                            hashlib.sha256
                        ).hexdigest()

                        headers['X-VintedBot-Signature'] = signature

                    # Send webhook
                    success = await self.send_webhook(
                        url=url,
                        event=event,
                        data=data,
                        headers=headers
                    )

                    if success:
                        successful += 1

                        # Update webhook stats
                        await conn.execute("""
                            UPDATE webhooks
                            SET last_triggered = NOW(),
                                total_calls = total_calls + 1,
                                successful_calls = successful_calls + 1
                            WHERE id = $1
                        """, webhook.get('id'))
                    else:
                        # Update failed count
                        await conn.execute("""
                            UPDATE webhooks
                            SET last_triggered = NOW(),
                                total_calls = total_calls + 1,
                                failed_calls = failed_calls + 1
                            WHERE id = $1
                        """, webhook.get('id'))

                logger.info(f"📨 Sent {successful}/{len(webhooks)} webhooks for event: {event}")
                return successful

        except Exception as e:
            logger.error(f"❌ Error sending user webhooks: {e}")
            return 0

    async def register_webhook(
        self,
        user_id: str,
        url: str,
        events: Optional[List[str]] = None,
        secret: Optional[str] = None,
        headers: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Register a new webhook for a user

        Args:
            user_id: User ID
            url: Webhook URL
            events: List of events to subscribe to (None = all events)
            secret: Optional secret for signature verification
            headers: Optional custom headers

        Returns:
            Webhook ID or None if failed
        """
        from backend.core.database import get_db_pool
        import uuid

        try:
            pool = await get_db_pool()

            webhook_id = str(uuid.uuid4())

            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO webhooks
                    (id, user_id, url, events, secret, headers, active, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, true, NOW())
                """,
                    webhook_id,
                    user_id,
                    url,
                    events,
                    secret,
                    json.dumps(headers) if headers else None
                )

            logger.info(f"✅ Registered webhook: {webhook_id} for user {user_id}")
            return webhook_id

        except Exception as e:
            logger.error(f"❌ Failed to register webhook: {e}")
            return None

    async def delete_webhook(
        self,
        webhook_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a webhook

        Args:
            webhook_id: Webhook ID
            user_id: User ID (for verification)

        Returns:
            True if successful
        """
        from backend.core.database import get_db_pool

        try:
            pool = await get_db_pool()

            async with pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM webhooks
                    WHERE id = $1 AND user_id = $2
                """, webhook_id, user_id)

                if result == "DELETE 1":
                    logger.info(f"✅ Deleted webhook: {webhook_id}")
                    return True
                else:
                    return False

        except Exception as e:
            logger.error(f"❌ Failed to delete webhook: {e}")
            return False

    async def get_user_webhooks(self, user_id: str) -> List[Dict]:
        """
        Get all webhooks for a user

        Args:
            user_id: User ID

        Returns:
            List of webhooks
        """
        from backend.core.database import get_db_pool

        try:
            pool = await get_db_pool()

            async with pool.acquire() as conn:
                webhooks = await conn.fetch("""
                    SELECT id, url, events, active, created_at,
                           last_triggered, total_calls, successful_calls, failed_calls
                    FROM webhooks
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                """, user_id)

                return [dict(webhook) for webhook in webhooks]

        except Exception as e:
            logger.error(f"❌ Failed to get user webhooks: {e}")
            return []

    async def test_webhook(
        self,
        url: str,
        headers: Optional[Dict] = None
    ) -> Dict:
        """
        Test a webhook URL

        Args:
            url: Webhook URL
            headers: Optional custom headers

        Returns:
            Test result
        """
        test_data = {
            "test": True,
            "message": "This is a test webhook from VintedBot"
        }

        success = await self.send_webhook(
            url=url,
            event="webhook.test",
            data=test_data,
            headers=headers
        )

        return {
            "success": success,
            "url": url,
            "message": "Test webhook sent successfully" if success else "Test webhook failed"
        }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Event helper functions
async def trigger_listing_created(user_id: str, listing_data: Dict):
    """Trigger listing.created webhook"""
    service = WebhookService()
    await service.send_user_webhooks(
        user_id=user_id,
        event="listing.created",
        data=listing_data
    )
    await service.close()


async def trigger_listing_sold(user_id: str, listing_data: Dict):
    """Trigger listing.sold webhook"""
    service = WebhookService()
    await service.send_user_webhooks(
        user_id=user_id,
        event="listing.sold",
        data=listing_data
    )
    await service.close()


async def trigger_message_received(user_id: str, message_data: Dict):
    """Trigger message.received webhook"""
    service = WebhookService()
    await service.send_user_webhooks(
        user_id=user_id,
        event="message.received",
        data=message_data
    )
    await service.close()


async def trigger_automation_completed(user_id: str, automation_data: Dict):
    """Trigger automation.completed webhook"""
    service = WebhookService()
    await service.send_user_webhooks(
        user_id=user_id,
        event="automation.completed",
        data=automation_data
    )
    await service.close()


# Global instance
webhook_service = WebhookService()
