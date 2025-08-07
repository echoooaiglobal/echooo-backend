# routes/api/v0/influencer_assignment_histories.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from app.Http.Controllers.InfluencerAssignmentHistoryController import (
    InfluencerAssignmentHistoryController, ReassignmentReasonController
)
from app.Models.auth_models import User
from app.Schemas.influencer_assignment_history import (
    InfluencerAssignmentHistoryCreate, InfluencerAssignmentHistoryUpdate,
    InfluencerAssignmentHistoryResponse, InfluencerAssignmentHistoryListResponse,
    InfluencerAssignmentHistoryBulkCreate, AssignmentHistoryStatsResponse,
    ReassignmentReasonCreate, ReassignmentReasonUpdate, ReassignmentReasonResponse
)
from app.Utils.Helpers import (
    has_role, has_permission
)
from config.database import get_db

router = APIRouter(prefix="/assignment-histories", tags=["Assignment Histories"])

# Assignment History CRUD endpoints
@router.post("/", response_model=InfluencerAssignmentHistoryResponse)
async def create_assignment_history(
    data: InfluencerAssignmentHistoryCreate,
    current_user: User = Depends(has_permission("assignment_history:create")),
    db: Session = Depends(get_db)
):
    """Create a new assignment history record"""
    return await InfluencerAssignmentHistoryController.create_assignment_history(
        data.model_dump(), db
    )

@router.get("/", response_model=InfluencerAssignmentHistoryListResponse)
async def get_assignment_histories(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    campaign_influencer_id: Optional[str] = Query(None, description="Filter by campaign influencer ID"),
    agent_assignment_id: Optional[str] = Query(None, description="Filter by agent assignment ID"),
    from_agent_id: Optional[str] = Query(None, description="Filter by from agent ID"),
    to_agent_id: Optional[str] = Query(None, description="Filter by to agent ID"),
    reassignment_reason_id: Optional[str] = Query(None, description="Filter by reassignment reason ID"),
    triggered_by: Optional[str] = Query(None, description="Filter by trigger type (system/user/agent)"),
    reassigned_by: Optional[str] = Query(None, description="Filter by user who performed reassignment"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    include_relations: bool = Query(False, description="Include related data"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(has_permission("assignment_history:read")),
    db: Session = Depends(get_db)
):
    """Get assignment histories with filtering and pagination"""
    return await InfluencerAssignmentHistoryController.get_assignment_histories(
        db=db,
        page=page,
        size=size,
        campaign_influencer_id=campaign_influencer_id,
        agent_assignment_id=agent_assignment_id,
        from_agent_id=from_agent_id,
        to_agent_id=to_agent_id,
        reassignment_reason_id=reassignment_reason_id,
        triggered_by=triggered_by,
        reassigned_by=reassigned_by,
        start_date=start_date,
        end_date=end_date,
        include_relations=include_relations,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/{history_id}", response_model=InfluencerAssignmentHistoryResponse)
async def get_assignment_history(
    history_id: uuid.UUID,
    include_relations: bool = Query(True, description="Include related data"),
    current_user: User = Depends(has_permission("assignment_history:read")),
    db: Session = Depends(get_db)
):
    """Get assignment history by ID"""
    return await InfluencerAssignmentHistoryController.get_assignment_history(
        history_id, db, include_relations
    )

@router.put("/{history_id}", response_model=InfluencerAssignmentHistoryResponse)
async def update_assignment_history(
    history_id: uuid.UUID,
    data: InfluencerAssignmentHistoryUpdate,
    current_user: User = Depends(has_permission("assignment_history:update")),
    db: Session = Depends(get_db)
):
    """Update assignment history (limited fields)"""
    return await InfluencerAssignmentHistoryController.update_assignment_history(
        history_id, data.model_dump(exclude_unset=True), db
    )

# Bulk operations
@router.post("/bulk", response_model=List[InfluencerAssignmentHistoryResponse])
async def bulk_create_assignment_histories(
    data: InfluencerAssignmentHistoryBulkCreate,
    current_user: User = Depends(has_permission("assignment_history:create")),
    db: Session = Depends(get_db)
):
    """Bulk create assignment history records"""
    histories_data = [history.model_dump() for history in data.histories]
    return await InfluencerAssignmentHistoryController.bulk_create_assignment_histories(
        histories_data, db
    )

# Query endpoints by related entities
@router.get("/campaign-influencer/{campaign_influencer_id}", response_model=InfluencerAssignmentHistoryListResponse)
async def get_histories_by_campaign_influencer(
    campaign_influencer_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(has_permission("assignment_history:read")),
    db: Session = Depends(get_db)
):
    """Get assignment histories for a specific campaign influencer"""
    return await InfluencerAssignmentHistoryController.get_by_campaign_influencer(
        campaign_influencer_id=campaign_influencer_id,
        db=db,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/agent/{agent_id}", response_model=InfluencerAssignmentHistoryListResponse)
async def get_histories_by_agent(
    agent_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    direction: str = Query("to", description="Direction filter (to/from/both)"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(has_permission("assignment_history:read")),
    db: Session = Depends(get_db)
):
    """Get assignment histories for a specific agent"""
    return await InfluencerAssignmentHistoryController.get_by_agent(
        agent_id=agent_id,
        db=db,
        page=page,
        size=size,
        direction=direction,
        sort_by=sort_by,
        sort_order=sort_order
    )

# Statistics endpoint
@router.get("/stats/summary", response_model=AssignmentHistoryStatsResponse)
async def get_assignment_history_stats(
    campaign_influencer_id: Optional[str] = Query(None, description="Filter by campaign influencer ID"),
    agent_assignment_id: Optional[str] = Query(None, description="Filter by agent assignment ID"),
    from_agent_id: Optional[str] = Query(None, description="Filter by from agent ID"),
    to_agent_id: Optional[str] = Query(None, description="Filter by to agent ID"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    current_user: User = Depends(has_permission("assignment_history:read")),
    db: Session = Depends(get_db)
):
    """Get statistics for assignment histories"""
    return await InfluencerAssignmentHistoryController.get_assignment_history_stats(
        db=db,
        campaign_influencer_id=campaign_influencer_id,
        agent_assignment_id=agent_assignment_id,
        from_agent_id=from_agent_id,
        to_agent_id=to_agent_id,
        start_date=start_date,
        end_date=end_date
    )

# Reassignment Reasons endpoints
@router.get("/reasons/", response_model=List[ReassignmentReasonResponse])
async def get_reassignment_reasons(
    active_only: bool = Query(True, description="Return only active reasons"),
    triggered_by: Optional[str] = Query(None, description="Filter by trigger type (system/user)"),
    current_user: User = Depends(has_permission("assignment_history:read")),
    db: Session = Depends(get_db)
):
    """Get all reassignment reasons"""
    return await ReassignmentReasonController.get_all_reasons(
        db, active_only, triggered_by
    )

@router.get("/reasons/{reason_id}", response_model=ReassignmentReasonResponse)
async def get_reassignment_reason(
    reason_id: uuid.UUID,
    current_user: User = Depends(has_permission("assignment_history:read")),
    db: Session = Depends(get_db)
):
    """Get reassignment reason by ID"""
    return await ReassignmentReasonController.get_reason(reason_id, db)

@router.post("/reasons/", response_model=ReassignmentReasonResponse)
async def create_reassignment_reason(
    data: ReassignmentReasonCreate,
    current_user: User = Depends(has_role(["platform_admin", "system_admin"])),
    db: Session = Depends(get_db)
):
    """Create a new reassignment reason"""
    return await ReassignmentReasonController.create_reason(
        data.model_dump(), db
    )

@router.put("/reasons/{reason_id}", response_model=ReassignmentReasonResponse)
async def update_reassignment_reason(
    reason_id: uuid.UUID,
    data: ReassignmentReasonUpdate,
    current_user: User = Depends(has_role(["platform_admin", "system_admin"])),
    db: Session = Depends(get_db)
):
    """Update a reassignment reason"""
    return await ReassignmentReasonController.update_reason(
        reason_id, data.model_dump(exclude_unset=True), db
    )

@router.delete("/reasons/{reason_id}")
async def delete_reassignment_reason(
    reason_id: uuid.UUID,
    current_user: User = Depends(has_role(["platform_admin", "system_admin"])),
    db: Session = Depends(get_db)
):
    """Delete (deactivate) a reassignment reason"""
    return await ReassignmentReasonController.delete_reason(reason_id, db)

# Agent-specific endpoints
@router.get("/my-reassignments/", response_model=InfluencerAssignmentHistoryListResponse)
async def get_my_reassignments(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    direction: str = Query("both", description="Direction filter (to/from/both)"),
    current_user: User = Depends(has_role(["outreach_agent", "agent_manager"])),
    db: Session = Depends(get_db)
):
    """Get reassignment histories for the current user's agent"""
    # This would need additional logic to find the user's agent
    # For now, return empty list - would need to implement agent lookup
    return InfluencerAssignmentHistoryListResponse(
        items=[],
        total=0,
        page=page,
        size=size,
        pages=1
    )

# Utility endpoints for reporting
@router.get("/reports/reassignment-trends")
async def get_reassignment_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(has_permission("assignment_history:read")),
    db: Session = Depends(get_db)
):
    """Get reassignment trends over time"""
    from datetime import datetime, timedelta
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    stats = await InfluencerAssignmentHistoryController.get_assignment_history_stats(
        db=db,
        start_date=start_date,
        end_date=end_date
    )
    
    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "stats": stats
    }

@router.get("/reports/agent-performance")
async def get_agent_reassignment_performance(
    agent_id: Optional[str] = Query(None, description="Specific agent ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(has_permission("assignment_history:read")),
    db: Session = Depends(get_db)
):
    """Get agent performance based on reassignment patterns"""
    from datetime import datetime, timedelta
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # This would need more complex logic to calculate agent performance metrics
    # based on reassignment patterns, success rates, etc.
    return {
        "message": "Agent performance analysis would be implemented here",
        "agent_id": agent_id,
        "period_days": days,
        "metrics": {
            "total_received_reassignments": 0,
            "total_lost_reassignments": 0,
            "avg_attempts_before_reassignment": 0.0,
            "success_rate_after_reassignment": 0.0
        }
    }

# Advanced filtering endpoints
@router.get("/search/advanced", response_model=InfluencerAssignmentHistoryListResponse)
async def advanced_search_assignment_histories(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    # Date range filters
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    # Entity filters
    campaign_influencer_ids: Optional[str] = Query(None, description="Comma-separated campaign influencer IDs"),
    agent_assignment_ids: Optional[str] = Query(None, description="Comma-separated agent assignment IDs"),
    from_agent_ids: Optional[str] = Query(None, description="Comma-separated from agent IDs"),
    to_agent_ids: Optional[str] = Query(None, description="Comma-separated to agent IDs"),
    reassignment_reason_ids: Optional[str] = Query(None, description="Comma-separated reason IDs"),
    # Metadata filters
    triggered_by_list: Optional[str] = Query(None, description="Comma-separated trigger types"),
    min_attempts: Optional[int] = Query(None, description="Minimum attempts before reassignment"),
    max_attempts: Optional[int] = Query(None, description="Maximum attempts before reassignment"),
    # Advanced options
    include_relations: bool = Query(True, description="Include related data"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(has_permission("assignment_history:read")),
    db: Session = Depends(get_db)
):
    """Advanced search for assignment histories with multiple filters"""
    # TODO: Implement complex filtering logic for all parameters
    # Currently unused parameters (to be implemented):
    _ = (campaign_influencer_ids, agent_assignment_ids, from_agent_ids, 
         to_agent_ids, reassignment_reason_ids, triggered_by_list, 
         min_attempts, max_attempts)
    
    # For now, fall back to the basic search
    return await InfluencerAssignmentHistoryController.get_assignment_histories(
        db=db,
        page=page,
        size=size,
        start_date=start_date,
        end_date=end_date,
        include_relations=include_relations,
        sort_by=sort_by,
        sort_order=sort_order
    )

# Export endpoints
@router.get("/export/csv")
async def export_assignment_histories_csv(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    campaign_influencer_id: Optional[str] = Query(None, description="Filter by campaign influencer ID"),
    agent_assignment_id: Optional[str] = Query(None, description="Filter by agent assignment ID"),
    current_user: User = Depends(has_permission("assignment_history:export")),
    db: Session = Depends(get_db)
):
    """Export assignment histories to CSV format"""
    # This would implement CSV export functionality
    return {
        "message": "CSV export would be implemented here",
        "filters": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "campaign_influencer_id": campaign_influencer_id,
            "agent_assignment_id": agent_assignment_id
        }
    }

@router.get("/export/excel")
async def export_assignment_histories_excel(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    campaign_influencer_id: Optional[str] = Query(None, description="Filter by campaign influencer ID"),
    agent_assignment_id: Optional[str] = Query(None, description="Filter by agent assignment ID"),
    current_user: User = Depends(has_permission("assignment_history:export")),
    db: Session = Depends(get_db)
):
    """Export assignment histories to Excel format"""
    # This would implement Excel export functionality
    return {
        "message": "Excel export would be implemented here",
        "filters": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "campaign_influencer_id": campaign_influencer_id,
            "agent_assignment_id": agent_assignment_id
        }
    }