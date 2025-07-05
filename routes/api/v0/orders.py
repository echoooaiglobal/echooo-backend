# routes/api/v0/orders.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import csv
import io

from app.Http.Controllers.OrderController import OrderController
from app.Models.auth_models import User
from app.Schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse, OrderListResponse, OrderStatsResponse
)
from app.Utils.Helpers import (
    get_current_active_user, has_permission, has_role
)
from config.database import get_db

router = APIRouter(prefix="/orders", tags=["Orders"])

# ============== WEBHOOK ENDPOINTS (NO AUTHENTICATION) ==============

@router.post("/webhooks/shopify", summary="Universal Shopify Order Webhook")
async def shopify_universal_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Universal Shopify webhook endpoint for all order operations
    
    Handles the following webhook topics:
    - orders/create: Create new orders
    - orders/updated: Update existing orders  
    - orders/paid: Update payment status
    - orders/fulfilled: Mark orders as fulfilled
    - orders/cancelled: Mark orders as cancelled
    - orders/delete: Delete orders
    
    Configure this URL in your Shopify webhook settings for all order events:
    URL: https://yourdomain.com/api/v0/orders/webhooks/shopify
    """
    return await OrderController.shopify_universal_webhook_handler(request, background_tasks, db)

# ============== MANUAL CRUD OPERATIONS (AUTHENTICATED) ==============

@router.post("/", response_model=OrderResponse, summary="Create Order Manually")
async def create_order_manually(
    order_data: OrderCreate,
    current_user: User = Depends(has_permission("order:create")),
    db: Session = Depends(get_db)
):
    """
    Manually create a new order (not from webhook)
    
    - **order_data**: Complete order information including items
    - Requires 'order:create' permission
    """
    return await OrderController.create_order_manually(order_data, db)

@router.put("/{order_id}", response_model=OrderResponse, summary="Update Order Manually")
async def update_order_manually(
    order_id: uuid.UUID,
    order_data: OrderUpdate,
    current_user: User = Depends(has_permission("order:update")),
    db: Session = Depends(get_db)
):
    """
    Manually update an existing order
    
    - **order_id**: The UUID of the order to update
    - **order_data**: Fields to update (only provided fields will be updated)
    - Requires 'order:update' permission
    """
    return await OrderController.update_order_manually(order_id, order_data, db)

@router.delete("/{order_id}", summary="Delete Order Manually")
async def delete_order_manually(
    order_id: uuid.UUID,
    current_user: User = Depends(has_permission("order:delete")),
    db: Session = Depends(get_db)
):
    """
    Manually delete an order
    
    - **order_id**: The UUID of the order to delete
    - Requires 'order:delete' permission
    - This will also delete all associated order items (cascade delete)
    """
    return await OrderController.delete_order_manually(order_id, db)

# ============== READ OPERATIONS (AUTHENTICATED) ==============

@router.get("/", response_model=OrderListResponse, summary="Get All Orders")
async def get_all_orders(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    sort_by: str = Query("created_at", description="Column to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    status_filter: Optional[str] = Query(None, description="Filter by order status"),
    financial_status_filter: Optional[str] = Query(None, description="Filter by financial status"),
    discount_code_filter: Optional[str] = Query(None, description="Filter by discount code"),
    current_user: User = Depends(has_permission("order:read")),
    db: Session = Depends(get_db)
):
    """
    Get all orders with pagination, sorting, and filtering
    
    - **page**: Page number (starts from 1)
    - **per_page**: Number of results per page (1-100)
    - **sort_by**: Column to sort by (created_at, order_number, total_price, etc.)
    - **sort_order**: Sort direction (asc or desc)
    - **status_filter**: Filter by order status (open, closed, cancelled)
    - **financial_status_filter**: Filter by financial status (paid, pending, refunded)
    - **discount_code_filter**: Filter by specific discount code
    """
    return await OrderController.get_all_orders(
        db, page, per_page, sort_by, sort_order, 
        status_filter, financial_status_filter, discount_code_filter
    )

@router.get("/{order_id}", response_model=OrderResponse, summary="Get Order by ID")
async def get_order(
    order_id: uuid.UUID,
    current_user: User = Depends(has_permission("order:read")),
    db: Session = Depends(get_db)
):
    """
    Get a specific order by its UUID
    
    - **order_id**: The UUID of the order to retrieve
    """
    return await OrderController.get_order(order_id, db)

@router.get("/shopify/{shopify_order_id}", response_model=OrderResponse, summary="Get Order by Shopify ID")
async def get_order_by_shopify_id(
    shopify_order_id: str,
    current_user: User = Depends(has_permission("order:read")),
    db: Session = Depends(get_db)
):
    """
    Get a specific order by its Shopify order ID
    
    - **shopify_order_id**: The Shopify order ID to search for
    """
    return await OrderController.get_order_by_shopify_id(shopify_order_id, db)

@router.get("/search/{search_term}", response_model=OrderListResponse, summary="Search Orders")
async def search_orders(
    search_term: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    current_user: User = Depends(has_permission("order:read")),
    db: Session = Depends(get_db)
):
    """
    Search orders by order number, customer email, customer name, discount code, or Shopify order ID
    
    - **search_term**: Term to search for in order details
    - **page**: Page number (starts from 1)
    - **per_page**: Number of results per page (1-100)
    """
    return await OrderController.search_orders(db, search_term, page, per_page)

@router.get("/discount/{discount_code}", response_model=OrderListResponse, summary="Get Orders by Discount Code")
async def get_orders_by_discount_code(
    discount_code: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    # current_user: User = Depends(has_permission("order:read")),
    db: Session = Depends(get_db)
):
    """
    Get all orders that used a specific discount code
    
    - **discount_code**: The discount code to search for
    - **page**: Page number (starts from 1)
    - **per_page**: Number of results per page (1-100)
    """
    return await OrderController.get_orders_by_discount_code(db, discount_code, page, per_page)

@router.get("/customer/{customer_email}", response_model=OrderListResponse, summary="Get Orders by Customer Email")
async def get_orders_by_customer_email(
    customer_email: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    current_user: User = Depends(has_permission("order:read")),
    db: Session = Depends(get_db)
):
    """
    Get all orders for a specific customer by email address
    
    - **customer_email**: The customer's email address
    - **page**: Page number (starts from 1)
    - **per_page**: Number of results per page (1-100)
    """
    try:
        from app.Models.order_models import Order
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get total count
        total = db.query(Order).filter(Order.customer_email == customer_email).count()
        
        # Get results
        orders = db.query(Order).filter(Order.customer_email == customer_email)\
            .order_by(Order.created_at.desc())\
            .offset(offset)\
            .limit(per_page)\
            .all()
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        return OrderListResponse(
            orders=[OrderResponse.model_validate(order) for order in orders],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get orders by customer email"
        )

@router.get("/recent/week", response_model=OrderListResponse, summary="Get Recent Orders")
async def get_recent_orders(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    current_user: User = Depends(has_permission("order:read")),
    db: Session = Depends(get_db)
):
    """
    Get orders from the last 7 days
    
    - **page**: Page number (starts from 1)
    - **per_page**: Number of results per page (1-100)
    """
    try:
        from app.Models.order_models import Order
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Date filter (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        # Get total count
        total = db.query(Order).filter(Order.created_at >= seven_days_ago).count()
        
        # Get results
        orders = db.query(Order).filter(Order.created_at >= seven_days_ago)\
            .order_by(Order.created_at.desc())\
            .offset(offset)\
            .limit(per_page)\
            .all()
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        return OrderListResponse(
            orders=[OrderResponse.model_validate(order) for order in orders],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recent orders"
        )

# ============== ANALYTICS AND STATISTICS ==============

@router.get("/analytics/stats", response_model=OrderStatsResponse, summary="Get Order Statistics")
async def get_order_statistics(
    current_user: User = Depends(has_permission("order:read")),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive order statistics and analytics
    
    Returns:
    - Total orders count
    - Total revenue
    - Orders breakdown by status
    - Orders breakdown by financial status
    - Top discount codes usage
    - Recent orders count (last 7 days)
    """
    return await OrderController.get_order_statistics(db)

@router.get("/analytics/discount-codes", summary="Get Discount Code Analytics")
async def get_discount_code_analytics(
    current_user: User = Depends(has_permission("order:read")),
    db: Session = Depends(get_db)
):
    """
    Get detailed analytics for discount code usage
    
    Returns:
    - Total unique discount codes used
    - Most popular discount codes (all time) with revenue
    - Recent popular discount codes (last 30 days)
    """
    return await OrderController.get_discount_code_analytics(db)

# ============== ORDER STATUS MANAGEMENT ==============

@router.patch("/{order_id}/fulfill", response_model=OrderResponse, summary="Mark Order as Fulfilled")
async def mark_order_fulfilled(
    order_id: uuid.UUID,
    fulfillment_status: str = Query("fulfilled", description="Fulfillment status"),
    current_user: User = Depends(has_permission("order:update")),
    db: Session = Depends(get_db)
):
    """
    Manually mark an order as fulfilled
    
    - **order_id**: The UUID of the order to fulfill
    - **fulfillment_status**: Fulfillment status (default: 'fulfilled')
    """
    try:
        from app.Services.OrderService import OrderService
        
        order = await OrderService.get_order_by_id(order_id, db)
        
        # Update fulfillment status
        order.fulfillment_status = fulfillment_status
        order.updated_at = datetime.utcnow()
        
        # Update order items fulfillment status
        for item in order.order_items:
            item.fulfillment_status = fulfillment_status
            item.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(order)
        
        return OrderResponse.model_validate(order)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark order as fulfilled"
        )

@router.patch("/{order_id}/cancel", response_model=OrderResponse, summary="Cancel Order")
async def cancel_order(
    order_id: uuid.UUID,
    cancel_reason: Optional[str] = Query(None, description="Reason for cancellation"),
    current_user: User = Depends(has_permission("order:update")),
    db: Session = Depends(get_db)
):
    """
    Manually cancel an order
    
    - **order_id**: The UUID of the order to cancel
    - **cancel_reason**: Optional reason for cancellation
    """
    try:
        from app.Services.OrderService import OrderService
        
        order = await OrderService.get_order_by_id(order_id, db)
        
        # Update order status to cancelled
        order.order_status = 'cancelled'
        order.cancelled_at = datetime.utcnow()
        order.cancel_reason = cancel_reason
        order.updated_at = datetime.utcnow()
        
        # Add cancellation info to notes
        cancellation_note = f"Order cancelled at {datetime.utcnow().isoformat()}"
        if cancel_reason:
            cancellation_note += f" - Reason: {cancel_reason}"
        
        if order.note:
            order.note += f"\n{cancellation_note}"
        else:
            order.note = cancellation_note
        
        db.commit()
        db.refresh(order)
        
        return OrderResponse.model_validate(order)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order"
        )

# ============== BULK OPERATIONS ==============

@router.post("/bulk/delete", summary="Bulk Delete Orders")
async def bulk_delete_orders(
    order_ids: List[uuid.UUID],
    current_user: User = Depends(has_permission("order:delete")),
    db: Session = Depends(get_db)
):
    """
    Delete multiple orders at once
    
    - **order_ids**: List of order UUIDs to delete
    - Requires 'order:delete' permission
    """
    try:
        from app.Models.order_models import Order
        
        deleted_count = 0
        errors = []
        
        for order_id in order_ids:
            try:
                order = db.query(Order).filter(Order.id == order_id).first()
                if order:
                    db.delete(order)
                    deleted_count += 1
                else:
                    errors.append(f"Order {order_id} not found")
            except Exception as e:
                errors.append(f"Failed to delete order {order_id}: {str(e)}")
        
        db.commit()
        
        return {
            "status": "completed",
            "deleted_count": deleted_count,
            "total_requested": len(order_ids),
            "errors": errors
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk delete"
        )

@router.patch("/bulk/update-status", summary="Bulk Update Order Status")
async def bulk_update_order_status(
    order_ids: List[uuid.UUID],
    new_status: str = Query(..., description="New order status"),
    current_user: User = Depends(has_permission("order:update")),
    db: Session = Depends(get_db)
):
    """
    Update status for multiple orders at once
    
    - **order_ids**: List of order UUIDs to update
    - **new_status**: New status to apply to all orders
    - Requires 'order:update' permission
    """
    try:
        from app.Models.order_models import Order
        
        updated_count = 0
        errors = []
        
        for order_id in order_ids:
            try:
                order = db.query(Order).filter(Order.id == order_id).first()
                if order:
                    order.order_status = new_status
                    order.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    errors.append(f"Order {order_id} not found")
            except Exception as e:
                errors.append(f"Failed to update order {order_id}: {str(e)}")
        
        db.commit()
        
        return {
            "status": "completed",
            "updated_count": updated_count,
            "total_requested": len(order_ids),
            "new_status": new_status,
            "errors": errors
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk status update"
        )

# ============== EXPORT FUNCTIONALITY ==============

@router.get("/export/csv", summary="Export Orders to CSV")
async def export_orders_csv(
    status_filter: Optional[str] = Query(None, description="Filter by order status"),
    financial_status_filter: Optional[str] = Query(None, description="Filter by financial status"),
    discount_code_filter: Optional[str] = Query(None, description="Filter by discount code"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(has_permission("order:read")),
    db: Session = Depends(get_db)
):
    """
    Export orders to CSV format with optional filters
    
    - **status_filter**: Filter by order status
    - **financial_status_filter**: Filter by financial status
    - **discount_code_filter**: Filter by discount code
    - **date_from**: Start date for date range filter
    - **date_to**: End date for date range filter
    """
    try:
        from app.Models.order_models import Order
        from fastapi.responses import StreamingResponse
        
        # Build query with filters
        query = db.query(Order)
        
        if status_filter:
            query = query.filter(Order.order_status == status_filter)
        if financial_status_filter:
            query = query.filter(Order.financial_status == financial_status_filter)
        if discount_code_filter:
            query = query.filter(Order.used_discount_code == discount_code_filter)
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Order.created_at >= date_from_obj)
        if date_to:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Order.created_at <= date_to_obj)
        
        orders = query.order_by(Order.created_at.desc()).all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Order Number', 'Shopify Order ID', 'Customer Email', 'Customer Name',
            'Order Status', 'Financial Status', 'Fulfillment Status',
            'Total Price', 'Currency', 'Discount Code', 'Created At', 'Cancelled At', 'Cancel Reason'
        ])
        
        # Write data
        for order in orders:
            customer_name = f"{order.customer_first_name or ''} {order.customer_last_name or ''}".strip()
            writer.writerow([
                order.order_number,
                order.shopify_order_id,
                order.customer_email or '',
                customer_name,
                order.order_status or '',
                order.financial_status or '',
                order.fulfillment_status or '',
                float(order.total_price) if order.total_price else 0,
                order.currency,
                order.used_discount_code,
                order.created_at.isoformat() if order.created_at else '',
                order.cancelled_at.isoformat() if order.cancelled_at else '',
                order.cancel_reason or ''
            ])
        
        output.seek(0)
        
        # Create streaming response
        def iter_csv():
            yield output.getvalue()
        
        filename = f"orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            iter_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export orders: {str(e)}"
        )