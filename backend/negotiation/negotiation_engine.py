"""
Auto-Negotiation Engine - Smart automated offer handling
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import sqlite3
import json


class ActionType(str, Enum):
    """Negotiation action types"""
    ACCEPT = "accept"
    REJECT = "reject"
    COUNTER = "counter"
    IGNORE = "ignore"


class RuleCondition(str, Enum):
    """Conditions for rules"""
    PERCENTAGE_ABOVE = "percentage_above"  # Offer is X% above minimum
    ABSOLUTE_ABOVE = "absolute_above"  # Offer is X€ above minimum
    BUYER_RATING = "buyer_rating"  # Buyer rating threshold
    ITEM_AGE = "item_age"  # Days since listing created
    VIEWS_COUNT = "views_count"  # Number of views
    OFFER_COUNT = "offer_count"  # Number of offers received


@dataclass
class NegotiationRule:
    """A negotiation rule"""
    id: str
    name: str
    condition: RuleCondition
    threshold: float
    action: ActionType
    counter_percentage: Optional[float] = None  # For COUNTER action
    priority: int = 0  # Higher priority rules are checked first
    enabled: bool = True
    description: str = ""


@dataclass
class OfferAnalysis:
    """Analysis of an offer"""
    offer_id: str
    listing_id: str
    offer_amount: float
    list_price: float
    min_acceptable: float
    discount_percentage: float
    is_acceptable: bool
    recommended_action: ActionType
    counter_offer_amount: Optional[float]
    reasoning: str
    buyer_score: float  # 0-1 buyer quality score
    urgency_score: float  # 0-1 how urgent to sell


@dataclass
class NegotiationStats:
    """Negotiation statistics"""
    total_offers: int
    auto_accepted: int
    auto_rejected: int
    auto_countered: int
    manual_needed: int
    acceptance_rate: float
    avg_discount: float
    revenue_saved: float  # By not accepting low offers


class NegotiationEngine:
    """
    Auto-Negotiation Engine

    Features:
    - Rule-based automatic responses to offers
    - Smart counter-offer calculations
    - Buyer quality scoring
    - Urgency detection
    - Multi-round negotiation tracking
    """

    def __init__(self, db_path: str = "/data/vintedbot.db"):
        self.db_path = db_path

        # Default rules (can be customized per user)
        self.DEFAULT_RULES = [
            NegotiationRule(
                id="rule_1",
                name="Auto-accept high offers",
                condition=RuleCondition.PERCENTAGE_ABOVE,
                threshold=90.0,  # 90% or more of asking price
                action=ActionType.ACCEPT,
                priority=10,
                description="Automatically accept offers at 90%+ of asking price"
            ),
            NegotiationRule(
                id="rule_2",
                name="Reject very low offers",
                condition=RuleCondition.PERCENTAGE_ABOVE,
                threshold=50.0,  # Below 50% of asking price
                action=ActionType.REJECT,
                priority=9,
                description="Automatically reject offers below 50% of asking price"
            ),
            NegotiationRule(
                id="rule_3",
                name="Counter medium offers",
                condition=RuleCondition.PERCENTAGE_ABOVE,
                threshold=70.0,  # 70-89% of asking price
                action=ActionType.COUNTER,
                counter_percentage=85.0,  # Counter at 85%
                priority=5,
                description="Counter offers at 70-89% with 85% counter"
            ),
            NegotiationRule(
                id="rule_4",
                name="Accept if stale listing",
                condition=RuleCondition.ITEM_AGE,
                threshold=30.0,  # 30+ days old
                action=ActionType.ACCEPT,
                priority=8,
                description="Be more flexible with old listings (30+ days)"
            ),
        ]

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def analyze_offer(
        self,
        offer_id: str,
        listing_id: str,
        offer_amount: float,
        buyer_id: str,
        user_id: str
    ) -> OfferAnalysis:
        """
        Analyze an offer and recommend action

        Returns detailed analysis including:
        - Is the offer acceptable
        - Recommended action
        - Counter offer amount (if applicable)
        - Reasoning
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Get listing details
        cursor.execute("""
            SELECT price, title, category, created_at, views, likes
            FROM listings
            WHERE id = ? AND user_id = ?
        """, (listing_id, user_id))

        listing = cursor.fetchone()
        if not listing:
            conn.close()
            raise ValueError(f"Listing {listing_id} not found")

        list_price = listing['price']

        # Calculate minimum acceptable (70% by default, can be customized)
        min_acceptable = list_price * 0.70

        # Calculate discount
        discount_percentage = ((list_price - offer_amount) / list_price) * 100

        # Get buyer quality score
        buyer_score = await self._calculate_buyer_score(buyer_id, cursor)

        # Calculate urgency score
        urgency_score = self._calculate_urgency_score(
            listing['created_at'],
            listing['views'],
            listing['likes'],
            cursor,
            user_id
        )

        # Get user's rules
        rules = self._get_user_rules(user_id, cursor)

        # Determine recommended action
        recommended_action, counter_amount, reasoning = self._apply_rules(
            offer_amount=offer_amount,
            list_price=list_price,
            min_acceptable=min_acceptable,
            buyer_score=buyer_score,
            urgency_score=urgency_score,
            listing=listing,
            rules=rules
        )

        # Check if acceptable
        is_acceptable = offer_amount >= min_acceptable

        conn.close()

        return OfferAnalysis(
            offer_id=offer_id,
            listing_id=listing_id,
            offer_amount=offer_amount,
            list_price=list_price,
            min_acceptable=min_acceptable,
            discount_percentage=discount_percentage,
            is_acceptable=is_acceptable,
            recommended_action=recommended_action,
            counter_offer_amount=counter_amount,
            reasoning=reasoning,
            buyer_score=buyer_score,
            urgency_score=urgency_score
        )

    async def _calculate_buyer_score(
        self,
        buyer_id: str,
        cursor: sqlite3.Cursor
    ) -> float:
        """
        Calculate buyer quality score (0-1)

        Based on:
        - Number of completed purchases
        - Rating/feedback
        - Account age
        """
        # Get buyer's purchase history
        cursor.execute("""
            SELECT COUNT(*) as purchase_count
            FROM transactions
            WHERE buyer_id = ?
            AND status = 'completed'
        """, (buyer_id,))

        purchase_data = cursor.fetchone()
        purchase_count = purchase_data['purchase_count'] if purchase_data else 0

        # Score based on purchase history
        if purchase_count >= 10:
            score = 1.0  # Trusted buyer
        elif purchase_count >= 5:
            score = 0.8  # Good buyer
        elif purchase_count >= 2:
            score = 0.6  # Decent buyer
        elif purchase_count >= 1:
            score = 0.4  # New buyer with history
        else:
            score = 0.3  # Unknown buyer

        return score

    def _calculate_urgency_score(
        self,
        created_at: str,
        views: int,
        likes: int,
        cursor: sqlite3.Cursor,
        user_id: str
    ) -> float:
        """
        Calculate urgency to sell (0-1)

        Higher urgency = more willing to accept lower offers
        """
        # Days since created
        days_old = (datetime.utcnow() - datetime.fromisoformat(created_at)).days

        # Age component (older = more urgent)
        if days_old >= 60:
            age_urgency = 1.0
        elif days_old >= 30:
            age_urgency = 0.7
        elif days_old >= 14:
            age_urgency = 0.4
        else:
            age_urgency = 0.2

        # Interest component (low interest = more urgent)
        if views < 10:
            interest_urgency = 0.8
        elif views < 30:
            interest_urgency = 0.5
        else:
            interest_urgency = 0.2

        # Like rate component
        like_rate = likes / views if views > 0 else 0
        if like_rate < 0.05:
            like_urgency = 0.7
        else:
            like_urgency = 0.3

        # Combined urgency
        urgency = (
            age_urgency * 0.5 +
            interest_urgency * 0.3 +
            like_urgency * 0.2
        )

        return urgency

    def _get_user_rules(
        self,
        user_id: str,
        cursor: sqlite3.Cursor
    ) -> List[NegotiationRule]:
        """Get user's negotiation rules (or defaults)"""
        cursor.execute("""
            SELECT * FROM negotiation_rules
            WHERE user_id = ?
            AND enabled = 1
            ORDER BY priority DESC
        """, (user_id,))

        rows = cursor.fetchall()

        if rows:
            rules = []
            for row in rows:
                rules.append(NegotiationRule(
                    id=row['id'],
                    name=row['name'],
                    condition=RuleCondition(row['condition']),
                    threshold=row['threshold'],
                    action=ActionType(row['action']),
                    counter_percentage=row['counter_percentage'],
                    priority=row['priority'],
                    enabled=bool(row['enabled']),
                    description=row['description']
                ))
            return rules
        else:
            # Return defaults
            return self.DEFAULT_RULES

    def _apply_rules(
        self,
        offer_amount: float,
        list_price: float,
        min_acceptable: float,
        buyer_score: float,
        urgency_score: float,
        listing: sqlite3.Row,
        rules: List[NegotiationRule]
    ) -> Tuple[ActionType, Optional[float], str]:
        """
        Apply negotiation rules to determine action

        Returns: (action, counter_amount, reasoning)
        """
        offer_percentage = (offer_amount / list_price) * 100
        days_old = (datetime.utcnow() - datetime.fromisoformat(listing['created_at'])).days

        # Check rules in priority order
        for rule in sorted(rules, key=lambda r: r.priority, reverse=True):
            if not rule.enabled:
                continue

            matched = False
            context = ""

            if rule.condition == RuleCondition.PERCENTAGE_ABOVE:
                if rule.action == ActionType.ACCEPT and offer_percentage >= rule.threshold:
                    matched = True
                    context = f"Offer is {offer_percentage:.1f}% of asking price (≥{rule.threshold}%)"
                elif rule.action == ActionType.REJECT and offer_percentage < rule.threshold:
                    matched = True
                    context = f"Offer is {offer_percentage:.1f}% of asking price (<{rule.threshold}%)"
                elif rule.action == ActionType.COUNTER and offer_percentage >= rule.threshold:
                    matched = True
                    context = f"Offer is {offer_percentage:.1f}% of asking price"

            elif rule.condition == RuleCondition.ITEM_AGE:
                if days_old >= rule.threshold:
                    matched = True
                    context = f"Listing is {days_old} days old (≥{rule.threshold} days)"

            elif rule.condition == RuleCondition.BUYER_RATING:
                if buyer_score >= rule.threshold:
                    matched = True
                    context = f"Buyer quality score: {buyer_score:.2f}"

            elif rule.condition == RuleCondition.VIEWS_COUNT:
                if listing['views'] >= rule.threshold:
                    matched = True
                    context = f"{listing['views']} views"

            if matched:
                counter_amount = None
                reasoning = f"{rule.description}. {context}"

                if rule.action == ActionType.COUNTER:
                    counter_amount = list_price * (rule.counter_percentage / 100)
                    reasoning += f". Counter-offering at {rule.counter_percentage}% ({counter_amount:.2f}€)"

                # Adjust for urgency
                if urgency_score > 0.7 and rule.action == ActionType.REJECT:
                    # Override reject with counter if very urgent
                    counter_amount = min_acceptable
                    reasoning = f"Urgency override: {reasoning}. Countering at minimum acceptable ({counter_amount:.2f}€)"
                    return ActionType.COUNTER, counter_amount, reasoning

                return rule.action, counter_amount, reasoning

        # Default: manual review needed
        return ActionType.IGNORE, None, "No rules matched - manual review recommended"

    async def execute_offer_action(
        self,
        offer_id: str,
        analysis: OfferAnalysis,
        user_id: str
    ) -> Dict:
        """
        Execute the recommended action for an offer

        Returns the result of the action
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Log the action
        cursor.execute("""
            INSERT INTO offer_history (
                id, offer_id, listing_id, user_id,
                offer_amount, action, counter_amount,
                reasoning, buyer_score, urgency_score,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"hist_{datetime.utcnow().timestamp()}",
            offer_id,
            analysis.listing_id,
            user_id,
            analysis.offer_amount,
            analysis.recommended_action.value,
            analysis.counter_offer_amount,
            analysis.reasoning,
            analysis.buyer_score,
            analysis.urgency_score,
            datetime.utcnow().isoformat()
        ))

        conn.commit()

        result = {
            'offer_id': offer_id,
            'action': analysis.recommended_action.value,
            'reasoning': analysis.reasoning,
            'timestamp': datetime.utcnow().isoformat()
        }

        if analysis.recommended_action == ActionType.COUNTER:
            result['counter_amount'] = analysis.counter_offer_amount

        conn.close()

        return result

    async def get_negotiation_stats(
        self,
        user_id: str,
        days: int = 30
    ) -> NegotiationStats:
        """
        Get negotiation statistics for a user
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        since_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

        # Get offer history
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN action = 'accept' THEN 1 ELSE 0 END) as accepted,
                SUM(CASE WHEN action = 'reject' THEN 1 ELSE 0 END) as rejected,
                SUM(CASE WHEN action = 'counter' THEN 1 ELSE 0 END) as countered,
                SUM(CASE WHEN action = 'ignore' THEN 1 ELSE 0 END) as manual,
                AVG(CASE WHEN action = 'accept' THEN
                    ((l.price - oh.offer_amount) / l.price * 100)
                    ELSE NULL END) as avg_discount
            FROM offer_history oh
            LEFT JOIN listings l ON oh.listing_id = l.id
            WHERE oh.user_id = ?
            AND oh.created_at >= ?
        """, (user_id, since_date))

        stats = cursor.fetchone()

        total = stats['total'] or 0
        accepted = stats['accepted'] or 0
        rejected = stats['rejected'] or 0
        countered = stats['countered'] or 0
        manual = stats['manual'] or 0

        acceptance_rate = (accepted / total * 100) if total > 0 else 0
        avg_discount = stats['avg_discount'] or 0

        # Calculate revenue saved (rejected low offers)
        cursor.execute("""
            SELECT SUM(l.price - oh.offer_amount) as saved
            FROM offer_history oh
            LEFT JOIN listings l ON oh.listing_id = l.id
            WHERE oh.user_id = ?
            AND oh.action = 'reject'
            AND oh.created_at >= ?
        """, (user_id, since_date))

        saved_data = cursor.fetchone()
        revenue_saved = saved_data['saved'] or 0

        conn.close()

        return NegotiationStats(
            total_offers=total,
            auto_accepted=accepted,
            auto_rejected=rejected,
            auto_countered=countered,
            manual_needed=manual,
            acceptance_rate=acceptance_rate,
            avg_discount=avg_discount,
            revenue_saved=revenue_saved
        )

    async def create_rule(
        self,
        user_id: str,
        name: str,
        condition: RuleCondition,
        threshold: float,
        action: ActionType,
        counter_percentage: Optional[float] = None,
        priority: int = 5,
        description: str = ""
    ) -> NegotiationRule:
        """Create a new negotiation rule for user"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        rule_id = f"rule_{user_id}_{datetime.utcnow().timestamp()}"

        cursor.execute("""
            INSERT INTO negotiation_rules (
                id, user_id, name, condition, threshold,
                action, counter_percentage, priority,
                description, enabled, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (
            rule_id, user_id, name, condition.value, threshold,
            action.value, counter_percentage, priority,
            description, datetime.utcnow().isoformat()
        ))

        conn.commit()
        conn.close()

        return NegotiationRule(
            id=rule_id,
            name=name,
            condition=condition,
            threshold=threshold,
            action=action,
            counter_percentage=counter_percentage,
            priority=priority,
            enabled=True,
            description=description
        )

    async def get_user_rules_list(self, user_id: str) -> List[NegotiationRule]:
        """Get all rules for a user"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        rules = self._get_user_rules(user_id, cursor)

        conn.close()
        return rules

    async def update_rule(
        self,
        rule_id: str,
        user_id: str,
        **updates
    ) -> NegotiationRule:
        """Update a negotiation rule"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Build update query
        allowed_fields = ['name', 'threshold', 'counter_percentage', 'priority', 'enabled', 'description']
        set_parts = []
        values = []

        for field, value in updates.items():
            if field in allowed_fields:
                set_parts.append(f"{field} = ?")
                values.append(value)

        if not set_parts:
            raise ValueError("No valid fields to update")

        values.extend([rule_id, user_id])

        cursor.execute(f"""
            UPDATE negotiation_rules
            SET {', '.join(set_parts)}
            WHERE id = ? AND user_id = ?
        """, values)

        conn.commit()

        # Get updated rule
        cursor.execute("""
            SELECT * FROM negotiation_rules
            WHERE id = ? AND user_id = ?
        """, (rule_id, user_id))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise ValueError(f"Rule {rule_id} not found")

        return NegotiationRule(
            id=row['id'],
            name=row['name'],
            condition=RuleCondition(row['condition']),
            threshold=row['threshold'],
            action=ActionType(row['action']),
            counter_percentage=row['counter_percentage'],
            priority=row['priority'],
            enabled=bool(row['enabled']),
            description=row['description']
        )

    async def delete_rule(self, rule_id: str, user_id: str) -> bool:
        """Delete a negotiation rule"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM negotiation_rules
            WHERE id = ? AND user_id = ?
        """, (rule_id, user_id))

        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted
