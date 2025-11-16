"""
Upselling Service
Automatically suggests similar items to buyers after a sale
"""
from typing import List, Dict, Optional
from loguru import logger


class UpsellingService:
    """
    Service for intelligent upselling automation

    After a user sells an item, this service:
    1. Finds similar available items
    2. Generates a personalized message
    3. Optionally sends it automatically to the buyer
    """

    async def find_similar_items(
        self,
        sold_item_id: str,
        user_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find similar items to upsell

        Args:
            sold_item_id: ID of the sold item
            user_id: User ID
            limit: Max number of similar items to return

        Returns:
            List of similar items with similarity scores
        """
        from backend.core.database import get_db_pool

        logger.info(f"Finding similar items to upsell for sold item {sold_item_id}")

        try:
            pool = await get_db_pool()

            async with pool.acquire() as conn:
                # Get sold item details
                sold_item = await conn.fetchrow(
                    "SELECT * FROM drafts WHERE id = $1 AND user_id = $2",
                    sold_item_id, user_id
                )

                if not sold_item:
                    logger.warning(f"Sold item {sold_item_id} not found")
                    return []

                # Find similar available items using scoring algorithm
                # Scoring factors:
                # - Same category: +30 points
                # - Same brand: +25 points
                # - Same size: +15 points
                # - Similar price (±10€): +20 points
                # - Same color: +10 points

                query = """
                    SELECT
                        *,
                        (
                            CASE WHEN category = $1 THEN 30 ELSE 0 END +
                            CASE WHEN brand = $2 THEN 25 ELSE 0 END +
                            CASE WHEN size = $3 THEN 15 ELSE 0 END +
                            CASE WHEN ABS(price - $4) < 10 THEN 20 ELSE 0 END +
                            CASE WHEN color = $5 THEN 10 ELSE 0 END
                        ) as similarity_score
                    FROM drafts
                    WHERE
                        user_id = $6
                        AND id != $7
                        AND status IN ('published', 'active')
                        AND sold = false
                    ORDER BY similarity_score DESC
                    LIMIT $8
                """

                similar_items = await conn.fetch(
                    query,
                    sold_item.get('category'),
                    sold_item.get('brand'),
                    sold_item.get('size'),
                    sold_item.get('price', 0),
                    sold_item.get('color'),
                    user_id,
                    sold_item_id,
                    limit
                )

                # Filter items with score > 30 (at least 2 matching criteria)
                results = [
                    dict(item) for item in similar_items
                    if item.get('similarity_score', 0) >= 30
                ]

                logger.info(f"Found {len(results)} similar items for upselling")
                return results

        except Exception as e:
            logger.error(f"Error finding similar items: {e}")
            return []

    async def generate_upsell_message(
        self,
        sold_item: Dict,
        similar_items: List[Dict],
        buyer_name: Optional[str] = None
    ) -> str:
        """
        Generate personalized upselling message using AI

        Args:
            sold_item: The item that was sold
            similar_items: List of similar items to suggest
            buyer_name: Optional buyer name for personalization

        Returns:
            Generated message text
        """
        from backend.services.ai_message_service import AIMessageService

        if not similar_items:
            return ""

        logger.info(f"Generating upsell message for {len(similar_items)} items")

        try:
            ai_service = AIMessageService()

            # Build items list for prompt
            items_text = "\n".join([
                f"- {item.get('title', 'Article')} ({item.get('price', 0)}€)"
                for item in similar_items[:3]  # Max 3 items
            ])

            greeting = f"Bonjour {buyer_name}" if buyer_name else "Bonjour"

            prompt = f"""Génère un message Vinted court et naturel pour proposer des articles similaires à un acheteur.

{greeting}, tu viens d'acheter: {sold_item.get('title', 'un article')}

J'ai d'autres articles similaires disponibles:
{items_text}

Génère un message amical et non forcé (max 80 mots) pour proposer ces articles.
Le message doit être naturel, pas commercial.
"""

            message = await ai_service.generate_custom_message(
                user_message=prompt,
                context="upselling"
            )

            logger.info(f"Generated upsell message: {len(message)} chars")
            return message

        except Exception as e:
            logger.error(f"Error generating upsell message: {e}")

            # Fallback to simple template
            items_list = ", ".join([
                item.get('title', 'Article')[:30]
                for item in similar_items[:2]
            ])

            return f"{greeting}, merci pour ton achat ! Si tu cherches d'autres articles similaires, j'ai aussi: {items_list}. N'hésite pas si ça t'intéresse ! 😊"

    async def execute_upselling(
        self,
        sold_item_id: str,
        user_id: str,
        buyer_name: Optional[str] = None,
        auto_send: bool = False
    ) -> Dict:
        """
        Execute complete upselling workflow

        Args:
            sold_item_id: ID of sold item
            user_id: User ID
            buyer_name: Optional buyer name
            auto_send: Whether to automatically send the message

        Returns:
            Dict with upselling results
        """
        from backend.core.database import get_db_pool
        import json
        from datetime import datetime

        logger.info(f"Executing upselling for sold item {sold_item_id}")

        # Find similar items
        similar_items = await self.find_similar_items(
            sold_item_id=sold_item_id,
            user_id=user_id,
            limit=5
        )

        if not similar_items:
            return {
                "success": False,
                "message": "No similar items found for upselling",
                "similar_items": []
            }

        # Get sold item details
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            sold_item = await conn.fetchrow(
                "SELECT * FROM drafts WHERE id = $1",
                sold_item_id
            )

        # Generate message
        message = await self.generate_upsell_message(
            sold_item=dict(sold_item),
            similar_items=similar_items,
            buyer_name=buyer_name
        )

        # Log upselling attempt
        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO upsell_attempts
                    (user_id, sold_item_id, buyer_name, message, similar_items_ids, auto_sent, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    user_id,
                    sold_item_id,
                    buyer_name,
                    message,
                    json.dumps([item['id'] for item in similar_items]),
                    auto_send,
                    datetime.now()
                )
        except Exception as e:
            logger.warning(f"Could not log upsell attempt: {e}")

        result = {
            "success": True,
            "message": message,
            "similar_items": similar_items[:3],  # Return top 3
            "auto_sent": auto_send
        }

        # TODO: If auto_send=True, send message via Vinted API
        if auto_send:
            logger.info("Auto-send enabled - message would be sent via Vinted API")
            # from backend.services.vinted_api_client import VintedAPIClient
            # vinted_client = VintedAPIClient(session_cookie)
            # await vinted_client.send_message(conversation_id, message)

        return result
