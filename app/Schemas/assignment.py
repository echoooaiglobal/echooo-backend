# app/Schemas/assignment.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Agent Brief Schema
class AgentBrief(BaseModel):
    id: str
    name: str
    platform_id: str
    is_available: bool
    status_id: Optional[str] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'platform_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Campaign Brief Schema
class CampaignBrief(BaseModel):
    id: str
    name: str
    company_id: str
    brand_name: Optional[str] = None
    description: Optional[str] = None
    status_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'company_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Campaign List Brief Schema (Enhanced)
class CampaignListBrief(BaseModel):
    id: str
    campaign_id: str
    name: str
    description: Optional[str] = None
    message_template_id: Optional[str] = None
    notes: Optional[str] = None  # New field
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'campaign_id', 'message_template_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Status Brief Schema
class StatusBrief(BaseModel):
    id: str
    name: str
    model: str
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Assignment Response Schema
class AssignmentResponse(BaseModel):
    id: str
    list_id: str
    agent_id: str
    status_id: str
    created_at: datetime
    updated_at: datetime
    
    # Related data
    agent: Optional[AgentBrief] = None
    campaign_list: Optional[CampaignListBrief] = None
    campaign: Optional[CampaignBrief] = None
    status: Optional[StatusBrief] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'list_id', 'agent_id', 'status_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Assignments Overview Response
class AssignmentsResponse(BaseModel):
    assignments: List[AssignmentResponse]
    total_assignments: int
    agent_info: Optional[AgentBrief] = None  # For single agent view
    
    model_config = {"from_attributes": True}