# app/Models/order_models.py
import uuid
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, Text, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.Models.base import Base

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Shopify order details
    shopify_order_id = Column(String(100), unique=True, nullable=False, index=True)
    order_number = Column(String(50), nullable=False, index=True)
    order_status_url = Column(String(500), nullable=True)
    
    # Customer information
    customer_email = Column(String(255), nullable=True, index=True)
    customer_phone = Column(String(50), nullable=True)
    customer_first_name = Column(String(100), nullable=True)
    customer_last_name = Column(String(100), nullable=True)
    
    # Order status and financial details
    financial_status = Column(String(50), nullable=True)  # paid, pending, refunded, etc.
    fulfillment_status = Column(String(50), nullable=True)  # fulfilled, partial, pending, etc.
    order_status = Column(String(50), nullable=True)  # open, closed, cancelled
    
    # Pricing information
    total_price = Column(Numeric(10, 2), nullable=True)
    subtotal_price = Column(Numeric(10, 2), nullable=True)
    total_tax = Column(Numeric(10, 2), nullable=True)
    total_discounts = Column(Numeric(10, 2), nullable=True)
    shipping_price = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(10), nullable=False, default='USD')
    
    # Discount information
    used_discount_code = Column(String(100), nullable=False, index=True)  # Primary discount code used (REQUIRED)
    discount_codes = Column(JSON, nullable=True)  # Store array of discount codes with details (for reference)
    discount_applications = Column(JSON, nullable=True)  # Store discount application details
    
    # Shipping information
    shipping_address = Column(JSON, nullable=True)  # Store complete shipping address
    billing_address = Column(JSON, nullable=True)   # Store complete billing address
    
    # Order timestamps
    shopify_created_at = Column(DateTime(timezone=True), nullable=True)
    shopify_updated_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # System timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Additional order metadata
    tags = Column(String(500), nullable=True)  # Shopify tags
    note = Column(Text, nullable=True)  # Order notes
    source_name = Column(String(100), nullable=True)  # web, mobile_app, etc.
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = 'order_items'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    
    # Shopify line item details
    shopify_line_item_id = Column(String(100), nullable=True)
    shopify_product_id = Column(String(100), nullable=True, index=True)
    shopify_variant_id = Column(String(100), nullable=True, index=True)
    
    # Product information
    product_title = Column(String(255), nullable=False)
    variant_title = Column(String(255), nullable=True)
    vendor = Column(String(100), nullable=True)
    product_type = Column(String(100), nullable=True)
    sku = Column(String(100), nullable=True, index=True)
    
    # Quantity and pricing
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(Numeric(10, 2), nullable=False)
    total_discount = Column(Numeric(10, 2), nullable=True, default=0)
    
    # Product properties and customizations
    properties = Column(JSON, nullable=True)  # Custom properties/personalizations
    
    # Fulfillment details
    fulfillment_status = Column(String(50), nullable=True)
    fulfillable_quantity = Column(Integer, nullable=True)
    
    # System timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="order_items")