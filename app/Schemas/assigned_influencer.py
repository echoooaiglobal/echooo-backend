# app/Schemas/assigned_influencer.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
from app.Schemas.common import PaginationInfo

class AssignmentTypeEnum(str, Enum):
    active = "active"
    archived = "archived"
    completed = "completed"

class AssignedInfluencerBase(BaseModel):
    """Base schema for assigned influencers"""
    campaign_influencer_id: str = Field(..., description="ID of the campaign influencer")
    agent_assignment_id: str = Field(..., description="ID of the agent assignment")
    type: Optional[AssignmentTypeEnum] = Field(default=AssignmentTypeEnum.active, description="Assignment type")
    status_id: str = Field(..., description="Status ID of the assignment")
    attempts_made: Optional[int] = Field(default=0, description="Number of contact attempts made")
    last_contacted_at: Optional[datetime] = Field(default=None, description="Last contact timestamp")
    next_contact_at: Optional[datetime] = Field(default=None, description="Next scheduled contact timestamp")
    responded_at: Optional[datetime] = Field(default=None, description="When influencer responded")
    assigned_at: Optional[datetime] = Field(default=None, description="Assignment timestamp")
    archived_at: Optional[datetime] = Field(default=None, description="Archive timestamp")
    notes: Optional[str] = Field(default=None, description="Assignment notes")

    @field_validator('campaign_influencer_id', 'agent_assignment_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class AssignedInfluencerCreate(AssignedInfluencerBase):
    """Schema for creating assigned influencers"""
    pass

class AssignedInfluencerUpdate(BaseModel):
    """Schema for updating assigned influencers"""
    campaign_influencer_id: Optional[str] = None
    agent_assignment_id: Optional[str] = None
    type: Optional[AssignmentTypeEnum] = None
    status_id: Optional[str] = None
    attempts_made: Optional[int] = None
    last_contacted_at: Optional[datetime] = None
    next_contact_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    notes: Optional[str] = None

    @field_validator('campaign_influencer_id', 'agent_assignment_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if v is not None and isinstance(v, uuid.UUID):
            return str(v)
        return v

class AssignedInfluencerStatusUpdate(BaseModel):
    """Schema for updating only the status of an assigned influencer"""
    status_id: str = Field(..., description="New status ID")

    @field_validator('status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class AssignedInfluencerBulkStatusUpdate(BaseModel):
    """Schema for bulk status updates"""
    influencer_ids: List[str] = Field(..., description="List of assigned influencer IDs")
    status_id: str = Field(..., description="New status ID")

    @field_validator('status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class AssignedInfluencerContactUpdate(BaseModel):
    """Schema for updating contact information"""
    attempts_made: Optional[int] = None
    last_contacted_at: Optional[datetime] = None
    next_contact_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    notes: Optional[str] = None

class AssignedInfluencerTransfer(BaseModel):
    """Schema for transferring assigned influencer to another agent"""
    new_agent_assignment_id: str = Field(..., description="New agent assignment ID")
    transfer_reason: Optional[str] = Field(default=None, description="Reason for transfer")

    @field_validator('new_agent_assignment_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class SocialAccountBrief(BaseModel):
    """Brief social account information for assigned influencers"""
    id: str
    full_name: str
    platform_id: str
    account_handle: str
    followers_count: Optional[int] = None
    is_verified: Optional[bool] = None
    profile_pic_url: Optional[str] = None
    account_url: Optional[str] = None
    
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
    
# MODIFY existing CampaignInfluencerBrief to add social_account field
class CampaignInfluencerBrief(BaseModel):
    """Brief campaign influencer information"""
    id: str
    campaign_list_id: str
    social_account_id: str
    status_id: str
    total_contact_attempts: int
    collaboration_price: Optional[float] = None
    currency: Optional[str] = None
    is_ready_for_onboarding: bool
    created_at: datetime
    status: Optional[StatusBrief] = None  # Keep this field
    
    # ADD this field to existing schema
    social_account: Optional[SocialAccountBrief] = None
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', 'campaign_list_id', 'social_account_id', 'status_id', mode='before')
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
    assigned_influencers_count: int
    completed_influencers_count: int
    pending_influencers_count: int
    assigned_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', 'outreach_agent_id', 'campaign_list_id', 'status_id', mode='before')
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
    description: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class AssignedInfluencerResponse(BaseModel):
    """Schema for assigned influencer responses"""
    id: str
    campaign_influencer_id: str
    agent_assignment_id: str
    type: AssignmentTypeEnum
    status_id: str
    attempts_made: int
    last_contacted_at: Optional[datetime] = None
    next_contact_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    assigned_at: datetime
    archived_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Related objects (REMOVE agent_assignment, keep others)
    campaign_influencer: Optional[CampaignInfluencerBrief] = None
    # agent_assignment: Optional[AgentAssignmentBrief] = None  # REMOVE this line
    status: Optional[StatusBrief] = None
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', 'campaign_influencer_id', 'agent_assignment_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class AssignedInfluencerListResponse(BaseModel):
    """Schema for paginated list of assigned influencers"""
    influencers: List[AssignedInfluencerResponse]
    pagination: PaginationInfo

class AssignedInfluencerStatsResponse(BaseModel):
    """Schema for assigned influencer statistics"""
    total_assigned: int
    by_status: dict
    by_type: dict
    by_agent: dict
    avg_attempts: float
    response_rate: float
    completion_rate: float

class RecordContactRequest(BaseModel):
    """Optional data for recording contact attempt"""
    notes: Optional[str] = Field(None, description="Notes about this contact attempt")
    custom_next_contact_hours: Optional[int] = Field(None, description="Override default followup delay")
    
class RecordContactResponse(BaseModel):
    """Response for contact attempt recording"""
    success: bool
    message: str
    assigned_influencer: AssignedInfluencerResponse
    next_template_info: Optional[Dict[str, Any]] = None  # Info about next template to use

    