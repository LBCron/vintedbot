"""
Automated publisher for scheduled publications
Runs every 15 minutes to publish items at their scheduled time
"""
import asyncio
import logging
from datetime import datetime
from backend.core.database import get_db_pool

logger = logging.getLogger(__name__)


async def publish_scheduled_items():
    """
    Job that runs every 15 minutes to publish scheduled items

    Finds all scheduled_publications where:
    - scheduled_time <= now
    - status = 'pending'

    Then publishes them and updates status
    """
    logger.info("🕒 Running scheduled publisher job...")

    db_pool = await get_db_pool()

    try:
        async with db_pool.acquire() as conn:
            # Get items ready to publish
            items = await conn.fetch(
                """
                SELECT sp.id, sp.draft_id, sp.user_id, d.title
                FROM scheduled_publications sp
                JOIN drafts d ON sp.draft_id = d.id
                WHERE sp.scheduled_time <= NOW()
                AND sp.status = 'pending'
                ORDER BY sp.scheduled_time
                LIMIT 50
                """,
            )

            if not items:
                logger.info("No items to publish")
                return

            logger.info(f"Found {len(items)} items to publish")

            for item in items:
                try:
                    # TODO: Integrate with actual Vinted publishing service
                    # For now, mark as published
                    logger.info(f"📤 Publishing: {item['title']}")

                    # Update status to published
                    await conn.execute(
                        """
                        UPDATE scheduled_publications
                        SET status = 'published', published_at = NOW()
                        WHERE id = $1
                        """,
                        item['id']
                    )

                    # Update draft status
                    await conn.execute(
                        """
                        UPDATE drafts
                        SET status = 'published', published_at = NOW()
                        WHERE id = $1
                        """,
                        item['draft_id']
                    )

                    logger.info(f"✅ Published: {item['title']}")

                except Exception as e:
                    logger.error(f"❌ Failed to publish {item['title']}: {e}")

                    # Mark as failed
                    await conn.execute(
                        """
                        UPDATE scheduled_publications
                        SET status = 'failed', error = $1
                        WHERE id = $2
                        """,
                        str(e),
                        item['id']
                    )

            logger.info(f"✅ Scheduled publisher job complete. Published {len(items)} items.")

    except Exception as e:
        logger.error(f"❌ Scheduled publisher job failed: {e}")
        raise


def main():
    """Main entry point for cron job"""
    asyncio.run(publish_scheduled_items())


if __name__ == "__main__":
    # Run directly: python -m backend.jobs.scheduled_publisher
    main()
