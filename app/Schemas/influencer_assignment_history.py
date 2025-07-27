# app/Schemas/influencer_assignment_history.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class TriggeredByEnum(str, Enum):
    system = "system"
    user = "user"
    agent = "agent"

class InfluencerAssignmentHistoryBase(BaseModel):
    """Base schema for influencer assignment history"""
    campaign_influencer_id: str = Field(..., description="ID of the campaign influencer")
    agent_assignment_id: str = Field(..., description="ID of the agent assignment")
    from_outreach_agent_id: Optional[str] = Field(default=None, description="ID of the previous agent")
    to_outreach_agent_id: str = Field(..., description="ID of the new agent")
    reassignment_reason_id: str = Field(..., description="ID of the reassignment reason")
    attempts_before_reassignment: Optional[int] = Field(default=0, description="Contact attempts before reassignment")
    reassignment_triggered_by: TriggeredByEnum = Field(..., description="Who/what triggered the reassignment")
    reassigned_by: Optional[str] = Field(default=None, description="ID of user who performed the reassignment")
    reassignment_notes: Optional[str] = Field(default=None, description="Additional notes about the reassignment")
    previous_assignment_data: Optional[Dict[str, Any]] = Field(default=None, description="Snapshot of previous assignment data")

    @field_validator('campaign_influencer_id', 'agent_assignment_id', 'from_outreach_agent_id', 
                     'to_outreach_agent_id', 'reassignment_reason_id', 'reassigned_by', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if v is not None and isinstance(v, uuid.UUID):
            return str(v)
        return v

class InfluencerAssignmentHistoryCreate(InfluencerAssignmentHistoryBase):
    """Schema for creating assignment history records"""
    pass

class InfluencerAssignmentHistoryUpdate(BaseModel):
    """Schema for updating assignment history records (limited fields)"""
    reassignment_notes: Optional[str] = None
    previous_assignment_data: Optional[Dict[str, Any]] = None

class InfluencerAssignmentHistoryBulkCreate(BaseModel):
    """Schema for bulk creating assignment history records"""
    histories: List[InfluencerAssignmentHistoryCreate] = Field(..., description="List of history records to create")

# Related schemas for nested data
class ReassignmentReasonBrief(BaseModel):
    """Brief reassignment reason information"""
    id: str
    code: str
    name: str
    description: Optional[str] = None
    is_system_triggered: bool
    is_user_triggered: bool
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class OutreachAgentBrief(BaseModel):
    """Brief outreach agent information"""
    id: str
    assigned_user_id: str
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

class UserBrief(BaseModel):
    """Brief user information"""
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class CampaignInfluencerHistoryBrief(BaseModel):
    """Brief campaign influencer information for history"""
    id: str
    campaign_list_id: str
    social_account_id: str
    status_id: str
    total_contact_attempts: int
    collaboration_price: Optional[float] = None
    is_ready_for_onboarding: bool
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', 'campaign_list_id', 'social_account_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class AgentAssignmentHistoryBrief(BaseModel):
    """Brief agent assignment information for history"""
    id: str
    outreach_agent_id: str
    campaign_list_id: str
    status_id: str
    assigned_influencers_count: int
    completed_influencers_count: int
    assigned_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', 'outreach_agent_id', 'campaign_list_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class InfluencerAssignmentHistoryResponse(BaseModel):
    """Schema for assignment history responses"""
    id: str
    campaign_influencer_id: str
    agent_assignment_id: str
    from_outreach_agent_id: Optional[str] = None
    to_outreach_agent_id: str
    reassignment_reason_id: str
    attempts_before_reassignment: int
    reassignment_triggered_by: TriggeredByEnum
    reassigned_by: Optional[str] = None
    reassignment_notes: Optional[str] = None
    previous_assignment_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    # Related objects (optional for detailed responses)
    campaign_influencer: Optional[CampaignInfluencerHistoryBrief] = None
    agent_assignment: Optional[AgentAssignmentHistoryBrief] = None
    reassignment_reason: Optional[ReassignmentReasonBrief] = None
    from_agent: Optional[OutreachAgentBrief] = None
    to_agent: Optional[OutreachAgentBrief] = None
    reassigned_by_user: Optional[UserBrief] = None
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', 'campaign_influencer_id', 'agent_assignment_id', 'from_outreach_agent_id',
                     'to_outreach_agent_id', 'reassignment_reason_id', 'reassigned_by', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if v is not None and isinstance(v, uuid.UUID):
            return str(v)
        return v

class InfluencerAssignmentHistoryListResponse(BaseModel):
    """Schema for paginated list of assignment histories"""
    items: List[InfluencerAssignmentHistoryResponse]
    total: int
    page: int
    size: int
    pages: int

class AssignmentHistoryStatsResponse(BaseModel):
    """Schema for assignment history statistics"""
    total_reassignments: int
    by_trigger: Dict[str, int]
    by_reason: Dict[str, int]
    by_agent: Dict[str, int]
    avg_attempts_before_reassignment: float
    most_common_reasons: List[Dict[str, Any]]
    reassignments_by_month: List[Dict[str, Any]]

class ReassignmentReasonResponse(BaseModel):
    """Schema for reassignment reason responses"""
    id: str
    code: str
    name: str
    description: Optional[str] = None
    is_system_triggered: bool
    is_user_triggered: bool
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class ReassignmentReasonCreate(BaseModel):
    """Schema for creating reassignment reasons"""
    code: str = Field(..., description="Unique code for the reason")
    name: str = Field(..., description="Display name for the reason")
    description: Optional[str] = Field(default=None, description="Detailed description")
    is_system_triggered: bool = Field(default=True, description="Can be triggered by system")
    is_user_triggered: bool = Field(default=True, description="Can be triggered by user")
    is_active: bool = Field(default=True, description="Is active for new assignments")
    display_order: int = Field(default=0, description="Display order in UI")

class ReassignmentReasonUpdate(BaseModel):
    """Schema for updating reassignment reasons"""
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_system_triggered: Optional[bool] = None
    is_user_triggered: Optional[bool] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None