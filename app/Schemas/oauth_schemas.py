# app/Schemas/oauth_schemas.py - FIXED TO MATCH LoginResponse
from pydantic import BaseModel, field_validator, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

# Import auth schemas to reuse UserResponse and RoleResponse
from app.Schemas.auth import UserResponse, RoleResponse, CompanyBriefResponse

# OAuth Account Schemas
class OAuthAccountBase(BaseModel):
    provider: str
    provider_id: str
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    profile_image_url: Optional[str] = None
    scope: Optional[str] = None
    is_active: bool = True

class OAuthAccountCreate(OAuthAccountBase):
    pass

class OAuthAccountUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_active: Optional[bool] = None

class OAuthAccountResponse(OAuthAccountBase):
    id: str
    user_id: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'user_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# OAuth Provider Configuration
class OAuthProviderConfig(BaseModel):
    provider: str
    client_id: str
    authorize_url: str
    scope: str
    enabled: bool

class OAuthProvidersResponse(BaseModel):
    providers: List[OAuthProviderConfig]
    count: int
    redirect_url: str

# OAuth Authorization
class OAuthAuthorizationRequest(BaseModel):
    provider: str
    link_mode: Optional[bool] = False

class OAuthAuthorizationResponse(BaseModel):
    authorization_url: str
    state: str
    provider: str
    link_mode: bool = False

# OAuth Callback - FIXED TO MATCH LoginResponse STRUCTURE
class OAuthCallbackResponse(BaseModel):
    """
    OAuth callback response that matches LoginResponse structure
    Includes both standard login fields and OAuth-specific fields
    """
    # Standard login response fields (matching LoginResponse from auth.py)
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    expires_in: Optional[int] = None
    user: Optional[UserResponse] = None
    roles: Optional[List[RoleResponse]] = None
    company: Optional[CompanyBriefResponse] = None
    
    # OAuth-specific fields
    message: str
    provider: str
    login_method: Optional[str] = None  # 'oauth_login', 'oauth_signup', 'oauth_link'
    oauth_account_id: Optional[str] = None
    linked_to_user: Optional[str] = None
    
    # Completion flags for OAuth registration flows
    needs_completion: Optional[bool] = False
    completion_type: Optional[str] = None  # 'company', 'influencer', or None
    redirect_path: Optional[str] = None

# Linked Accounts
class LinkedOAuthAccount(BaseModel):
    id: str
    provider: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[str] = None
    profile_image_url: Optional[str] = None
    connected_at: str
    last_updated: str
    expires_at: Optional[str] = None
    scope: Optional[str] = None

class LinkedAccountsResponse(BaseModel):
    linked_accounts: List[LinkedOAuthAccount]
    count: int

# Unlink Account
class UnlinkAccountResponse(BaseModel):
    message: str
    provider: str
    unlinked_at: str

# Error Schemas
class OAuthErrorResponse(BaseModel):
    error: str
    error_description: Optional[str] = None
    error_uri: Optional[str] = None
    state: Optional[str] = None

# Success Response
class OAuthSuccessResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()

# Agent Social Connection Schemas
class AgentSocialConnectionBase(BaseModel):
    platform: str
    platform_user_id: str
    platform_username: Optional[str] = None
    display_name: Optional[str] = None
    profile_image_url: Optional[str] = None
    instagram_business_account_id: Optional[str] = None
    facebook_page_id: Optional[str] = None
    facebook_page_name: Optional[str] = None
    connection_type: str = "business_api"
    is_active: bool = True

class AgentSocialConnectionCreate(AgentSocialConnectionBase):
    pass

class AgentSocialConnectionUpdate(BaseModel):
    platform_username: Optional[str] = None
    display_name: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_active: Optional[bool] = None

class AgentSocialConnectionResponse(AgentSocialConnectionBase):
    id: str
    user_id: str
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'user_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v