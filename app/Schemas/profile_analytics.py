# app/Schemas/profile_analytics.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

# Social Account Data Schema for creating with analytics
class SocialAccountData(BaseModel):
    """Social account data for creating/updating with analytics"""
    platform_id: str = Field(..., description="Platform ID (UUID as string)")
    platform_account_id: str = Field(..., min_length=1, max_length=255, description="Platform-specific account ID")
    account_handle: str = Field(..., min_length=1, max_length=100, description="Social media account handle")
    full_name: str = Field(..., min_length=1, max_length=150, description="Full name of the account holder")
    profile_pic_url: Optional[str] = Field(None, max_length=255, description="Profile picture URL")
    profile_pic_url_hd: Optional[str] = Field(None, max_length=255, description="HD profile picture URL")
    bio: Optional[str] = Field(None, description="Account bio/description")
    website_url: Optional[str] = Field(None, max_length=255, description="Website URL")
    is_verified: bool = Field(default=False, description="Whether the account is verified")
    is_private: bool = Field(default=False, description="Whether the account is private")
    category_id: Optional[str] = Field(None, description="Category ID (UUID as string)")

# Create Analytics with Social Account
class ProfileAnalyticsWithSocialAccountCreate(BaseModel):
    """Schema for creating profile analytics along with social account"""
    social_account_data: SocialAccountData = Field(..., description="Social account information")
    analytics: Dict[str, Any] = Field(..., description="Complete analytics object as JSON")

# Basic Analytics Schemas
class ProfileAnalyticsBase(BaseModel):
    social_account_id: str = Field(..., description="Social account ID (UUID as string)")
    analytics: Dict[str, Any] = Field(..., description="Complete analytics object as JSON")

class ProfileAnalyticsCreate(ProfileAnalyticsBase):
    """Schema for creating profile analytics directly"""
    pass

class ProfileAnalyticsUpdate(BaseModel):
    """Schema for updating profile analytics"""
    analytics: Optional[Dict[str, Any]] = Field(None, description="Complete analytics object as JSON")

class ProfileAnalyticsResponse(ProfileAnalyticsBase):
    """Schema for profile analytics response"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    # Related data
    social_account: Optional[Dict[str, Any]] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'social_account_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class ProfileAnalyticsBrief(BaseModel):
    """Brief profile analytics info for use in other responses"""
    id: str
    social_account_id: str
    created_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'social_account_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class ProfileAnalyticsListResponse(BaseModel):
    """Response for paginated profile analytics lists"""
    analytics: List[ProfileAnalyticsResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class ProfileAnalyticsStatsResponse(BaseModel):
    """Response for profile analytics statistics"""
    total_profiles: int
    profiles_by_platform: Dict[str, int]
    recent_analytics: List[ProfileAnalyticsBrief]
    top_platforms: List[Dict[str, Any]]

class SocialAccountWithAnalyticsResponse(BaseModel):
    """Response for social account with its analytics"""
    social_account: Dict[str, Any]
    analytics: List[ProfileAnalyticsResponse]
    analytics_count: int

class ProfileAnalyticsWithSocialAccountResponse(BaseModel):
    """Response for creating analytics with social account"""
    social_account: Dict[str, Any]
    analytics: ProfileAnalyticsResponse
    message: str