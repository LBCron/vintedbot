"""
Vinted API Client
Handles direct integration with Vinted's API for feedback, labels, and messaging
"""
import httpx
from typing import Dict, Optional, List
from loguru import logger


class VintedAPIClient:
    """
    Client for interacting with Vinted's API

    Note: This requires a valid Vinted session cookie.
    Users must provide their session cookie from vinted.fr
    """

    BASE_URL = "https://www.vinted.fr/api/v2"

    def __init__(self, session_cookie: str):
        """
        Initialize client with session cookie

        Args:
            session_cookie: Value of _vinted_fr_session cookie
        """
        self.session_cookie = session_cookie
        self.headers = {
            'Cookie': f'_vinted_fr_session={session_cookie}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }

    async def send_feedback(
        self,
        transaction_id: str,
        rating: int,
        comment: str
    ) -> Dict:
        """
        Send feedback for a transaction

        Args:
            transaction_id: Vinted transaction ID
            rating: 1-5 stars
            comment: Feedback comment

        Returns:
            API response
        """
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        url = f"{self.BASE_URL}/transactions/{transaction_id}/feedbacks"

        payload = {
            "rating": rating,
            "comment": comment
        }

        logger.info(f"Sending feedback for transaction {transaction_id}: {rating} stars")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=payload
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Feedback sent successfully")
            return result

    async def get_shipping_label(
        self,
        transaction_id: str
    ) -> bytes:
        """
        Download shipping label PDF for a transaction

        Args:
            transaction_id: Vinted transaction ID

        Returns:
            PDF content as bytes
        """
        url = f"{self.BASE_URL}/transactions/{transaction_id}/shipping_label"

        logger.info(f"Downloading shipping label for transaction {transaction_id}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers=self.headers
            )

            response.raise_for_status()

            logger.info(f"Shipping label downloaded ({len(response.content)} bytes)")
            return response.content

    async def send_message(
        self,
        conversation_id: str,
        message: str
    ) -> Dict:
        """
        Send a message in a conversation

        Args:
            conversation_id: Vinted conversation ID
            message: Message text

        Returns:
            API response
        """
        url = f"{self.BASE_URL}/conversations/{conversation_id}/messages"

        payload = {
            "text": message
        }

        logger.info(f"Sending message to conversation {conversation_id}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=payload
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Message sent successfully")
            return result

    async def get_user_stats(self) -> Dict:
        """
        Get current user's statistics

        Returns:
            User stats including items count, sales, etc.
        """
        url = f"{self.BASE_URL}/users/current"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers=self.headers
            )

            response.raise_for_status()
            return response.json()

    async def get_transactions(
        self,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get user's transactions

        Args:
            status: Filter by status (e.g., 'completed', 'pending')
            limit: Max number of transactions to return

        Returns:
            List of transactions
        """
        url = f"{self.BASE_URL}/transactions"

        params = {"per_page": limit}
        if status:
            params["status"] = status

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers=self.headers,
                params=params
            )

            response.raise_for_status()
            result = response.json()

            return result.get("transactions", [])

    async def get_conversation_messages(
        self,
        conversation_id: str
    ) -> List[Dict]:
        """
        Get all messages in a conversation

        Args:
            conversation_id: Conversation ID

        Returns:
            List of messages
        """
        url = f"{self.BASE_URL}/conversations/{conversation_id}/messages"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers=self.headers
            )

            response.raise_for_status()
            result = response.json()

            return result.get("messages", [])
