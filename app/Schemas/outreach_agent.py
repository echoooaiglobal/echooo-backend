# app/Schemas/outreach_agent.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Brief schemas for related models
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

class UserBrief(BaseModel):
    id: str
    email: str
    full_name: str
    profile_image_url: Optional[str] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class AgentSocialConnectionBrief(BaseModel):
    id: str
    platform_id: str
    platform_username: str
    display_name: Optional[str] = None
    is_active: bool
    status_id: Optional[str] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'platform_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class AgentListAssignmentBrief(BaseModel):
    id: str
    campaign_list_id: str
    assignment_status: str
    assigned_influencers_count: int
    completed_influencers_count: int
    assigned_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'campaign_list_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Outreach Agent schemas
class OutreachAgentBase(BaseModel):
    assigned_user_id: str
    is_automation_enabled: bool = False
    automation_settings: Optional[Dict[str, Any]] = None
    is_available_for_assignment: bool = True
    status_id: Optional[str] = None

class OutreachAgentCreate(OutreachAgentBase):
    pass

class OutreachAgentUpdate(BaseModel):
    assigned_user_id: Optional[str] = None
    is_automation_enabled: Optional[bool] = None
    automation_settings: Optional[Dict[str, Any]] = None
    is_available_for_assignment: Optional[bool] = None
    status_id: Optional[str] = None
    current_automation_session_id: Optional[str] = None

class OutreachAgentResponse(BaseModel):
    id: str
    assigned_user_id: str
    active_lists_count: int
    active_influencers_count: int
    is_automation_enabled: bool
    automation_settings: Optional[Dict[str, Any]] = None
    messages_sent_today: int
    is_available_for_assignment: bool
    current_automation_session_id: Optional[str] = None
    last_activity_at: Optional[datetime] = None
    status_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    # Related data populated by controller
    assigned_user: Optional[UserBrief] = None
    status: Optional[StatusBrief] = None
    social_connections: Optional[List[AgentSocialConnectionBrief]] = None
    list_assignments: Optional[List[AgentListAssignmentBrief]] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'assigned_user_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Pagination schemas
class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

class OutreachAgentsPaginatedResponse(BaseModel):
    agents: List[OutreachAgentResponse]
    pagination: PaginationInfo
    
    model_config = {"from_attributes": True}

# Agent status update schemas
class AgentStatusUpdate(BaseModel):
    status_id: str

class AgentAvailabilityUpdate(BaseModel):
    is_available_for_assignment: bool

class AgentAutomationUpdate(BaseModel):
    is_automation_enabled: bool
    automation_settings: Optional[Dict[str, Any]] = None

# Agent statistics schemas
class AgentStatistics(BaseModel):
    total_agents: int
    active_agents: int
    available_agents: int
    automation_enabled_agents: int
    total_messages_today: int
    total_active_lists: int
    total_active_influencers: int

class AgentPerformanceMetrics(BaseModel):
    agent_id: str
    messages_sent_today: int
    active_lists_count: int
    active_influencers_count: int
    completion_rate: Optional[float] = None
    response_rate: Optional[float] = None
    last_activity_at: Optional[datetime] = None
    
    @field_validator('agent_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v