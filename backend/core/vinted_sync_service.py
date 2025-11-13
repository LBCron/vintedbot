"""
Sprint 1 Feature 1B: Bidirectional Vinted Synchronization Service

Handles real-time synchronization between VintedBot and Vinted:
- Pull: Fetch changes from Vinted (price, description, status updates)
- Push: Send local changes to Vinted
- Conflict resolution: Merge strategy for simultaneous changes
- Intelligent polling: Rate-limited checks to avoid API abuse
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from backend.core.vinted_api_client import VintedAPIClient
from backend.core.session import get_vinted_session
from backend.core.storage import get_store
from backend.core.smart_rate_limiter import SmartRateLimiter


class SyncConflictStrategy(Enum):
    """Strategy for resolving sync conflicts"""
    VINTED_WINS = "vinted_wins"  # Vinted state takes precedence
    LOCAL_WINS = "local_wins"    # Local state takes precedence
    NEWEST_WINS = "newest_wins"  # Most recent change wins
    MANUAL = "manual"            # Require manual resolution


class SyncStatus(Enum):
    """Current sync status"""
    IDLE = "idle"
    SYNCING = "syncing"
    SUCCESS = "success"
    ERROR = "error"
    CONFLICT = "conflict"


@dataclass
class SyncChange:
    """Represents a detected change in listing"""
    listing_id: str
    field: str
    local_value: Any
    vinted_value: Any
    local_updated_at: Optional[datetime]
    vinted_updated_at: Optional[datetime]
    conflict: bool = False


@dataclass
class SyncResult:
    """Result of a sync operation"""
    status: SyncStatus
    pulled_changes: int = 0
    pushed_changes: int = 0
    conflicts: List[SyncChange] = None
    errors: List[str] = None
    synced_at: datetime = None

    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []
        if self.errors is None:
            self.errors = []
        if self.synced_at is None:
            self.synced_at = datetime.utcnow()


class VintedSyncService:
    """
    Bidirectional synchronization service for Vinted listings

    Features:
    - Real-time change detection
    - Intelligent polling with exponential backoff
    - Conflict resolution with multiple strategies
    - Rate limiting to prevent API abuse
    - Change tracking and audit log
    """

    def __init__(
        self,
        user_id: int,
        conflict_strategy: SyncConflictStrategy = SyncConflictStrategy.VINTED_WINS,
        poll_interval_seconds: int = 300  # 5 minutes default
    ):
        self.user_id = user_id
        self.conflict_strategy = conflict_strategy
        self.poll_interval = poll_interval_seconds
        self.status = SyncStatus.IDLE
        self.last_sync: Optional[datetime] = None
        self.rate_limiter = SmartRateLimiter(
            requests_per_minute=10,  # Conservative rate
            burst_size=5
        )

    async def pull_changes(
        self,
        listing_ids: Optional[List[str]] = None
    ) -> SyncResult:
        """
        Pull changes from Vinted and update local database

        Args:
            listing_ids: Specific listings to sync (None = sync all)

        Returns:
            SyncResult with pulled changes and conflicts
        """
        logger.info(f"[SYNC-PULL] Starting pull for user {self.user_id}")
        self.status = SyncStatus.SYNCING

        result = SyncResult(status=SyncStatus.SYNCING)

        try:
            # Get Vinted session
            session = get_vinted_session(self.user_id)
            if not session:
                raise ValueError(f"No Vinted session found for user {self.user_id}")

            # Get Vinted API client
            vinted_client = VintedAPIClient(session=session)

            # Get local listings from database
            store = get_store()
            local_listings = store.get_published_listings(self.user_id)

            if listing_ids:
                local_listings = [l for l in local_listings if l['vinted_id'] in listing_ids]

            logger.info(f"[SYNC-PULL] Found {len(local_listings)} local listings to check")

            # Fetch each listing from Vinted with rate limiting
            for local_listing in local_listings:
                vinted_id = local_listing.get('vinted_id')
                if not vinted_id:
                    continue

                # Rate limit check
                await self.rate_limiter.acquire()

                try:
                    # Fetch listing from Vinted API
                    vinted_data = await vinted_client.get_listing(vinted_id)

                    if not vinted_data:
                        logger.warning(f"[SYNC-PULL] Listing {vinted_id} not found on Vinted")
                        continue

                    # Detect changes
                    changes = self._detect_changes(local_listing, vinted_data)

                    if changes:
                        logger.info(f"[SYNC-PULL] Detected {len(changes)} changes for listing {vinted_id}")

                        # Apply changes based on conflict strategy
                        for change in changes:
                            if change.conflict:
                                # Handle conflict
                                resolved_value = self._resolve_conflict(change)
                                if resolved_value is not None:
                                    self._apply_change(local_listing['draft_id'], change.field, resolved_value)
                                    result.pulled_changes += 1
                                else:
                                    result.conflicts.append(change)
                            else:
                                # No conflict, apply Vinted value
                                self._apply_change(local_listing['draft_id'], change.field, change.vinted_value)
                                result.pulled_changes += 1

                except Exception as e:
                    logger.error(f"[SYNC-PULL] Error syncing listing {vinted_id}: {e}")
                    result.errors.append(f"Listing {vinted_id}: {str(e)}")

            # Update sync result
            if result.conflicts:
                result.status = SyncStatus.CONFLICT
            elif result.errors:
                result.status = SyncStatus.ERROR
            else:
                result.status = SyncStatus.SUCCESS

            self.last_sync = datetime.utcnow()
            self.status = result.status

            logger.info(
                f"[SYNC-PULL] Complete: {result.pulled_changes} changes, "
                f"{len(result.conflicts)} conflicts, {len(result.errors)} errors"
            )

            return result

        except Exception as e:
            logger.error(f"[SYNC-PULL] Failed: {e}")
            result.status = SyncStatus.ERROR
            result.errors.append(str(e))
            self.status = SyncStatus.ERROR
            return result

    async def push_changes(
        self,
        draft_ids: Optional[List[str]] = None
    ) -> SyncResult:
        """
        Push local changes to Vinted

        Args:
            draft_ids: Specific drafts to push (None = push all modified)

        Returns:
            SyncResult with pushed changes
        """
        logger.info(f"[SYNC-PUSH] Starting push for user {self.user_id}")
        self.status = SyncStatus.SYNCING

        result = SyncResult(status=SyncStatus.SYNCING)

        try:
            # Get Vinted session
            session = get_vinted_session(self.user_id)
            if not session:
                raise ValueError(f"No Vinted session found for user {self.user_id}")

            # Get Vinted API client
            vinted_client = VintedAPIClient(session=session)

            # Get modified local listings
            store = get_store()
            modified_listings = store.get_modified_listings(self.user_id)

            if draft_ids:
                modified_listings = [l for l in modified_listings if l['draft_id'] in draft_ids]

            logger.info(f"[SYNC-PUSH] Found {len(modified_listings)} modified listings to push")

            # Push each listing with rate limiting
            for listing in modified_listings:
                vinted_id = listing.get('vinted_id')
                if not vinted_id:
                    logger.warning(f"[SYNC-PUSH] Listing {listing['draft_id']} has no vinted_id")
                    continue

                # Rate limit check
                await self.rate_limiter.acquire()

                try:
                    # Build update payload
                    update_data = {
                        'title': listing.get('title'),
                        'description': listing.get('description'),
                        'price': listing.get('price'),
                        'brand': listing.get('brand'),
                        'size': listing.get('size'),
                        'condition': listing.get('condition'),
                        'color': listing.get('color')
                    }

                    # Update on Vinted
                    success = await vinted_client.update_listing(vinted_id, update_data)

                    if success:
                        # Mark as synced in database
                        store.mark_listing_synced(listing['draft_id'])
                        result.pushed_changes += 1
                        logger.info(f"[SYNC-PUSH] Successfully pushed listing {vinted_id}")
                    else:
                        result.errors.append(f"Failed to update listing {vinted_id}")

                except Exception as e:
                    logger.error(f"[SYNC-PUSH] Error pushing listing {vinted_id}: {e}")
                    result.errors.append(f"Listing {vinted_id}: {str(e)}")

            # Update sync result
            if result.errors:
                result.status = SyncStatus.ERROR
            else:
                result.status = SyncStatus.SUCCESS

            self.last_sync = datetime.utcnow()
            self.status = result.status

            logger.info(
                f"[SYNC-PUSH] Complete: {result.pushed_changes} changes, "
                f"{len(result.errors)} errors"
            )

            return result

        except Exception as e:
            logger.error(f"[SYNC-PUSH] Failed: {e}")
            result.status = SyncStatus.ERROR
            result.errors.append(str(e))
            self.status = SyncStatus.ERROR
            return result

    async def full_sync(self) -> SyncResult:
        """
        Perform full bidirectional sync (pull + push)

        Returns:
            Combined SyncResult
        """
        logger.info(f"[SYNC-FULL] Starting full sync for user {self.user_id}")

        # Pull changes from Vinted first
        pull_result = await self.pull_changes()

        # Then push local changes
        push_result = await self.push_changes()

        # Combine results
        combined = SyncResult(
            status=SyncStatus.SUCCESS,
            pulled_changes=pull_result.pulled_changes,
            pushed_changes=push_result.pushed_changes,
            conflicts=pull_result.conflicts,
            errors=pull_result.errors + push_result.errors
        )

        if combined.conflicts:
            combined.status = SyncStatus.CONFLICT
        elif combined.errors:
            combined.status = SyncStatus.ERROR

        logger.info(
            f"[SYNC-FULL] Complete: pulled {combined.pulled_changes}, "
            f"pushed {combined.pushed_changes}, "
            f"{len(combined.conflicts)} conflicts, {len(combined.errors)} errors"
        )

        return combined

    def _detect_changes(
        self,
        local_listing: Dict[str, Any],
        vinted_data: Dict[str, Any]
    ) -> List[SyncChange]:
        """
        Detect differences between local and Vinted data

        Returns:
            List of detected changes
        """
        changes = []

        # Fields to monitor
        fields_to_check = {
            'title': 'title',
            'description': 'description',
            'price': 'price',
            'status': 'status',
            'brand': 'brand_title',
            'size': 'size_title',
            'color': 'color'
        }

        local_updated = local_listing.get('updated_at')
        vinted_updated = vinted_data.get('updated_at')

        for local_field, vinted_field in fields_to_check.items():
            local_value = local_listing.get(local_field)
            vinted_value = vinted_data.get(vinted_field)

            # Normalize values for comparison
            if local_field == 'price':
                local_value = float(local_value) if local_value else None
                vinted_value = float(vinted_value) if vinted_value else None

            # Compare values
            if local_value != vinted_value:
                # Check if it's a conflict (both modified)
                is_conflict = (
                    local_updated and vinted_updated and
                    local_updated > self.last_sync and
                    vinted_updated > self.last_sync
                ) if self.last_sync else False

                change = SyncChange(
                    listing_id=local_listing.get('vinted_id'),
                    field=local_field,
                    local_value=local_value,
                    vinted_value=vinted_value,
                    local_updated_at=local_updated,
                    vinted_updated_at=vinted_updated,
                    conflict=is_conflict
                )
                changes.append(change)

        return changes

    def _resolve_conflict(self, change: SyncChange) -> Optional[Any]:
        """
        Resolve a sync conflict based on strategy

        Returns:
            Resolved value or None if manual resolution required
        """
        if self.conflict_strategy == SyncConflictStrategy.VINTED_WINS:
            logger.info(f"[CONFLICT] {change.field}: Vinted wins strategy")
            return change.vinted_value

        elif self.conflict_strategy == SyncConflictStrategy.LOCAL_WINS:
            logger.info(f"[CONFLICT] {change.field}: Local wins strategy")
            return change.local_value

        elif self.conflict_strategy == SyncConflictStrategy.NEWEST_WINS:
            if change.vinted_updated_at and change.local_updated_at:
                if change.vinted_updated_at > change.local_updated_at:
                    logger.info(f"[CONFLICT] {change.field}: Vinted is newer")
                    return change.vinted_value
                else:
                    logger.info(f"[CONFLICT] {change.field}: Local is newer")
                    return change.local_value
            # Fallback to Vinted if timestamps unclear
            return change.vinted_value

        elif self.conflict_strategy == SyncConflictStrategy.MANUAL:
            logger.warning(f"[CONFLICT] {change.field}: Manual resolution required")
            return None

        return None

    def _apply_change(self, draft_id: str, field: str, value: Any):
        """Apply a synced change to local database"""
        try:
            store = get_store()
            update_data = {field: value}
            store.update_draft(draft_id, update_data)
            logger.info(f"[SYNC-APPLY] Updated {field} for draft {draft_id}")
        except Exception as e:
            logger.error(f"[SYNC-APPLY] Failed to apply change: {e}")

    async def start_polling(self):
        """Start continuous polling loop"""
        logger.info(f"[SYNC-POLL] Starting polling every {self.poll_interval}s")

        while True:
            try:
                await asyncio.sleep(self.poll_interval)

                # Perform full sync
                result = await self.full_sync()

                if result.status == SyncStatus.CONFLICT:
                    logger.warning(f"[SYNC-POLL] Conflicts detected: {len(result.conflicts)}")
                elif result.status == SyncStatus.ERROR:
                    logger.error(f"[SYNC-POLL] Errors: {result.errors}")
                else:
                    logger.info(f"[SYNC-POLL] Success: {result.pulled_changes + result.pushed_changes} changes")

            except Exception as e:
                logger.error(f"[SYNC-POLL] Polling error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry


# Global sync service registry
_sync_services: Dict[int, VintedSyncService] = {}


def get_sync_service(user_id: int) -> VintedSyncService:
    """Get or create sync service for user"""
    if user_id not in _sync_services:
        _sync_services[user_id] = VintedSyncService(user_id)
    return _sync_services[user_id]
