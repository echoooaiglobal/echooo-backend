# app/Services/OrderService.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import and_, desc, asc, func
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from app.Models.order_models import Order, OrderItem
from app.Schemas.order import OrderCreate, OrderUpdate, ShopifyWebhookOrder, OrderItemCreate
from app.Utils.Logger import logger

class OrderService:
    """Service for managing orders and order items"""

    @staticmethod
    def _normalize_properties(properties: Any) -> Optional[Dict[str, Any]]:
        """
        Convert Shopify properties from list format to dict format for storage
        
        Args:
            properties: Properties in any format (list, dict, or None)
            
        Returns:
            Optional[Dict[str, Any]]: Normalized properties as dict
        """
        if not properties:
            return None
        
        # If it's already a dict, return as-is
        if isinstance(properties, dict):
            return properties
        
        # If it's a list (Shopify format), convert to dict
        if isinstance(properties, list):
            result = {}
            for prop in properties:
                if isinstance(prop, dict) and 'name' in prop and 'value' in prop:
                    result[prop['name']] = prop['value']
            return result if result else None
        
        # For any other type, try to convert or return None
        try:
            return dict(properties) if properties else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _extract_primary_discount_code(webhook_data: ShopifyWebhookOrder) -> Optional[str]:
        """
        Extract the primary discount code from webhook data
        
        Args:
            webhook_data: Shopify webhook order data
            
        Returns:
            Optional[str]: Primary discount code if found
        """
        # Check discount_codes first
        if webhook_data.discount_codes and len(webhook_data.discount_codes) > 0:
            first_discount = webhook_data.discount_codes[0]
            if isinstance(first_discount, dict) and 'code' in first_discount:
                return first_discount['code']
            elif isinstance(first_discount, str):
                return first_discount
        
        # If no discount_codes, check discount_applications
        if webhook_data.discount_applications and len(webhook_data.discount_applications) > 0:
            first_application = webhook_data.discount_applications[0]
            if isinstance(first_application, dict):
                # Try different possible fields for the code
                return (first_application.get('title') or 
                       first_application.get('code') or 
                       first_application.get('description'))
        
        return None

    @staticmethod
    async def create_order_from_shopify_webhook(webhook_data: ShopifyWebhookOrder, db: Session) -> Order:
        """
        Create an order from Shopify webhook data
        Only creates orders that have a discount code applied
        
        Args:
            webhook_data: Shopify webhook order data
            db: Database session
            
        Returns:
            Order: Created order instance
        """
        try:
            # Extract primary discount code
            primary_discount_code = OrderService._extract_primary_discount_code(webhook_data)
            
            # Only process orders with discount codes
            if not primary_discount_code:
                logger.info(f"Order {webhook_data.id} has no discount code, skipping...")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Order must have a discount code to be processed"
                )
            
            # Check if order already exists
            existing_order = db.query(Order).filter(
                Order.shopify_order_id == str(webhook_data.id)
            ).first()
            
            if existing_order:
                logger.info(f"Order {webhook_data.id} already exists, updating...")
                return await OrderService.update_order_from_webhook(existing_order, webhook_data, db)
            
            # Extract customer information
            customer_data = webhook_data.customer or {}
            
            # Calculate shipping price from shipping_lines
            shipping_price = Decimal('0')
            if webhook_data.shipping_lines:
                for shipping_line in webhook_data.shipping_lines:
                    shipping_price += Decimal(str(shipping_line.get('price', '0')))
            
            # Create order data
            order_data = {
                'shopify_order_id': str(webhook_data.id),
                'order_number': str(webhook_data.order_number),
                'order_status_url': webhook_data.order_status_url,
                'customer_email': webhook_data.email or customer_data.get('email'),
                'customer_phone': webhook_data.phone or customer_data.get('phone'),
                'customer_first_name': customer_data.get('first_name'),
                'customer_last_name': customer_data.get('last_name'),
                'financial_status': webhook_data.financial_status,
                'fulfillment_status': webhook_data.fulfillment_status,
                'order_status': 'open',  # Default status for new orders
                'total_price': Decimal(str(webhook_data.total_price)),
                'subtotal_price': Decimal(str(webhook_data.subtotal_price)),
                'total_tax': Decimal(str(webhook_data.total_tax)),
                'total_discounts': Decimal(str(webhook_data.total_discounts)),
                'shipping_price': shipping_price,
                'currency': webhook_data.currency,
                'used_discount_code': primary_discount_code,  # Store primary discount code
                'discount_codes': webhook_data.discount_codes,
                'discount_applications': webhook_data.discount_applications,
                'shipping_address': webhook_data.shipping_address,
                'billing_address': webhook_data.billing_address,
                'shopify_created_at': datetime.fromisoformat(webhook_data.created_at.replace('Z', '+00:00')),
                'shopify_updated_at': datetime.fromisoformat(webhook_data.updated_at.replace('Z', '+00:00')),
                'processed_at': datetime.fromisoformat(webhook_data.processed_at.replace('Z', '+00:00')) if webhook_data.processed_at else None,
                'tags': webhook_data.tags,
                'note': webhook_data.note,
                'source_name': webhook_data.source_name,
            }
            
            # Create the order
            order = Order(**order_data)
            db.add(order)
            db.flush()  # Get the order ID
            
            # Create order items
            for line_item in webhook_data.line_items:
                order_item_data = {
                    'order_id': order.id,
                    'shopify_line_item_id': str(line_item.get('id')),
                    'shopify_product_id': str(line_item.get('product_id')) if line_item.get('product_id') else None,
                    'shopify_variant_id': str(line_item.get('variant_id')) if line_item.get('variant_id') else None,
                    'product_title': line_item.get('title', 'Unknown Product'),
                    'variant_title': line_item.get('variant_title'),
                    'vendor': line_item.get('vendor'),
                    'product_type': line_item.get('product_type'),
                    'sku': line_item.get('sku'),
                    'quantity': line_item.get('quantity', 1),
                    'price': Decimal(str(line_item.get('price', '0'))),
                    'total_discount': Decimal(str(line_item.get('total_discount', '0'))),
                    'properties': OrderService._normalize_properties(line_item.get('properties')),
                    'fulfillment_status': line_item.get('fulfillment_status'),
                    'fulfillable_quantity': line_item.get('fulfillable_quantity'),
                }
                
                order_item = OrderItem(**order_item_data)
                db.add(order_item)
            
            db.commit()
            db.refresh(order)
            
            logger.info(f"Successfully created order {order.order_number} from Shopify webhook with discount code: {primary_discount_code}")
            return order
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error creating order from webhook: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Order with Shopify ID {webhook_data.id} already exists"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating order from webhook: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create order from webhook"
            )

    @staticmethod
    async def update_order_from_webhook(order: Order, webhook_data: ShopifyWebhookOrder, db: Session) -> Order:
        """
        Update existing order from Shopify webhook data
        
        Args:
            order: Existing order to update
            webhook_data: Shopify webhook order data
            db: Database session
            
        Returns:
            Order: Updated order instance
        """
        try:
            # Extract primary discount code for updates
            primary_discount_code = OrderService._extract_primary_discount_code(webhook_data)
            
            # Update order fields
            order.financial_status = webhook_data.financial_status
            order.fulfillment_status = webhook_data.fulfillment_status
            order.total_price = Decimal(str(webhook_data.total_price))
            order.subtotal_price = Decimal(str(webhook_data.subtotal_price))
            order.total_tax = Decimal(str(webhook_data.total_tax))
            order.total_discounts = Decimal(str(webhook_data.total_discounts))
            order.discount_codes = webhook_data.discount_codes
            order.discount_applications = webhook_data.discount_applications
            order.shopify_updated_at = datetime.fromisoformat(webhook_data.updated_at.replace('Z', '+00:00'))
            order.tags = webhook_data.tags
            order.note = webhook_data.note
            
            # Update primary discount code if available
            if primary_discount_code:
                order.used_discount_code = primary_discount_code
            
            db.commit()
            db.refresh(order)
            
            logger.info(f"Successfully updated order {order.order_number} from Shopify webhook")
            return order
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating order from webhook: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update order from webhook"
            )

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
    ) -> Tuple[List[Order], int]:
        """
        Get all orders with pagination, sorting, and filtering
        
        Args:
            db: Database session
            page: Page number (1-indexed)
            per_page: Results per page
            sort_by: Column to sort by
            sort_order: Sort direction (asc/desc)
            status_filter: Filter by order status
            financial_status_filter: Filter by financial status
            discount_code_filter: Filter by discount code used
            
        Returns:
            Tuple[List[Order], int]: List of orders and total count
        """
        try:
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Build query
            query = db.query(Order).options(joinedload(Order.order_items))
            
            # Apply filters
            if status_filter:
                query = query.filter(Order.order_status == status_filter)
            if financial_status_filter:
                query = query.filter(Order.financial_status == financial_status_filter)
            if discount_code_filter:
                query = query.filter(Order.used_discount_code == discount_code_filter)
            
            # Get total count before pagination
            total = query.count()
            
            # Build sort criteria
            sort_column = getattr(Order, sort_by, Order.created_at)
            order = desc(sort_column) if sort_order.lower() == "desc" else asc(sort_column)
            
            # Apply pagination and sorting
            orders = query.order_by(order).offset(offset).limit(per_page).all()
            
            return orders, total
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_all_orders: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )

    @staticmethod
    async def get_order_by_id(order_id: uuid.UUID, db: Session) -> Order:
        """
        Get an order by ID
        
        Args:
            order_id: ID of the order
            db: Database session
            
        Returns:
            Order: Order instance
        """
        try:
            order = db.query(Order).options(joinedload(Order.order_items)).filter(Order.id == order_id).first()
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            return order
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting order by ID: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve order"
            )

    @staticmethod
    async def get_order_by_shopify_id(shopify_order_id: str, db: Session) -> Optional[Order]:
        """
        Get an order by Shopify order ID
        
        Args:
            shopify_order_id: Shopify order ID
            db: Database session
            
        Returns:
            Optional[Order]: Order instance if found
        """
        try:
            order = db.query(Order).filter(Order.shopify_order_id == shopify_order_id).first()
            return order
            
        except Exception as e:
            logger.error(f"Error getting order by Shopify ID: {str(e)}")
            return None

    @staticmethod
    async def get_orders_by_discount_code(
        db: Session,
        discount_code: str,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Order], int]:
        """
        Get orders that used a specific discount code
        
        Args:
            db: Database session
            discount_code: Discount code to search for
            page: Page number
            per_page: Results per page
            
        Returns:
            Tuple[List[Order], int]: Orders with the discount code and total count
        """
        try:
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Query orders by the used_discount_code field
            query = db.query(Order).filter(Order.used_discount_code == discount_code)
            
            # Get total count
            total = query.count()
            
            # Get results with pagination
            orders = query.order_by(Order.created_at.desc()).offset(offset).limit(per_page).all()
            
            return orders, total
            
        except Exception as e:
            logger.error(f"Error getting orders by discount code: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get orders by discount code"
            )

    @staticmethod
    async def get_order_statistics(db: Session) -> Dict[str, Any]:
        """
        Get order statistics and insights
        
        Args:
            db: Database session
            
        Returns:
            Dict[str, Any]: Order statistics
        """
        try:
            # Total orders and revenue
            total_orders = db.query(func.count(Order.id)).scalar()
            total_revenue = db.query(func.sum(Order.total_price)).scalar() or Decimal('0')
            
            # Orders by status
            status_stats = db.query(
                Order.order_status,
                func.count(Order.id)
            ).group_by(Order.order_status).all()
            
            # Orders by financial status
            financial_stats = db.query(
                Order.financial_status,
                func.count(Order.id)
            ).group_by(Order.financial_status).all()
            
            # Top discount codes usage (last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            top_discount_codes = db.query(
                Order.used_discount_code,
                func.count(Order.id).label('usage_count')
            ).filter(
                Order.created_at >= thirty_days_ago
            ).group_by(
                Order.used_discount_code
            ).order_by(
                func.count(Order.id).desc()
            ).limit(10).all()
            
            # Recent orders count (last 7 days)
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_orders_count = db.query(func.count(Order.id)).filter(
                Order.created_at >= seven_days_ago
            ).scalar()
            
            return {
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'orders_by_status': dict(status_stats),
                'orders_by_financial_status': dict(financial_stats),
                'top_discount_codes': [
                    {'code': code, 'usage_count': count}
                    for code, count in top_discount_codes
                ],
                'recent_orders_count': recent_orders_count
            }
            
        except Exception as e:
            logger.error(f"Error getting order statistics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve order statistics"
            )