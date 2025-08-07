# app/Schemas/platform.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class PlatformBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=50)
    status: str = Field(default="ACTIVE")
    url: Optional[str] = Field(None, max_length=200)
    provider: Optional[str] = Field(None, max_length=100)
    work_platform_id: Optional[str] = Field(None, max_length=100)
    products: Optional[Dict[str, Any]] = None

class PlatformCreate(PlatformBase):
    pass

class PlatformUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None)
    url: Optional[str] = Field(None, max_length=200)
    provider: Optional[str] = Field(None, max_length=100)  
    work_platform_id: Optional[str] = Field(None, max_length=100)
    products: Optional[Dict[str, Any]] = None

class PlatformResponse(PlatformBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class PlatformBrief(BaseModel):
    """Brief platform info for use in other responses"""
    id: str
    name: str
    logo_url: Optional[str] = None
    category: Optional[str] = None
    status: str
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class PlatformStats(BaseModel):
    """Platform statistics"""
    total_platforms: int
    platforms_by_category: Dict[str, int]
    platforms_by_status: Dict[str, int]
    active_platforms: int

# Platform product schemas for better structure
class PlatformProduct(BaseModel):
    name: str
    description: Optional[str] = None
    features: List[str] = []
    pricing: Optional[Dict[str, Any]] = None
    api_available: bool = False

class PlatformWithProducts(PlatformResponse):
    """Platform response with structured products"""
    structured_products: List[PlatformProduct] = []
    
    @field_validator('structured_products', mode='before')
    @classmethod
    def parse_products(cls, v, info):
        """Convert products JSON to structured format"""
        if 'products' in info.data and info.data['products']:
            products_data = info.data['products']
            if isinstance(products_data, dict) and 'products' in products_data:
                return [PlatformProduct(**product) for product in products_data['products']]
        return []