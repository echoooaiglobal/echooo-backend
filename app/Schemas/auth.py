# app/Schemas/auth.py - Updated with first_name and last_name fields
from pydantic import BaseModel, EmailStr, ConfigDict, Field, validator, root_validator
import uuid
from typing import List, Optional, Dict
from datetime import datetime
import re
import pydantic
from packaging import version
PYDANTIC_V2 = version.parse(pydantic.__version__) >= version.parse("2.0.0")

if PYDANTIC_V2:
    from pydantic import field_validator
else:
    from pydantic import validator

class TokenData(BaseModel):
    email: Optional[str] = None   
    user_id: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class RoleResponse(BaseModel):
    id: str  # Change from int to str to handle UUID
    name: str
    description: Optional[str] = None
    
    model_config = {
        "from_attributes": True  # For Pydantic v2 (formerly orm_mode)
    }
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class UserBase(BaseModel):
    email: EmailStr
    # Updated to include new name fields
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    full_name: str  # Keep for backward compatibility
    phone_number: Optional[str] = None
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, v):
        if v is not None:
            v = v.strip()
            if v and not v.replace(' ', '').replace('-', '').replace("'", '').isalpha():
                raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        return v

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    user_type: str = Field(..., pattern=r'^(platform|b2c|influencer)$')
    company_id: Optional[str] = None  # Use str for UUID
    role_name: Optional[str] = None

    # Company related fields
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    
    # Override to make first_name and last_name required for user creation
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    
    @field_validator('password')
    def password_strength(cls, v: str) -> str:
        """Validate password meets complexity requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v
    
    @field_validator('user_type')
    def validate_user_type(cls, v):
        valid_types = ['platform', 'b2c', 'influencer']
        if v not in valid_types:
            raise ValueError(f'User type must be one of: {", ".join(valid_types)}')
        return v
    
    @field_validator('company_id')
    @classmethod
    def validate_company_id(cls, v, info):
        # For Pydantic v2, data is accessed through info.data
        if 'user_type' in info.data and info.data['user_type'] == 'b2c' and v is None:
            raise ValueError('Company ID is required for b2c users')
        return v

class UserUpdate(BaseModel):
    # Updated to include new name fields
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = None  # Keep for backward compatibility
    phone_number: Optional[str] = None
    profile_image_url: Optional[str] = None
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, v):
        if v is not None:
            v = v.strip()
            if v and not v.replace(' ', '').replace('-', '').replace("'", '').isalpha():
                raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        return v

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    # Updated to include new name fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: str
    phone_number: Optional[str] = None
    status: str
    user_type: Optional[str] = None
    email_verified: bool
    profile_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    
    model_config = {
        "from_attributes": True  # Formerly orm_mode
    }
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    # Compute full_name if not provided
    @field_validator('full_name', mode='before')
    @classmethod
    def compute_full_name(cls, v, info):
        if not v and hasattr(info, 'data'):
            first_name = info.data.get('first_name', '')
            last_name = info.data.get('last_name', '')
            if first_name and last_name:
                return f"{first_name} {last_name}"
            elif first_name:
                return first_name
            elif last_name:
                return last_name
        return v or ""
    
class CompanyBriefResponse(BaseModel):
    id: str
    name: str
    domain: Optional[str] = None
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v 

class CompanyBase(BaseModel):
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: str
    logo_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True  # For Pydantic v2
    }

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class InfluencerBase(BaseModel):
    bio: Optional[str] = None
    primary_platform: Optional[str] = None
    niche: Optional[str] = None

class InfluencerCreate(InfluencerBase):
    user_id: str

class InfluencerResponse(InfluencerBase):
    id: str
    user_id: int
    audience_size: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True  # For Pydantic v2
    }

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class SocialAccountBase(BaseModel):
    platform: str
    username: str
    follower_count: Optional[int] = None
    verified: bool = False

class SocialAccountCreate(SocialAccountBase):
    influencer_id: str

class SocialAccountResponse(SocialAccountBase):
    id: int
    influencer_id: int
    
    model_config = ConfigDict(from_attributes=True)

class UserDetailResponse(UserResponse):
    """Extended user response with additional details like company info"""
    roles: List[RoleResponse] = []
    company: Optional[CompanyBriefResponse] = None
    
    model_config = {
        "from_attributes": True
    }

class LoginResponse(TokenResponse):
    user: UserResponse
    roles: List[RoleResponse]
    refresh_token: str
    company: Optional[CompanyBriefResponse] = None
    
class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    email: EmailStr
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @field_validator('confirm_password')
    def passwords_match(cls, v: str, info) -> str:
        if v != info.data.get('new_password'):
            raise ValueError('Passwords do not match')
        return v
    
    @field_validator('new_password')
    def password_strength(cls, v: str) -> str:
        """Validate password meets complexity requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v
    
class EmailVerificationRequest(BaseModel):
    email: EmailStr

class EmailVerificationToken(BaseModel):
    token: str

class EmailVerificationResponse(BaseModel):
    message: str
    user_id: str
    email_verified: bool
    
    @field_validator('user_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class ResendVerificationRequest(BaseModel):
    email: EmailStr

# For development - Manual verification
class ManualVerificationRequest(BaseModel):
    user_id: str
    verification_type: str = Field(..., pattern=r'^(email|b2c|influencer)$')
    
    @field_validator('verification_type')
    def validate_verification_type(cls, v):
        valid_types = ['email', 'b2c', 'influencer']
        if v not in valid_types:
            raise ValueError(f'Verification type must be one of: {", ".join(valid_types)}')
        return v
    
#-----------------------------new------------------------------------
class UserStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r'^(active|inactive|pending|suspended)$')

class UserRoleUpdate(BaseModel):
    role_ids: List[str]  # List of role UUIDs as strings

class AdminPasswordReset(BaseModel):
    new_password: str = Field(..., min_length=8)
    
    @field_validator('new_password')
    def password_strength(cls, v: str) -> str:
        """Validate password meets complexity requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v

class UserListResponse(BaseModel):
    users: List[UserDetailResponse]
    total: int
    skip: int
    limit: int

class UserStatsResponse(BaseModel):
    total_users: int
    users_by_type: Dict[str, int]
    users_by_status: Dict[str, int]
    recent_registrations: int

# Extend existing UserUpdate for admin operations
class AdminUserUpdate(UserUpdate):
    email: Optional[EmailStr] = None
    user_type: Optional[str] = Field(None, pattern=r'^(platform|b2c|influencer)$') 
    status: Optional[str] = Field(None, pattern=r'^(active|inactive|pending|suspended)$')
    email_verified: Optional[bool] = None

# Additional schemas for profile image management
class ProfileImageResponse(BaseModel):
    message: str
    profile_image_url: str
    file_path: str