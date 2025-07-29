# routes/api/v0/bulk_assignments.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from app.Services.CounterSyncService import CounterSyncService
from app.Http.Controllers.BulkAssignmentController import BulkAssignmentController
from app.Models.auth_models import User
from app.Schemas.bulk_assignment import (
    BulkAssignmentRequest, BulkAssignmentResponse, BulkAssignmentValidationRequest,
    BulkAssignmentValidationResponse, ReassignmentRequest, ReassignmentResponse
)
from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission
)
from config.database import get_db

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bulk-assignments", tags=["Bulk Assignments"])

# Validation endpoint
@router.post("/validate", response_model=BulkAssignmentValidationResponse)
async def validate_bulk_assignment(
    data: BulkAssignmentValidationRequest,
    current_user: User = Depends(has_permission("agent_assignment:bulk_assign")),
    db: Session = Depends(get_db)
):
    """
    Validate if bulk assignment is possible for a campaign list
    
    This endpoint checks:
    - Available unassigned influencers in the campaign list
    - Available agents with capacity
    - Total capacity vs requirement
    - Provides recommendations for optimal assignment
    """
    return await BulkAssignmentController.validate_bulk_assignment(
        campaign_list_id=data.campaign_list_id,
        preferred_agent_ids=data.preferred_agent_ids,
        db=db
    )

# Execute bulk assignment
@router.post("/execute", response_model=BulkAssignmentResponse)
async def execute_bulk_assignment(
    data: BulkAssignmentRequest,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """
    Execute bulk assignment of influencers to agents
    
    This endpoint:
    - Distributes unassigned influencers among available agents
    - Creates agent assignments and assigned influencer records
    - Updates all relevant counters
    - Returns summary of successful and failed assignments
    
    Supports different distribution strategies:
    - round_robin: Evenly distribute influencers among agents
    - load_balanced: Assign based on current agent workload
    - manual: Use only preferred agents
    """
    
    result = await BulkAssignmentController.execute_bulk_assignment(
        campaign_list_id=data.campaign_list_id,
        strategy=data.strategy.value,
        preferred_agent_ids=data.preferred_agent_ids,
        max_influencers_per_agent=data.max_influencers_per_agent,
        force_new_assignments=data.force_new_assignments,
        db=db
    )
    
    # Additional counter validation after bulk assignment (optional)
    # This ensures counters are accurate after the operation
    try:
        await CounterSyncService.sync_all_agent_counters(db)
        logger.info("Agent counters synced after bulk assignment")
    except Exception as sync_error:
        logger.warning(f"Counter sync failed: {str(sync_error)}")

    
    return result

# Single influencer reassignment
@router.post("/reassign", response_model=ReassignmentResponse)
async def reassign_influencer(
    data: ReassignmentRequest,
    current_user: User = Depends(has_permission("assigned_influencer:transfer")),
    db: Session = Depends(get_db)
):
    """
    Reassign a single influencer to a different agent
    
    This endpoint:
    - Archives the current assignment
    - Finds the best available agent for reassignment
    - Creates new assignment with priority for agents already working on same campaign list
    - Creates assignment history record for audit trail
    """
    return await BulkAssignmentController.reassign_influencer(
        assigned_influencer_id=data.assigned_influencer_id,
        reason=data.reason,
        prefer_existing_assignments=data.prefer_existing_assignments,
        reassigned_by=current_user.id,
        db=db
    )

# Get available agents for campaign
@router.get("/campaign-list/{campaign_list_id}/available-agents")
async def get_available_agents(
    campaign_list_id: uuid.UUID,
    current_user: User = Depends(has_permission("agent_assignment:read")),
    db: Session = Depends(get_db)
):
    """
    Get available agents for a specific campaign list with capacity information
    
    Returns agents that can be assigned to this campaign list, considering:
    - Company exclusivity rules
    - Agent availability status
    - Current capacity and limits
    - Existing assignments for this campaign list
    """
    return await BulkAssignmentController.get_available_agents_for_campaign(
        campaign_list_id=campaign_list_id,
        db=db
    )

# Get assignment recommendations
@router.get("/campaign-list/{campaign_list_id}/recommendations")
async def get_assignment_recommendations(
    campaign_list_id: uuid.UUID,
    current_user: User = Depends(has_permission("agent_assignment:read")),
    db: Session = Depends(get_db)
):
    """
    Get recommendations for optimal assignment strategy
    
    Analyzes the campaign list and available agents to provide:
    - Recommended assignment strategy
    - Estimated number of agents needed
    - Capacity analysis and potential issues
    - Actionable recommendations for successful assignment
    """
    return await BulkAssignmentController.get_assignment_recommendations(
        campaign_list_id=campaign_list_id,
        db=db
    )

# Get assignment progress for a campaign list
@router.get("/campaign-list/{campaign_list_id}/progress")
async def get_assignment_progress(
    campaign_list_id: uuid.UUID,
    current_user: User = Depends(has_permission("agent_assignment:read")),
    db: Session = Depends(get_db)
):
    """
    Get assignment progress statistics for a campaign list
    
    Returns:
    - Total influencers in the list
    - Assigned vs unassigned counts
    - Assignment breakdown by agent
    - Progress percentage and completion estimates
    """
    try:
        from app.Models.campaign_lists import CampaignList
        from app.Models.campaign_influencers import CampaignInfluencer
        from app.Models.agent_assignments import AgentAssignment
        from app.Models.assigned_influencers import AssignedInfluencer
        from sqlalchemy import func, and_
        
        # Get campaign list
        campaign_list = db.query(CampaignList).filter(
            CampaignList.id == campaign_list_id
        ).first()
        
        if not campaign_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign list not found"
            )
        
        # Get assignment statistics
        total_influencers = db.query(CampaignInfluencer).filter(
            CampaignInfluencer.campaign_list_id == campaign_list_id
        ).count()
        
        assigned_influencers = db.query(CampaignInfluencer).filter(
            CampaignInfluencer.campaign_list_id == campaign_list_id,
            CampaignInfluencer.is_assigned_to_agent == True
        ).count()
        
        unassigned_influencers = total_influencers - assigned_influencers
        
        # Get agent assignments for this list
        agent_assignments = db.query(AgentAssignment).filter(
            AgentAssignment.campaign_list_id == campaign_list_id,
            AgentAssignment.is_deleted == False
        ).all()
        
        # Calculate progress
        progress_percentage = (assigned_influencers / total_influencers * 100) if total_influencers > 0 else 0
        
        # Build agent assignment data with runtime calculations
        agent_assignment_data = []
        for assignment in agent_assignments:
            # Calculate counts at runtime
            assigned_count = db.query(AssignedInfluencer).filter(
                AssignedInfluencer.agent_assignment_id == assignment.id
            ).count()
            
            completed_count = db.query(AssignedInfluencer).filter(
                AssignedInfluencer.agent_assignment_id == assignment.id,
                AssignedInfluencer.type == 'completed'
            ).count()
            
            pending_count = db.query(AssignedInfluencer).filter(
                AssignedInfluencer.agent_assignment_id == assignment.id,
                AssignedInfluencer.type == 'active'
            ).count()
            
            agent_assignment_data.append({
                "id": str(assignment.id),
                "agent_id": str(assignment.outreach_agent_id),
                "assigned_influencers_count": assigned_count,
                "completed_influencers_count": completed_count,
                "pending_influencers_count": pending_count,
                "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None
            })
        
        return {
            "campaign_list_id": str(campaign_list_id),
            "campaign_list_name": getattr(campaign_list, 'name', None),
            "statistics": {
                "total_influencers": total_influencers,
                "assigned_influencers": assigned_influencers,
                "unassigned_influencers": unassigned_influencers,
                "progress_percentage": round(progress_percentage, 2)
            },
            "agent_assignments": agent_assignment_data
        }
        
    except Exception as e:
        logger.error(f"Error getting assignment progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting assignment progress: {str(e)}"
        )

# Automatic reassignment trigger (for max attempts reached)
@router.post("/auto-reassign/{assigned_influencer_id}")
async def trigger_auto_reassignment(
    assigned_influencer_id: uuid.UUID,
    current_user: User = Depends(has_permission("assigned_influencer:transfer")),
    db: Session = Depends(get_db)
):
    """
    Trigger automatic reassignment when max attempts reached
    
    This endpoint is called when an influencer reaches max contact attempts
    and needs to be automatically reassigned to a different agent.
    
    The system will:
    - Archive current assignment
    - Find best available agent (preferring those working on same campaign list)
    - Create new assignment with reset attempt counter
    - Log the reassignment in history
    """
    try:
        from app.Models.assigned_influencers import AssignedInfluencer
        from app.Models.system_settings import SystemSetting
        
        # Get current assignment
        assigned_influencer = db.query(AssignedInfluencer).filter(
            AssignedInfluencer.id == assigned_influencer_id,
            AssignedInfluencer.type == 'active'
        ).first()
        
        if not assigned_influencer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active assigned influencer not found"
            )
        
        # Check if max attempts reached
        max_attempts_setting = db.query(SystemSetting).filter(
            SystemSetting.setting_key == "max_attempts_per_agent"
        ).first()
        max_attempts = int(max_attempts_setting.setting_value) if max_attempts_setting else 3
        
        if assigned_influencer.attempts_made < max_attempts:
            return {
                "success": False,
                "message": f"Max attempts ({max_attempts}) not yet reached. Current attempts: {assigned_influencer.attempts_made}"
            }
        
        # Trigger reassignment
        reassignment_result = await BulkAssignmentController.reassign_influencer(
            assigned_influencer_id=assigned_influencer_id,
            reason="Maximum contact attempts reached - automatic reassignment",
            prefer_existing_assignments=True,
            reassigned_by=None,  # System triggered
            db=db
        )
        
        return {
            "success": reassignment_result.success,
            "message": reassignment_result.message,
            "new_assignment": reassignment_result.new_assignment,
            "assignment_history_id": reassignment_result.assignment_history_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in auto reassignment: {str(e)}"
        )
    
@router.post("/maintenance/sync-counters")
async def sync_all_counters(
    current_user: User = Depends(has_permission("system:maintain")),  # or appropriate permission
    db: Session = Depends(get_db)
):
    """
    Synchronize all agent and assignment counters with actual data
    
    Use this endpoint if counters get out of sync or for maintenance
    """
    
    # Sync agent assignment counters first
    assignment_result = await CounterSyncService.sync_agent_assignment_counters(db)
    
    # Then sync agent counters
    agent_result = await CounterSyncService.sync_all_agent_counters(db)
    
    return {
        "success": True,
        "assignment_sync": assignment_result,
        "agent_sync": agent_result,
        "message": "All counters synchronized successfully"
    }

@router.get("/maintenance/validate-counters")
async def validate_counter_integrity(
    current_user: User = Depends(has_permission("system:maintain")),
    db: Session = Depends(get_db)
):
    """
    Validate that all counters are accurate without updating them
    
    Returns any discrepancies found between stored and actual counts
    """
    
    return await CounterSyncService.validate_counter_integrity(db)

@router.post("/maintenance/sync-agent-counters/{agent_id}")
async def sync_single_agent_counters(
    agent_id: uuid.UUID,
    current_user: User = Depends(has_permission("system:maintain")),
    db: Session = Depends(get_db)
):
    """
    Synchronize counters for a single agent
    
    Useful for fixing specific agent counter issues
    """
    
    return await CounterSyncService.sync_single_agent_counters(agent_id, db)