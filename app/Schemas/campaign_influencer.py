# app/Schemas/campaign_influencer.py
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid
import re
from app.Schemas.common import PaginationInfo

# Brief schemas for related models
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
    logo_url: Optional[str] = None
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
    platform: Optional[PlatformBrief] = None
    
    @field_validator('id', 'platform_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Social account data schema (for input)
class SocialAccountData(BaseModel):
    id: str  # Platform-specific account ID
    username: str
    name: Optional[str] = None
    profileImage: Optional[str] = None
    followers: Optional[str] = None
    isVerified: Optional[bool] = False

# Campaign Influencer schemas - Based on screenshot structure
class CampaignInfluencerBase(BaseModel):
    campaign_list_id: str
    platform_id: str
    social_account_id: Optional[str] = None  # Make this optional for bulk creation
    status_id: Optional[str] = None
    is_assigned_to_agent: bool = False  # ADDED MISSING FIELD
    total_contact_attempts: int = 0
    collaboration_price: Optional[Decimal] = None  # Changed to Decimal for precision
    currency: Optional[str] = Field(default="USD", max_length=3)  # ADDED MISSING FIELD
    is_ready_for_onboarding: bool = False
    notes: Optional[str] = None

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        if v is not None:
            # Validate ISO 4217 currency code format (3 uppercase letters)
            if not re.match(r'^[A-Z]{3}$', v):
                raise ValueError('Currency must be a valid 3-letter ISO 4217 code (e.g., USD, EUR, GBP)')
        return v

class CampaignInfluencerCreate(CampaignInfluencerBase):
    # Optional field for social data (for bulk creation)
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

class CampaignInfluencerBulkCreate(BaseModel):
    campaign_list_id: str
    platform_id: str  # Required for bulk creation
    influencers: List[SocialAccountData]

class CampaignInfluencerUpdate(BaseModel):
    status_id: Optional[str] = None
    is_assigned_to_agent: Optional[bool] = None  # ADDED MISSING FIELD
    total_contact_attempts: Optional[int] = None
    collaboration_price: Optional[Decimal] = None  # Changed to Decimal
    currency: Optional[str] = Field(default=None, max_length=3)  # ADDED MISSING FIELD
    is_ready_for_onboarding: Optional[bool] = None
    onboarded_at: Optional[datetime] = None
    notes: Optional[str] = None

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        if v is not None:
            # Validate ISO 4217 currency code format (3 uppercase letters)
            if not re.match(r'^[A-Z]{3}$', v):
                raise ValueError('Currency must be a valid 3-letter ISO 4217 code (e.g., USD, EUR, GBP)')
        return v

# Separate update schemas for specific operations
class CampaignInfluencerPriceUpdate(BaseModel):
    """Schema specifically for updating collaboration price and currency"""
    collaboration_price: Optional[Decimal] = None
    currency: Optional[str] = Field(default=None, max_length=3)

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        if v is not None:
            if not re.match(r'^[A-Z]{3}$', v):
                raise ValueError('Currency must be a valid 3-letter ISO 4217 code (e.g., USD, EUR, GBP)')
        return v

class CampaignInfluencerStatusUpdate(BaseModel):
    """Schema specifically for status updates"""
    status_id: str = Field(..., description="New status ID")
    assigned_influencer_id: Optional[str] = Field(None, description="Assigned influencer ID to update")

    @field_validator('status_id', 'assigned_influencer_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if v is not None and isinstance(v, uuid.UUID):
            return str(v)
        return v

class CampaignInfluencerNotesUpdate(BaseModel):
    """Schema specifically for notes updates"""
    notes: Optional[str] = None

class CampaignInfluencerResponse(BaseModel):
    id: str
    campaign_list_id: str
    social_account_id: str
    status_id: str
    is_assigned_to_agent: bool  # ADDED MISSING FIELD
    total_contact_attempts: int
    collaboration_price: Optional[Decimal] = None  # Changed to Decimal
    currency: Optional[str] = None  # ADDED MISSING FIELD
    is_ready_for_onboarding: bool
    onboarded_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None  # ADDED MISSING FIELD
    
    # Related data populated by controller
    status: Optional[StatusBrief] = None
    social_account: Optional[SocialAccountBrief] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'campaign_list_id', 'social_account_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class BatchOperationResponse(BaseModel):
    message: str
    success_count: int
    total_requested: int
    errors: List[Dict[str, str]] = []

class CopyOperationResponse(BaseModel):
    message: str
    copied_count: int
    skipped_count: int
    total_processed: int
    errors: List[Dict[str, str]] = []

class CampaignInfluencersPaginatedResponse(BaseModel):
    influencers: List[CampaignInfluencerResponse]
    pagination: PaginationInfo
    
    model_config = {"from_attributes": True}

class UpdateSuccessResponse(BaseModel):
    """Standard success response for update operations"""
    success: bool = True
    message: str
    influencer_id: str