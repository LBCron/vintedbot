"""
Sprint 1 Feature 1C: Multi-Account Intelligent Manager

Smart account rotation and load balancing for Vinted accounts:
- Health tracking per account (rate limits, bans, success rate)
- Intelligent load balancing based on account health
- Automatic quarantine for problematic accounts
- Session pooling and warm-up
- Cooldown periods between operations
- Priority-based selection

This prevents rate limiting and bans by distributing load across multiple accounts.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
from loguru import logger

from backend.core.session import VintedSession, get_vinted_session
from backend.core.storage import get_store


class AccountStatus(Enum):
    """Account health status"""
    HEALTHY = "healthy"
    WARNING = "warning"  # Approaching rate limits
    RATE_LIMITED = "rate_limited"  # Hit rate limit
    BANNED = "banned"  # Account banned
    QUARANTINED = "quarantined"  # Temporarily disabled
    INACTIVE = "inactive"  # Not used recently


class AccountPriority(Enum):
    """Account priority for selection"""
    HIGH = 3
    MEDIUM = 2
    LOW = 1


@dataclass
class AccountHealth:
    """Health metrics for a Vinted account"""
    account_id: str
    user_id: int
    status: AccountStatus = AccountStatus.HEALTHY
    priority: AccountPriority = AccountPriority.MEDIUM

    # Usage statistics
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    rate_limit_hits: int = 0
    captcha_hits: int = 0

    # Timing
    last_used_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    quarantined_until: Optional[datetime] = None

    # Computed metrics
    success_rate: float = 1.0
    operations_per_hour: float = 0.0
    cooldown_minutes: int = 5  # Minimum time between operations

    def update_success(self):
        """Record successful operation"""
        self.total_operations += 1
        self.successful_operations += 1
        self.last_used_at = datetime.utcnow()
        self.last_success_at = datetime.utcnow()
        self._recalculate_metrics()

    def update_failure(self, is_rate_limit: bool = False, is_captcha: bool = False):
        """Record failed operation"""
        self.total_operations += 1
        self.failed_operations += 1
        self.last_used_at = datetime.utcnow()
        self.last_failure_at = datetime.utcnow()

        if is_rate_limit:
            self.rate_limit_hits += 1
            self.status = AccountStatus.RATE_LIMITED
            # Quarantine for 1 hour
            self.quarantined_until = datetime.utcnow() + timedelta(hours=1)
            logger.warning(f"Account {self.account_id} hit rate limit, quarantined for 1h")

        if is_captcha:
            self.captcha_hits += 1
            # If too many captchas, mark as warning
            if self.captcha_hits > 3:
                self.status = AccountStatus.WARNING

        self._recalculate_metrics()

    def _recalculate_metrics(self):
        """Recalculate health metrics"""
        if self.total_operations > 0:
            self.success_rate = self.successful_operations / self.total_operations

            # Adjust cooldown based on success rate
            if self.success_rate < 0.5:
                self.cooldown_minutes = 15  # Long cooldown for problematic accounts
            elif self.success_rate < 0.8:
                self.cooldown_minutes = 10
            else:
                self.cooldown_minutes = 5  # Default

        # Update status based on metrics
        if self.status == AccountStatus.RATE_LIMITED:
            # Check if quarantine expired
            if self.quarantined_until and datetime.utcnow() > self.quarantined_until:
                self.status = AccountStatus.HEALTHY
                self.quarantined_until = None
                logger.info(f"Account {self.account_id} recovered from rate limit")
        elif self.success_rate < 0.3 and self.total_operations > 10:
            self.status = AccountStatus.QUARANTINED
            self.quarantined_until = datetime.utcnow() + timedelta(hours=24)
            logger.warning(f"Account {self.account_id} quarantined due to low success rate")
        elif self.success_rate < 0.7:
            self.status = AccountStatus.WARNING
        else:
            self.status = AccountStatus.HEALTHY

    def is_available(self) -> bool:
        """Check if account is available for use"""
        # Check quarantine
        if self.quarantined_until and datetime.utcnow() < self.quarantined_until:
            return False

        # Check status
        if self.status in [AccountStatus.BANNED, AccountStatus.QUARANTINED]:
            return False

        # Check cooldown
        if self.last_used_at:
            time_since_last_use = (datetime.utcnow() - self.last_used_at).total_seconds() / 60
            if time_since_last_use < self.cooldown_minutes:
                return False

        return True

    def get_score(self) -> float:
        """
        Calculate selection score for load balancing

        Higher score = better candidate for selection
        """
        if not self.is_available():
            return 0.0

        score = 0.0

        # Base score from success rate
        score += self.success_rate * 100

        # Bonus for high priority
        score += self.priority.value * 20

        # Bonus for recent inactivity (distribute load)
        if self.last_used_at:
            hours_since_use = (datetime.utcnow() - self.last_used_at).total_seconds() / 3600
            score += min(hours_since_use * 10, 50)  # Max 50 bonus
        else:
            score += 50  # Never used, good candidate

        # Penalty for rate limit hits
        score -= self.rate_limit_hits * 10

        # Penalty for captcha hits
        score -= self.captcha_hits * 5

        # Random factor for variety (±10%)
        score *= random.uniform(0.9, 1.1)

        return max(score, 0.0)


class MultiAccountManager:
    """
    Intelligent multi-account manager with load balancing

    Features:
    - Smart account selection based on health and load
    - Automatic rotation to distribute operations
    - Health tracking and monitoring
    - Quarantine management for problematic accounts
    - Session pooling for quick access
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.accounts: Dict[str, AccountHealth] = {}
        self._session_pool: Dict[str, VintedSession] = {}
        self._initialized = False

    async def initialize(self):
        """Initialize accounts from database"""
        if self._initialized:
            return

        logger.info(f"[MULTI-ACCOUNT] Initializing for user {self.user_id}")

        # Load accounts from database
        store = get_store()
        # Assuming there's a method to get all accounts for a user
        # For now, we'll use a placeholder

        # TODO: Implement get_user_accounts() in storage
        # accounts = store.get_user_accounts(self.user_id)

        # For now, load the default account
        try:
            session = get_vinted_session(self.user_id)
            if session:
                account_id = f"account_{self.user_id}"
                self.accounts[account_id] = AccountHealth(
                    account_id=account_id,
                    user_id=self.user_id,
                    priority=AccountPriority.HIGH  # Default account has high priority
                )
                self._session_pool[account_id] = session
                logger.info(f"[MULTI-ACCOUNT] Loaded default account {account_id}")
        except Exception as e:
            logger.error(f"[MULTI-ACCOUNT] Failed to load accounts: {e}")

        self._initialized = True

    async def get_best_account(self) -> Tuple[Optional[str], Optional[VintedSession]]:
        """
        Select best account for next operation using intelligent load balancing

        Returns:
            (account_id, session) or (None, None) if no accounts available
        """
        if not self._initialized:
            await self.initialize()

        if not self.accounts:
            logger.warning("[MULTI-ACCOUNT] No accounts available")
            return (None, None)

        # Calculate scores for all accounts
        candidates = []
        for account_id, health in self.accounts.items():
            score = health.get_score()
            if score > 0:
                candidates.append((account_id, score, health))

        if not candidates:
            logger.warning("[MULTI-ACCOUNT] All accounts unavailable")
            return (None, None)

        # Sort by score (highest first)
        candidates.sort(key=lambda x: x[1], reverse=True)

        # Select best account
        account_id, score, health = candidates[0]
        session = self._session_pool.get(account_id)

        logger.info(
            f"[MULTI-ACCOUNT] Selected account {account_id} "
            f"(score: {score:.1f}, success rate: {health.success_rate:.2%})"
        )

        return (account_id, session)

    async def record_operation(
        self,
        account_id: str,
        success: bool,
        is_rate_limit: bool = False,
        is_captcha: bool = False
    ):
        """
        Record operation result for account health tracking

        Args:
            account_id: Account ID
            success: Whether operation succeeded
            is_rate_limit: Whether failure was due to rate limit
            is_captcha: Whether failure was due to captcha
        """
        if account_id not in self.accounts:
            logger.warning(f"[MULTI-ACCOUNT] Unknown account {account_id}")
            return

        health = self.accounts[account_id]

        if success:
            health.update_success()
            logger.info(
                f"[MULTI-ACCOUNT] Account {account_id} operation success "
                f"(rate: {health.success_rate:.2%})"
            )
        else:
            health.update_failure(is_rate_limit=is_rate_limit, is_captcha=is_captcha)
            logger.warning(
                f"[MULTI-ACCOUNT] Account {account_id} operation failed "
                f"(rate: {health.success_rate:.2%}, status: {health.status.value})"
            )

    def get_account_stats(self, account_id: str) -> Optional[Dict]:
        """Get statistics for a specific account"""
        if account_id not in self.accounts:
            return None

        health = self.accounts[account_id]
        return {
            "account_id": account_id,
            "status": health.status.value,
            "priority": health.priority.value,
            "total_operations": health.total_operations,
            "successful_operations": health.successful_operations,
            "failed_operations": health.failed_operations,
            "success_rate": health.success_rate,
            "rate_limit_hits": health.rate_limit_hits,
            "captcha_hits": health.captcha_hits,
            "last_used_at": health.last_used_at.isoformat() if health.last_used_at else None,
            "is_available": health.is_available(),
            "score": health.get_score()
        }

    def get_all_stats(self) -> List[Dict]:
        """Get statistics for all accounts"""
        return [self.get_account_stats(aid) for aid in self.accounts.keys()]

    async def add_account(
        self,
        account_id: str,
        session: VintedSession,
        priority: AccountPriority = AccountPriority.MEDIUM
    ):
        """
        Add a new account to the pool

        Args:
            account_id: Unique account identifier
            session: VintedSession for this account
            priority: Account priority level
        """
        self.accounts[account_id] = AccountHealth(
            account_id=account_id,
            user_id=self.user_id,
            priority=priority
        )
        self._session_pool[account_id] = session
        logger.info(f"[MULTI-ACCOUNT] Added account {account_id} with priority {priority.value}")

    async def remove_account(self, account_id: str):
        """Remove account from pool"""
        if account_id in self.accounts:
            del self.accounts[account_id]
        if account_id in self._session_pool:
            del self._session_pool[account_id]
        logger.info(f"[MULTI-ACCOUNT] Removed account {account_id}")

    async def warm_up_accounts(self):
        """
        Warm up all accounts with lightweight operations

        This ensures sessions are valid and reduces cold start time
        """
        logger.info("[MULTI-ACCOUNT] Warming up accounts...")

        for account_id, session in self._session_pool.items():
            try:
                # Simple validation check (could be a lightweight API call)
                # For now, just mark as used
                health = self.accounts[account_id]
                health.last_used_at = datetime.utcnow()
                logger.info(f"[MULTI-ACCOUNT] Warmed up account {account_id}")
            except Exception as e:
                logger.error(f"[MULTI-ACCOUNT] Failed to warm up account {account_id}: {e}")


# Global manager registry
_managers: Dict[int, MultiAccountManager] = {}


async def get_account_manager(user_id: int) -> MultiAccountManager:
    """Get or create multi-account manager for user"""
    if user_id not in _managers:
        manager = MultiAccountManager(user_id)
        await manager.initialize()
        _managers[user_id] = manager
    return _managers[user_id]
