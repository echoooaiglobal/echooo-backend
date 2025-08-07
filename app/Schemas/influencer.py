# app/Schemas/influencer.py
from pydantic import BaseModel,ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class PlatformBase(BaseModel):
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    url: Optional[str] = None
    work_platform_id: Optional[str] = None
    products: Optional[Dict[str, Any]] = None

class PlatformCreate(PlatformBase):
    pass

class PlatformUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class PlatformResponse(PlatformBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None

class CategoryResponse(CategoryBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class InfluencerContactBase(BaseModel):
    platform_specific: bool = False
    platform_id: Optional[uuid.UUID] = None
    social_account_id: Optional[uuid.UUID] = None  # Added field
    role_id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    contact_type: str
    contact_value: str
    is_primary: bool = False

class InfluencerContactCreate(InfluencerContactBase):
    influencer_id: uuid.UUID

class InfluencerContactUpdate(BaseModel):
    platform_specific: Optional[bool] = None
    platform_id: Optional[uuid.UUID] = None
    social_account_id: Optional[uuid.UUID] = None  # Added field
    role_id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    contact_type: Optional[str] = None
    contact_value: Optional[str] = None
    is_primary: Optional[bool] = None

class InfluencerContactResponse(InfluencerContactBase):
    id: uuid.UUID
    influencer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SocialAccountBase(BaseModel):
    platform_id: uuid.UUID
    platform_account_id: str
    account_handle: str
    full_name: str
    profile_pic_url: Optional[str] = None
    profile_pic_url_hd: Optional[str] = None
    account_url: Optional[str] = None
    is_private: bool = False
    is_verified: bool = False
    is_business: bool = False
    media_count: Optional[int] = None
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    subscribers_count: Optional[int] = None
    likes_count: Optional[int] = None
    biography: Optional[str] = None
    has_highlight_reels: bool = False
    category_id: Optional[uuid.UUID] = None
    has_clips: bool = False
    additional_metrics: Optional[Dict[str, Any]] = None
    # New fields
    claimed_at: Optional[datetime] = None
    claimed_status: Optional[str] = None
    verification_method: Optional[str] = None

class SocialAccountCreate(SocialAccountBase):
    influencer_id: uuid.UUID

class SocialAccountCreate(SocialAccountBase):
    influencer_id: uuid.UUID

class SocialAccountUpdate(BaseModel):
    platform_account_id: Optional[str] = None
    account_handle: Optional[str] = None
    full_name: Optional[str] = None
    profile_pic_url: Optional[str] = None
    profile_pic_url_hd: Optional[str] = None
    account_url: Optional[str] = None
    is_private: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_business: Optional[bool] = None
    media_count: Optional[int] = None
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    subscribers_count: Optional[int] = None
    likes_count: Optional[int] = None
    biography: Optional[str] = None
    has_highlight_reels: Optional[bool] = None
    category_id: Optional[uuid.UUID] = None
    has_clips: Optional[bool] = None
    additional_metrics: Optional[Dict[str, Any]] = None
    # New fields
    claimed_at: Optional[datetime] = None
    claimed_status: Optional[str] = None
    verification_method: Optional[str] = None

class SocialAccountResponse(SocialAccountBase):
    id: uuid.UUID
    influencer_id: uuid.UUID
    platform: PlatformResponse
    category: Optional[CategoryResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InfluencerBase(BaseModel):
    user_id: Optional[uuid.UUID] = None

class InfluencerCreate(InfluencerBase):
    pass

class InfluencerUpdate(BaseModel):
    user_id: Optional[uuid.UUID] = None

class InfluencerResponse(InfluencerBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    social_accounts: List[SocialAccountResponse] = []
    contacts: List[InfluencerContactResponse] = []

    model_config = ConfigDict(from_attributes=True)