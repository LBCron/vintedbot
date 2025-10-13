from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.models.db import db
from backend.services.pricing import pricing_service
from backend.models.schemas import ItemStatus


scheduler = BackgroundScheduler()


def daily_price_drop_job():
    print("🔄 Running daily price drop job...")
    items = db.get_by_status(ItemStatus.LISTED)
    
    for item in items:
        updated_item = pricing_service.apply_price_drop(item)
        db.update(item.id, updated_item)
    
    print(f"✅ Price drop job completed. Processed {len(items)} listed items.")


def start_scheduler():
    scheduler.add_job(
        daily_price_drop_job,
        CronTrigger(hour=0, minute=0),
        id='daily_price_drop',
        name='Daily price drop for listed items',
        replace_existing=True
    )
    scheduler.start()
    print("📅 Scheduler started successfully")


def stop_scheduler():
    scheduler.shutdown()
    print("📅 Scheduler stopped")


def get_scheduler_jobs_count() -> int:
    return len(scheduler.get_jobs())
