# app/Schemas/agent_assignment.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
import uuid
from app.Schemas.common import PaginationInfo

class AgentAssignmentBase(BaseModel):
    """Base schema for agent assignments"""
    outreach_agent_id: str = Field(..., description="ID of the outreach agent")
    campaign_list_id: str = Field(..., description="ID of the campaign list")
    status_id: str = Field(..., description="Status ID of the assignment")
    assigned_influencers_count: Optional[int] = Field(default=0, description="Number of assigned influencers")
    completed_influencers_count: Optional[int] = Field(default=0, description="Number of completed influencers")
    pending_influencers_count: Optional[int] = Field(default=0, description="Number of pending influencers")
    archived_influencers_count: Optional[int] = Field(default=0, description="Number of archived influencers")
    assigned_at: Optional[datetime] = Field(default=None, description="Assignment date")
    completed_at: Optional[datetime] = Field(default=None, description="Completion date")

    @field_validator('outreach_agent_id', 'campaign_list_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class AgentAssignmentCreate(AgentAssignmentBase):
    """Schema for creating agent assignments"""
    pass

class AgentAssignmentUpdate(BaseModel):
    """Schema for updating agent assignments"""
    outreach_agent_id: Optional[str] = None
    campaign_list_id: Optional[str] = None
    status_id: Optional[str] = None
    # assigned_influencers_count: Optional[int] = None
    # completed_influencers_count: Optional[int] = None
    # pending_influencers_count: Optional[int] = None
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @field_validator('outreach_agent_id', 'campaign_list_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class AgentAssignmentStatusUpdate(BaseModel):
    """Schema for updating only the status of an assignment"""
    status_id: str = Field(..., description="New status ID")

    @field_validator('status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# need to remove this class, we are calculatinf directly in the agent assignments response.
class AgentAssignmentCountsUpdate(BaseModel):
    """Schema for updating assignment counts"""
    assigned_influencers_count: Optional[int] = None
    completed_influencers_count: Optional[int] = None
    pending_influencers_count: Optional[int] = None
    archived_influencers_count: Optional[int] = None

# Related schemas for nested data
class OutreachAgentBrief(BaseModel):
    """Brief outreach agent information"""
    id: str
    assigned_user_id: str
    active_lists_count: int
    active_influencers_count: int
    is_automation_enabled: bool
    is_available_for_assignment: bool
    messages_sent_today: int
    last_activity_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', 'assigned_user_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class CampaignListBrief(BaseModel):
    """Brief campaign list information"""
    id: str
    campaign_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', 'campaign_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class StatusBrief(BaseModel):
    """Brief status information"""
    id: str
    name: str
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class MessageTemplateBrief(BaseModel):
    """Brief message template information with follow-up details"""
    id: str
    subject: Optional[str] = None  # Can be null for follow-ups
    content: str
    template_type: str = "initial"  # 'initial' or 'followup'
    followup_sequence: Optional[int] = None  # 1, 2, 3... for follow-up order
    followup_delay_hours: Optional[int] = None  # Hours to wait before sending
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
class CampaignBrief(BaseModel):
    id: str
    name: str
    brand_name: Optional[str] = None
    description: Optional[str] = None
    status_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # ADD this field
    message_templates: Optional[List[MessageTemplateBrief]] = None
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class AgentAssignmentResponse(AgentAssignmentBase):
    """Schema for agent assignment responses"""
    id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    # Related data
    campaign: Optional[CampaignBrief] = None
    campaign_list: Optional[CampaignListBrief] = None
    status: Optional[StatusBrief] = None
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class AgentAssignmentsPaginatedResponse(BaseModel):
    """Paginated response for agent assignments"""
    assignments: List[AgentAssignmentResponse]
    pagination: PaginationInfo

class AgentAssignmentStatsResponse(BaseModel):
    """Statistics response for agent assignments"""
    total_assignments: int
    active_assignments: int
    completed_assignments: int
    pending_assignments: int
    total_assigned_influencers: int
    total_completed_influencers: int
    total_pending_influencers: int
    avg_completion_rate: float

    