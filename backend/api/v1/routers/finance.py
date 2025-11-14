"""
API endpoints for Financial Dashboard
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime

from backend.finance.finance_manager import (
    FinanceManager,
    TransactionType
)
from backend.core.auth import get_current_user

router = APIRouter(prefix="/finance", tags=["finance"])


# ============================================================================
# Request/Response Models
# ============================================================================

class RecordSaleRequest(BaseModel):
    amount: float
    listing_id: str
    shipping_cost: float = 0
    inventory_cost: float = 0


class RecordExpenseRequest(BaseModel):
    amount: float
    description: str
    category: str = "other"


class ProfitLossResponse(BaseModel):
    period_start: str
    period_end: str
    gross_revenue: float
    refunds: float
    net_revenue: float
    platform_fees: float
    payment_fees: float
    shipping_costs: float
    inventory_costs: float
    other_expenses: float
    total_costs: float
    gross_profit: float
    net_profit: float
    profit_margin: float


class TaxReportResponse(BaseModel):
    year: int
    gross_revenue: float
    deductible_expenses: float
    taxable_income: float
    estimated_tax: float
    transactions_count: int


class ForecastResponse(BaseModel):
    period: str
    forecasted_revenue: float
    forecasted_profit: float
    confidence: float
    based_on_days: int


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/sales")
async def record_sale(
    request: RecordSaleRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Record a sale

    Automatically calculates:
    - Vinted fees (5% + 0.70€)
    - Payment processing fees (~3%)
    - Net amount after all fees
    """
    try:
        manager = FinanceManager()
        transaction = await manager.record_sale(
            user_id=current_user['id'],
            amount=request.amount,
            listing_id=request.listing_id,
            shipping_cost=request.shipping_cost,
            inventory_cost=request.inventory_cost
        )

        return {
            'ok': True,
            'transaction_id': transaction.id,
            'amount': transaction.amount,
            'vinted_fee': transaction.vinted_fee,
            'payment_fee': transaction.payment_fee,
            'net_amount': transaction.net_amount
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording sale: {str(e)}")


@router.post("/expenses")
async def record_expense(
    request: RecordExpenseRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Record a business expense

    Categories: inventory, shipping, marketing, packaging, other
    """
    try:
        manager = FinanceManager()
        transaction = await manager.record_expense(
            user_id=current_user['id'],
            amount=request.amount,
            description=request.description,
            category=request.category
        )

        return {
            'ok': True,
            'transaction_id': transaction.id,
            'amount': transaction.amount,
            'category': transaction.category
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording expense: {str(e)}")


@router.get("/profit-loss", response_model=ProfitLossResponse)
async def get_profit_loss_statement(
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get Profit & Loss statement

    Query params:
    - period_start: ISO date (default: start of current month)
    - period_end: ISO date (default: now)
    """
    try:
        manager = FinanceManager()

        start = datetime.fromisoformat(period_start) if period_start else None
        end = datetime.fromisoformat(period_end) if period_end else None

        pl = await manager.get_profit_loss_statement(
            user_id=current_user['id'],
            period_start=start,
            period_end=end
        )

        return ProfitLossResponse(
            period_start=pl.period_start.isoformat(),
            period_end=pl.period_end.isoformat(),
            gross_revenue=pl.gross_revenue,
            refunds=pl.refunds,
            net_revenue=pl.net_revenue,
            platform_fees=pl.platform_fees,
            payment_fees=pl.payment_fees,
            shipping_costs=pl.shipping_costs,
            inventory_costs=pl.inventory_costs,
            other_expenses=pl.other_expenses,
            total_costs=pl.total_costs,
            gross_profit=pl.gross_profit,
            net_profit=pl.net_profit,
            profit_margin=pl.profit_margin
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating P&L: {str(e)}")


@router.get("/tax-report/{year}", response_model=TaxReportResponse)
async def get_tax_report(
    year: int,
    tax_rate: float = 0.20,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get tax report for a year

    Query params:
    - tax_rate: Your applicable tax rate (default: 0.20 for 20%)
    """
    try:
        manager = FinanceManager()
        report = await manager.get_tax_report(
            user_id=current_user['id'],
            year=year,
            tax_rate=tax_rate
        )

        return TaxReportResponse(
            year=year,
            gross_revenue=report.gross_revenue,
            deductible_expenses=report.deductible_expenses,
            taxable_income=report.taxable_income,
            estimated_tax=report.estimated_tax,
            transactions_count=report.transactions_count
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating tax report: {str(e)}")


@router.get("/forecast", response_model=ForecastResponse)
async def forecast_revenue(
    period: str = "next_month",
    current_user: Dict = Depends(get_current_user)
):
    """
    Forecast future revenue

    Query params:
    - period: "next_week", "next_month", "next_quarter"
    """
    try:
        if period not in ["next_week", "next_month", "next_quarter"]:
            raise HTTPException(status_code=400, detail="Invalid period. Use: next_week, next_month, or next_quarter")

        manager = FinanceManager()
        forecast = await manager.forecast_revenue(
            user_id=current_user['id'],
            period=period
        )

        return ForecastResponse(
            period=forecast.period,
            forecasted_revenue=forecast.forecasted_revenue,
            forecasted_profit=forecast.forecasted_profit,
            confidence=forecast.confidence,
            based_on_days=forecast.based_on_days
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error forecasting: {str(e)}")


@router.get("/summary")
async def get_financial_summary(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get comprehensive financial summary

    Returns:
    - Today's stats
    - This month's P&L
    - Year-to-date summary
    - Next month forecast
    """
    try:
        manager = FinanceManager()
        summary = await manager.get_financial_summary(current_user['id'])

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting summary: {str(e)}")


@router.get("/transactions")
async def get_transactions(
    transaction_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get transaction history

    Query params:
    - transaction_type: sale, refund, expense, fee, shipping, tax
    - start_date: ISO date
    - end_date: ISO date
    - limit: Max transactions to return (default: 50)
    """
    try:
        manager = FinanceManager()

        txn_type = TransactionType(transaction_type) if transaction_type else None
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        transactions = await manager.get_transactions(
            user_id=current_user['id'],
            transaction_type=txn_type,
            start_date=start,
            end_date=end,
            limit=limit
        )

        return [
            {
                'id': t.id,
                'type': t.transaction_type.value,
                'amount': t.amount,
                'description': t.description,
                'category': t.category,
                'listing_id': t.listing_id,
                'vinted_fee': t.vinted_fee,
                'payment_fee': t.payment_fee,
                'shipping_cost': t.shipping_cost,
                'net_amount': t.net_amount,
                'created_at': t.created_at.isoformat()
            }
            for t in transactions
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting transactions: {str(e)}")


@router.get("/expenses/breakdown")
async def get_expense_breakdown(
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get expense breakdown by category

    Query params:
    - period_start: ISO date (default: start of current month)
    - period_end: ISO date (default: now)
    """
    try:
        manager = FinanceManager()

        start = datetime.fromisoformat(period_start) if period_start else None
        end = datetime.fromisoformat(period_end) if period_end else None

        breakdown = await manager.get_expense_breakdown(
            user_id=current_user['id'],
            period_start=start,
            period_end=end
        )

        return breakdown

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting breakdown: {str(e)}")
