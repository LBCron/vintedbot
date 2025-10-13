import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from backend.utils.logger import logger
from backend.db import get_db_session
from backend.models import Session, Listing, ListingStatus
from backend.vinted_connector import fetch_inbox, validate_session_cookie
from sqlmodel import select

scheduler = AsyncIOScheduler()

SYNC_INTERVAL_MIN = int(os.getenv("SYNC_INTERVAL_MIN", "15"))
PRICE_DROP_CRON = os.getenv("PRICE_DROP_CRON", "0 3 * * *")


async def inbox_sync_job():
    """Sync inbox for all active sessions"""
    logger.info("📥 Running inbox sync job")
    
    try:
        with get_db_session() as db:
            sessions = db.exec(select(Session)).all()
            
            for session in sessions:
                try:
                    from backend.utils.crypto import decrypt_blob
                    cookie = decrypt_blob(session.encrypted_cookie)
                    
                    # Validate session first
                    is_valid = await validate_session_cookie(cookie)
                    if not is_valid:
                        logger.warning(f"Session {session.id} is no longer valid")
                        continue
                    
                    # Fetch inbox
                    conversations = await fetch_inbox(cookie)
                    logger.info(f"Fetched {len(conversations)} conversations for session {session.id}")
                    
                    # Update last validated timestamp
                    session.last_validated_at = datetime.utcnow()
                    db.add(session)
                
                except Exception as e:
                    logger.error(f"Error syncing inbox for session {session.id}: {e}")
            
            db.commit()
        
        logger.info("✅ Inbox sync completed")
    
    except Exception as e:
        logger.error(f"Inbox sync job error: {e}")


async def publish_poll_job():
    """Poll publish queue and trigger worker tasks"""
    logger.info("📋 Checking publish queue")
    
    try:
        from backend.models import PublishJob, JobStatus
        
        with get_db_session() as db:
            queued_jobs = db.exec(
                select(PublishJob)
                .where(PublishJob.status == JobStatus.queued)
            ).all()
            
            if queued_jobs:
                logger.info(f"Found {len(queued_jobs)} queued jobs")
                # Jobs will be picked up by the Playwright worker
            
    except Exception as e:
        logger.error(f"Publish poll job error: {e}")


async def price_drop_job():
    """Scheduled price drop for listings"""
    logger.info("💸 Running price drop job")
    
    try:
        with get_db_session() as db:
            listings = db.exec(
                select(Listing)
                .where(Listing.status == ListingStatus.listed)
            ).all()
            
            drop_percentage = 0.05  # 5% drop
            
            for listing in listings:
                old_price = listing.price
                new_price = round(old_price * (1 - drop_percentage), 2)
                
                # Don't drop below a minimum (e.g., $5)
                if new_price >= 5.0:
                    listing.price = new_price
                    listing.updated_at = datetime.utcnow()
                    db.add(listing)
                    logger.info(f"Dropped price for listing {listing.id}: ${old_price} → ${new_price}")
            
            db.commit()
            logger.info(f"✅ Price drop completed for {len(listings)} listings")
    
    except Exception as e:
        logger.error(f"Price drop job error: {e}")


def start_scheduler():
    """Start the APScheduler with all jobs"""
    
    # Inbox sync - every N minutes
    scheduler.add_job(
        inbox_sync_job,
        trigger=IntervalTrigger(minutes=SYNC_INTERVAL_MIN),
        id="inbox_sync",
        name="Inbox Sync",
        replace_existing=True
    )
    
    # Publish queue poll - every 30 seconds
    scheduler.add_job(
        publish_poll_job,
        trigger=IntervalTrigger(seconds=30),
        id="publish_poll",
        name="Publish Queue Poll",
        replace_existing=True
    )
    
    # Price drop - daily at 3 AM (configurable via cron)
    scheduler.add_job(
        price_drop_job,
        trigger=CronTrigger.from_crontab(PRICE_DROP_CRON),
        id="price_drop",
        name="Daily Price Drop",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"⏰ Scheduler started with {len(scheduler.get_jobs())} jobs")
    logger.info(f"   - Inbox sync: every {SYNC_INTERVAL_MIN} minutes")
    logger.info(f"   - Publish poll: every 30 seconds")
    logger.info(f"   - Price drop: {PRICE_DROP_CRON}")


def stop_scheduler():
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("⏰ Scheduler stopped")
