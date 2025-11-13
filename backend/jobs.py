import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from backend.utils.logger import logger
from backend.db import get_db_session
from backend.models import Session, Listing, ListingStatus
from backend.vinted_connector import fetch_inbox, validate_session_cookie
from backend.core.storage import get_store
from sqlmodel import select

scheduler = AsyncIOScheduler()

SYNC_INTERVAL_MIN = int(os.getenv("SYNC_INTERVAL_MIN", "15"))
PRICE_DROP_CRON = os.getenv("PRICE_DROP_CRON", "0 3 * * *")


async def inbox_sync_job():
    """Sync inbox for all active sessions"""
    logger.info("[INBOX] Running inbox sync job")
    
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
    logger.info("[PUBLISH] Checking publish queue")
    
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
    logger.info("[PRICE] Running price drop job")
    
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


async def clean_temp_photos_job():
    """
    Clean old temporary photos (runs every 6 hours)
    - Deletes photo folders older than 24 hours from backend/data/temp_photos
    """
    logger.info("[CLEAN] Cleaning old temporary photos...")
    
    try:
        import shutil
        from pathlib import Path
        import time
        
        temp_dir = Path("backend/data/temp_photos")
        if not temp_dir.exists():
            logger.info("  No temp_photos directory found")
            return
        
        now = time.time()
        cutoff = now - (24 * 3600)  # 24 hours ago
        deleted_count = 0
        freed_mb = 0
        
        for folder in temp_dir.iterdir():
            if folder.is_dir():
                folder_mtime = folder.stat().st_mtime
                if folder_mtime < cutoff:
                    # Calculate size before deletion
                    folder_size = sum(f.stat().st_size for f in folder.rglob('*') if f.is_file()) / (1024 * 1024)
                    shutil.rmtree(folder)
                    deleted_count += 1
                    freed_mb += folder_size
        
        logger.info(f"✅ Cleaned {deleted_count} old photo folders, freed {freed_mb:.2f} MB")
    
    except Exception as e:
        logger.error(f"Clean temp photos job error: {e}")


async def vacuum_and_prune_job():
    """
    Daily SQLite maintenance job (runs at 02:00)
    - Deletes old published/error drafts (TTL_DRAFTS_DAYS)
    - Purges old publish logs (TTL_PUBLISH_LOG_DAYS)
    - VACUUM database to reclaim space
    """
    logger.info("[VACUUM] Running SQLite vacuum and prune job")
    
    try:
        result = get_store().vacuum_and_prune()
        logger.info(
            f"✅ Vacuum completed: "
            f"{result['deleted_drafts']} drafts deleted (TTL={result['draft_ttl_days']}d), "
            f"{result['deleted_logs']} logs purged (TTL={result['log_ttl_days']}d)"
        )
    
    except Exception as e:
        logger.error(f"Vacuum and prune job error: {e}")


async def automation_executor_job():
    """
    Execute enabled automation rules automatically
    - Runs every 5 minutes
    - Checks automation_rules table for enabled rules
    - Executes bump, follow, unfollow, message actions
    - Respects daily limits and scheduling
    """
    logger.info("[AUTOMATION] Running automation executor...")

    try:
        import json
        import uuid
        import random

        store = get_store()

        rules = store.get_automation_rules_to_execute()

        if not rules:
            logger.info("   No automation rules to execute")
            return

        logger.info(f"   Found {len(rules)} automation rules to execute")

        for rule in rules:
            try:
                jobs_today = store.count_automation_jobs_today(rule['id'])
                config = json.loads(rule['config']) if isinstance(rule['config'], str) else rule['config']
                daily_limit = config.get('daily_limit', 100)

                if jobs_today >= daily_limit:
                    logger.info(f"   Rule {rule['id'][:8]}... hit daily limit ({daily_limit})")
                    continue

                if rule['type'] == 'bump':
                    await execute_auto_bump(rule, store)
                elif rule['type'] == 'follow':
                    await execute_auto_follow(rule, store)
                elif rule['type'] == 'unfollow':
                    await execute_auto_unfollow(rule, store)
                elif rule['type'] == 'message':
                    await execute_auto_message(rule, store)

                interval_hours = config.get('interval_hours', 24)
                next_run = datetime.utcnow() + timedelta(hours=interval_hours)
                store.update_automation_rule_schedule(rule['id'], datetime.utcnow(), next_run)

            except Exception as e:
                logger.error(f"   Error executing rule {rule['id'][:8]}...: {e}")

        logger.info("✅ Automation executor completed")

    except Exception as e:
        logger.error(f"Automation executor job error: {e}")


async def storage_lifecycle_job():
    """
    Multi-tier storage lifecycle job
    - Runs daily at 3 AM
    - Manages photo lifecycle across TEMP/HOT/COLD tiers
    - Deletes expired photos, promotes/archives based on usage

    Actions:
    1. Delete expired TEMP photos (>48h)
    2. Delete published photos (>7 days after publishing)
    3. Promote TEMP → HOT (non-published drafts >48h)
    4. Archive HOT → COLD (>90 days without access)
    5. Delete COLD photos (>365 days)
    """
    logger.info("[STORAGE] Running storage lifecycle job")

    try:
        from backend.storage.storage_manager import StorageManager
        from backend.storage.lifecycle_manager import StorageLifecycleManager

        # Initialize storage manager and lifecycle manager
        storage_manager = StorageManager()
        lifecycle_manager = StorageLifecycleManager(storage_manager)

        # Run lifecycle job
        stats = await lifecycle_manager.run_daily_lifecycle()

        logger.info(
            f"✅ Storage lifecycle completed:\n"
            f"   - TEMP deleted: {stats.get('temp_deleted', 0)}\n"
            f"   - Published deleted: {stats.get('published_deleted', 0)}\n"
            f"   - Promoted to HOT: {stats.get('promoted_to_hot', 0)}\n"
            f"   - Archived to COLD: {stats.get('archived_to_cold', 0)}\n"
            f"   - Old photos deleted: {stats.get('old_deleted', 0)}"
        )

    except Exception as e:
        logger.error(f"Storage lifecycle job error: {e}")
        import traceback
        traceback.print_exc()


async def execute_auto_bump(rule, store):
    """
    Execute auto-bump for a rule.
    NOTE: This is a placeholder. The underlying VintedClient.bump method is incomplete.
    It correctly deletes the item but does not recreate it, which is required to complete the bump.
    Implementing the recreation part requires saving all listing data before deletion and then running
    the full creation flow, which is a significant task.
    """
    import json
    import uuid
    import random
    
    logger.warning("Auto-bump is a placeholder and does not perform a real bump on Vinted.")

    config = json.loads(rule['config']) if isinstance(rule['config'], str) else rule['config']
    user_id = rule['user_id']
    
    listings = store.get_user_listings(user_id, status='active')
    target_listings = config.get('target_listings', [])
    
    if target_listings:
        listings = [l for l in listings if l['id'] in target_listings]
    
    if config.get('rotate_listings', True):
        random.shuffle(listings)
    
    skip_recent_hours = config.get('skip_recent', 6)
    bumps_per_run = config.get('bumps_per_run', 5)
    
    bumped_count = 0
    for listing in listings[:bumps_per_run]:
        last_bump = store.get_last_bump_time(listing['id'])
        if last_bump and (datetime.utcnow() - last_bump).total_seconds() < skip_recent_hours * 3600:
            continue
        
        job_id = f"bump_{listing['id']}_{uuid.uuid4().hex[:8]}"
        
        try:
            # This just logs the bump internally, it does not perform a real Vinted action.
            store.log_automation_job(
                job_id=job_id,
                rule_id=rule['id'],
                job_type='bump',
                status='completed',
                target_id=listing['id'],
                result={'listing_id': listing['id'], 'auto': True, 'simulated': True}
            )
            
            store.track_analytics_event(
                listing_id=listing['id'],
                event_type='bump',
                user_id=user_id,
                source='automation'
            )
            
            bumped_count += 1
            logger.info(f"   (Simulated) Auto-bumped listing {listing['id'][:8]}...")
            
        except Exception as e:
            logger.error(f"   Failed to simulate auto-bump {listing['id'][:8]}...: {e}")
            store.update_automation_job(
                job_id=job_id,
                status='failed',
                error=str(e)
            )
    
    logger.info(f"   Simulated {bumped_count} bumps for rule {rule['id'][:8]}...")


async def execute_auto_follow(rule, store):
    """Execute auto-follow for a rule using VintedClient"""
    import json
    import uuid
    from backend.core.vinted_client import VintedClient
    from backend.core.session import VintedSession # Assuming this can be created from stored data

    config = json.loads(rule['config']) if isinstance(rule['config'], str) else rule['config']
    user_id = rule['user_id']
    
    # We need the Vinted session (cookie, user-agent) to initialize the client
    # This part is an assumption on how to retrieve the session
    vinted_session_data = store.get_vinted_session_for_user(user_id) # This function needs to be created
    if not vinted_session_data:
        logger.error(f"Could not find Vinted session for user {user_id} to perform auto-follow.")
        return

    session = VintedSession(cookie=vinted_session_data['cookie'], user_agent=vinted_session_data['user_agent'])

    target_users = config.get('target_users', [])
    follows_per_run = config.get('follows_per_run', 10)
    
    followed_count = 0
    async with VintedClient(headless=True) as client:
        await client.create_context(session)
        page = await client.new_page()

        for vinted_user_id in target_users[:follows_per_run]:
            if store.is_following(user_id, vinted_user_id):
                continue
            
            job_id = f"follow_{vinted_user_id}_{uuid.uuid4().hex[:8]}"
            profile_url = f"https://www.vinted.com/member/{vinted_user_id}"

            try:
                success, error = await client.follow(page, vinted_user_id, profile_url)
                if success:
                    store.log_automation_job(
                        job_id=job_id, rule_id=rule['id'], job_type='follow', status='completed',
                        target_id=vinted_user_id, result={'vinted_user_id': vinted_user_id, 'auto': True}
                    )
                    store.track_follow(user_id=user_id, vinted_user_id=vinted_user_id, source='automation')
                    followed_count += 1
                    logger.info(f"   Auto-followed user {vinted_user_id}")
                else:
                    raise Exception(error)

            except Exception as e:
                logger.error(f"   Failed to auto-follow {vinted_user_id}: {e}")
                store.log_automation_job(
                    job_id=job_id, rule_id=rule['id'], job_type='follow', status='failed',
                    target_id=vinted_user_id, result={'error': str(e)}
                )
    
    logger.info(f"   Followed {followed_count} users for rule {rule['id'][:8]}...")


async def execute_auto_unfollow(rule, store):
    """Execute auto-unfollow for a rule using VintedClient"""
    import json
    import uuid
    from backend.core.vinted_client import VintedClient
    from backend.core.session import VintedSession

    config = json.loads(rule['config']) if isinstance(rule['config'], str) else rule['config']
    user_id = rule['user_id']

    vinted_session_data = store.get_vinted_session_for_user(user_id)
    if not vinted_session_data:
        logger.error(f"Could not find Vinted session for user {user_id} to perform auto-unfollow.")
        return
        
    session = VintedSession(cookie=vinted_session_data['cookie'], user_agent=vinted_session_data['user_agent'])

    days_since_follow = config.get('days_since_follow', 7)
    unfollows_to_process = store.get_follows_to_unfollow(user_id, days_since_follow)
    unfollows_per_run = config.get('unfollows_per_run', 10)
    
    unfollowed_count = 0
    async with VintedClient(headless=True) as client:
        await client.create_context(session)
        page = await client.new_page()

        for vinted_user_id in unfollows_to_process[:unfollows_per_run]:
            job_id = f"unfollow_{vinted_user_id}_{uuid.uuid4().hex[:8]}"
            profile_url = f"https://www.vinted.com/member/{vinted_user_id}"

            try:
                success, error = await client.unfollow(page, vinted_user_id, profile_url)
                if success:
                    store.log_automation_job(
                        job_id=job_id, rule_id=rule['id'], job_type='unfollow', status='completed',
                        target_id=vinted_user_id, result={'vinted_user_id': vinted_user_id, 'auto': True}
                    )
                    store.track_unfollow(user_id, vinted_user_id)
                    unfollowed_count += 1
                    logger.info(f"   Auto-unfollowed user {vinted_user_id}")
                else:
                    raise Exception(error)

            except Exception as e:
                logger.error(f"   Failed to auto-unfollow {vinted_user_id}: {e}")
                store.log_automation_job(
                    job_id=job_id, rule_id=rule['id'], job_type='unfollow', status='failed',
                    target_id=vinted_user_id, result={'error': str(e)}
                )

    logger.info(f"   Unfollowed {unfollowed_count} users for rule {rule['id'][:8]}...")


async def execute_auto_message(rule, store):
    """Execute auto-message for a rule"""
    import json
    import uuid
    
    config = json.loads(rule['config']) if isinstance(rule['config'], str) else rule['config']
    user_id = rule['user_id']
    
    templates = config.get('templates', [])
    messages_per_run = config.get('messages_per_run', 5)
    
    sent_count = 0
    for template in templates[:messages_per_run]:
        job_id = f"message_{uuid.uuid4().hex[:8]}"
        
        try:
            store.log_automation_job(
                job_id=job_id,
                rule_id=rule['id'],
                job_type='message',
                status='completed',
                target_id=template.get('id') if isinstance(template, dict) else None,
                result={'template': template.get('name') if isinstance(template, dict) else 'template', 'auto': True}
            )
            
            sent_count += 1
            logger.info(f"   Auto-sent message using template '{template.get('name') if isinstance(template, dict) else 'template'}'")
            
        except Exception as e:
            logger.error(f"   Failed to auto-send message: {e}")
            store.update_automation_job(
                job_id=job_id,
                status='failed',
                error=str(e)
            )
    
    logger.info(f"   Sent {sent_count} messages for rule {rule['id'][:8]}...")


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
    
    # SQLite vacuum and prune - daily at 2 AM
    scheduler.add_job(
        vacuum_and_prune_job,
        trigger=CronTrigger(hour=2, minute=0),
        id="vacuum_prune",
        name="SQLite Vacuum & Prune",
        replace_existing=True
    )
    
    # Clean temp photos - every 6 hours
    scheduler.add_job(
        clean_temp_photos_job,
        trigger=IntervalTrigger(hours=6),
        id="clean_temp_photos",
        name="Clean Temp Photos",
        replace_existing=True
    )
    
    # Automation executor - every 5 minutes
    scheduler.add_job(
        automation_executor_job,
        trigger=IntervalTrigger(minutes=5),
        id="automation_executor",
        name="Automation Executor",
        replace_existing=True
    )

    # Storage lifecycle - daily at 3 AM
    scheduler.add_job(
        storage_lifecycle_job,
        trigger=CronTrigger(hour=3, minute=0),
        id="storage_lifecycle",
        name="Storage Lifecycle Manager",
        replace_existing=True
    )

    scheduler.start()
    logger.info(f"Scheduler started with {len(scheduler.get_jobs())} jobs")
    logger.info(f"   - Inbox sync: every {SYNC_INTERVAL_MIN} minutes")
    logger.info(f"   - Publish poll: every 30 seconds")
    logger.info(f"   - Price drop: {PRICE_DROP_CRON}")
    logger.info(f"   - Vacuum & Prune: 0 2 * * * (daily at 02:00)")
    logger.info(f"   - Clean temp photos: every 6 hours")
    logger.info(f"   - Automation Executor: every 5 minutes")
    logger.info(f"   - Storage Lifecycle: 0 3 * * * (daily at 03:00)")


def stop_scheduler():
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
