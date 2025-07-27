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
    code: str  # Abbreviation (e.g. "DM", "Story")
    description: Optional[str] = None  # Optional details or internal notes

class MessageChannelCreate(MessageChannelBase):
    pass

class MessageChannelUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
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
    
    # Influencer statistics for this specific list
    total_influencers_count: int = 0
    total_onboarded_count: int = 0
    total_contacted_count: int = 0
    avg_collaboration_price: Optional[float] = None
    completion_percentage: float = 0.0
    days_since_created: int = 0
    last_activity_date: Optional[datetime] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class MessageTemplatesBrief(BaseModel):
    id: str
    subject: Optional[str] = None
    content: str
    template_type: Optional[str]
    followup_sequence: Optional[int] = None
    followup_delay_hours: Optional[int] = None
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
    campaign_list_id: str  # Changed from list_id to match AgentAssignment model
    outreach_agent_id: str  # Changed from agent_id to match AgentAssignment model
    status_id: str
    created_at: datetime
    updated_at: datetime
    
    status: Optional[StatusBrief] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'campaign_list_id', 'outreach_agent_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class CampaignResponse(CampaignBase):
    id: str
    created_by: str
    default_filters: bool
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Relationship fields
    category: Optional[CategoryBrief] = None
    status: Optional[StatusBrief] = None
    campaign_lists: List[CampaignListBrief] = []  # Contains detailed stats per list
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
    assigned_influencer_id: str = Field(..., description="ID of the assigned influencer")
    agent_assignment_id: Optional[str] = Field(default=None, description="ID of the agent assignment")
    outreach_agent_id: str = Field(..., description="ID of the outreach agent")
    agent_social_connection_id: Optional[str] = Field(default=None, description="ID of the agent social connection")
    communication_channel_id: Optional[str] = Field(default=None, description="ID of the communication channel")
    message_status_id: Optional[str] = Field(default=None, description="ID of the message status")
    message_sent_at: Optional[datetime] = Field(default=None, description="When message was sent")
    error_code: Optional[str] = Field(default=None, description="Error code if message failed")
    error_reason: Optional[str] = Field(default=None, description="Detailed error reason")

class InfluencerOutreachCreate(InfluencerOutreachBase):
    pass

class InfluencerOutreachUpdate(BaseModel):
    agent_assignment_id: Optional[str] = None
    outreach_agent_id: Optional[str] = None
    agent_social_connection_id: Optional[str] = None
    communication_channel_id: Optional[str] = None
    message_status_id: Optional[str] = None
    message_sent_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_reason: Optional[str] = None

class InfluencerOutreachResponse(InfluencerOutreachBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'assigned_influencer_id', 'agent_assignment_id', 
                    'outreach_agent_id', 'agent_social_connection_id', 
                    'communication_channel_id', 'message_status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if v is not None and isinstance(v, uuid.UUID):
            return str(v)
        return v