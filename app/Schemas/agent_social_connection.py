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

# =============================================================================
# OAUTH FLOW SCHEMAS
# =============================================================================

class PlatformConnectionInitiateRequest(BaseModel):
    """Schema for initiating platform connection (OAuth flow)"""
    platform_id: str = Field(..., description="Platform ID to connect to")
    redirect_url: Optional[str] = Field(None, description="Custom redirect URL after OAuth completion")
    additional_scopes: Optional[List[str]] = Field(None, description="Additional OAuth scopes to request")

class OAuthInitiateResponse(BaseModel):
    """Response from OAuth initiation"""
    authorization_url: str = Field(..., description="URL for user to visit for OAuth authorization")
    state: str = Field(..., description="OAuth state parameter for security")
    platform: str = Field(..., description="Platform name being connected")
    expires_in: int = Field(default=600, description="State expiration time in seconds")
    instructions: str = Field(..., description="Instructions for user")

class OAuthCallbackResponse(BaseModel):
    """Response from OAuth callback processing"""
    success: bool = Field(..., description="Whether OAuth was successful")
    connection_id: Optional[str] = Field(None, description="Created connection ID if successful")
    platform: str = Field(..., description="Platform name")
    username: Optional[str] = Field(None, description="Connected account username")
    message: str = Field(..., description="Status message")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    redirect_url: str = Field(..., description="Frontend URL to redirect to")

class OAuthStatusResponse(BaseModel):
    """OAuth status check response"""
    status: str = Field(..., description="OAuth status: pending, completed, failed, expired")
    connection_id: Optional[str] = Field(None, description="Connection ID if completed")
    platform: str = Field(..., description="Platform name")
    created_at: Optional[datetime] = Field(None, description="Connection creation time")
    error_message: Optional[str] = Field(None, description="Error message if failed")

# =============================================================================
# EXISTING SCHEMAS (Updated)
# =============================================================================

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
    additional_data: Optional[Dict[str, Any]] = None

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
    automation_error_count: int = 0
    last_error_message: Optional[str] = None
    last_error_at: Optional[datetime] = None
    is_active: bool = True
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

class AgentSocialConnectionDetailResponse(AgentSocialConnectionResponse):
    """Detailed response with related entities"""
    user: Optional[UserBrief] = None
    platform: Optional[PlatformBrief] = None
    agent: Optional[AgentBrief] = None
    status: Optional[StatusBrief] = None

class AgentSocialConnectionsPaginatedResponse(BaseModel):
    """Paginated list of connections"""
    items: List[AgentSocialConnectionDetailResponse]
    total: int
    page: int
    size: int
    pages: int

class UserPlatformConnectionsStatus(BaseModel):
    """User's connection status across platforms"""
    user_id: str
    total_connections: int
    active_connections: int
    platforms: List[Dict[str, Any]]
    last_connection_date: Optional[datetime] = None
    
    @field_validator('user_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# =============================================================================
# LEGACY PLATFORM CONNECTION SCHEMAS (Keep for compatibility)
# =============================================================================

class PlatformConnectionRequest(BaseModel):
    """Legacy platform connection request (manual OAuth)"""
    platform_id: str
    oauth_code: Optional[str] = None
    oauth_state: Optional[str] = None
    platform_specific_data: Optional[Dict[str, Any]] = None

# =============================================================================
# TOKEN MANAGEMENT SCHEMAS
# =============================================================================

class TokenValidationRequest(BaseModel):
    connection_id: str

class TokenValidationResponse(BaseModel):
    connection_id: str
    is_valid: bool
    expires_at: Optional[datetime] = None
    expires_in_hours: Optional[int] = None
    needs_renewal: bool = False
    last_check: datetime

# =============================================================================
# AUTOMATION SCHEMAS
# =============================================================================

class AutomationToggleRequest(BaseModel):
    connection_id: str
    enable_automation: bool
    automation_features: Optional[List[str]] = None

class AutomationStatusResponse(BaseModel):
    connection_id: str
    is_automation_enabled: bool
    automation_capabilities: Dict[str, Any]
    last_automation_use: Optional[datetime] = None
    automation_error_count: int = 0
    last_error: Optional[str] = None

# =============================================================================
# BULK OPERATIONS SCHEMAS
# =============================================================================

class BulkConnectionUpdate(BaseModel):
    connection_ids: List[str]
    update_data: AgentSocialConnectionUpdate

class BulkOperationResponse(BaseModel):
    success_count: int
    failed_count: int
    errors: List[Dict[str, str]] = []

# =============================================================================
# HEALTH CHECK SCHEMAS
# =============================================================================

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

# =============================================================================
# PLATFORM-SPECIFIC SCHEMAS
# =============================================================================

# Instagram Schemas
class InstagramConnectionInfo(BaseModel):
    business_account_id: Optional[str] = None
    account_type: str = "PERSONAL"  # PERSONAL, BUSINESS, CREATOR
    profile_picture_url: Optional[str] = None
    biography: Optional[str] = None
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    media_count: Optional[int] = None

class InstagramConversation(BaseModel):
    id: str
    updated_time: datetime
    can_reply: bool
    message_count: int
    unread_count: int
    participants: List[Dict[str, Any]]

class InstagramMessage(BaseModel):
    id: str
    created_time: datetime
    from_id: str
    from_username: Optional[str] = None
    to_id: str
    to_username: Optional[str] = None
    message: str
    attachments: List[Dict[str, Any]] = []

# Facebook Schemas
class FacebookPageInfo(BaseModel):
    page_id: str
    page_name: str
    page_access_token: str
    category: Optional[str] = None
    page_url: Optional[str] = None
    followers_count: Optional[int] = None
    instagram_business_account: Optional[Dict[str, Any]] = None

# WhatsApp Schemas
class WhatsAppConnectionData(BaseModel):
    phone_number: str
    display_name: Optional[str] = None
    business_profile: Optional[Dict[str, Any]] = None
    webhook_url: Optional[str] = None

# TikTok Schemas
class TikTokConnectionData(BaseModel):
    open_id: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    likes_count: Optional[int] = None

# =============================================================================
# WEBHOOK SCHEMAS
# =============================================================================

class WebhookSetupRequest(BaseModel):
    webhook_url: str = Field(..., description="URL to receive webhook events")
    verify_token: str = Field(..., description="Token for webhook verification")
    events: List[str] = Field(default=["messages", "messaging_seen"], description="Events to subscribe to")

class WebhookSetupResponse(BaseModel):
    success: bool
    webhook_url: str
    subscribed_events: List[str]
    setup_at: datetime
    platform: str
    connection_id: str

# =============================================================================
# MESSAGING SCHEMAS
# =============================================================================

class SendMessageRequest(BaseModel):
    recipient_id: str = Field(..., description="Platform user ID of the recipient")
    message_text: str = Field(..., description="Message content to send")
    message_type: str = Field(default="text", description="Type of message (text, image, etc.)")
    attachment_url: Optional[str] = Field(None, description="URL of attachment if any")

class SendMessageResponse(BaseModel):
    message_id: str
    sent_at: datetime
    recipient_id: str
    message_text: str
    status: str = "sent"
    platform: str
    connection_id: str