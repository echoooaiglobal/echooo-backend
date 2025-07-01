# app/Http/Controllers/OrderController.py
from fastapi import HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import hmac
import hashlib
import json

from app.Services.OrderService import OrderService
from app.Schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse, OrderListResponse,
    ShopifyWebhookOrder, OrderStatsResponse
)
from app.Utils.Logger import logger
from config.settings import settings

class OrderController:
    """Controller for order management endpoints"""
    
    @staticmethod
    def _should_verify_signature() -> bool:
        """
        Determine if webhook signature should be verified
        Returns False in development/testing mode
        """
        # Skip verification if explicitly disabled
        if getattr(settings, 'DISABLE_WEBHOOK_SIGNATURE_VERIFICATION', True):
            logger.info("Webhook signature verification disabled by configuration")
            return False
        
        # Skip verification if no secret is configured
        if not hasattr(settings, 'SHOPIFY_WEBHOOK_SECRET') or not settings.SHOPIFY_WEBHOOK_SECRET:
            logger.info("Webhook signature verification skipped - no secret configured")
            return False
        
        # Skip verification in debug mode
        if getattr(settings, 'DEBUG', False):
            logger.info("Webhook signature verification skipped - debug mode enabled")
            return False
        
        return True

    @staticmethod
    async def shopify_webhook_handler(
        request: Request,
        background_tasks: BackgroundTasks,
        db: Session
    ) -> Dict[str, str]:
        """
        Handle Shopify order webhook
        Only processes orders that have discount codes
        
        Args:
            request: FastAPI request object
            background_tasks: Background tasks for async processing
            db: Database session
            
        Returns:
            Dict[str, str]: Success response
        """
        try:
            # Get raw body for signature verification
            body = await request.body()
            
            # Verify webhook signature (only if enabled and configured)
            if OrderController._should_verify_signature():
                signature = request.headers.get('X-Shopify-Hmac-Sha256')
                if not OrderController._verify_webhook_signature(body, signature, settings.SHOPIFY_WEBHOOK_SECRET):
                    logger.warning("Invalid Shopify webhook signature")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid webhook signature"
                    )
                logger.info("Webhook signature verified successfully")
            else:
                logger.info("Webhook signature verification skipped")
            
            # Parse webhook data
            webhook_data = json.loads(body.decode('utf-8'))
            
            # Validate and create order data
            shopify_order = ShopifyWebhookOrder(**webhook_data)
            
            # Quick check for discount codes before processing
            has_discount = (
                (shopify_order.discount_codes and len(shopify_order.discount_codes) > 0) or
                (shopify_order.discount_applications and len(shopify_order.discount_applications) > 0)
            )
            
            if not has_discount:
                logger.info(f"Order {shopify_order.id} has no discount codes, skipping processing")
                return {
                    "status": "skipped", 
                    "message": f"Order {shopify_order.id} has no discount codes, not processed"
                }
            
            # Process order in background to respond quickly to Shopify
            background_tasks.add_task(
                OrderController._process_order_webhook,
                shopify_order,
                db
            )
            
            logger.info(f"Received Shopify webhook for order {shopify_order.id} with discount codes")
            return {"status": "received", "message": "Order webhook processed successfully"}
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        except Exception as e:
            logger.error(f"Error processing Shopify webhook: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process webhook"
            )

    @staticmethod
    async def _process_order_webhook(shopify_order: ShopifyWebhookOrder, db: Session):
        """
        Background task to process order webhook
        
        Args:
            shopify_order: Validated Shopify order data
            db: Database session
        """
        try:
            await OrderService.create_order_from_shopify_webhook(shopify_order, db)
            logger.info(f"Successfully processed order webhook for order {shopify_order.id}")
        except HTTPException as e:
            if e.status_code == status.HTTP_400_BAD_REQUEST:
                logger.info(f"Order {shopify_order.id} skipped: {e.detail}")
            else:
                logger.error(f"Failed to process order webhook for order {shopify_order.id}: {e.detail}")
        except Exception as e:
            logger.error(f"Failed to process order webhook for order {shopify_order.id}: {str(e)}")

    @staticmethod
    def _verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
        """
        Verify Shopify webhook signature
        
        Args:
            body: Raw request body
            signature: Shopify signature header
            secret: Webhook secret
            
        Returns:
            bool: True if signature is valid
        """
        try:
            if not signature:
                return False
            
            # Calculate expected signature
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures securely
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False

    @staticmethod
    async def get_all_orders(
        db: Session,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        status_filter: Optional[str] = None,
        financial_status_filter: Optional[str] = None,
        discount_code_filter: Optional[str] = None
    ) -> OrderListResponse:
        """
        Get all orders with pagination and filtering
        
        Args:
            db: Database session
            page: Page number
            per_page: Results per page
            sort_by: Column to sort by
            sort_order: Sort direction
            status_filter: Filter by order status
            financial_status_filter: Filter by financial status
            discount_code_filter: Filter by discount code used
            
        Returns:
            OrderListResponse: Paginated order list
        """
        try:
            orders, total = await OrderService.get_all_orders(
                db, page, per_page, sort_by, sort_order, 
                status_filter, financial_status_filter, discount_code_filter
            )
            
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
            logger.error(f"Error in get_all_orders controller: {str(e)}")
            raise

    @staticmethod
    async def get_order(order_id: uuid.UUID, db: Session) -> OrderResponse:
        """
        Get a specific order by ID
        
        Args:
            order_id: Order UUID
            db: Database session
            
        Returns:
            OrderResponse: Order details
        """
        try:
            order = await OrderService.get_order_by_id(order_id, db)
            return OrderResponse.model_validate(order)
            
        except Exception as e:
            logger.error(f"Error in get_order controller: {str(e)}")
            raise

    @staticmethod
    async def get_order_by_shopify_id(shopify_order_id: str, db: Session) -> OrderResponse:
        """
        Get a specific order by Shopify order ID
        
        Args:
            shopify_order_id: Shopify order ID
            db: Database session
            
        Returns:
            OrderResponse: Order details
        """
        try:
            order = await OrderService.get_order_by_shopify_id(shopify_order_id, db)
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Order with Shopify ID {shopify_order_id} not found"
                )
            
            return OrderResponse.model_validate(order)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_order_by_shopify_id controller: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve order"
            )

    @staticmethod
    async def get_order_statistics(db: Session) -> OrderStatsResponse:
        """
        Get order statistics and insights
        
        Args:
            db: Database session
            
        Returns:
            OrderStatsResponse: Order statistics
        """
        try:
            stats = await OrderService.get_order_statistics(db)
            return OrderStatsResponse(**stats)
            
        except Exception as e:
            logger.error(f"Error in get_order_statistics controller: {str(e)}")
            raise

    @staticmethod
    async def search_orders(
        db: Session,
        search_term: str,
        page: int = 1,
        per_page: int = 20
    ) -> OrderListResponse:
        """
        Search orders by various criteria including discount codes
        
        Args:
            db: Database session
            search_term: Search term (order number, email, discount code, etc.)
            page: Page number
            per_page: Results per page
            
        Returns:
            OrderListResponse: Search results
        """
        try:
            from sqlalchemy import or_
            from app.Models.order_models import Order
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Build search query including discount code
            search_filter = or_(
                Order.order_number.ilike(f"%{search_term}%"),
                Order.customer_email.ilike(f"%{search_term}%"),
                Order.customer_first_name.ilike(f"%{search_term}%"),
                Order.customer_last_name.ilike(f"%{search_term}%"),
                Order.shopify_order_id.ilike(f"%{search_term}%"),
                Order.used_discount_code.ilike(f"%{search_term}%")  # Search by discount code
            )
            
            # Get total count
            total = db.query(Order).filter(search_filter).count()
            
            # Get results
            orders = db.query(Order).filter(search_filter)\
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
            logger.error(f"Error in search_orders controller: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search orders"
            )

    @staticmethod
    async def get_orders_by_discount_code(
        db: Session,
        discount_code: str,
        page: int = 1,
        per_page: int = 20
    ) -> OrderListResponse:
        """
        Get orders that used a specific discount code
        
        Args:
            db: Database session
            discount_code: Discount code to search for
            page: Page number
            per_page: Results per page
            
        Returns:
            OrderListResponse: Orders with the discount code
        """
        try:
            orders, total = await OrderService.get_orders_by_discount_code(
                db, discount_code, page, per_page
            )
            
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
            logger.error(f"Error in get_orders_by_discount_code controller: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get orders by discount code"
            )

    @staticmethod
    async def get_discount_code_analytics(db: Session) -> Dict[str, Any]:
        """
        Get analytics for discount code usage
        
        Args:
            db: Database session
            
        Returns:
            Dict[str, Any]: Discount code analytics
        """
        try:
            from sqlalchemy import func, desc
            from datetime import datetime, timedelta
            from app.Models.order_models import Order
            
            # Total unique discount codes used
            total_unique_codes = db.query(func.count(func.distinct(Order.used_discount_code))).scalar()
            
            # Most popular discount codes (all time)
            popular_codes = db.query(
                Order.used_discount_code,
                func.count(Order.id).label('usage_count'),
                func.sum(Order.total_price).label('total_revenue')
            ).group_by(
                Order.used_discount_code
            ).order_by(
                desc('usage_count')
            ).limit(20).all()
            
            # Recent discount code usage (last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_codes = db.query(
                Order.used_discount_code,
                func.count(Order.id).label('usage_count')
            ).filter(
                Order.created_at >= thirty_days_ago
            ).group_by(
                Order.used_discount_code
            ).order_by(
                desc('usage_count')
            ).limit(10).all()
            
            return {
                'total_unique_discount_codes': total_unique_codes,
                'most_popular_codes': [
                    {
                        'code': code,
                        'usage_count': count,
                        'total_revenue': float(revenue or 0)
                    }
                    for code, count, revenue in popular_codes
                ],
                'recent_popular_codes': [
                    {
                        'code': code,
                        'usage_count': count
                    }
                    for code, count in recent_codes
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in get_discount_code_analytics controller: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get discount code analytics"
            )