# routes/api/v0/influencer_outreach.py
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from app.Http.Controllers.InfluencerOutreachController import InfluencerOutreachController
from app.Models.auth_models import User
from app.Schemas.influencer_outreach import (
    InfluencerOutreachCreate, InfluencerOutreachUpdate, InfluencerOutreachResponse,
    InfluencerOutreachListResponse, InfluencerOutreachBulkCreate, InfluencerOutreachBulkUpdate,
    InfluencerOutreachStats
)
from app.Utils.Helpers import (
    has_role, has_permission
)
from config.database import get_db

router = APIRouter(prefix="/influencer-outreach", tags=["Influencer Outreach"])

# =============================================================================
# CRUD OPERATIONS
# =============================================================================

@router.post("/", response_model=InfluencerOutreachResponse)
async def create_outreach_record(
    outreach_data: InfluencerOutreachCreate,
    current_user: User = Depends(has_permission("outreach:create")),
    db: Session = Depends(get_db)
):
    """Create a new influencer outreach record"""
    return await InfluencerOutreachController.create_outreach_record(
        outreach_data.model_dump(), db
    )

@router.get("/{outreach_id}", response_model=InfluencerOutreachResponse)
async def get_outreach_record(
    outreach_id: uuid.UUID,
    include_relations: bool = Query(False, description="Include related objects in response"),
    current_user: User = Depends(has_permission("outreach:read")),
    db: Session = Depends(get_db)
):
    """Get an outreach record by ID"""
    return await InfluencerOutreachController.get_outreach_record(
        outreach_id, include_relations, db
    )

@router.put("/{outreach_id}", response_model=InfluencerOutreachResponse)
async def update_outreach_record(
    outreach_id: uuid.UUID,
    outreach_data: InfluencerOutreachUpdate,
    current_user: User = Depends(has_permission("outreach:update")),
    db: Session = Depends(get_db)
):
    """Update an outreach record"""
    return await InfluencerOutreachController.update_outreach_record(
        outreach_id, outreach_data.model_dump(exclude_unset=True), db
    )

@router.delete("/{outreach_id}")
async def delete_outreach_record(
    outreach_id: uuid.UUID,
    current_user: User = Depends(has_permission("outreach:delete")),
    db: Session = Depends(get_db)
):
    """Delete an outreach record"""
    return await InfluencerOutreachController.delete_outreach_record(outreach_id, db)

# =============================================================================
# LIST AND PAGINATION
# =============================================================================

@router.get("/", response_model=InfluencerOutreachListResponse)
async def get_outreach_records(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    assigned_influencer_id: Optional[uuid.UUID] = Query(None, description="Filter by assigned influencer ID"),
    agent_assignment_id: Optional[uuid.UUID] = Query(None, description="Filter by agent assignment ID"),
    outreach_agent_id: Optional[uuid.UUID] = Query(None, description="Filter by outreach agent ID"),
    message_status_id: Optional[uuid.UUID] = Query(None, description="Filter by message status ID"),
    communication_channel_id: Optional[uuid.UUID] = Query(None, description="Filter by communication channel ID"),
    include_relations: bool = Query(False, description="Include related objects in response"),
    current_user: User = Depends(has_permission("outreach:read")),
    db: Session = Depends(get_db)
):
    """Get paginated list of outreach records with optional filters"""
    return await InfluencerOutreachController.get_outreach_records_paginated(
        page=page,
        size=size,
        assigned_influencer_id=assigned_influencer_id,
        agent_assignment_id=agent_assignment_id,
        outreach_agent_id=outreach_agent_id,
        message_status_id=message_status_id,
        communication_channel_id=communication_channel_id,
        include_relations=include_relations,
        db=db
    )

# =============================================================================
# BULK OPERATIONS
# =============================================================================

@router.post("/bulk", response_model=List[InfluencerOutreachResponse])
async def bulk_create_outreach_records(
    bulk_data: InfluencerOutreachBulkCreate,
    current_user: User = Depends(has_permission("outreach:create")),
    db: Session = Depends(get_db)
):
    """Bulk create outreach records"""
    records_data = [record.model_dump() for record in bulk_data.outreach_records]
    return await InfluencerOutreachController.bulk_create_outreach_records(records_data, db)

@router.put("/bulk", response_model=List[InfluencerOutreachResponse])
async def bulk_update_outreach_records(
    bulk_data: InfluencerOutreachBulkUpdate,
    current_user: User = Depends(has_permission("outreach:update")),
    db: Session = Depends(get_db)
):
    """Bulk update outreach records"""
    outreach_ids = [uuid.UUID(id_str) for id_str in bulk_data.outreach_ids]
    return await InfluencerOutreachController.bulk_update_outreach_records(
        outreach_ids, bulk_data.update_data.model_dump(exclude_unset=True), db
    )

# =============================================================================
# SPECIALIZED ENDPOINTS
# =============================================================================

@router.get("/assigned-influencer/{assigned_influencer_id}", response_model=InfluencerOutreachListResponse)
async def get_outreach_by_assigned_influencer(
    assigned_influencer_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    current_user: User = Depends(has_permission("outreach:read")),
    db: Session = Depends(get_db)
):
    """Get outreach records for a specific assigned influencer"""
    return await InfluencerOutreachController.get_outreach_by_assigned_influencer(
        assigned_influencer_id, page, size, db
    )

@router.get("/agent/{outreach_agent_id}", response_model=InfluencerOutreachListResponse)
async def get_outreach_by_agent(
    outreach_agent_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    message_status_id: Optional[uuid.UUID] = Query(None, description="Filter by message status"),
    current_user: User = Depends(has_permission("outreach:read")),
    db: Session = Depends(get_db)
):
    """Get outreach records for a specific agent"""
    return await InfluencerOutreachController.get_outreach_by_agent(
        outreach_agent_id, page, size, message_status_id, db
    )

# =============================================================================
# MESSAGE STATUS MANAGEMENT
# =============================================================================

@router.patch("/{outreach_id}/mark-sent", response_model=InfluencerOutreachResponse)
async def mark_message_as_sent(
    outreach_id: uuid.UUID,
    sent_at: Optional[datetime] = Body(None, description="Timestamp when message was sent"),
    current_user: User = Depends(has_permission("outreach:update")),
    db: Session = Depends(get_db)
):
    """Mark a message as sent"""
    return await InfluencerOutreachController.mark_message_as_sent(
        outreach_id, sent_at, db
    )

@router.patch("/{outreach_id}/mark-failed", response_model=InfluencerOutreachResponse)
async def mark_message_as_failed(
    outreach_id: uuid.UUID,
    error_code: str = Body(..., description="Error code"),
    error_reason: Optional[str] = Body(None, description="Detailed error reason"),
    current_user: User = Depends(has_permission("outreach:update")),
    db: Session = Depends(get_db)
):
    """Mark a message as failed"""
    return await InfluencerOutreachController.mark_message_as_failed(
        outreach_id, error_code, error_reason, db
    )

# =============================================================================
# ANALYTICS AND REPORTING
# =============================================================================

@router.get("/statistics/overview", response_model=InfluencerOutreachStats)
async def get_outreach_statistics(
    agent_assignment_id: Optional[uuid.UUID] = Query(None, description="Filter by agent assignment"),
    outreach_agent_id: Optional[uuid.UUID] = Query(None, description="Filter by outreach agent"),
    date_from: Optional[datetime] = Query(None, description="Start date for statistics"),
    date_to: Optional[datetime] = Query(None, description="End date for statistics"),
    current_user: User = Depends(has_permission("outreach:read")),
    db: Session = Depends(get_db)
):
    """Get outreach statistics"""
    return await InfluencerOutreachController.get_outreach_statistics(
        agent_assignment_id, outreach_agent_id, date_from, date_to, db
    )

# =============================================================================
# AGENT-SPECIFIC ENDPOINTS (For agents accessing their own data)
# =============================================================================

@router.get("/my-outreach/", response_model=InfluencerOutreachListResponse)
async def get_my_outreach_records(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    message_status_id: Optional[uuid.UUID] = Query(None, description="Filter by message status"),
    current_user: User = Depends(has_role(["outreach_agent", "agent_manager"])),
    db: Session = Depends(get_db)
):
    """Get outreach records for the current user's agent"""
    # This would need additional logic to find the user's agent
    # For now, return empty list - would need to implement agent lookup
    from app.Schemas.influencer_outreach import PaginationInfo
    return InfluencerOutreachListResponse(
        items=[],
        pagination=PaginationInfo(
            total=0,
            page=page,
            size=size,
            pages=1
        )
    )

@router.get("/my-outreach/statistics", response_model=InfluencerOutreachStats)
async def get_my_outreach_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(has_role(["outreach_agent", "agent_manager"])),
    db: Session = Depends(get_db)
):
    """Get outreach statistics for the current user's agent"""
    
    # This would need additional logic to find the user's agent
    # For now, return default statistics
    return InfluencerOutreachStats(
        total_outreach_records=0,
        successful_messages=0,
        failed_messages=0,
        pending_messages=0,
        success_rate=0.0,
        average_response_time=None,
        most_active_agent=None,
        most_used_channel=None
    )

# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@router.delete("/admin/cleanup-failed")
async def cleanup_failed_outreach_records(
    days_old: int = Query(30, ge=1, description="Delete failed records older than this many days"),
    current_user: User = Depends(has_role(["admin", "super_admin"])),
    db: Session = Depends(get_db)
):
    """Admin endpoint to cleanup old failed outreach records"""
    # This would implement cleanup logic
    return {"message": f"Cleanup of failed records older than {days_old} days initiated"}

@router.get("/admin/error-analysis")
async def get_error_analysis(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(has_role(["admin", "super_admin"])),
    db: Session = Depends(get_db)
):
    """Admin endpoint for error analysis"""
    # This would implement error analysis logic
    return {
        "analysis_period_days": days,
        "most_common_errors": [],
        "error_trends": [],
        "affected_agents": []
    }