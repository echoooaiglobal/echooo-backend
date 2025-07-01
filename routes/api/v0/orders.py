# routes/api/v0/orders.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.Http.Controllers.OrderController import OrderController
from app.Models.auth_models import User
from app.Schemas.order import (
    OrderResponse, OrderListResponse, OrderStatsResponse
)
from app.Utils.Helpers import (
    get_current_active_user, has_permission, has_role
)
from config.database import get_db

router = APIRouter(prefix="/orders", tags=["Orders"])

# Shopify webhook endpoint (no authentication required)
@router.post("/webhooks/shopify", summary="Shopify Order Webhook")
async def shopify_order_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle Shopify order webhook
    
    This endpoint receives order data from Shopify webhooks and stores it in the database.
    Configure this URL in your Shopify webhook settings:
    - Event: Order creation, Order updated, Order paid
    - Format: JSON
    - URL: https://yourdomain.com/api/v0/orders/webhooks/shopify
    """
    return await OrderController.shopify_webhook_handler(request, background_tasks, db)

# Get all orders with pagination and filtering
@router.get("/", response_model=OrderListResponse, summary="Get All Orders")
async def get_all_orders(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    sort_by: str = Query("created_at", description="Column to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    status_filter: Optional[str] = Query(None, description="Filter by order status"),
    financial_status_filter: Optional[str] = Query(None, description="Filter by financial status"),
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
    """
    return await OrderController.get_all_orders(
        db, page, per_page, sort_by, sort_order, status_filter, financial_status_filter
    )

# Get a specific order by ID
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

# Get order by Shopify order ID
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

# Search orders
@router.get("/search/{search_term}", response_model=OrderListResponse, summary="Search Orders")
async def search_orders(
    search_term: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    current_user: User = Depends(has_permission("order:read")),
    db: Session = Depends(get_db)
):
    """
    Search orders by order number, customer email, customer name, or Shopify order ID
    
    - **search_term**: Term to search for in order details
    - **page**: Page number (starts from 1)
    - **per_page**: Number of results per page (1-100)
    """
    return await OrderController.search_orders(db, search_term, page, per_page)

# Get orders by discount code
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

# Get order statistics
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

# Additional endpoints for order management

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

# Get recent orders (last 7 days)
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
        from datetime import datetime, timedelta
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