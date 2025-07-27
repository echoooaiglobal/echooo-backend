# app/Schemas/influencer_outreach.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Brief schemas for related models
class AssignedInfluencerBrief(BaseModel):
    """Brief assigned influencer information"""
    id: str
    campaign_influencer_id: str
    agent_assignment_id: str
    status_id: str
    attempts_made: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', 'campaign_influencer_id', 'agent_assignment_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class AgentAssignmentBrief(BaseModel):
    """Brief agent assignment information"""
    id: str
    outreach_agent_id: str
    campaign_list_id: str
    status_id: str
    assigned_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', 'outreach_agent_id', 'campaign_list_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class OutreachAgentBrief(BaseModel):
    """Brief outreach agent information"""
    id: str
    user_id: str
    status_id: str
    name: Optional[str] = None
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', 'user_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class AgentSocialConnectionBrief(BaseModel):
    """Brief agent social connection information"""
    id: str
    outreach_agent_id: str
    platform_id: str
    status_id: str
    platform_account_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', 'outreach_agent_id', 'platform_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class CommunicationChannelBrief(BaseModel):
    """Brief communication channel information"""
    id: str
    name: str
    platform_id: str
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', 'platform_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class StatusBrief(BaseModel):
    """Brief status information"""
    id: str
    name: str
    model: str
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Main schemas
class InfluencerOutreachBase(BaseModel):
    """Base schema for influencer outreach"""
    assigned_influencer_id: str = Field(..., description="ID of the assigned influencer")
    agent_assignment_id: Optional[str] = Field(default=None, description="ID of the agent assignment")
    outreach_agent_id: str = Field(..., description="ID of the outreach agent")
    agent_social_connection_id: Optional[str] = Field(default=None, description="ID of the agent social connection")
    communication_channel_id: Optional[str] = Field(default=None, description="ID of the communication channel")
    message_status_id: Optional[str] = Field(default=None, description="ID of the message status")
    message_sent_at: Optional[datetime] = Field(default=None, description="When message was sent")
    error_code: Optional[str] = Field(default=None, max_length=20, description="Error code if message failed")
    error_reason: Optional[str] = Field(default=None, description="Detailed error reason")

    @field_validator('assigned_influencer_id', 'agent_assignment_id', 'outreach_agent_id', 
                     'agent_social_connection_id', 'communication_channel_id', 'message_status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if v is not None and isinstance(v, uuid.UUID):
            return str(v)
        return v

class InfluencerOutreachCreate(InfluencerOutreachBase):
    """Schema for creating influencer outreach records"""
    pass

class InfluencerOutreachUpdate(BaseModel):
    """Schema for updating influencer outreach records"""
    agent_assignment_id: Optional[str] = None
    outreach_agent_id: Optional[str] = None
    agent_social_connection_id: Optional[str] = None
    communication_channel_id: Optional[str] = None
    message_status_id: Optional[str] = None
    message_sent_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_reason: Optional[str] = None

    @field_validator('agent_assignment_id', 'outreach_agent_id', 'agent_social_connection_id', 
                     'communication_channel_id', 'message_status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if v is not None and isinstance(v, uuid.UUID):
            return str(v)
        return v

class InfluencerOutreachResponse(BaseModel):
    """Schema for influencer outreach responses"""
    id: str
    assigned_influencer_id: str
    agent_assignment_id: Optional[str] = None
    outreach_agent_id: str
    agent_social_connection_id: Optional[str] = None
    communication_channel_id: Optional[str] = None
    message_status_id: Optional[str] = None
    message_sent_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Related objects (optional for detailed responses)
    assigned_influencer: Optional[AssignedInfluencerBrief] = None
    agent_assignment: Optional[AgentAssignmentBrief] = None
    outreach_agent: Optional[OutreachAgentBrief] = None
    agent_social_connection: Optional[AgentSocialConnectionBrief] = None
    communication_channel: Optional[CommunicationChannelBrief] = None
    message_status: Optional[StatusBrief] = None
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', 'assigned_influencer_id', 'agent_assignment_id', 'outreach_agent_id',
                     'agent_social_connection_id', 'communication_channel_id', 'message_status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if v is not None and isinstance(v, uuid.UUID):
            return str(v)
        return v

# Bulk operations schemas
class InfluencerOutreachBulkCreate(BaseModel):
    """Schema for bulk creating outreach records"""
    outreach_records: List[InfluencerOutreachCreate] = Field(..., description="List of outreach records to create")

class InfluencerOutreachBulkUpdate(BaseModel):
    """Schema for bulk updating outreach records"""
    outreach_ids: List[str] = Field(..., description="List of outreach record IDs to update")
    update_data: InfluencerOutreachUpdate = Field(..., description="Data to update")

# List response schemas
class PaginationInfo(BaseModel):
    """Pagination information"""
    total: int
    page: int
    size: int
    pages: int

class InfluencerOutreachListResponse(BaseModel):
    """Schema for paginated outreach record lists"""
    items: List[InfluencerOutreachResponse]
    pagination: PaginationInfo

# Statistics schemas
class InfluencerOutreachStats(BaseModel):
    """Schema for outreach statistics"""
    total_outreach_records: int
    successful_messages: int
    failed_messages: int
    pending_messages: int
    success_rate: float
    average_response_time: Optional[float] = None  # in hours
    most_active_agent: Optional[str] = None
    most_used_channel: Optional[str] = None