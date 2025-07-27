# routes/api/v0/assigned_influencers.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.Http.Controllers.AssignedInfluencerController import AssignedInfluencerController
from app.Models.auth_models import User
from app.Schemas.assigned_influencer import (
    AssignedInfluencerCreate, AssignedInfluencerUpdate, AssignedInfluencerResponse,
    AssignedInfluencerListResponse, AssignedInfluencerStatusUpdate,
    AssignedInfluencerBulkStatusUpdate, AssignedInfluencerContactUpdate,
    AssignedInfluencerTransfer, AssignedInfluencerStatsResponse, RecordContactRequest,
    RecordContactResponse
)
from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission
)
from config.database import get_db

router = APIRouter(prefix="/assigned-influencers", tags=["Assigned Influencers"])

# Basic CRUD endpoints
@router.post("/", response_model=AssignedInfluencerResponse)
async def create_assigned_influencer(
    data: AssignedInfluencerCreate,
    current_user: User = Depends(has_permission("assignment:create")),
    db: Session = Depends(get_db)
):
    """Create a new assigned influencer"""
    return await AssignedInfluencerController.create_assigned_influencer(
        data.model_dump(), db
    )

@router.get("/", response_model=AssignedInfluencerListResponse)
async def get_assigned_influencers(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    agent_assignment_id: Optional[str] = Query(None, description="Filter by agent assignment ID"),
    campaign_influencer_id: Optional[str] = Query(None, description="Filter by campaign influencer ID"),
    status_id: Optional[str] = Query(None, description="Filter by status ID"),
    assignment_type: Optional[str] = Query(None, description="Filter by assignment type"),
    include_relations: bool = Query(False, description="Include related data"),
    sort_by: str = Query("assigned_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(has_permission("assigned_influencer:read")),
    db: Session = Depends(get_db)
):
    """Get assigned influencers with filtering and pagination"""
    return await AssignedInfluencerController.get_assigned_influencers(
        db=db,
        page=page,
        size=size,
        agent_assignment_id=agent_assignment_id,
        campaign_influencer_id=campaign_influencer_id,
        status_id=status_id,
        assignment_type=assignment_type,
        include_relations=include_relations,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/{assigned_influencer_id}", response_model=AssignedInfluencerResponse)
async def get_assigned_influencer(
    assigned_influencer_id: uuid.UUID,
    include_relations: bool = Query(True, description="Include related data"),
    current_user: User = Depends(has_permission("assigned_influencer:read")),
    db: Session = Depends(get_db)
):
    """Get an assigned influencer by ID"""
    return await AssignedInfluencerController.get_assigned_influencer(
        assigned_influencer_id, db, include_relations
    )

@router.put("/{assigned_influencer_id}", response_model=AssignedInfluencerResponse)
async def update_assigned_influencer(
    assigned_influencer_id: uuid.UUID,
    data: AssignedInfluencerUpdate,
    current_user: User = Depends(has_permission("assignment:update")),
    db: Session = Depends(get_db)
):
    """Update an assigned influencer"""
    return await AssignedInfluencerController.update_assigned_influencer(
        assigned_influencer_id, data.model_dump(exclude_unset=True), db
    )

@router.delete("/{assigned_influencer_id}")
async def delete_assigned_influencer(
    assigned_influencer_id: uuid.UUID,
    current_user: User = Depends(has_permission("assignment:delete")),
    db: Session = Depends(get_db)
):
    """Delete (archive) an assigned influencer"""
    return await AssignedInfluencerController.delete_assigned_influencer(
        assigned_influencer_id, db
    )

# Status management endpoints
@router.patch("/{assigned_influencer_id}/status", response_model=AssignedInfluencerResponse)
async def update_assigned_influencer_status(
    assigned_influencer_id: uuid.UUID,
    data: AssignedInfluencerStatusUpdate,
    current_user: User = Depends(has_permission("assignment:update")),
    db: Session = Depends(get_db)
):
    """Update only the status of an assigned influencer"""
    return await AssignedInfluencerController.update_status(
        assigned_influencer_id, data.status_id, db
    )

@router.patch("/bulk/status")
async def bulk_update_status(
    data: AssignedInfluencerBulkStatusUpdate,
    current_user: User = Depends(has_permission("assignment:update")),
    db: Session = Depends(get_db)
):
    """Bulk update status for multiple assigned influencers"""
    return await AssignedInfluencerController.bulk_update_status(
        data.influencer_ids, data.status_id, db
    )

# Contact management endpoints
@router.patch("/{assigned_influencer_id}/contact", response_model=AssignedInfluencerResponse)
async def update_contact_info(
    assigned_influencer_id: uuid.UUID,
    data: AssignedInfluencerContactUpdate,
    current_user: User = Depends(has_permission("assignment:update")),
    db: Session = Depends(get_db)
):
    """Update contact information for an assigned influencer"""
    return await AssignedInfluencerController.update_contact_info(
        assigned_influencer_id, data.model_dump(exclude_unset=True), db
    )

# Transfer endpoint
@router.post("/{assigned_influencer_id}/transfer", response_model=AssignedInfluencerResponse)
async def transfer_assigned_influencer(
    assigned_influencer_id: uuid.UUID,
    data: AssignedInfluencerTransfer,
    current_user: User = Depends(has_permission("assignment:update")),
    db: Session = Depends(get_db)
):
    """Transfer an assigned influencer to a different agent"""
    return await AssignedInfluencerController.transfer_to_agent(
        assigned_influencer_id,
        data.new_agent_assignment_id,
        data.transfer_reason,
        current_user.id,
        db
    )

# Query endpoints by related entities
@router.get("/agent-assignment/{agent_assignment_id}", response_model=AssignedInfluencerListResponse)
async def get_assigned_influencers_by_agent(
    agent_assignment_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    status_id: Optional[str] = Query(None, description="Filter by status ID"),
    assignment_type: Optional[str] = Query(None, description="Filter by assignment type"),
    type: Optional[str] = Query(None, description="Filter by type (active, archived, completed)"),  # ADD this line
    sort_by: str = Query("assigned_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(has_permission("assigned_influencer:read")),
    db: Session = Depends(get_db)
):
    """Get assigned influencers for a specific agent assignment"""
    return await AssignedInfluencerController.get_by_agent_assignment(
        agent_assignment_id=agent_assignment_id,
        db=db,
        page=page,
        size=size,
        status_id=status_id,
        assignment_type=assignment_type,
        type=type,  # ADD this line
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/campaign-influencer/{campaign_influencer_id}", response_model=AssignedInfluencerListResponse)
async def get_assigned_influencers_by_campaign_influencer(
    campaign_influencer_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    assignment_type: Optional[str] = Query(None, description="Filter by assignment type"),
    current_user: User = Depends(has_permission("assigned_influencer:read")),
    db: Session = Depends(get_db)
):
    """Get assigned influencers for a specific campaign influencer"""
    return await AssignedInfluencerController.get_by_campaign_influencer(
        campaign_influencer_id=campaign_influencer_id,
        db=db,
        page=page,
        size=size,
        assignment_type=assignment_type
    )

# Utility endpoints
@router.get("/overdue/contacts", response_model=AssignedInfluencerListResponse)
async def get_overdue_contacts(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    agent_assignment_id: Optional[str] = Query(None, description="Filter by agent assignment ID"),
    current_user: User = Depends(has_permission("assigned_influencer:read")),
    db: Session = Depends(get_db)
):
    """Get assigned influencers with overdue next contact dates"""
    return await AssignedInfluencerController.get_overdue_contacts(
        db=db,
        page=page,
        size=size,
        agent_assignment_id=agent_assignment_id
    )

# Statistics endpoint
@router.get("/stats/summary", response_model=AssignedInfluencerStatsResponse)
async def get_assigned_influencer_stats(
    agent_assignment_id: Optional[str] = Query(None, description="Filter by agent assignment ID"),
    campaign_list_id: Optional[str] = Query(None, description="Filter by campaign list ID"),
    current_user: User = Depends(has_permission("assigned_influencer:read")),
    db: Session = Depends(get_db)
):
    """Get statistics for assigned influencers"""
    return await AssignedInfluencerController.get_assigned_influencer_stats(
        db=db,
        agent_assignment_id=agent_assignment_id,
        campaign_list_id=campaign_list_id
    )

# Additional utility endpoints for agents
@router.get("/my-assignments/", response_model=AssignedInfluencerListResponse)
async def get_my_assigned_influencers(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    status_id: Optional[str] = Query(None, description="Filter by status ID"),
    assignment_type: Optional[str] = Query("active", description="Filter by assignment type"),
    current_user: User = Depends(has_role(["outreach_agent", "agent_manager"])),
    db: Session = Depends(get_db)
):
    """Get assigned influencers for the current user's agent assignments"""
    # This would need additional logic to find the user's agent assignments
    # For now, return empty list - would need to implement agent lookup
    return AssignedInfluencerListResponse(
        items=[],
        total=0,
        page=page,
        size=size,
        pages=1
    )

@router.post("/my-assignments/{assigned_influencer_id}/mark-contacted", response_model=AssignedInfluencerResponse)
async def mark_as_contacted(
    assigned_influencer_id: uuid.UUID,
    current_user: User = Depends(has_role(["outreach_agent", "agent_manager"])),
    db: Session = Depends(get_db)
):
    """Mark an assigned influencer as contacted (increment attempts, update last contacted)"""
    from datetime import datetime
    
    contact_data = {
        "attempts_made": None,  # Will be incremented in service
        "last_contacted_at": datetime.utcnow()
    }
    
    return await AssignedInfluencerController.update_contact_info(
        assigned_influencer_id, contact_data, db
    )

@router.post("/my-assignments/{assigned_influencer_id}/mark-responded", response_model=AssignedInfluencerResponse)
async def mark_as_responded(
    assigned_influencer_id: uuid.UUID,
    current_user: User = Depends(has_role(["outreach_agent", "agent_manager"])),
    db: Session = Depends(get_db)
):
    """Mark an assigned influencer as responded"""
    from datetime import datetime
    
    contact_data = {
        "responded_at": datetime.utcnow()
    }
    
    return await AssignedInfluencerController.update_contact_info(
        assigned_influencer_id, contact_data, db
    )


@router.post("/{assigned_influencer_id}/record-contact", response_model=RecordContactResponse)
async def record_contact_attempt(
    assigned_influencer_id: uuid.UUID,
    contact_data: Optional[RecordContactRequest] = None,
    current_user: User = Depends(has_permission("assigned_influencer:update")),
    db: Session = Depends(get_db)
):
    """
    Record a contact attempt for an assigned influencer
    
    This endpoint:
    1. Increments attempts_made by 1
    2. Sets last_contacted_at to current time
    3. Calculates next_contact_at based on message template followup sequence
    4. Updates total_contact_attempts in campaign_influencers table
    5. Optionally adds notes about the contact
    """
    contact_data_dict = contact_data.model_dump() if contact_data else None
    return await AssignedInfluencerController.record_contact_attempt(
        assigned_influencer_id, contact_data_dict, db
    )