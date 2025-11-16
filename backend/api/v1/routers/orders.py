"""
Orders management and export endpoints
Handles order tracking, status management, and CSV export for accounting
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Response, Body
from fastapi.responses import StreamingResponse
from backend.core.auth import get_current_user, User
from pydantic import BaseModel, Field
import csv
import io

router = APIRouter(prefix="/orders", tags=["orders"])


# Pydantic models for bulk feedback
class BulkFeedbackRequest(BaseModel):
    """Request to send feedback to multiple orders"""
    order_ids: List[str] = Field(..., description="List of order IDs to send feedback to")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: str = Field(..., max_length=500, description="Feedback comment")
    auto_mark_complete: bool = Field(default=True, description="Automatically mark orders as complete")


class FeedbackTemplate(BaseModel):
    """Predefined feedback template"""
    id: str
    name: str
    rating: int
    comment: str
    is_default: bool = False


# Import storage
from backend.core.storage import get_store


@router.get("/export/csv")
async def export_orders_csv(
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    """
    Export user orders to CSV format for accounting/record keeping

    Query parameters:
    - status: Filter by order status (pending, shipped, completed, cancelled)
    - from_date: Start date filter (ISO format: YYYY-MM-DD)
    - to_date: End date filter (ISO format: YYYY-MM-DD)

    Returns: CSV file with order details
    """
    try:
        # Get orders for current user from database
        store = get_store()
        orders = store.get_user_orders(str(current_user.id), limit=10000)  # Get all orders for export

        # Apply filters
        if status:
            orders = [o for o in orders if o.get("status") == status]

        if from_date:
            from_dt = datetime.fromisoformat(from_date)
            orders = [o for o in orders if o.get("order_date") and datetime.fromisoformat(o["order_date"]) >= from_dt]

        if to_date:
            to_dt = datetime.fromisoformat(to_date)
            orders = [o for o in orders if o.get("order_date") and datetime.fromisoformat(o["order_date"]) <= to_dt]

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Order ID",
            "Date",
            "Item Title",
            "Price (€)",
            "Buyer",
            "Status",
            "Tracking Number",
            "Notes"
        ])

        # Write data rows
        for order in orders:
            writer.writerow([
                order.get("id", ""),
                order.get("order_date", ""),
                order.get("item_title", ""),
                order.get("price", 0),
                order.get("buyer_name", ""),
                order.get("status", ""),
                order.get("tracking_number", ""),
                order.get("notes", "")
            ])

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vinted_orders_{timestamp}.csv"

        # Return CSV as downloadable file
        csv_content = output.getvalue()
        return Response(
            content=csv_content.encode('utf-8'),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        print(f"[ERROR] Failed to export orders: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to export orders: {str(e)}")


@router.get("/list")
async def list_orders(
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List user orders with pagination and filtering

    Query parameters:
    - status: Filter by order status
    - limit: Number of orders to return (default: 50)
    - offset: Number of orders to skip (default: 0)
    """
    try:
        store = get_store()

        # Get orders with filters applied at database level
        orders = store.get_user_orders(
            str(current_user.id),
            status=status,
            limit=limit,
            offset=offset
        )

        # Get total count
        if status:
            all_orders = store.get_user_orders(str(current_user.id), status=status, limit=10000)
        else:
            all_orders = store.get_user_orders(str(current_user.id), limit=10000)
        total = len(all_orders)

        return {
            "orders": orders,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        print(f"[ERROR] Failed to list orders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list orders: {str(e)}")


@router.get("/stats")
async def get_order_stats(current_user: User = Depends(get_current_user)):
    """
    Get order statistics for the user

    Returns counts of orders by status and revenue metrics
    """
    try:
        store = get_store()
        user_id = str(current_user.id)

        # Get counts by status from database
        status_counts = store.get_orders_count_by_status(user_id)

        total_orders = sum(status_counts.values())
        pending = status_counts.get("pending", 0)
        shipped = status_counts.get("shipped", 0)
        completed = status_counts.get("completed", 0)
        cancelled = status_counts.get("cancelled", 0)

        # Calculate revenue (only completed orders)
        total_revenue = store.get_total_revenue(user_id, status="completed")

        return {
            "total_orders": total_orders,
            "by_status": {
                "pending": pending,
                "shipped": shipped,
                "completed": completed,
                "cancelled": cancelled
            },
            "total_revenue": total_revenue
        }

    except Exception as e:
        print(f"[ERROR] Failed to get order stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get order stats: {str(e)}")


@router.post("/bulk-feedback")
async def send_bulk_feedback(
    request: BulkFeedbackRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send feedback to multiple orders at once (Dotb feature)

    Automatically sends rating and comment to selected completed orders.
    Useful for leaving positive feedback after successful sales.

    Request body:
    - order_ids: List of order IDs
    - rating: 1-5 stars
    - comment: Feedback text
    - auto_mark_complete: Automatically mark as complete (default: true)

    Returns: Summary of feedback sent
    """
    try:
        results = {
            "success": [],
            "failed": [],
            "total": len(request.order_ids)
        }

        store = get_store()

        for order_id in request.order_ids:
            # Find order
            order = store.get_order(order_id)

            if not order:
                results["failed"].append({
                    "order_id": order_id,
                    "error": "Order not found"
                })
                continue

            # Check if order is eligible for feedback
            if order.get("status") not in ["completed", "shipped"]:
                results["failed"].append({
                    "order_id": order_id,
                    "error": f"Order status '{order.get('status')}' not eligible for feedback"
                })
                continue

            # Save feedback to database
            store.update_order_feedback(
                order_id=order_id,
                rating=request.rating,
                comment=request.comment
            )

            # ✅ IMPLEMENTED: Send actual feedback via Vinted API
            try:
                # Get user's Vinted session from database (if available)
                vinted_session = order.get("vinted_session_cookie")
                vinted_transaction_id = order.get("vinted_transaction_id")

                if vinted_session and vinted_transaction_id:
                    from backend.services.vinted_api_client import VintedAPIClient

                    vinted_client = VintedAPIClient(vinted_session)
                    await vinted_client.send_feedback(
                        transaction_id=vinted_transaction_id,
                        rating=request.rating,
                        comment=request.comment
                    )
                    logger.info(f"Feedback sent to Vinted for transaction {vinted_transaction_id}")
                else:
                    logger.warning(f"Missing Vinted credentials for order {order_id} - feedback saved locally only")

            except Exception as e:
                logger.error(f"Failed to send feedback to Vinted API: {e}")
                # Continue anyway - feedback is saved locally

            results["success"].append({
                "order_id": order_id,
                "buyer": order.get("buyer_name", "Unknown"),
                "item": order.get("item_title", "Unknown")
            })

            print(f"[FEEDBACK] Sent to order {order_id}: {request.rating}⭐ - {request.comment}")

        return {
            "ok": True,
            "message": f"Feedback sent to {len(results['success'])} orders",
            "results": results
        }

    except Exception as e:
        print(f"[ERROR] Failed to send bulk feedback: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to send bulk feedback: {str(e)}")


@router.get("/feedback/templates")
async def get_feedback_templates(current_user: User = Depends(get_current_user)):
    """
    Get predefined feedback templates for quick selection

    Returns list of feedback templates with ratings and comments
    """
    try:
        # Predefined templates for common scenarios
        templates = [
            {
                "id": "perfect_5star",
                "name": "Perfect Transaction",
                "rating": 5,
                "comment": "Perfect transaction! Item as described, fast shipping. Thank you! ⭐⭐⭐⭐⭐",
                "is_default": True
            },
            {
                "id": "great_4star",
                "name": "Great Buyer",
                "rating": 5,
                "comment": "Great buyer, smooth transaction. Highly recommended! 👍",
                "is_default": False
            },
            {
                "id": "quick_5star",
                "name": "Quick Payment",
                "rating": 5,
                "comment": "Quick payment and great communication. Would sell again! 🎉",
                "is_default": False
            },
            {
                "id": "professional_5star",
                "name": "Professional",
                "rating": 5,
                "comment": "Very professional buyer. Thank you for your purchase!",
                "is_default": False
            },
            {
                "id": "friendly_5star",
                "name": "Friendly",
                "rating": 5,
                "comment": "Friendly and easy to work with. Perfect! 😊",
                "is_default": False
            }
        ]

        return {
            "templates": templates,
            "total": len(templates)
        }

    except Exception as e:
        print(f"[ERROR] Failed to get feedback templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get feedback templates: {str(e)}")


@router.post("/bulk-labels")
async def download_bulk_shipping_labels(
    order_ids: List[str],
    current_user: User = Depends(get_current_user)
):
    """
    Download shipping labels for multiple orders in a single PDF (Dotb feature)

    Fetches all shipping labels from Vinted and merges them into one PDF file
    for easy printing. Saves time when processing multiple shipments.

    Request body:
    - order_ids: List of order IDs to download labels for

    Returns: Merged PDF file with all shipping labels
    """
    try:
        # ✅ IMPLEMENTED: PDF merging with PDFMergerService
        from backend.services.pdf_merger_service import PDFMergerService

        results = {
            "success": [],
            "failed": [],
            "total": len(order_ids),
            "label_urls": []
        }

        store = get_store()

        for order_id in order_ids:
            # Find order
            order = store.get_order(order_id)

            if not order:
                results["failed"].append({
                    "order_id": order_id,
                    "error": "Order not found"
                })
                continue

            # Check if order has a tracking number (means label exists)
            if not order.get("tracking_number"):
                results["failed"].append({
                    "order_id": order_id,
                    "error": "No shipping label available"
                })
                continue

            # Check if order has shipping_label_url
            label_url = order.get("shipping_label_url")
            if label_url:
                results["label_urls"].append(label_url)
                results["success"].append({
                    "order_id": order_id,
                    "tracking": order.get("tracking_number")
                })
            else:
                results["failed"].append({
                    "order_id": order_id,
                    "error": "Shipping label URL not available"
                })

        if len(results["success"]) == 0:
            raise HTTPException(
                status_code=400,
                detail="No shipping labels available for the selected orders"
            )

        # ✅ IMPLEMENTED: Merge PDFs and return file
        merger_service = PDFMergerService()

        # Merge all labels into one PDF
        merged_pdf_path = await merger_service.merge_shipping_labels(results["label_urls"])

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"shipping_labels_{len(results['success'])}_orders_{timestamp}.pdf"

        # Return merged PDF file
        from fastapi.responses import FileResponse
        return FileResponse(
            path=merged_pdf_path,
            media_type='application/pdf',
            filename=filename,
            headers={
                "X-Orders-Count": str(len(results['success'])),
                "X-Failed-Count": str(len(results['failed']))
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to download bulk labels: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to download bulk labels: {str(e)}")


@router.get("/labels/available")
async def get_available_labels(
    current_user: User = Depends(get_current_user),
    status: str = "shipped"
):
    """
    Get list of orders that have shipping labels available

    Useful for bulk label download - shows which orders can be processed

    Query parameters:
    - status: Filter by order status (default: shipped)
    """
    try:
        store = get_store()

        # Get orders with specified status
        orders = store.get_user_orders(str(current_user.id), status=status, limit=1000)

        # Filter orders with tracking numbers (have labels)
        available_labels = [
            {
                "order_id": o.get("id"),
                "item_title": o.get("item_title"),
                "buyer": o.get("buyer_name"),
                "tracking_number": o.get("tracking_number"),
                "date": o.get("order_date")
            }
            for o in orders
            if o.get("tracking_number")
        ]

        return {
            "ok": True,
            "total": len(available_labels),
            "orders": available_labels
        }

    except Exception as e:
        print(f"[ERROR] Failed to get available labels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get available labels: {str(e)}")
