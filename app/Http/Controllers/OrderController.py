# app/Http/Controllers/OrderController.py
from fastapi import HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any, Optional
import uuid
import hmac
import hashlib
import json

# Import here to avoid circular imports
from app.Models.order_models import Order

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
    async def shopify_universal_webhook_handler(
        request: Request,
        background_tasks: BackgroundTasks,
        db: Session
    ) -> Dict[str, str]:
        """
        Universal Shopify webhook handler for all order operations
        Handles: creation, updates, fulfillment, cancellation
        
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
            
            # Get webhook topic from headers
            webhook_topic = request.headers.get('X-Shopify-Topic', '')
            logger.info(f"Received Shopify webhook with topic: {webhook_topic}")
            
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
            
            # Route to appropriate handler based on webhook topic
            if webhook_topic in ['orders/create', 'orders/updated', 'orders/paid']:
                return await OrderController._handle_order_creation_update(webhook_data, background_tasks, db)
            elif webhook_topic == 'orders/fulfilled':
                return await OrderController._handle_order_fulfillment(webhook_data, background_tasks, db)
            elif webhook_topic == 'orders/cancelled':
                return await OrderController._handle_order_cancellation(webhook_data, background_tasks, db)
            elif webhook_topic == 'orders/delete':
                return await OrderController._handle_order_deletion(webhook_data, background_tasks, db)
            else:
                logger.warning(f"Unhandled webhook topic: {webhook_topic}")
                return {"status": "ignored", "message": f"Webhook topic {webhook_topic} not handled"}
            
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
    async def _handle_order_creation_update(webhook_data: dict, background_tasks: BackgroundTasks, db: Session) -> Dict[str, str]:
        """Handle order creation and update webhooks"""
        try:
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
            
            # Process order in background
            background_tasks.add_task(
                OrderController._process_order_webhook,
                shopify_order,
                db
            )
            
            logger.info(f"Received Shopify webhook for order {shopify_order.id} with discount codes")
            return {"status": "received", "message": "Order webhook processed successfully"}
            
        except Exception as e:
            logger.error(f"Error handling order creation/update: {str(e)}")
            raise

    @staticmethod
    async def _handle_order_fulfillment(webhook_data: dict, background_tasks: BackgroundTasks, db: Session) -> Dict[str, str]:
        """Handle order fulfillment webhooks"""
        try:
            shopify_order_id = str(webhook_data.get('id'))
            fulfillment_status = webhook_data.get('fulfillment_status', 'fulfilled')
            
            # Process fulfillment in background
            background_tasks.add_task(
                OrderService.mark_order_as_fulfilled,
                shopify_order_id,
                fulfillment_status,
                db
            )
            
            logger.info(f"Order {shopify_order_id} marked for fulfillment processing")
            return {"status": "received", "message": f"Order fulfillment webhook processed for order {shopify_order_id}"}
            
        except Exception as e:
            logger.error(f"Error handling order fulfillment: {str(e)}")
            raise

    @staticmethod
    async def _handle_order_cancellation(webhook_data: dict, background_tasks: BackgroundTasks, db: Session) -> Dict[str, str]:
        """Handle order cancellation webhooks"""
        try:
            shopify_order_id = str(webhook_data.get('id'))
            cancelled_at = webhook_data.get('cancelled_at')
            cancel_reason = webhook_data.get('cancel_reason')
            
            # Process cancellation in background
            background_tasks.add_task(
                OrderService.mark_order_as_cancelled,
                shopify_order_id,
                cancelled_at,
                cancel_reason,
                db
            )
            
            logger.info(f"Order {shopify_order_id} marked for cancellation processing")
            return {"status": "received", "message": f"Order cancellation webhook processed for order {shopify_order_id}"}
            
        except Exception as e:
            logger.error(f"Error handling order cancellation: {str(e)}")
            raise

    @staticmethod
    async def _handle_order_deletion(webhook_data: dict, background_tasks: BackgroundTasks, db: Session) -> Dict[str, str]:
        """Handle order deletion webhooks"""
        try:
            shopify_order_id = str(webhook_data.get('id'))
            
            # Process deletion in background
            background_tasks.add_task(
                OrderService.delete_order_by_shopify_id,
                shopify_order_id,
                db
            )
            
            logger.info(f"Order {shopify_order_id} marked for deletion processing")
            return {"status": "received", "message": f"Order deletion webhook processed for order {shopify_order_id}"}
            
        except Exception as e:
            logger.error(f"Error handling order deletion: {str(e)}")
            raise

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

    # Manual CRUD Operations
    @staticmethod
    async def create_order_manually(order_data: OrderCreate, db: Session) -> OrderResponse:
        """
        Manually create an order (not from webhook)
        
        Args:
            order_data: Order creation data
            db: Database session
            
        Returns:
            OrderResponse: Created order
        """
        try:
            order = await OrderService.create_order_manually(order_data, db)
            return OrderResponse.model_validate(order)
        except Exception as e:
            logger.error(f"Error in create_order_manually controller: {str(e)}")
            raise

    @staticmethod
    async def update_order_manually(order_id: uuid.UUID, order_data: OrderUpdate, db: Session) -> OrderResponse:
        """
        Manually update an order
        
        Args:
            order_id: Order UUID
            order_data: Order update data
            db: Database session
            
        Returns:
            OrderResponse: Updated order
        """
        try:
            order = await OrderService.update_order_manually(order_id, order_data, db)
            return OrderResponse.model_validate(order)
        except Exception as e:
            logger.error(f"Error in update_order_manually controller: {str(e)}")
            raise

    @staticmethod
    async def delete_order_manually(order_id: uuid.UUID, db: Session) -> Dict[str, str]:
        """
        Manually delete an order
        
        Args:
            order_id: Order UUID
            db: Database session
            
        Returns:
            Dict[str, str]: Success message
        """
        try:
            await OrderService.delete_order_manually(order_id, db)
            return {"status": "success", "message": f"Order {order_id} deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_order_manually controller: {str(e)}")
            raise

    # Existing methods (keeping all your current functionality)
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
        """Get a specific order by ID"""
        try:
            order = await OrderService.get_order_by_id(order_id, db)
            return OrderResponse.model_validate(order)
        except Exception as e:
            logger.error(f"Error in get_order controller: {str(e)}")
            raise

    @staticmethod
    async def get_order_by_shopify_id(shopify_order_id: str, db: Session) -> OrderResponse:
        """Get a specific order by Shopify order ID"""
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
        """Get order statistics and insights"""
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
        """Search orders by various criteria including discount codes"""
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
                Order.used_discount_code.ilike(f"%{search_term}%")
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
        """Get orders that used a specific discount code"""
        try:
            
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # CRITICAL FIX: Add joinedload to fetch order_items
            search_filter = Order.used_discount_code.ilike(f"%{discount_code}%")
            
            # Get total count
            total = db.query(Order).filter(search_filter).count()
            
            # Get results with order_items loaded using joinedload
            orders = db.query(Order).options(joinedload(Order.order_items))\
                .filter(search_filter)\
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
            logger.error(f"Error in get_orders_by_discount_code controller: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get orders by discount code"
            )

    @staticmethod
    async def get_discount_code_analytics(db: Session) -> Dict[str, Any]:
        """Get analytics for discount code usage"""
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