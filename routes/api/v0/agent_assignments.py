# routes/api/v0/agent_assignments.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.Http.Controllers.AgentAssignmentController import AgentAssignmentController
from app.Models.auth_models import User
from app.Schemas.agent_assignment import (
    AgentAssignmentCreate, AgentAssignmentUpdate, AgentAssignmentResponse,
    AgentAssignmentsPaginatedResponse, AgentAssignmentStatsResponse,
    AgentAssignmentStatusUpdate, AgentAssignmentCountsUpdate
)
from app.Utils.Helpers import (
    has_permission
)
from config.database import get_db

router = APIRouter(prefix="/agent-assignments", tags=["Agent Assignments"])

# Get current user's agent assignments (for outreach agent dashboard)
@router.get("/", response_model=AgentAssignmentsPaginatedResponse)
async def get_my_assignments(
    skip: int = Query(0, ge=0, description="Number of assignments to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of assignments to return"),
    current_user: User = Depends(has_permission("agent_assignment:read")),
    db: Session = Depends(get_db)
):
    """
    Get assignments for the current user's outreach agent
    
    This endpoint automatically finds the outreach agent associated with the current user
    and returns their assignments. Perfect for outreach agent dashboards.
    
    - **skip**: Number of assignments to skip for pagination
    - **limit**: Maximum number of assignments to return
    """
    return await AgentAssignmentController.get_my_assignments(
        skip=skip,
        limit=limit,
        current_user=current_user,
        db=db
    )

# Get all assignments with filtering and pagination (for administrators)
@router.get("/all", response_model=AgentAssignmentsPaginatedResponse)
async def get_all_assignments(
    skip: int = Query(0, ge=0, description="Number of assignments to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of assignments to return"),
    status_filter: Optional[str] = Query(None, description="Filter by status name"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    campaign_list_id: Optional[str] = Query(None, description="Filter by campaign list ID"),
    include_deleted: bool = Query(False, description="Include soft-deleted assignments"),
    current_user: User = Depends(has_permission("agent_assignment:admin")),  # Higher permission for admin
    db: Session = Depends(get_db)
):
    """
    Get all agent assignments with optional filtering and pagination (Admin only)
    
    - **skip**: Number of assignments to skip for pagination
    - **limit**: Maximum number of assignments to return (1-1000)
    - **status_filter**: Filter assignments by status name
    - **agent_id**: Filter assignments by specific agent
    - **campaign_list_id**: Filter assignments by specific campaign list
    - **include_deleted**: Include soft-deleted assignments in results
    """
    return await AgentAssignmentController.get_all_assignments(
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        agent_id=agent_id,
        campaign_list_id=campaign_list_id,
        include_deleted=include_deleted,
        current_user=current_user,
        db=db
    )

# Get assignment statistics
@router.get("/stats", response_model=AgentAssignmentStatsResponse)
async def get_assignment_stats(
    current_user: User = Depends(has_permission("agent_assignment:read")),
    db: Session = Depends(get_db)
):
    """
    Get agent assignment statistics
    
    Returns comprehensive statistics about all agent assignments including:
    - Total assignments by status
    - Influencer counts and completion rates
    - Overall performance metrics
    """
    return await AgentAssignmentController.get_assignment_stats(
        current_user=current_user,
        db=db
    )

# Get assignments by specific agent (for admin use)
@router.get("/agent/{agent_id}", response_model=AgentAssignmentsPaginatedResponse)
async def get_assignments_by_agent(
    agent_id: str,
    skip: int = Query(0, ge=0, description="Number of assignments to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of assignments to return"),
    current_user: User = Depends(has_permission("agent_assignment:admin")),  # Admin permission
    db: Session = Depends(get_db)
):
    """
    Get all assignments for a specific agent (Admin only)
    
    - **agent_id**: ID of the agent to get assignments for
    - **skip**: Number of assignments to skip for pagination
    - **limit**: Maximum number of assignments to return
    """
    return await AgentAssignmentController.get_assignments_by_agent(
        agent_id=agent_id,
        skip=skip,
        limit=limit,
        current_user=current_user,
        db=db
    )

# Get assignments by campaign list
@router.get("/campaign-list/{campaign_list_id}", response_model=AgentAssignmentsPaginatedResponse)
async def get_assignments_by_campaign_list(
    campaign_list_id: str,
    skip: int = Query(0, ge=0, description="Number of assignments to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of assignments to return"),
    current_user: User = Depends(has_permission("agent_assignment:read")),
    db: Session = Depends(get_db)
):
    """
    Get all assignments for a specific campaign list
    
    - **campaign_list_id**: ID of the campaign list to get assignments for
    - **skip**: Number of assignments to skip for pagination
    - **limit**: Maximum number of assignments to return
    """
    return await AgentAssignmentController.get_assignments_by_campaign_list(
        campaign_list_id=campaign_list_id,
        skip=skip,
        limit=limit,
        current_user=current_user,
        db=db
    )

# Get specific assignment
@router.get("/{assignment_id}", response_model=AgentAssignmentResponse)
async def get_assignment(
    assignment_id: str,
    current_user: User = Depends(has_permission("agent_assignment:read")),
    db: Session = Depends(get_db)
):
    """
    Get a specific agent assignment by ID
    
    - **assignment_id**: ID of the assignment to retrieve
    """
    return await AgentAssignmentController.get_assignment(
        assignment_id=assignment_id,
        current_user=current_user,
        db=db
    )

# Create new assignment
@router.post("/", response_model=AgentAssignmentResponse)
async def create_assignment(
    assignment_data: AgentAssignmentCreate,
    current_user: User = Depends(has_permission("assignment:create")),
    db: Session = Depends(get_db)
):
    """
    Create a new agent assignment
    
    - **outreach_agent_id**: ID of the agent to assign
    - **campaign_list_id**: ID of the campaign list to assign
    - **status_id**: Initial status of the assignment
    - **assigned_influencers_count**: Number of influencers assigned (optional)
    - **completed_influencers_count**: Number of influencers completed (optional)
    - **pending_influencers_count**: Number of influencers pending (optional)
    """
    return await AgentAssignmentController.create_assignment(
        assignment_data=assignment_data.model_dump(exclude_unset=True),
        current_user=current_user,
        db=db
    )

# Update assignment
@router.put("/{assignment_id}", response_model=AgentAssignmentResponse)
async def update_assignment(
    assignment_id: str,
    assignment_data: AgentAssignmentUpdate,
    current_user: User = Depends(has_permission("assignment:update")),
    db: Session = Depends(get_db)
):
    """
    Update an agent assignment
    
    - **assignment_id**: ID of the assignment to update
    - All fields in the request body are optional and will only update provided values
    """
    return await AgentAssignmentController.update_assignment(
        assignment_id=assignment_id,
        assignment_data=assignment_data.model_dump(exclude_unset=True),
        current_user=current_user,
        db=db
    )

# Update assignment status
@router.patch("/{assignment_id}/status", response_model=AgentAssignmentResponse)
async def update_assignment_status(
    assignment_id: str,
    status_update: AgentAssignmentStatusUpdate,
    current_user: User = Depends(has_permission("assignment:update")),
    db: Session = Depends(get_db)
):
    """
    Update only the status of an agent assignment
    
    - **assignment_id**: ID of the assignment to update
    - **status_id**: New status ID for the assignment
    """
    return await AgentAssignmentController.update_assignment_status(
        assignment_id=assignment_id,
        status_id=status_update.status_id,
        current_user=current_user,
        db=db
    )

# Update assignment counts
@router.patch("/{assignment_id}/counts", response_model=AgentAssignmentResponse)
async def update_assignment_counts(
    assignment_id: str,
    counts_update: AgentAssignmentCountsUpdate,
    current_user: User = Depends(has_permission("assignment:update")),
    db: Session = Depends(get_db)
):
    """
    Update influencer counts for an assignment
    
    - **assignment_id**: ID of the assignment to update
    - **assigned_influencers_count**: New assigned influencers count (optional)
    - **completed_influencers_count**: New completed influencers count (optional)
    - **pending_influencers_count**: New pending influencers count (optional)
    """
    return await AgentAssignmentController.update_assignment_counts(
        assignment_id=assignment_id,
        counts_data=counts_update.model_dump(exclude_unset=True),
        current_user=current_user,
        db=db
    )

# Soft delete assignment
@router.delete("/{assignment_id}", response_model=AgentAssignmentResponse)
async def delete_assignment(
    assignment_id: str,
    hard_delete: bool = Query(False, description="Perform hard delete instead of soft delete"),
    current_user: User = Depends(has_permission("assignment:delete")),
    db: Session = Depends(get_db)
):
    """
    Delete an agent assignment
    
    - **assignment_id**: ID of the assignment to delete
    - **hard_delete**: If true, performs permanent deletion; otherwise soft deletes (default: false)
    
    By default, this performs a soft delete (sets deleted_at timestamp).
    Use hard_delete=true for permanent deletion.
    """
    return await AgentAssignmentController.delete_assignment(
        assignment_id=assignment_id,
        soft_delete=not hard_delete,
        current_user=current_user,
        db=db
    )