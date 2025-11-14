"""
API endpoints for Auto-Negotiation System
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional
from pydantic import BaseModel

from backend.negotiation.negotiation_engine import (
    NegotiationEngine,
    NegotiationRule,
    OfferAnalysis,
    NegotiationStats,
    ActionType,
    RuleCondition
)
from backend.core.auth import get_current_user

router = APIRouter(prefix="/negotiation", tags=["negotiation"])


# ============================================================================
# Request/Response Models
# ============================================================================

class AnalyzeOfferRequest(BaseModel):
    """Request to analyze an offer"""
    offer_id: str
    listing_id: str
    offer_amount: float
    buyer_id: str


class OfferAnalysisResponse(BaseModel):
    """Offer analysis response"""
    offer_id: str
    listing_id: str
    offer_amount: float
    list_price: float
    min_acceptable: float
    discount_percentage: float
    is_acceptable: bool
    recommended_action: str
    counter_offer_amount: Optional[float]
    reasoning: str
    buyer_score: float
    urgency_score: float

    class Config:
        from_attributes = True


class NegotiationRuleRequest(BaseModel):
    """Request to create/update a rule"""
    name: str
    condition: str
    threshold: float
    action: str
    counter_percentage: Optional[float] = None
    priority: int = 5
    description: str = ""


class NegotiationRuleResponse(BaseModel):
    """Negotiation rule response"""
    id: str
    name: str
    condition: str
    threshold: float
    action: str
    counter_percentage: Optional[float]
    priority: int
    enabled: bool
    description: str

    class Config:
        from_attributes = True


class NegotiationStatsResponse(BaseModel):
    """Negotiation statistics response"""
    total_offers: int
    auto_accepted: int
    auto_rejected: int
    auto_countered: int
    manual_needed: int
    acceptance_rate: float
    avg_discount: float
    revenue_saved: float


class ExecuteActionResponse(BaseModel):
    """Execute action response"""
    offer_id: str
    action: str
    reasoning: str
    counter_amount: Optional[float] = None
    timestamp: str


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/analyze", response_model=OfferAnalysisResponse)
async def analyze_offer(
    request: AnalyzeOfferRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Analyze an offer and get recommendation

    Returns:
    - Whether the offer is acceptable
    - Recommended action (accept/reject/counter/ignore)
    - Counter offer amount (if applicable)
    - Detailed reasoning
    - Buyer quality score
    - Urgency score
    """
    try:
        engine = NegotiationEngine()
        analysis = await engine.analyze_offer(
            offer_id=request.offer_id,
            listing_id=request.listing_id,
            offer_amount=request.offer_amount,
            buyer_id=request.buyer_id,
            user_id=current_user['id']
        )

        return OfferAnalysisResponse(
            offer_id=analysis.offer_id,
            listing_id=analysis.listing_id,
            offer_amount=analysis.offer_amount,
            list_price=analysis.list_price,
            min_acceptable=analysis.min_acceptable,
            discount_percentage=analysis.discount_percentage,
            is_acceptable=analysis.is_acceptable,
            recommended_action=analysis.recommended_action.value,
            counter_offer_amount=analysis.counter_offer_amount,
            reasoning=analysis.reasoning,
            buyer_score=analysis.buyer_score,
            urgency_score=analysis.urgency_score
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing offer: {str(e)}")


@router.post("/execute", response_model=ExecuteActionResponse)
async def execute_offer_action(
    request: AnalyzeOfferRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Analyze and execute the recommended action for an offer

    This is a convenience endpoint that:
    1. Analyzes the offer
    2. Executes the recommended action
    3. Logs the action in history
    """
    try:
        engine = NegotiationEngine()

        # Analyze
        analysis = await engine.analyze_offer(
            offer_id=request.offer_id,
            listing_id=request.listing_id,
            offer_amount=request.offer_amount,
            buyer_id=request.buyer_id,
            user_id=current_user['id']
        )

        # Execute
        result = await engine.execute_offer_action(
            offer_id=request.offer_id,
            analysis=analysis,
            user_id=current_user['id']
        )

        return ExecuteActionResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing action: {str(e)}")


@router.get("/stats", response_model=NegotiationStatsResponse)
async def get_negotiation_stats(
    days: int = 30,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get negotiation statistics

    Query params:
    - days: Number of days to look back (default: 30)

    Returns:
    - Total offers received
    - Auto-accepted/rejected/countered counts
    - Acceptance rate
    - Average discount given
    - Revenue saved by rejecting low offers
    """
    try:
        engine = NegotiationEngine()
        stats = await engine.get_negotiation_stats(
            user_id=current_user['id'],
            days=days
        )

        return NegotiationStatsResponse(
            total_offers=stats.total_offers,
            auto_accepted=stats.auto_accepted,
            auto_rejected=stats.auto_rejected,
            auto_countered=stats.auto_countered,
            manual_needed=stats.manual_needed,
            acceptance_rate=stats.acceptance_rate,
            avg_discount=stats.avg_discount,
            revenue_saved=stats.revenue_saved
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@router.get("/rules", response_model=List[NegotiationRuleResponse])
async def get_negotiation_rules(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get all negotiation rules for current user

    Returns list of rules sorted by priority (highest first)
    """
    try:
        engine = NegotiationEngine()
        rules = await engine.get_user_rules_list(user_id=current_user['id'])

        return [
            NegotiationRuleResponse(
                id=rule.id,
                name=rule.name,
                condition=rule.condition.value,
                threshold=rule.threshold,
                action=rule.action.value,
                counter_percentage=rule.counter_percentage,
                priority=rule.priority,
                enabled=rule.enabled,
                description=rule.description
            )
            for rule in rules
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting rules: {str(e)}")


@router.post("/rules", response_model=NegotiationRuleResponse)
async def create_negotiation_rule(
    request: NegotiationRuleRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a new negotiation rule

    Example rules:
    - Auto-accept offers at 95%+ of asking price
    - Reject offers below 60% of asking price
    - Counter offers at 70-89% with 85% counter
    - Be more flexible with old listings (30+ days)
    """
    try:
        engine = NegotiationEngine()
        rule = await engine.create_rule(
            user_id=current_user['id'],
            name=request.name,
            condition=RuleCondition(request.condition),
            threshold=request.threshold,
            action=ActionType(request.action),
            counter_percentage=request.counter_percentage,
            priority=request.priority,
            description=request.description
        )

        return NegotiationRuleResponse(
            id=rule.id,
            name=rule.name,
            condition=rule.condition.value,
            threshold=rule.threshold,
            action=rule.action.value,
            counter_percentage=rule.counter_percentage,
            priority=rule.priority,
            enabled=rule.enabled,
            description=rule.description
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating rule: {str(e)}")


@router.patch("/rules/{rule_id}", response_model=NegotiationRuleResponse)
async def update_negotiation_rule(
    rule_id: str,
    updates: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Update a negotiation rule

    Updatable fields:
    - name
    - threshold
    - counter_percentage
    - priority
    - enabled
    - description
    """
    try:
        engine = NegotiationEngine()
        rule = await engine.update_rule(
            rule_id=rule_id,
            user_id=current_user['id'],
            **updates
        )

        return NegotiationRuleResponse(
            id=rule.id,
            name=rule.name,
            condition=rule.condition.value,
            threshold=rule.threshold,
            action=rule.action.value,
            counter_percentage=rule.counter_percentage,
            priority=rule.priority,
            enabled=rule.enabled,
            description=rule.description
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating rule: {str(e)}")


@router.delete("/rules/{rule_id}")
async def delete_negotiation_rule(
    rule_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete a negotiation rule"""
    try:
        engine = NegotiationEngine()
        deleted = await engine.delete_rule(
            rule_id=rule_id,
            user_id=current_user['id']
        )

        if not deleted:
            raise HTTPException(status_code=404, detail="Rule not found")

        return {"ok": True, "message": "Rule deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting rule: {str(e)}")


@router.get("/templates/rules", response_model=List[NegotiationRuleResponse])
async def get_rule_templates():
    """
    Get pre-built rule templates that users can enable

    These are common negotiation strategies that users can activate
    """
    engine = NegotiationEngine()

    templates = [
        NegotiationRuleResponse(
            id="template_aggressive_accept",
            name="Agressif - Accepter à 90%+",
            condition="percentage_above",
            threshold=90.0,
            action="accept",
            counter_percentage=None,
            priority=10,
            enabled=False,
            description="Accepte automatiquement les offres à 90%+ du prix demandé"
        ),
        NegotiationRuleResponse(
            id="template_reject_lowball",
            name="Rejeter offres très basses (<50%)",
            condition="percentage_above",
            threshold=50.0,
            action="reject",
            counter_percentage=None,
            priority=9,
            enabled=False,
            description="Rejette automatiquement les offres en dessous de 50%"
        ),
        NegotiationRuleResponse(
            id="template_counter_medium",
            name="Contre-offre moyenne (70-89% → 85%)",
            condition="percentage_above",
            threshold=70.0,
            action="counter",
            counter_percentage=85.0,
            priority=5,
            enabled=False,
            description="Contre-offre à 85% pour les offres entre 70-89%"
        ),
        NegotiationRuleResponse(
            id="template_flexible_old",
            name="Flexible avec anciennes annonces (30j+)",
            condition="item_age",
            threshold=30.0,
            action="accept",
            counter_percentage=None,
            priority=8,
            enabled=False,
            description="Plus flexible avec les annonces de 30 jours ou plus"
        ),
    ]

    return templates
