# app/Schemas/influencer_contact.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import uuid
import re  # Import re module at the top

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

def validate_international_phone(phone: str) -> bool:
    """
    Validates international phone numbers with flexible formatting
    Supports various international formats including:
    - +1234567890
    - +1 234 567 8900
    - +1 (234) 567-8900
    - +44 20 7946 0958
    - +91 98765 43210
    - etc.
    """
    # Remove all non-digit and non-plus characters for counting
    digits_only = re.sub(r'[^\d+]', '', phone)
    
    # Must start with + for international format (recommended)
    # or be at least 7 digits for local format
    if digits_only.startswith('+'):
        # International format: + followed by country code (1-4 digits) + number (4-15 digits)
        # Total length should be between 8-19 characters (including +)
        if len(digits_only) < 8 or len(digits_only) > 19:
            return False
        # Check if it's a valid international format
        return bool(re.match(r'^\+[1-9]\d{6,17}$', digits_only))
    else:
        # Local format: at least 7 digits, max 15 digits
        if len(digits_only) < 7 or len(digits_only) > 15:
            return False
        return bool(re.match(r'^\d{7,15}$', digits_only))

def validate_email_format(email: str) -> bool:
    """
    Validates email format using a comprehensive regex
    """
    email_pattern = r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    return bool(re.match(email_pattern, email))

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
        
        # Email validation
        if contact_type == 'email':
            if not validate_email_format(v):
                raise ValueError('Invalid email format')
        
        # Phone/WhatsApp validation - support international formats
        elif contact_type in ['phone', 'whatsapp']:
            if not validate_international_phone(v):
                raise ValueError(
                    'Invalid phone number format. Please use international format (+country_code followed by number) '
                    'or local format (7-15 digits). Examples: +1234567890, +44 20 7946 0958, +91 98765 43210'
                )
        
        # Telegram validation (username format)
        elif contact_type == 'telegram':
            # Telegram usernames: 5-32 characters, alphanumeric + underscores, no consecutive underscores
            telegram_pattern = r'^@?[a-zA-Z0-9]([a-zA-Z0-9_]*[a-zA-Z0-9])?$'
            if not re.match(telegram_pattern, v) or len(v.replace('@', '')) < 5 or len(v.replace('@', '')) > 32:
                raise ValueError('Invalid Telegram username. Must be 5-32 characters, alphanumeric and underscores only')
        
        # Discord validation (username or user ID)
        elif contact_type == 'discord':
            # Discord username format or numeric ID
            if not (re.match(r'^[a-zA-Z0-9._]{2,32}$', v) or re.match(r'^\d{17,19}$', v)):
                raise ValueError('Invalid Discord username or ID format')
        
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
        
        # Email validation
        if contact_type == 'email':
            if not validate_email_format(v):
                raise ValueError('Invalid email format')
        
        # Phone/WhatsApp validation - support international formats
        elif contact_type in ['phone', 'whatsapp']:
            if not validate_international_phone(v):
                raise ValueError(
                    'Invalid phone number format. Please use international format (+country_code followed by number) '
                    'or local format (7-15 digits). Examples: +1234567890, +44 20 7946 0958, +91 98765 43210'
                )
        
        # Telegram validation
        elif contact_type == 'telegram':
            telegram_pattern = r'^@?[a-zA-Z0-9]([a-zA-Z0-9_]*[a-zA-Z0-9])?$'
            if not re.match(telegram_pattern, v) or len(v.replace('@', '')) < 5 or len(v.replace('@', '')) > 32:
                raise ValueError('Invalid Telegram username. Must be 5-32 characters, alphanumeric and underscores only')
        
        # Discord validation
        elif contact_type == 'discord':
            if not (re.match(r'^[a-zA-Z0-9._]{2,32}$', v) or re.match(r'^\d{17,19}$', v)):
                raise ValueError('Invalid Discord username or ID format')
        
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