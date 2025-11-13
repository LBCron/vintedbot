"""
Sprint 2 Feature: Strategic Auto-Follow System
Automatically follows relevant sellers to increase visibility and engagement
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import random
from loguru import logger

from backend.core.vinted_api_client import VintedAPIClient
from backend.core.session import get_vinted_session


class FollowStrategy(Enum):
    """Follow targeting strategies"""
    SAME_CATEGORY = "same_category"      # Follow sellers in same category
    TOP_SELLERS = "top_sellers"          # Follow high-rated active sellers
    RECENT_BUYERS = "recent_buyers"      # Follow people who bought from you
    COMPETITORS = "competitors"          # Follow sellers with similar items
    TRENDING = "trending"                # Follow trending sellers
    SMART_AI = "smart_ai"               # AI-powered targeting


class FollowStatus(Enum):
    """Follow action status"""
    PENDING = "pending"
    SUCCESS = "success"
    ALREADY_FOLLOWING = "already_following"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    USER_NOT_FOUND = "user_not_found"


@dataclass
class FollowTarget:
    """Target user to follow"""
    user_id: str
    username: str
    follower_count: int
    item_count: int
    rating: float
    category: Optional[str] = None
    reason: str = "strategic"  # Why we're following them
    priority: int = 5  # 1-10
    status: FollowStatus = FollowStatus.PENDING
    followed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'status': self.status.value,
            'followed_at': self.followed_at.isoformat() if self.followed_at else None
        }


@dataclass
class UnfollowRule:
    """Rules for unfollowing users"""
    unfollow_inactive_days: int = 30        # Unfollow if no activity in X days
    unfollow_low_rating: float = 3.5        # Unfollow if rating drops below X
    unfollow_if_not_following_back: bool = True  # Unfollow if they don't follow back
    max_following: int = 500                # Maximum users to follow
    check_interval_hours: int = 24          # How often to run cleanup


class TargetAnalyzer:
    """Analyzes and identifies strategic follow targets"""

    @staticmethod
    async def find_same_category_sellers(
        client: VintedAPIClient,
        user_category: str,
        limit: int = 20
    ) -> List[FollowTarget]:
        """Find active sellers in same category"""
        logger.info(f"Finding sellers in category: {user_category}")

        targets = []

        try:
            # Search for items in category
            search_results = await client.search_items(
                catalog_ids=[user_category],
                per_page=50
            )

            if not search_results:
                return targets

            # Extract unique sellers
            seen_users = set()

            for item in search_results[:50]:
                user = item.get('user', {})
                user_id = str(user.get('id'))

                if user_id in seen_users:
                    continue

                seen_users.add(user_id)

                # Filter: active sellers with good metrics
                item_count = user.get('item_count', 0)
                rating = user.get('feedback_reputation', 0)

                if item_count < 5 or rating < 4.0:
                    continue  # Skip inactive or low-rated sellers

                target = FollowTarget(
                    user_id=user_id,
                    username=user.get('login', 'unknown'),
                    follower_count=user.get('followers_count', 0),
                    item_count=item_count,
                    rating=rating,
                    category=user_category,
                    reason=f"Active seller in {user_category}",
                    priority=7
                )

                targets.append(target)

                if len(targets) >= limit:
                    break

            logger.info(f"Found {len(targets)} potential targets in {user_category}")
            return targets

        except Exception as e:
            logger.error(f"Error finding category sellers: {e}")
            return []

    @staticmethod
    async def find_top_sellers(
        client: VintedAPIClient,
        limit: int = 20
    ) -> List[FollowTarget]:
        """Find top-rated sellers with high activity"""
        logger.info("Finding top sellers...")

        targets = []

        try:
            # Get popular items and extract sellers
            popular_items = await client.search_items(
                order="relevance",
                per_page=100
            )

            if not popular_items:
                return targets

            # Score sellers based on multiple factors
            seller_scores = {}

            for item in popular_items:
                user = item.get('user', {})
                user_id = str(user.get('id'))

                if user_id in seller_scores:
                    seller_scores[user_id]['score'] += 1
                else:
                    seller_scores[user_id] = {
                        'user': user,
                        'score': 1
                    }

            # Sort by score and create targets
            sorted_sellers = sorted(
                seller_scores.items(),
                key=lambda x: x[1]['score'],
                reverse=True
            )

            for user_id, data in sorted_sellers[:limit]:
                user = data['user']

                target = FollowTarget(
                    user_id=user_id,
                    username=user.get('login', 'unknown'),
                    follower_count=user.get('followers_count', 0),
                    item_count=user.get('item_count', 0),
                    rating=user.get('feedback_reputation', 0),
                    reason="Top seller with high visibility",
                    priority=8
                )

                targets.append(target)

            logger.info(f"Found {len(targets)} top sellers")
            return targets

        except Exception as e:
            logger.error(f"Error finding top sellers: {e}")
            return []

    @staticmethod
    async def find_competitors(
        client: VintedAPIClient,
        user_items: List[Dict[str, Any]],
        limit: int = 15
    ) -> List[FollowTarget]:
        """Find sellers with similar items (competitors)"""
        logger.info("Finding competitors with similar items...")

        if not user_items:
            return []

        targets = []
        seen_users = set()

        try:
            # Search for similar items
            for user_item in user_items[:5]:  # Check first 5 items
                title = user_item.get('title', '')

                # Extract keywords
                keywords = ' '.join(title.split()[:3])

                similar_items = await client.search_items(
                    search_text=keywords,
                    per_page=30
                )

                if not similar_items:
                    continue

                for item in similar_items:
                    user = item.get('user', {})
                    user_id = str(user.get('id'))

                    if user_id in seen_users:
                        continue

                    seen_users.add(user_id)

                    target = FollowTarget(
                        user_id=user_id,
                        username=user.get('login', 'unknown'),
                        follower_count=user.get('followers_count', 0),
                        item_count=user.get('item_count', 0),
                        rating=user.get('feedback_reputation', 0),
                        reason=f"Competitor selling similar items",
                        priority=6
                    )

                    targets.append(target)

                    if len(targets) >= limit:
                        break

                if len(targets) >= limit:
                    break

            logger.info(f"Found {len(targets)} competitors")
            return targets

        except Exception as e:
            logger.error(f"Error finding competitors: {e}")
            return []


class AutoFollowService:
    """
    Strategic Auto-Follow Service

    Features:
    - Multiple targeting strategies
    - Smart rate limiting (10-20 follows/day)
    - Auto-unfollow inactive users
    - Analytics and performance tracking
    - Respects Vinted limits to avoid bans
    """

    # Vinted safe limits
    MAX_FOLLOWS_PER_DAY = 20
    MAX_FOLLOWS_PER_HOUR = 5
    MIN_DELAY_BETWEEN_FOLLOWS = 120  # 2 minutes minimum

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.daily_follow_count = 0
        self.hourly_follow_count = 0
        self.last_follow_time: Optional[datetime] = None
        self.running = False
        self.follow_queue: List[FollowTarget] = []
        self.unfollow_rules = UnfollowRule()

    async def add_targets(
        self,
        strategy: FollowStrategy,
        limit: int = 20,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add follow targets based on strategy

        Args:
            strategy: Targeting strategy
            limit: Maximum targets to add
            category: Category for SAME_CATEGORY strategy

        Returns:
            Status and targets added
        """
        logger.info(f"Adding follow targets (strategy: {strategy.value}, limit: {limit})")

        # Get Vinted session
        session = get_vinted_session(self.user_id)
        if not session:
            return {
                'success': False,
                'error': 'No Vinted session found'
            }

        async with VintedAPIClient(session=session) as client:
            targets = []

            if strategy == FollowStrategy.SAME_CATEGORY:
                if not category:
                    return {'success': False, 'error': 'Category required for SAME_CATEGORY strategy'}
                targets = await TargetAnalyzer.find_same_category_sellers(client, category, limit)

            elif strategy == FollowStrategy.TOP_SELLERS:
                targets = await TargetAnalyzer.find_top_sellers(client, limit)

            elif strategy == FollowStrategy.COMPETITORS:
                # Get user's published items
                from backend.core.storage import get_store
                user_drafts = get_store().get_published_listings(self.user_id)
                user_items = [d.get('item_json', {}) for d in user_drafts if d.get('item_json')]
                targets = await TargetAnalyzer.find_competitors(client, user_items, limit)

            elif strategy == FollowStrategy.SMART_AI:
                # Combine multiple strategies with weighted priority
                cat_targets = await TargetAnalyzer.find_same_category_sellers(client, category, 10) if category else []
                top_targets = await TargetAnalyzer.find_top_sellers(client, 10)
                targets = cat_targets + top_targets

            # Add to queue
            self.follow_queue.extend(targets)

            # Remove duplicates
            seen = set()
            unique_queue = []
            for target in self.follow_queue:
                if target.user_id not in seen:
                    seen.add(target.user_id)
                    unique_queue.append(target)

            self.follow_queue = unique_queue

            logger.info(f"✅ Added {len(targets)} targets to follow queue")

            return {
                'success': True,
                'targets_added': len(targets),
                'queue_size': len(self.follow_queue),
                'targets': [t.to_dict() for t in targets]
            }

    async def execute_follow(self, target: FollowTarget) -> Tuple[bool, Optional[str]]:
        """Execute a single follow action"""

        # Check rate limits
        if self.daily_follow_count >= self.MAX_FOLLOWS_PER_DAY:
            logger.warning("Daily follow limit reached")
            return (False, "Daily limit reached")

        if self.hourly_follow_count >= self.MAX_FOLLOWS_PER_HOUR:
            logger.warning("Hourly follow limit reached")
            return (False, "Hourly limit reached")

        # Check minimum delay
        if self.last_follow_time:
            elapsed = (datetime.now() - self.last_follow_time).total_seconds()
            if elapsed < self.MIN_DELAY_BETWEEN_FOLLOWS:
                wait_time = self.MIN_DELAY_BETWEEN_FOLLOWS - elapsed
                logger.info(f"Waiting {wait_time:.0f}s before next follow...")
                await asyncio.sleep(wait_time)

        # Get session
        session = get_vinted_session(self.user_id)
        if not session:
            return (False, "No Vinted session")

        # Execute follow via API
        async with VintedAPIClient(session=session) as client:
            success, error = await client.follow_user(target.user_id)

            if success:
                target.status = FollowStatus.SUCCESS
                target.followed_at = datetime.now()

                self.daily_follow_count += 1
                self.hourly_follow_count += 1
                self.last_follow_time = datetime.now()

                logger.info(f"✅ Followed @{target.username} ({target.reason})")
                return (True, None)
            else:
                if "already following" in error.lower():
                    target.status = FollowStatus.ALREADY_FOLLOWING
                elif "rate limit" in error.lower():
                    target.status = FollowStatus.RATE_LIMITED
                else:
                    target.status = FollowStatus.FAILED

                logger.error(f"❌ Failed to follow @{target.username}: {error}")
                return (False, error)

    async def run_auto_follow(self):
        """
        Background task for continuous following

        Usage:
            asyncio.create_task(service.run_auto_follow())
        """
        logger.info(f"🚀 Auto-follow service started for user {self.user_id}")
        self.running = True

        while self.running:
            try:
                # Reset hourly counter every hour
                if self.last_follow_time and \
                   (datetime.now() - self.last_follow_time).total_seconds() > 3600:
                    self.hourly_follow_count = 0

                # Process queue (priority sorted)
                if self.follow_queue:
                    self.follow_queue.sort(key=lambda t: t.priority, reverse=True)

                    target = self.follow_queue.pop(0)
                    await self.execute_follow(target)

                    # Random delay (2-5 minutes) between follows
                    await asyncio.sleep(random.randint(120, 300))
                else:
                    # No targets in queue, wait 10 minutes
                    await asyncio.sleep(600)

            except Exception as e:
                logger.error(f"Error in auto-follow loop: {e}")
                await asyncio.sleep(60)

    async def cleanup_inactive_follows(self):
        """Unfollow inactive users based on rules"""
        logger.info("Running follow cleanup...")

        session = get_vinted_session(self.user_id)
        if not session:
            return

        async with VintedAPIClient(session=session) as client:
            # Get current following list
            success, following, error = await client.get_following()

            if not success or not following:
                logger.error(f"Failed to get following list: {error}")
                return

            unfollowed_count = 0

            for user in following:
                user_id = str(user.get('id'))

                # Check unfollow rules
                should_unfollow = False

                # Rule 1: Low rating
                if user.get('feedback_reputation', 5.0) < self.unfollow_rules.unfollow_low_rating:
                    should_unfollow = True
                    reason = "low rating"

                # Rule 2: Not following back (if enabled)
                if self.unfollow_rules.unfollow_if_not_following_back:
                    if not user.get('is_following_back', False):
                        should_unfollow = True
                        reason = "not following back"

                if should_unfollow:
                    success, error = await client.unfollow_user(user_id)
                    if success:
                        unfollowed_count += 1
                        logger.info(f"Unfollowed @{user.get('login')} ({reason})")

                    # Delay between unfollows
                    await asyncio.sleep(random.randint(30, 60))

            logger.info(f"✅ Cleanup complete: unfollowed {unfollowed_count} users")

    def stop(self):
        """Stop auto-follow service"""
        logger.info("Stopping auto-follow service...")
        self.running = False

    def get_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            'running': self.running,
            'queue_size': len(self.follow_queue),
            'daily_follows': self.daily_follow_count,
            'hourly_follows': self.hourly_follow_count,
            'daily_limit': self.MAX_FOLLOWS_PER_DAY,
            'last_follow': self.last_follow_time.isoformat() if self.last_follow_time else None,
            'next_available': (
                (self.last_follow_time + timedelta(seconds=self.MIN_DELAY_BETWEEN_FOLLOWS)).isoformat()
                if self.last_follow_time else datetime.now().isoformat()
            )
        }


# Global service instances
_auto_follow_services: Dict[int, AutoFollowService] = {}


def get_auto_follow_service(user_id: int) -> AutoFollowService:
    """Get or create auto-follow service for user"""
    if user_id not in _auto_follow_services:
        _auto_follow_services[user_id] = AutoFollowService(user_id)
    return _auto_follow_services[user_id]
