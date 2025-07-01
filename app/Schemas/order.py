# app/Schemas/order.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from decimal import Decimal
import uuid

class ShippingAddressSchema(BaseModel):
    """Schema for shipping/billing address"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None

class DiscountCodeSchema(BaseModel):
    """Schema for discount code information"""
    code: Optional[str] = None
    amount: Optional[str] = None
    type: Optional[str] = None

class DiscountApplicationSchema(BaseModel):
    """Schema for discount application details"""
    type: Optional[str] = None
    value: Optional[str] = None
    value_type: Optional[str] = None
    allocation_method: Optional[str] = None
    target_selection: Optional[str] = None
    target_type: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None

class OrderItemBase(BaseModel):
    """Base schema for order items"""
    shopify_line_item_id: Optional[str] = None
    shopify_product_id: Optional[str] = None
    shopify_variant_id: Optional[str] = None
    product_title: str
    variant_title: Optional[str] = None
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    sku: Optional[str] = None
    quantity: int = 1
    price: Decimal
    total_discount: Optional[Decimal] = 0
    properties: Optional[Any] = None  # Can be dict, list, or any JSON structure
    fulfillment_status: Optional[str] = None
    fulfillable_quantity: Optional[int] = None

class OrderItemCreate(OrderItemBase):
    """Schema for creating order items"""
    pass

class OrderItemResponse(OrderItemBase):
    """Schema for order item responses"""
    id: str
    order_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', 'order_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class OrderBase(BaseModel):
    """Base schema for orders"""
    shopify_order_id: str
    order_number: str
    order_status_url: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_first_name: Optional[str] = None
    customer_last_name: Optional[str] = None
    financial_status: Optional[str] = None
    fulfillment_status: Optional[str] = None
    order_status: Optional[str] = None
    total_price: Optional[Decimal] = None
    subtotal_price: Optional[Decimal] = None
    total_tax: Optional[Decimal] = None
    total_discounts: Optional[Decimal] = None
    shipping_price: Optional[Decimal] = None
    currency: str = 'USD'
    used_discount_code: str = Field(..., description="Primary discount code used for this order")  # REQUIRED
    discount_codes: Optional[List[Dict[str, Any]]] = None
    discount_applications: Optional[List[Dict[str, Any]]] = None
    shipping_address: Optional[Dict[str, Any]] = None
    billing_address: Optional[Dict[str, Any]] = None
    shopify_created_at: Optional[datetime] = None
    shopify_updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    tags: Optional[str] = None
    note: Optional[str] = None
    source_name: Optional[str] = None

class OrderCreate(OrderBase):
    """Schema for creating orders"""
    order_items: List[OrderItemCreate] = []

class OrderUpdate(BaseModel):
    """Schema for updating orders"""
    financial_status: Optional[str] = None
    fulfillment_status: Optional[str] = None
    order_status: Optional[str] = None
    total_price: Optional[Decimal] = None
    subtotal_price: Optional[Decimal] = None
    total_tax: Optional[Decimal] = None
    total_discounts: Optional[Decimal] = None
    shipping_price: Optional[Decimal] = None
    used_discount_code: Optional[str] = None
    discount_codes: Optional[List[Dict[str, Any]]] = None
    discount_applications: Optional[List[Dict[str, Any]]] = None
    shopify_updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    tags: Optional[str] = None
    note: Optional[str] = None

class OrderResponse(OrderBase):
    """Schema for order responses"""
    id: str
    created_at: datetime
    updated_at: datetime
    order_items: List[OrderItemResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class OrderListResponse(BaseModel):
    """Schema for paginated order lists"""
    orders: List[OrderResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class ShopifyWebhookOrder(BaseModel):
    """Schema for Shopify webhook order payload"""
    id: int
    order_number: int
    order_status_url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    customer: Optional[Dict[str, Any]] = None
    financial_status: Optional[str] = None
    fulfillment_status: Optional[str] = None
    name: str
    total_price: str
    subtotal_price: str
    total_tax: str
    total_discounts: str
    currency: str
    discount_codes: Optional[List[Dict[str, Any]]] = []
    discount_applications: Optional[List[Dict[str, Any]]] = []
    shipping_address: Optional[Dict[str, Any]] = None
    billing_address: Optional[Dict[str, Any]] = None
    line_items: List[Dict[str, Any]] = []
    created_at: str
    updated_at: str
    processed_at: Optional[str] = None
    tags: Optional[str] = None
    note: Optional[str] = None
    source_name: Optional[str] = None
    shipping_lines: Optional[List[Dict[str, Any]]] = []

class OrderStatsResponse(BaseModel):
    """Schema for order statistics"""
    total_orders: int
    total_revenue: Decimal
    orders_by_status: Dict[str, int]
    orders_by_financial_status: Dict[str, int]
    top_discount_codes: List[Dict[str, Any]]
    recent_orders_count: int