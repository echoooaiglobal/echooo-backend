# app/Schemas/agent_social_connection.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

# Platform Brief Schema
class PlatformBrief(BaseModel):
    id: str
    name: str
    logo_url: Optional[str] = None
    category: Optional[str] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Status Brief Schema
class StatusBrief(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# User Brief Schema
class UserBrief(BaseModel):
    id: str
    email: str
    full_name: str
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Agent Brief Schema
class AgentBrief(BaseModel):
    id: str
    assigned_user_id: str
    is_automation_enabled: bool
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'assigned_user_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Base Schemas
class AgentSocialConnectionBase(BaseModel):
    platform_user_id: str = Field(..., description="Unique identifier from the social platform")
    platform_username: str = Field(..., description="Username on the social platform")
    display_name: Optional[str] = Field(None, description="Display name on the social platform")
    profile_image_url: Optional[str] = Field(None, description="Profile image URL from the platform")

# Create Schema
class AgentSocialConnectionCreate(AgentSocialConnectionBase):
    user_id: str = Field(..., description="User ID who owns this connection")
    platform_id: str = Field(..., description="Platform ID (Instagram, Facebook, etc.)")
    access_token: Optional[str] = Field(None, description="OAuth access token (will be encrypted)")
    refresh_token: Optional[str] = Field(None, description="OAuth refresh token (will be encrypted)")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")
    scope: Optional[str] = Field(None, description="OAuth permissions granted")
    
    # Instagram/Facebook specific fields
    instagram_business_account_id: Optional[str] = Field(None, description="Instagram Business Account ID")
    facebook_page_id: Optional[str] = Field(None, description="Connected Facebook Page ID")
    facebook_page_access_token: Optional[str] = Field(None, description="Facebook Page access token")
    facebook_page_name: Optional[str] = Field(None, description="Facebook Page name")
    
    # Platform-specific data
    automation_capabilities: Optional[Dict[str, Any]] = Field(None, description="Platform-specific automation features")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional platform-specific data")

# Update Schema
class AgentSocialConnectionUpdate(BaseModel):
    platform_username: Optional[str] = None
    display_name: Optional[str] = None
    profile_image_url: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None
    instagram_business_account_id: Optional[str] = None
    facebook_page_id: Optional[str] = None
    facebook_page_access_token: Optional[str] = None
    facebook_page_name: Optional[str] = None
    automation_capabilities: Optional[Dict[str, Any]] = None
    playwright_session_data: Optional[Dict[str, Any]] = None
    automation_error_count: Optional[int] = None
    last_error_message: Optional[str] = None
    is_active: Optional[bool] = None
    additional_data: Optional[Dict[str, Any]] = None
    status_id: Optional[str] = None

# Response Schemas
class AgentSocialConnectionResponse(AgentSocialConnectionBase):
    id: str
    user_id: str
    platform_id: str
    expires_at: Optional[datetime] = None
    last_oauth_check_at: Optional[datetime] = None
    scope: Optional[str] = None
    instagram_business_account_id: Optional[str] = None
    facebook_page_id: Optional[str] = None
    facebook_page_name: Optional[str] = None
    automation_capabilities: Optional[Dict[str, Any]] = None
    last_automation_use_at: Optional[datetime] = None
    automation_error_count: int
    last_error_message: Optional[str] = None
    last_error_at: Optional[datetime] = None
    is_active: bool
    additional_data: Optional[Dict[str, Any]] = None
    status_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'user_id', 'platform_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Detailed Response with Relations
class AgentSocialConnectionDetailResponse(AgentSocialConnectionResponse):
    user: Optional[UserBrief] = None
    platform: Optional[PlatformBrief] = None
    agent: Optional[AgentBrief] = None
    status: Optional[StatusBrief] = None

# Paginated Response
class AgentSocialConnectionsPaginatedResponse(BaseModel):
    connections: List[AgentSocialConnectionDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# Platform Connection Status
class PlatformConnectionStatus(BaseModel):
    platform_id: str
    platform_name: str
    is_connected: bool
    connection_count: int
    active_connections: int
    last_connected: Optional[datetime] = None

class UserPlatformConnectionsStatus(BaseModel):
    user_id: str
    platforms: List[PlatformConnectionStatus]
    total_connections: int
    active_connections: int

# OAuth Token Validation
class TokenValidationRequest(BaseModel):
    connection_id: str

class TokenValidationResponse(BaseModel):
    connection_id: str
    is_valid: bool
    expires_at: Optional[datetime] = None
    expires_in_hours: Optional[float] = None
    needs_renewal: bool
    last_check: datetime

# Automation Control
class AutomationToggleRequest(BaseModel):
    connection_id: str
    enabled: bool

class AutomationStatusResponse(BaseModel):
    connection_id: str
    is_automation_enabled: bool
    automation_capabilities: Optional[Dict[str, Any]] = None
    last_automation_use: Optional[datetime] = None
    error_count: int
    last_error: Optional[str] = None

# Bulk Operations
class BulkConnectionUpdate(BaseModel):
    connection_ids: List[str]
    update_data: AgentSocialConnectionUpdate

class BulkOperationResponse(BaseModel):
    success_count: int
    failed_count: int
    errors: List[Dict[str, Any]] = []

# Platform-Specific Schemas for Instagram
class InstagramConnectionData(BaseModel):
    business_account_id: str
    page_id: Optional[str] = None
    page_name: Optional[str] = None
    followers_count: Optional[int] = None
    media_count: Optional[int] = None
    
class InstagramProfileInfo(BaseModel):
    account_id: str
    username: str
    name: Optional[str] = None
    biography: Optional[str] = None
    followers_count: int
    follows_count: int
    media_count: int
    profile_picture_url: Optional[str] = None
    website: Optional[str] = None
    is_business_account: bool
    is_professional_account: bool

# Platform-Specific Schemas for WhatsApp
class WhatsAppConnectionData(BaseModel):
    phone_number: str
    display_name: Optional[str] = None
    business_profile: Optional[Dict[str, Any]] = None

# Platform-Specific Schemas for TikTok
class TikTokConnectionData(BaseModel):
    open_id: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    likes_count: Optional[int] = None

# Generic Platform Connection Request
class PlatformConnectionRequest(BaseModel):
    platform_id: str
    oauth_code: Optional[str] = None
    oauth_state: Optional[str] = None
    platform_specific_data: Optional[Dict[str, Any]] = None

# Connection Health Check
class ConnectionHealthCheck(BaseModel):
    connection_id: str
    platform_name: str
    is_healthy: bool
    last_successful_operation: Optional[datetime] = None
    issues: List[str] = []
    recommendations: List[str] = []

class SystemHealthReport(BaseModel):
    total_connections: int
    healthy_connections: int
    unhealthy_connections: int
    platforms_status: List[Dict[str, Any]]
    last_check: datetime