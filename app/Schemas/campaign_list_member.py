# app/Schemas/campaign_list_member.py (Updated)
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Brief schemas for related models (keeping existing ones)
class StatusBrief(BaseModel):
    id: str
    name: str
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class PlatformBrief(BaseModel):
    id: str
    name: str
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class SocialAccountBrief(BaseModel):
    id: str
    full_name: str
    platform_id: str
    account_handle: str
    followers_count: Optional[int] = None
    platform_account_id: Optional[str] = None
    is_verified: Optional[bool] = None
    profile_pic_url: Optional[str] = None
    is_private: Optional[bool] = None
    is_business: Optional[bool] = None
    media_count: Optional[int] = None
    following_count: Optional[int] = None
    subscribers_count: Optional[int] = None
    likes_count: Optional[int] = None
    account_url: Optional[str] = None
    additional_metrics: Optional[Dict[str, Any]] = None
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'platform_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Social account data schema (for input) - keeping existing
class SocialAccountData(BaseModel):
    id: str  # Platform-specific account ID
    username: str
    name: Optional[str] = None
    profileImage: Optional[str] = None
    followers: Optional[str] = None
    isVerified: Optional[bool] = False

# Campaign List Member schemas - UPDATED
class CampaignListMemberBase(BaseModel):
    list_id: str
    platform_id: str
    social_account_id: Optional[str] = None  # Make this optional
    status_id: Optional[str] = None
    contact_attempts: int = 0
    next_contact_at: Optional[datetime] = None
    collaboration_price: Optional[float] = None
    ready_to_onboard: bool = False  # New field
    notes: Optional[str] = None  # New field

class CampaignListMemberCreate(CampaignListMemberBase):
    # Optional field for social data
    social_data: Optional[Dict[str, Any]] = None
    
    # Add validator to ensure either social_account_id or social_data is provided
    @model_validator(mode='before')
    @classmethod
    def validate_social_info(cls, data):
        if isinstance(data, dict):
            social_account_id = data.get('social_account_id')
            social_data = data.get('social_data')
            
            if social_account_id is None and social_data is None:
                raise ValueError("Either social_account_id or social_data must be provided")
        
        return data

class CampaignListMemberBulkCreate(BaseModel):
    list_id: str
    platform_id: str
    members: List[SocialAccountData]

class CampaignListMemberUpdate(BaseModel):
    status_id: Optional[str] = None
    platform_id: Optional[str] = None  # Add missing field
    contact_attempts: Optional[int] = None
    last_contacted_at: Optional[datetime] = None  # Add missing field
    next_contact_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None  # Add missing field
    collaboration_price: Optional[float] = None
    ready_to_onboard: Optional[bool] = None  # New field
    notes: Optional[str] = None  # New field

class CampaignListMemberResponse(BaseModel):
    id: str
    list_id: str
    social_account_id: str
    platform_id: str
    status_id: str
    contact_attempts: int
    next_contact_at: Optional[datetime] = None
    collaboration_price: Optional[float] = None
    last_contacted_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    ready_to_onboard: bool  # New field
    onboarded_at: Optional[datetime] = None
    notes: Optional[str] = None  # New field
    created_at: datetime
    updated_at: datetime
    
    # These will be populated by the controller
    status: Optional[StatusBrief] = None
    platform: Optional[PlatformBrief] = None
    social_account: Optional[SocialAccountBrief] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'list_id', 'social_account_id', 'status_id', 'platform_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Keep existing pagination schemas
class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

# Update the response to include pagination
class CampaignListMembersPaginatedResponse(BaseModel):
    members: List[CampaignListMemberResponse]
    pagination: PaginationInfo
    
    model_config = {"from_attributes": True}