"""
Webhook Service
Sends events to external services (Zapier, Make, custom webhooks)

SECURITY: SSRF protection implemented to prevent attacks on internal services
"""
import httpx
import hashlib
import hmac
import json
import ipaddress
from urllib.parse import urlparse
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
    - subscription.updated

    SECURITY FEATURES:
    - ✅ SSRF protection (blocks private IPs, localhost, metadata endpoints)
    - ✅ HMAC signature for webhook verification
    - ✅ Timeout protection (5s max)
    - ✅ Request size limits
    - ✅ Retry logic with exponential backoff
    """

    # SECURITY: Blocked domains and IP ranges (SSRF protection)
    BLOCKED_DOMAINS = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "169.254.169.254",  # AWS metadata
        "metadata.google.internal",  # GCP metadata
        "metadata",
        "::1",  # IPv6 localhost
    ]

    BLOCKED_IP_RANGES = [
        ipaddress.ip_network("10.0.0.0/8"),      # Private
        ipaddress.ip_network("172.16.0.0/12"),   # Private
        ipaddress.ip_network("192.168.0.0/16"),  # Private
        ipaddress.ip_network("127.0.0.0/8"),     # Loopback
        ipaddress.ip_network("169.254.0.0/16"),  # Link-local (AWS metadata)
        ipaddress.ip_network("::1/128"),         # IPv6 loopback
        ipaddress.ip_network("fc00::/7"),        # IPv6 private
    ]


    @staticmethod
    async def validate_webhook_url(url: str) -> bool:
        """
        Validate webhook URL to prevent SSRF attacks

        SECURITY: Critical protection against internal service attacks
        """
        try:
            parsed = urlparse(url)

            # Must be HTTP or HTTPS
            if parsed.scheme not in ["http", "https"]:
                logger.warning(f"🔒 SSRF: Invalid scheme {parsed.scheme}")
                return False

            # SECURITY: Block localhost and internal domains
            hostname = parsed.hostname
            if not hostname:
                return False

            hostname_lower = hostname.lower()
            for blocked in WebhookService.BLOCKED_DOMAINS:
                if blocked in hostname_lower:
                    logger.warning(f"🔒 SSRF: Blocked domain {hostname}")
                    return False

            # SECURITY: Resolve IP and check against private ranges
            try:
                # Note: In production, use async DNS resolution
                import socket
                ip_str = socket.gethostbyname(hostname)
                ip = ipaddress.ip_address(ip_str)

                for blocked_range in WebhookService.BLOCKED_IP_RANGES:
                    if ip in blocked_range:
                        logger.warning(f"🔒 SSRF: Blocked IP {ip} in range {blocked_range}")
                        return False

            except (socket.gaierror, ValueError) as e:
                logger.error(f"DNS resolution failed for {hostname}: {e}")
                return False

            # SECURITY: Require HTTPS for production webhooks (recommended)
            # if parsed.scheme != "https":
            #     logger.warning(f"⚠️ Webhook uses HTTP (not HTTPS): {url}")

            return True

        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False


    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        """
        Generate HMAC signature for webhook verification
        """
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()


    @staticmethod
    async def send_webhook(
        url: str,
        event_type: str,
        data: Dict,
        secret: Optional[str] = None,
        retry_count: int = 3
    ) -> bool:
        """
        Send webhook to external URL with security protections

        Returns True if webhook was delivered successfully
        """
        # SECURITY FIX: Validate URL to prevent SSRF
        if not await WebhookService.validate_webhook_url(url):
            logger.error(f"🔒 SSRF protection: Blocked webhook to {url}")
            return False

        payload = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0"
        }

        payload_str = json.dumps(payload)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "VintedBot-Webhook/1.0"
        }

        # Add signature if secret provided
        if secret:
            signature = WebhookService.generate_signature(payload_str, secret)
            headers["X-Webhook-Signature"] = signature
            headers["X-Webhook-Signature-Algorithm"] = "sha256"

        # SECURITY: Timeout protection (5 seconds max)
        timeout = httpx.Timeout(5.0, connect=2.0)

        # SECURITY: Size limit (1MB max payload)
        if len(payload_str) > 1024 * 1024:
            logger.error("Webhook payload too large (>1MB)")
            return False

        # Retry logic with exponential backoff
        for attempt in range(retry_count):
            try:
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
                    response = await client.post(
                        url,
                        content=payload_str,
                        headers=headers
                    )

                    if response.status_code in [200, 201, 202, 204]:
                        logger.info(f"✅ Webhook delivered: {event_type} to {url}")
                        return True
                    else:
                        logger.warning(f"Webhook failed: {response.status_code} from {url}")

            except httpx.TimeoutException:
                logger.warning(f"Webhook timeout (attempt {attempt + 1}/{retry_count}): {url}")

            except httpx.RequestError as e:
                logger.error(f"Webhook request error: {e}")

            except Exception as e:
                logger.error(f"Unexpected webhook error: {e}")

            # Wait before retry (exponential backoff: 1s, 2s, 4s)
            if attempt < retry_count - 1:
                await httpx.AsyncClient().aclose()  # Cleanup
                import asyncio
                await asyncio.sleep(2 ** attempt)

        logger.error(f"❌ Webhook failed after {retry_count} attempts: {url}")
        return False


    @staticmethod
    async def trigger_event(
        event_type: str,
        data: Dict,
        user_id: int,
        db_pool
    ) -> Dict:
        """
        Trigger webhook event for all registered webhooks of a user

        Returns statistics about webhook deliveries
        """
        async with db_pool.acquire() as conn:
            # Get all active webhooks for this user and event type
            rows = await conn.fetch("""
                SELECT id, url, secret, events
                FROM webhooks
                WHERE user_id = $1
                AND is_active = true
                AND $2 = ANY(events)
            """, user_id, event_type)

            if not rows:
                logger.debug(f"No webhooks registered for event {event_type}")
                return {"delivered": 0, "failed": 0}

            delivered = 0
            failed = 0

            for row in rows:
                webhook_id = row["id"]
                url = row["url"]
                secret = row["secret"]

                success = await WebhookService.send_webhook(
                    url=url,
                    event_type=event_type,
                    data=data,
                    secret=secret
                )

                if success:
                    delivered += 1
                    # Update last_triggered_at
                    await conn.execute("""
                        UPDATE webhooks
                        SET last_triggered_at = NOW(),
                            delivery_count = delivery_count + 1
                        WHERE id = $1
                    """, webhook_id)
                else:
                    failed += 1
                    # Update failure count
                    await conn.execute("""
                        UPDATE webhooks
                        SET failure_count = failure_count + 1
                        WHERE id = $1
                    """, webhook_id)

            logger.info(f"📤 Webhook event {event_type}: {delivered} delivered, {failed} failed")

            return {
                "event": event_type,
                "delivered": delivered,
                "failed": failed,
                "total": len(rows)
            }


    @staticmethod
    async def test_webhook(url: str, secret: Optional[str] = None) -> Dict:
        """
        Test a webhook URL before saving it

        Returns success status and response time
        """
        start_time = datetime.utcnow()

        success = await WebhookService.send_webhook(
            url=url,
            event_type="webhook.test",
            data={"message": "This is a test webhook from VintedBot"},
            secret=secret,
            retry_count=1
        )

        response_time = (datetime.utcnow() - start_time).total_seconds()

        return {
            "success": success,
            "response_time_seconds": response_time,
            "tested_at": start_time.isoformat()
        }


# Singleton instance
webhook_service = WebhookService()
