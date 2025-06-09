# app/Schemas/influencer_contact.py
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid

# Brief schemas for related models
class SocialAccountBrief(BaseModel):
    id: str
    account_handle: str
    full_name: str
    platform_id: str
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'platform_id', mode='before')
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

class RoleBrief(BaseModel):
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

# Contact type validation
VALID_CONTACT_TYPES = ["email", "phone", "whatsapp", "telegram", "discord", "other"]

# Influencer Contact schemas
class InfluencerContactBase(BaseModel):
    social_account_id: str
    platform_specific: bool = False
    platform_id: Optional[str] = None
    role_id: Optional[str] = None
    name: Optional[str] = None
    contact_type: str = Field(..., description="Type of contact (email, phone, whatsapp, telegram, discord, other)")
    contact_value: str = Field(..., min_length=1, max_length=150)
    is_primary: bool = False
    
    @field_validator('contact_type')
    @classmethod
    def validate_contact_type(cls, v):
        if v.lower() not in VALID_CONTACT_TYPES:
            raise ValueError(f'Contact type must be one of: {", ".join(VALID_CONTACT_TYPES)}')
        return v.lower()
    
    @field_validator('contact_value')
    @classmethod
    def validate_contact_value(cls, v, info):
        contact_type = info.data.get('contact_type', '').lower()
        
        # Basic email validation for email type
        if contact_type == 'email':
            # Simple email regex check
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('Invalid email format')
        
        # Basic phone validation for phone/whatsapp
        elif contact_type in ['phone', 'whatsapp']:
            # Remove common phone formatting
            phone_digits = re.sub(r'[^\d+]', '', v)
            if len(phone_digits) < 10:
                raise ValueError('Phone number must have at least 10 digits')
        
        return v

class InfluencerContactCreate(InfluencerContactBase):
    pass

class InfluencerContactUpdate(BaseModel):
    platform_specific: Optional[bool] = None
    platform_id: Optional[str] = None
    role_id: Optional[str] = None
    name: Optional[str] = None
    contact_type: Optional[str] = None
    contact_value: Optional[str] = None
    is_primary: Optional[bool] = None
    
    @field_validator('contact_type')
    @classmethod
    def validate_contact_type(cls, v):
        if v and v.lower() not in VALID_CONTACT_TYPES:
            raise ValueError(f'Contact type must be one of: {", ".join(VALID_CONTACT_TYPES)}')
        return v.lower() if v else v
    
    @field_validator('contact_value')
    @classmethod
    def validate_contact_value(cls, v, info):
        if not v:
            return v
            
        contact_type = info.data.get('contact_type', '').lower()
        
        # Basic email validation for email type
        if contact_type == 'email':
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('Invalid email format')
        
        # Basic phone validation for phone/whatsapp
        elif contact_type in ['phone', 'whatsapp']:
            import re
            phone_digits = re.sub(r'[^\d+]', '', v)
            if len(phone_digits) < 10:
                raise ValueError('Phone number must have at least 10 digits')
        
        return v

class InfluencerContactResponse(BaseModel):
    id: str
    social_account_id: str
    platform_specific: bool
    platform_id: Optional[str] = None
    role_id: Optional[str] = None
    name: Optional[str] = None
    contact_type: str
    contact_value: str
    is_primary: bool
    created_at: datetime
    updated_at: datetime
    
    # Related data
    social_account: Optional[SocialAccountBrief] = None
    platform: Optional[PlatformBrief] = None
    role: Optional[RoleBrief] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'social_account_id', 'platform_id', 'role_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Bulk operations
class InfluencerContactBulkCreate(BaseModel):
    social_account_id: str
    contacts: List[InfluencerContactCreate]

class InfluencerContactBulkResponse(BaseModel):
    created_contacts: List[InfluencerContactResponse]
    failed_contacts: List[dict]  # Contains error info for failed creations

# Search and filter
class InfluencerContactFilter(BaseModel):
    social_account_id: Optional[str] = None
    contact_type: Optional[str] = None
    platform_id: Optional[str] = None
    is_primary: Optional[bool] = None
    
    @field_validator('contact_type')
    @classmethod
    def validate_contact_type(cls, v):
        if v and v.lower() not in VALID_CONTACT_TYPES:
            raise ValueError(f'Contact type must be one of: {", ".join(VALID_CONTACT_TYPES)}')
        return v.lower() if v else v