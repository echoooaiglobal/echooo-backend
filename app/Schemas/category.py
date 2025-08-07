# app/Schemas/category.py
from pydantic import BaseModel, field_validator
import uuid
from typing import Optional, List
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None  # UUID as string

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: str  # UUID as string
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }
    
    @field_validator('id', 'parent_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class CategoryWithSubsResponse(CategoryResponse):
    subcategories: List['CategoryResponse'] = []
    
    model_config = {
        "from_attributes": True
    }