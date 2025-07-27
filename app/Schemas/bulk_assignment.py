# app/Schemas/bulk_assignment.py

from pydantic import BaseModel, Field, UUID4
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class AssignmentStrategy(str, Enum):
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    MANUAL = "manual"

class BulkAssignmentRequest(BaseModel):
    campaign_list_id: UUID4 = Field(..., description="ID of the campaign list to assign")
    strategy: AssignmentStrategy = Field(default=AssignmentStrategy.ROUND_ROBIN, description="Assignment distribution strategy")
    preferred_agent_ids: Optional[List[UUID4]] = Field(None, description="Preferred agents for assignment (optional)")
    max_influencers_per_agent: Optional[int] = Field(None, description="Override default max influencers per agent")
    force_new_assignments: bool = Field(default=False, description="Force creation of new assignments instead of using existing ones")

class AgentAssignmentSummary(BaseModel):
    agent_id: UUID4
    agent_assignment_id: UUID4
    assigned_influencers_count: int = Field(..., description="Number of influencers assigned in this API call")
    total_influencers_in_assignment: int = Field(..., description="Total influencers in this assignment (including previous)")
    is_new_assignment: bool
    influencer_ids: List[UUID4] = Field(..., description="IDs of influencers assigned in this API call")

class BulkAssignmentResponse(BaseModel):
    assignment_summary: Dict[str, Any]
    agent_assignments: List[AgentAssignmentSummary]
    unassigned_influencers: List[UUID4] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    success_message: Optional[str] = Field(None, description="User-friendly success message")

    class Config:
        json_encoders = {
            UUID4: str,
            datetime: lambda v: v.isoformat()
        }

class BulkAssignmentValidationRequest(BaseModel):
    campaign_list_id: UUID4
    preferred_agent_ids: Optional[List[UUID4]] = None

class AgentCapacityInfo(BaseModel):
    agent_id: UUID4
    current_influencers_count: int
    max_concurrent_influencers: int
    available_capacity: int
    existing_assignments_for_list: List[UUID4] = Field(default_factory=list)
    can_accept_new: bool

class BulkAssignmentValidationResponse(BaseModel):
    campaign_list_info: Dict[str, Any]
    available_agents: List[AgentCapacityInfo]
    total_unassigned_influencers: int
    total_available_capacity: int
    can_assign_all: bool
    recommendations: List[str] = Field(default_factory=list)

class ReassignmentRequest(BaseModel):
    assigned_influencer_id: UUID4
    reason: str = Field(..., description="Reason for reassignment")
    prefer_existing_assignments: bool = Field(default=True, description="Prefer agents already working on same campaign list")

class ReassignmentResponse(BaseModel):
    success: bool
    new_assignment: Optional[AgentAssignmentSummary] = None
    assignment_history_id: UUID4
    message: str