"""
Sprint 2 Feature: Intelligent Auto-Bump System
Automatically bumps items at optimal times for maximum visibility
"""
import asyncio
from datetime import datetime, time, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import random
from loguru import logger

from backend.core.vinted_api_client import VintedAPIClient
from backend.core.session import get_vinted_session
from backend.core.storage import get_store


class BumpStrategy(Enum):
    """Bump timing strategies"""
    PEAK_HOURS = "peak_hours"          # Bump during peak traffic (18h-21h)
    BUSINESS_HOURS = "business_hours"  # Bump during work breaks (12h-14h, 17h-20h)
    WEEKEND_OPTIMIZER = "weekend"      # Optimize for weekend shoppers
    CONTINUOUS = "continuous"          # Spread evenly throughout day
    SMART_AI = "smart_ai"             # AI-powered optimal timing


class BumpStatus(Enum):
    """Bump execution status"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    NO_BUMPS_LEFT = "no_bumps_left"


@dataclass
class BumpSchedule:
    """Scheduled bump configuration"""
    item_id: str
    draft_id: str
    scheduled_time: datetime
    strategy: BumpStrategy
    priority: int = 5  # 1-10, higher = more important
    status: BumpStatus = BumpStatus.SCHEDULED
    last_bumped_at: Optional[datetime] = None
    next_bump_at: Optional[datetime] = None
    bump_count: int = 0
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'strategy': self.strategy.value,
            'status': self.status.value,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'last_bumped_at': self.last_bumped_at.isoformat() if self.last_bumped_at else None,
            'next_bump_at': self.next_bump_at.isoformat() if self.next_bump_at else None
        }


class OptimalTimingAnalyzer:
    """Analyzes optimal bump times based on Vinted traffic patterns"""

    # Peak hours based on French Vinted user behavior analysis
    PEAK_HOURS = {
        'weekday': [
            (time(12, 0), time(14, 0)),   # Lunch break
            (time(18, 0), time(21, 30)),  # Evening after work - HIGHEST traffic
        ],
        'weekend': [
            (time(10, 0), time(12, 0)),   # Late morning
            (time(14, 0), time(16, 0)),   # Afternoon
            (time(19, 0), time(22, 0)),   # Evening
        ]
    }

    @staticmethod
    def get_next_optimal_time(
        strategy: BumpStrategy,
        current_time: Optional[datetime] = None
    ) -> datetime:
        """Calculate next optimal bump time based on strategy"""
        if current_time is None:
            current_time = datetime.now()

        if strategy == BumpStrategy.PEAK_HOURS:
            return OptimalTimingAnalyzer._next_peak_hour(current_time)

        elif strategy == BumpStrategy.BUSINESS_HOURS:
            return OptimalTimingAnalyzer._next_business_hour(current_time)

        elif strategy == BumpStrategy.WEEKEND_OPTIMIZER:
            return OptimalTimingAnalyzer._next_weekend_slot(current_time)

        elif strategy == BumpStrategy.CONTINUOUS:
            # Bump every 4-6 hours randomly
            hours_delta = random.randint(4, 6)
            return current_time + timedelta(hours=hours_delta)

        elif strategy == BumpStrategy.SMART_AI:
            # AI-powered: combines peak hours + user's historical success
            return OptimalTimingAnalyzer._ai_optimal_time(current_time)

        else:
            return current_time + timedelta(hours=4)

    @staticmethod
    def _next_peak_hour(current_time: datetime) -> datetime:
        """Find next peak hour slot"""
        is_weekend = current_time.weekday() >= 5
        peak_slots = OptimalTimingAnalyzer.PEAK_HOURS['weekend' if is_weekend else 'weekday']

        current_time_only = current_time.time()

        # Check if we can bump today
        for start, end in peak_slots:
            if current_time_only < start:
                # Schedule for this slot today
                return datetime.combine(
                    current_time.date(),
                    start
                ) + timedelta(minutes=random.randint(0, 30))

        # All slots passed today, schedule for tomorrow's first slot
        tomorrow = current_time.date() + timedelta(days=1)
        is_tomorrow_weekend = tomorrow.weekday() >= 5
        tomorrow_slots = OptimalTimingAnalyzer.PEAK_HOURS['weekend' if is_tomorrow_weekend else 'weekday']

        first_slot_start = tomorrow_slots[0][0]
        return datetime.combine(tomorrow, first_slot_start) + timedelta(minutes=random.randint(0, 30))

    @staticmethod
    def _next_business_hour(current_time: datetime) -> datetime:
        """Next business hours slot (12h-14h or 17h-20h)"""
        current_time_only = current_time.time()

        if current_time_only < time(12, 0):
            target = datetime.combine(current_time.date(), time(12, 0))
        elif current_time_only < time(17, 0):
            target = datetime.combine(current_time.date(), time(17, 0))
        else:
            # Next day lunch
            target = datetime.combine(
                current_time.date() + timedelta(days=1),
                time(12, 0)
            )

        return target + timedelta(minutes=random.randint(0, 45))

    @staticmethod
    def _next_weekend_slot(current_time: datetime) -> datetime:
        """Next weekend slot"""
        if current_time.weekday() >= 5:
            # Already weekend
            return OptimalTimingAnalyzer._next_peak_hour(current_time)
        else:
            # Schedule for next Saturday
            days_until_saturday = 5 - current_time.weekday()
            saturday = current_time.date() + timedelta(days=days_until_saturday)
            return datetime.combine(saturday, time(10, 0)) + timedelta(hours=random.randint(0, 2))

    @staticmethod
    def _ai_optimal_time(current_time: datetime) -> datetime:
        """AI-powered optimal time (combines multiple factors)"""
        # For now, use peak hours with slight randomization
        # TODO: Integrate ML model trained on user's bump success rates
        base_time = OptimalTimingAnalyzer._next_peak_hour(current_time)

        # Add randomness to avoid predictable patterns
        variance_minutes = random.randint(-15, 15)
        return base_time + timedelta(minutes=variance_minutes)


class AutoBumpService:
    """
    Intelligent Auto-Bump Service

    Features:
    - Multiple timing strategies (peak hours, business hours, weekend, AI)
    - Rate limiting and bump quota tracking
    - Priority-based scheduling
    - Retry logic for failed bumps
    - Analytics and performance tracking
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.schedules: Dict[str, BumpSchedule] = {}
        self.running = False
        self.bump_queue: List[BumpSchedule] = []

    async def enable_auto_bump(
        self,
        draft_ids: List[str],
        strategy: BumpStrategy = BumpStrategy.PEAK_HOURS,
        priority: int = 5
    ) -> Dict[str, Any]:
        """
        Enable auto-bump for specific drafts

        Args:
            draft_ids: List of draft IDs to auto-bump
            strategy: Bump timing strategy
            priority: Priority level (1-10)

        Returns:
            Status and scheduled times
        """
        logger.info(f"Enabling auto-bump for {len(draft_ids)} items (strategy: {strategy.value})")

        scheduled = []

        for draft_id in draft_ids:
            # Get draft data
            draft = get_store().get_draft(draft_id)
            if not draft or draft.get('user_id') != str(self.user_id):
                logger.warning(f"Draft {draft_id} not found or unauthorized")
                continue

            # Get item_id from draft
            item_json = draft.get('item_json', {})
            item_id = item_json.get('vinted_id') or item_json.get('listing_id')

            if not item_id:
                logger.warning(f"Draft {draft_id} not published yet, skipping")
                continue

            # Calculate next bump time
            next_bump = OptimalTimingAnalyzer.get_next_optimal_time(strategy)

            # Create schedule
            schedule = BumpSchedule(
                item_id=item_id,
                draft_id=draft_id,
                scheduled_time=next_bump,
                strategy=strategy,
                priority=priority,
                next_bump_at=next_bump
            )

            self.schedules[draft_id] = schedule
            scheduled.append(schedule.to_dict())

            logger.info(f"✅ Scheduled auto-bump for draft {draft_id} at {next_bump}")

        return {
            'success': True,
            'scheduled_count': len(scheduled),
            'schedules': scheduled
        }

    async def disable_auto_bump(self, draft_ids: List[str]) -> Dict[str, Any]:
        """Disable auto-bump for specific drafts"""
        disabled = []

        for draft_id in draft_ids:
            if draft_id in self.schedules:
                del self.schedules[draft_id]
                disabled.append(draft_id)

        logger.info(f"Disabled auto-bump for {len(disabled)} items")

        return {
            'success': True,
            'disabled_count': len(disabled)
        }

    async def execute_bump(self, schedule: BumpSchedule) -> Tuple[bool, Optional[str]]:
        """Execute a single bump"""
        logger.info(f"Executing bump for item {schedule.item_id}...")

        # Get Vinted session
        session = get_vinted_session(self.user_id)
        if not session:
            return (False, "No Vinted session found")

        # Execute bump via API client
        async with VintedAPIClient(session=session) as client:
            success, error = await client.bump_item(schedule.item_id)

            if success:
                schedule.status = BumpStatus.SUCCESS
                schedule.last_bumped_at = datetime.now()
                schedule.bump_count += 1

                # Schedule next bump
                schedule.next_bump_at = OptimalTimingAnalyzer.get_next_optimal_time(
                    schedule.strategy,
                    datetime.now()
                )
                schedule.scheduled_time = schedule.next_bump_at
                schedule.status = BumpStatus.SCHEDULED

                logger.info(f"✅ Bump successful! Next bump at {schedule.next_bump_at}")
                return (True, None)

            else:
                # Handle errors
                if "Rate limited" in error:
                    schedule.status = BumpStatus.RATE_LIMITED
                    # Retry in 1 hour
                    schedule.next_bump_at = datetime.now() + timedelta(hours=1)
                elif "exhausted" in error:
                    schedule.status = BumpStatus.NO_BUMPS_LEFT
                    schedule.next_bump_at = None  # No more bumps available
                else:
                    schedule.status = BumpStatus.FAILED
                    schedule.error_message = error
                    # Retry in 30 minutes
                    schedule.next_bump_at = datetime.now() + timedelta(minutes=30)

                logger.error(f"❌ Bump failed: {error}")
                return (False, error)

    async def run_scheduler(self):
        """
        Background task that runs continuously and executes scheduled bumps

        Usage:
            asyncio.create_task(service.run_scheduler())
        """
        logger.info(f"🚀 Auto-bump scheduler started for user {self.user_id}")
        self.running = True

        while self.running:
            try:
                current_time = datetime.now()

                # Find schedules ready to execute
                ready_schedules = [
                    schedule for schedule in self.schedules.values()
                    if schedule.next_bump_at and schedule.next_bump_at <= current_time
                    and schedule.status in [BumpStatus.SCHEDULED, BumpStatus.FAILED]
                ]

                # Sort by priority (higher first)
                ready_schedules.sort(key=lambda s: s.priority, reverse=True)

                # Execute bumps with rate limiting
                for schedule in ready_schedules:
                    await self.execute_bump(schedule)

                    # Human-like delay between bumps (2-5 minutes)
                    await asyncio.sleep(random.randint(120, 300))

                # Sleep for 1 minute before checking again
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Error in auto-bump scheduler: {e}")
                await asyncio.sleep(60)

    def stop_scheduler(self):
        """Stop the background scheduler"""
        logger.info("Stopping auto-bump scheduler...")
        self.running = False

    def get_status(self) -> Dict[str, Any]:
        """Get current auto-bump status"""
        total = len(self.schedules)
        active = sum(1 for s in self.schedules.values() if s.status == BumpStatus.SCHEDULED)
        rate_limited = sum(1 for s in self.schedules.values() if s.status == BumpStatus.RATE_LIMITED)

        upcoming = sorted(
            [s for s in self.schedules.values() if s.next_bump_at],
            key=lambda s: s.next_bump_at
        )[:5]

        return {
            'running': self.running,
            'total_schedules': total,
            'active': active,
            'rate_limited': rate_limited,
            'upcoming_bumps': [s.to_dict() for s in upcoming]
        }


# Global service instances (one per user)
_auto_bump_services: Dict[int, AutoBumpService] = {}


def get_auto_bump_service(user_id: int) -> AutoBumpService:
    """Get or create auto-bump service for user"""
    if user_id not in _auto_bump_services:
        _auto_bump_services[user_id] = AutoBumpService(user_id)
    return _auto_bump_services[user_id]
