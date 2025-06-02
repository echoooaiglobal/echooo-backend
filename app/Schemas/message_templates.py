# app/Schemas/message_templates.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Message Template schemas
class MessageTemplateBase(BaseModel):
    subject: str
    content: str
    company_id: str
    campaign_id: str
    is_global: bool = False

class MessageTemplateCreate(MessageTemplateBase):
    auto_assign_agent: Optional[bool] = False
    target_list_id: Optional[str] = None

class MessageTemplateUpdate(BaseModel):
    subject: Optional[str] = None
    content: Optional[str] = None
    is_global: Optional[bool] = None

class MessageTemplateResponse(MessageTemplateBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'company_id', 'campaign_id', 'created_by', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Update InfluencerListMemberBase to remove message field
class InfluencerListMemberBase(BaseModel):
    influencer_id: str
    platform_id: str
    status_id: Optional[str] = None
    # Remove the message field
    collaboration_price: Optional[float] = None
    next_contact_at: Optional[datetime] = None

# Update InfluencerListMemberUpdate to remove message field
class InfluencerListMemberUpdate(BaseModel):
    status_id: Optional[str] = None
    # Remove the message field
    collaboration_price: Optional[float] = None
    next_contact_at: Optional[datetime] = None

# Update InfluencerListBase to include message_template_id
class InfluencerListBase(BaseModel):
    campaign_id: str
    subject: str
    description: Optional[str] = None
    message_template_id: Optional[str] = None  # Add this field

# Update InfluencerListUpdate to include message_template_id
class InfluencerListUpdate(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    message_template_id: Optional[str] = None  # Add this field