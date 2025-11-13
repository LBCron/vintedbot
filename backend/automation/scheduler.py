"""
Sprint 2 Feature: Smart Publication Scheduler
Schedules and publishes items at optimal times throughout the day
"""
import asyncio
from datetime import datetime, time, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import random
from loguru import logger

from backend.core.vinted_client import VintedClient
from backend.core.session import get_vinted_session, VintedSession
from backend.core.storage import get_store


class ScheduleStrategy(Enum):
    """Publication scheduling strategies"""
    SPREAD_EVENLY = "spread_evenly"       # Distribute evenly throughout day
    PEAK_HOURS_ONLY = "peak_hours_only"   # Only publish during peak hours
    BUSINESS_HOURS = "business_hours"     # Publish during business hours (9h-18h)
    WEEKEND_FOCUS = "weekend_focus"       # Prioritize weekends
    CUSTOM_TIMES = "custom_times"         # User-defined specific times


class PublicationStatus(Enum):
    """Publication task status"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RATE_LIMITED = "rate_limited"


@dataclass
class ScheduledPublication:
    """Scheduled publication task"""
    schedule_id: str
    draft_id: str
    scheduled_time: datetime
    strategy: ScheduleStrategy
    status: PublicationStatus = PublicationStatus.SCHEDULED
    priority: int = 5  # 1-10
    retry_count: int = 0
    max_retries: int = 3
    published_at: Optional[datetime] = None
    listing_url: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'strategy': self.strategy.value,
            'status': self.status.value,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'published_at': self.published_at.isoformat() if self.published_at else None
        }


class OptimalPublishingTimes:
    """Analyzes and provides optimal publishing times"""

    # Peak times based on Vinted user behavior
    PEAK_TIMES_WEEKDAY = [
        time(8, 0),    # Morning commute
        time(12, 30),  # Lunch break
        time(18, 0),   # Evening after work - BEST
        time(20, 0),   # Evening browsing
    ]

    PEAK_TIMES_WEEKEND = [
        time(10, 0),   # Late morning
        time(14, 0),   # Afternoon
        time(19, 0),   # Evening
        time(21, 0),   # Night browsing
    ]

    @staticmethod
    def get_next_optimal_slot(
        current_time: datetime,
        strategy: ScheduleStrategy,
        count: int = 1
    ) -> List[datetime]:
        """
        Get next N optimal publication slots

        Args:
            current_time: Starting time
            strategy: Scheduling strategy
            count: Number of slots to generate

        Returns:
            List of optimal datetimes
        """
        if strategy == ScheduleStrategy.SPREAD_EVENLY:
            return OptimalPublishingTimes._spread_evenly(current_time, count)

        elif strategy == ScheduleStrategy.PEAK_HOURS_ONLY:
            return OptimalPublishingTimes._peak_hours_only(current_time, count)

        elif strategy == ScheduleStrategy.BUSINESS_HOURS:
            return OptimalPublishingTimes._business_hours(current_time, count)

        elif strategy == ScheduleStrategy.WEEKEND_FOCUS:
            return OptimalPublishingTimes._weekend_focus(current_time, count)

        else:
            # Default: spread evenly
            return OptimalPublishingTimes._spread_evenly(current_time, count)

    @staticmethod
    def _spread_evenly(current_time: datetime, count: int) -> List[datetime]:
        """Spread publications evenly throughout the day"""
        slots = []

        # Distribute across next 7 days (avoid publishing too many on same day)
        hours_between = 24 // min(count, 5)  # Max 5 per day

        for i in range(count):
            # Calculate slot time
            hours_delta = (i * hours_between) + random.randint(0, 2)
            slot_time = current_time + timedelta(hours=hours_delta)

            # Adjust to daytime hours (8h-22h)
            if slot_time.hour < 8:
                slot_time = slot_time.replace(hour=8)
            elif slot_time.hour > 22:
                slot_time = slot_time.replace(hour=20)

            # Add random minutes
            slot_time += timedelta(minutes=random.randint(0, 59))

            slots.append(slot_time)

        return slots

    @staticmethod
    def _peak_hours_only(current_time: datetime, count: int) -> List[datetime]:
        """Schedule only during peak hours"""
        slots = []

        current_date = current_time.date()
        days_offset = 0

        while len(slots) < count:
            target_date = current_date + timedelta(days=days_offset)
            is_weekend = target_date.weekday() >= 5

            peak_times = (
                OptimalPublishingTimes.PEAK_TIMES_WEEKEND
                if is_weekend
                else OptimalPublishingTimes.PEAK_TIMES_WEEKDAY
            )

            for peak_time in peak_times:
                slot = datetime.combine(target_date, peak_time)

                # Only future times
                if slot > current_time:
                    # Add random variance (±15 minutes)
                    variance = timedelta(minutes=random.randint(-15, 15))
                    slot += variance
                    slots.append(slot)

                    if len(slots) >= count:
                        break

            days_offset += 1

            # Safety: max 14 days ahead
            if days_offset > 14:
                break

        return slots[:count]

    @staticmethod
    def _business_hours(current_time: datetime, count: int) -> List[datetime]:
        """Schedule during business hours (9h-18h)"""
        slots = []

        for i in range(count):
            # Distribute across multiple days
            day_offset = i // 3  # Max 3 per day
            hours_offset = (i % 3) * 3  # 0, 3, 6 hours apart

            slot = current_time + timedelta(days=day_offset, hours=hours_offset)

            # Ensure within business hours (9h-18h)
            if slot.hour < 9:
                slot = slot.replace(hour=9)
            elif slot.hour > 18:
                slot = slot.replace(hour=random.randint(10, 16))

            # Add random minutes
            slot += timedelta(minutes=random.randint(0, 59))

            slots.append(slot)

        return slots

    @staticmethod
    def _weekend_focus(current_time: datetime, count: int) -> List[datetime]:
        """Prioritize weekend slots"""
        slots = []

        # Find next weekend
        days_until_saturday = (5 - current_time.weekday()) % 7
        if days_until_saturday == 0 and current_time.hour > 20:
            days_until_saturday = 7  # Next weekend

        next_saturday = current_time.date() + timedelta(days=days_until_saturday)

        # 60% on weekend, 40% on weekdays
        weekend_count = int(count * 0.6)
        weekday_count = count - weekend_count

        # Weekend slots
        for i in range(weekend_count):
            day = 0 if i < weekend_count // 2 else 1  # Sat or Sun
            peak_time = random.choice(OptimalPublishingTimes.PEAK_TIMES_WEEKEND)

            slot = datetime.combine(
                next_saturday + timedelta(days=day),
                peak_time
            ) + timedelta(minutes=random.randint(-15, 15))

            slots.append(slot)

        # Weekday slots (fill remaining)
        weekday_slots = OptimalPublishingTimes._spread_evenly(current_time, weekday_count)
        slots.extend(weekday_slots)

        # Sort chronologically
        slots.sort()

        return slots


class PublicationScheduler:
    """
    Smart Publication Scheduler

    Features:
    - Multiple scheduling strategies
    - Automatic retry on failure
    - Rate limiting respect
    - Priority-based queue
    - Analytics and reporting
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.schedules: Dict[str, ScheduledPublication] = {}
        self.running = False

        # Limits
        self.max_publications_per_day = 50  # Vinted safe limit
        self.daily_publication_count = 0
        self.last_publication_time: Optional[datetime] = None

    async def schedule_publications(
        self,
        draft_ids: List[str],
        strategy: ScheduleStrategy,
        start_time: Optional[datetime] = None,
        custom_times: Optional[List[datetime]] = None
    ) -> Dict[str, Any]:
        """
        Schedule publications for multiple drafts

        Args:
            draft_ids: Drafts to publish
            strategy: Scheduling strategy
            start_time: When to start scheduling (default: now)
            custom_times: For CUSTOM_TIMES strategy

        Returns:
            Scheduling result with all scheduled times
        """
        logger.info(f"Scheduling {len(draft_ids)} publications (strategy: {strategy.value})")

        if start_time is None:
            start_time = datetime.now()

        scheduled = []

        # Generate optimal times
        if strategy == ScheduleStrategy.CUSTOM_TIMES:
            if not custom_times or len(custom_times) < len(draft_ids):
                return {
                    'success': False,
                    'error': 'custom_times must contain times for all drafts'
                }
            times = custom_times[:len(draft_ids)]
        else:
            times = OptimalPublishingTimes.get_next_optimal_slot(
                start_time,
                strategy,
                len(draft_ids)
            )

        # Create schedules
        for i, draft_id in enumerate(draft_ids):
            # Verify draft exists and belongs to user
            draft = get_store().get_draft(draft_id)
            if not draft or draft.get('user_id') != str(self.user_id):
                logger.warning(f"Draft {draft_id} not found or unauthorized")
                continue

            # Check not already published
            item_json = draft.get('item_json', {})
            if item_json.get('vinted_id') or item_json.get('listing_id'):
                logger.warning(f"Draft {draft_id} already published, skipping")
                continue

            # Create schedule
            schedule_id = f"sched_{draft_id}_{int(times[i].timestamp())}"

            schedule = ScheduledPublication(
                schedule_id=schedule_id,
                draft_id=draft_id,
                scheduled_time=times[i],
                strategy=strategy,
                priority=5
            )

            self.schedules[schedule_id] = schedule
            scheduled.append(schedule.to_dict())

            logger.info(f"✅ Scheduled {draft_id} for {times[i]}")

        return {
            'success': True,
            'scheduled_count': len(scheduled),
            'schedules': scheduled
        }

    async def cancel_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Cancel a scheduled publication"""
        if schedule_id not in self.schedules:
            return {
                'success': False,
                'error': 'Schedule not found'
            }

        schedule = self.schedules[schedule_id]
        schedule.status = PublicationStatus.CANCELLED

        logger.info(f"Cancelled schedule {schedule_id}")

        return {
            'success': True,
            'schedule': schedule.to_dict()
        }

    async def execute_publication(self, schedule: ScheduledPublication) -> Tuple[bool, Optional[str]]:
        """Execute a single scheduled publication"""
        logger.info(f"Executing publication for draft {schedule.draft_id}...")

        schedule.status = PublicationStatus.IN_PROGRESS

        # Get draft data
        draft = get_store().get_draft(schedule.draft_id)
        if not draft:
            schedule.status = PublicationStatus.FAILED
            schedule.error_message = "Draft not found"
            return (False, "Draft not found")

        # Get Vinted session
        session = get_vinted_session(self.user_id)
        if not session:
            schedule.status = PublicationStatus.FAILED
            schedule.error_message = "No Vinted session"
            return (False, "No Vinted session")

        try:
            # Prepare item data
            title = draft.get('title', '')
            price = draft.get('price', 0)
            description = draft.get('description', '')
            photos = draft.get('photos', [])

            # Resolve photo paths
            import os
            resolved_photos = []
            for photo in photos:
                if os.path.exists(photo):
                    resolved_photos.append(photo)
                elif os.path.exists(f"/app/backend/data/{photo}"):
                    resolved_photos.append(f"/app/backend/data/{photo}")

            if not resolved_photos:
                schedule.status = PublicationStatus.FAILED
                schedule.error_message = "No valid photos found"
                return (False, "No valid photos")

            # Publish via VintedClient
            async with VintedClient(headless=True) as client:
                await client.init()
                await client.create_context(session)
                page = await client.new_page()

                success, error, result_data = await client.publish_item_complete(
                    page=page,
                    title=title,
                    price=price,
                    description=description,
                    photos=resolved_photos,
                    publish_mode="auto"
                )

                if success and result_data:
                    # Update schedule
                    schedule.status = PublicationStatus.SUCCESS
                    schedule.published_at = datetime.now()
                    schedule.listing_url = result_data.get('listing_url')

                    # Update draft in storage
                    item_json = draft.get('item_json', {})
                    item_json.update(result_data)
                    get_store().update_draft_item_json(schedule.draft_id, item_json)
                    get_store().mark_draft_published(schedule.draft_id)

                    # Update counters
                    self.daily_publication_count += 1
                    self.last_publication_time = datetime.now()

                    logger.info(f"✅ Published {schedule.draft_id} successfully!")
                    return (True, None)

                else:
                    # Handle failure
                    if "rate limit" in error.lower() if error else "":
                        schedule.status = PublicationStatus.RATE_LIMITED
                    else:
                        schedule.status = PublicationStatus.FAILED

                    schedule.error_message = error
                    schedule.retry_count += 1

                    # Retry logic
                    if schedule.retry_count < schedule.max_retries:
                        # Reschedule for 30 minutes later
                        schedule.scheduled_time = datetime.now() + timedelta(minutes=30)
                        schedule.status = PublicationStatus.SCHEDULED
                        logger.warning(f"Publication failed, retrying in 30min (attempt {schedule.retry_count}/{schedule.max_retries})")

                    logger.error(f"❌ Publication failed: {error}")
                    return (False, error)

        except Exception as e:
            schedule.status = PublicationStatus.FAILED
            schedule.error_message = str(e)
            logger.error(f"Exception during publication: {e}")
            return (False, str(e))

    async def run_scheduler(self):
        """
        Background task that executes scheduled publications

        Usage:
            asyncio.create_task(scheduler.run_scheduler())
        """
        logger.info(f"🚀 Publication scheduler started for user {self.user_id}")
        self.running = True

        while self.running:
            try:
                current_time = datetime.now()

                # Find schedules ready to execute
                ready_schedules = [
                    schedule for schedule in self.schedules.values()
                    if schedule.scheduled_time <= current_time
                    and schedule.status == PublicationStatus.SCHEDULED
                ]

                # Sort by priority (higher first), then by scheduled time
                ready_schedules.sort(key=lambda s: (s.priority, s.scheduled_time), reverse=True)

                # Execute publications with rate limiting
                for schedule in ready_schedules:
                    # Check daily limit
                    if self.daily_publication_count >= self.max_publications_per_day:
                        logger.warning(f"Daily publication limit reached ({self.max_publications_per_day})")
                        break

                    # Execute
                    await self.execute_publication(schedule)

                    # Human-like delay (3-8 minutes between publications)
                    await asyncio.sleep(random.randint(180, 480))

                # Reset daily counter at midnight
                if current_time.hour == 0 and current_time.minute < 5:
                    self.daily_publication_count = 0
                    logger.info("Daily publication counter reset")

                # Sleep for 1 minute before checking again
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)

    def stop_scheduler(self):
        """Stop the scheduler"""
        logger.info("Stopping publication scheduler...")
        self.running = False

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        total = len(self.schedules)
        scheduled = sum(1 for s in self.schedules.values() if s.status == PublicationStatus.SCHEDULED)
        completed = sum(1 for s in self.schedules.values() if s.status == PublicationStatus.SUCCESS)
        failed = sum(1 for s in self.schedules.values() if s.status == PublicationStatus.FAILED)

        upcoming = sorted(
            [s for s in self.schedules.values() if s.status == PublicationStatus.SCHEDULED],
            key=lambda s: s.scheduled_time
        )[:10]

        return {
            'running': self.running,
            'total_schedules': total,
            'scheduled': scheduled,
            'completed': completed,
            'failed': failed,
            'daily_publications': self.daily_publication_count,
            'daily_limit': self.max_publications_per_day,
            'upcoming_publications': [s.to_dict() for s in upcoming]
        }


# Global service instances
_publication_schedulers: Dict[int, PublicationScheduler] = {}


def get_publication_scheduler(user_id: int) -> PublicationScheduler:
    """Get or create publication scheduler for user"""
    if user_id not in _publication_schedulers:
        _publication_schedulers[user_id] = PublicationScheduler(user_id)
    return _publication_schedulers[user_id]
