# app/Schemas/campaign.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Status schemas
class StatusBase(BaseModel):
    model: str  # Where it's used (e.g. "list_member", "outreach")
    name: str   # e.g. "discovered", "assigned_to_ai", "responded"

class StatusCreate(StatusBase):
    pass

class StatusUpdate(BaseModel):
    model: Optional[str] = None
    name: Optional[str] = None

class StatusResponse(StatusBase):
    id: str  # UUID as string
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# MessageChannel schemas
class MessageChannelBase(BaseModel):
    name: str  # Full name of the channel (e.g. "Direct Message")
    shortname: str  # Abbreviation (e.g. "DM", "Story")
    description: Optional[str] = None  # Optional details or internal notes

class MessageChannelCreate(MessageChannelBase):
    pass

class MessageChannelUpdate(BaseModel):
    name: Optional[str] = None
    shortname: Optional[str] = None
    description: Optional[str] = None

class MessageChannelResponse(MessageChannelBase):
    id: str  # UUID as string
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Agent schemas
class AgentBase(BaseModel):
    name: str  # Agent's display name
    platform_id: str  # FK -> platforms.id (e.g. Instagram, WhatsApp)
    credentials: Optional[Dict[str, Any]] = None  # Serialized credentials
    assigned_to_user_id: Optional[str] = None  # FK -> users.id
    is_available: bool = True  # Whether agent is available for assignment

class AgentCreate(AgentBase):
    pass

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    platform_id: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None
    assigned_to_user_id: Optional[str] = None
    is_available: Optional[bool] = None
    current_assignment_id: Optional[str] = None

class AgentResponse(AgentBase):
    id: str  # UUID as string
    current_assignment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'platform_id', 'assigned_to_user_id', 'current_assignment_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
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

# Campaign schemas
class CampaignBase(BaseModel):
    company_id: str  # FK -> companies.id
    name: str  # Campaign name
    description: Optional[str] = None  # Campaign details
    brand_name: Optional[str] = None  # Brand name
    category_id: Optional[str] = None  # FK -> categories.id
    audience_age_group: Optional[str] = None  # Target audience age group
    budget: Optional[float] = None  # Campaign budget
    currency_code: Optional[str] = None  # Currency code (e.g., USD, EUR)
    status_id: Optional[str] = None  # FK -> statuses.id
    start_date: Optional[datetime] = None  # Campaign start date
    end_date: Optional[datetime] = None  # Campaign end date

class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    brand_name: Optional[str] = None
    category_id: Optional[str] = None
    audience_age_group: Optional[str] = None
    budget: Optional[float] = None
    currency_code: Optional[str] = None
    status_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    default_filters: Optional[bool] = None 

class CategoryBrief(BaseModel):
    id: str
    name: str
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
class CampaignListBrief(BaseModel):
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

class MessageTemplatesBrief(BaseModel):
    id: str
    subject: str
    content: str
    company_id: str
    campaign_id: str
    is_global: bool = False
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
    
class ListAssignmentBrief(BaseModel):
    id: str
    list_id: str
    agent_id: str
    status_id: str
    created_at: datetime
    updated_at: datetime
    
    status: Optional[StatusBrief] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'list_id', 'agent_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class CampaignResponse(CampaignBase):
    id: str  # UUID as string
    created_by: str  # FK -> users.id
    default_filters: bool  # Include in response for frontend logic
    is_deleted: bool = False  # Include soft delete status
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None  # UUID as string
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryBrief] = None  # Include category info
    status: Optional[StatusBrief] = None  # Include status info
    campaign_lists: List[CampaignListBrief] = []  # Include influencer lists
    message_templates: List[MessageTemplatesBrief] = []
    list_assignments: List[ListAssignmentBrief] = []
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'company_id', 'created_by', 'category_id', 'status_id', 'deleted_by', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# CampaignList schemas
class CampaignListBase(BaseModel):
    campaign_id: str
    name: str
    description: Optional[str] = None
    message_template_id: Optional[str] = None

class CampaignListCreate(CampaignListBase):
    pass

class CampaignListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    message_template_id: Optional[str] = None

class CampaignListResponse(CampaignListBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'campaign_id', 'created_by', 'message_template_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# ListAssignment schemas
class ListAssignmentBase(BaseModel):
    list_id: str  # FK -> campaign_lists.id (required)
    agent_id: Optional[str] = None  # FK -> agents.id (optional - will auto-assign if not provided)
    status_id: Optional[str] = None  # FK -> statuses.id (optional - will default to 'pending')

class ListAssignmentCreate(ListAssignmentBase):
    pass

class ListAssignmentUpdate(BaseModel):
    status_id: Optional[str] = None
    agent_id: Optional[str] = None

class ListAssignmentStatusUpdate(BaseModel):
    """Schema specifically for status updates"""
    status_id: str  # Required when updating status

class ListAssignmentResponse(BaseModel):
    id: str  # UUID as string
    list_id: str
    agent_id: str
    status_id: str
    created_at: datetime
    updated_at: datetime
    
    # Include related data
    status: Optional[StatusBrief] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'list_id', 'agent_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# InfluencerOutreach schemas
class InfluencerOutreachBase(BaseModel):
    social_account_id: str  # FK -> influencers.id
    list_id: str  # FK -> influencer_lists.id
    list_member_id: str  # FK -> influencer_list_members.id
    assignment_id: Optional[str] = None  # FK -> list_assignments.id
    message_channel_id: Optional[str] = None  # FK -> message_channels.id
    message_status_id: Optional[str] = None  # FK -> statuses.id
    message_sent_at: Optional[datetime] = None  # When message was sent
    error_code: Optional[str] = None  # Error code if outreach failed
    error_reason: Optional[str] = None  # Reason or message of the error

class InfluencerOutreachCreate(InfluencerOutreachBase):
    pass

class InfluencerOutreachUpdate(BaseModel):
    message_channel_id: Optional[str] = None
    message_status_id: Optional[str] = None
    message_sent_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_reason: Optional[str] = None

class InfluencerOutreachResponse(InfluencerOutreachBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'social_account_id', 'list_id', 'list_member_id', 
                    'assignment_id', 'message_channel_id', 'message_status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v