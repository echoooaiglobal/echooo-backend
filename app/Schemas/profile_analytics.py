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
    account_url: Optional[str] = Field(None, max_length=200, description="Account URL")
    is_private: bool = Field(default=False, description="Whether the account is private")
    is_verified: bool = Field(default=False, description="Whether the account is verified")
    is_business: bool = Field(default=False, description="Whether the account is a business account")
    media_count: Optional[int] = Field(None, description="Number of media posts")
    followers_count: Optional[int] = Field(None, description="Number of followers")
    following_count: Optional[int] = Field(None, description="Number of following")
    subscribers_count: Optional[int] = Field(None, description="Number of subscribers")
    likes_count: Optional[int] = Field(None, description="Total likes count")
    biography: Optional[str] = Field(None, description="Account biography/bio")
    has_highlight_reels: bool = Field(default=False, description="Whether account has highlight reels")
    category_id: Optional[str] = Field(None, description="Category ID (UUID as string)")
    has_clips: bool = Field(default=False, description="Whether account has clips")
    additional_metrics: Optional[Dict[str, Any]] = Field(None, description="Additional metrics as JSON")
    claimed_status: Optional[str] = Field(None, max_length=50, description="Claim status (pending, verified, rejected)")
    verification_method: Optional[str] = Field(None, max_length=100, description="Verification method (email, dm, phone)")

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
    # social_account: Dict[str, Any]
    analytics_data: List[ProfileAnalyticsResponse]
    analytics_count: int

class ProfileAnalyticsWithSocialAccountResponse(BaseModel):
    """Response for creating analytics with social account"""
    social_account: Dict[str, Any]
    analytics_data: ProfileAnalyticsResponse
    message: str

# Custom Social Account Response for analytics (handles nullable influencer_id)
class SocialAccountForAnalyticsResponse(BaseModel):
    """Social account response that handles nullable influencer_id"""
    id: str
    influencer_id: Optional[str] = None  # Make this optional
    platform_id: str
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
    category_id: Optional[str] = None
    has_clips: bool = False
    additional_metrics: Optional[Dict[str, Any]] = None
    claimed_at: Optional[datetime] = None
    claimed_status: Optional[str] = None
    verification_method: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'influencer_id', 'platform_id', 'category_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        elif v is None:
            return None
        return v

# Analytics Existence Check Response
class AnalyticsExistsResponse(BaseModel):
    """Response for checking if analytics exist"""
    exists: bool = Field(..., description="Whether analytics exist for this platform account")
    platform_account_id: str = Field(..., description="The platform account ID that was checked")
    platform_id: Optional[str] = Field(None, description="Platform ID if provided")
    social_account_id: Optional[str] = Field(None, description="Social account ID if found")
    analytics_count: int = Field(0, description="Number of analytics records found")
    latest_analytics_date: Optional[datetime] = Field(None, description="Date of the latest analytics record")