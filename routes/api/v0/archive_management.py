# routes/api/v0/archive_management.py

"""
API endpoints for managing automatic archiving of assigned influencers
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel, Field

from app.Models.auth_models import User
from app.Services.AssignedInfluencerArchiveService import AssignedInfluencerArchiveService
from app.Utils.schedulers.daily_reset_scheduler import daily_reset_scheduler
from app.Utils.Helpers import has_role, has_permission
from app.Utils.Logger import logger
from config.database import get_db

router = APIRouter(prefix="/archive-management", tags=["Archive Management"])

class ArchiveSettingsUpdate(BaseModel):
    enabled: bool = Field(description="Enable/disable automatic archiving")
    batch_size: int = Field(ge=1, le=10000, description="Maximum records to process per run")
    hours_threshold: int = Field(ge=1, description="Hours after last contact to archive")
    tolerance_hours: float = Field(ge=0.1, le=24, description="Tolerance window in hours")

class ArchiveProcessResponse(BaseModel):
    success: bool
    message: str
    processed: int
    archived: int
    errors: list
    execution_time_seconds: float
    remaining_candidates: int = 0

class ArchiveStatsResponse(BaseModel):
    candidates_count: int
    settings: Dict[str, Any]
    next_run_time: str = None

@router.get("/stats", response_model=ArchiveStatsResponse)
async def get_archive_stats(
    current_user: User = Depends(has_permission("admin:read")),
    db: Session = Depends(get_db)
):
    """
    Get statistics about potential archives and current settings
    """
    try:
        # Get count of candidates
        candidates_count = await AssignedInfluencerArchiveService.get_archive_candidates_count(db)
        
        # Get scheduler status
        scheduler_status = daily_reset_scheduler.get_scheduler_status()
        
        # Find next archive job run time
        next_run_time = None
        if scheduler_status.get("jobs"):
            for job in scheduler_status["jobs"]:
                if job["id"] == "influencer_archive_hourly":
                    next_run_time = job.get("next_run")
                    break
        
        return ArchiveStatsResponse(
            candidates_count=candidates_count,
            settings=scheduler_status.get("archive_settings", {}),
            next_run_time=next_run_time
        )
        
    except Exception as e:
        logger.error(f"Error getting archive stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving archive statistics"
        )

@router.post("/process-now", response_model=ArchiveProcessResponse)
async def process_archive_now(
    batch_size: int = Query(1000, ge=1, le=10000, description="Override batch size for this run"),
    current_user: User = Depends(has_permission("admin:execute")),
    db: Session = Depends(get_db)
):
    """
    Manually trigger archive processing immediately (Admin only)
    """
    try:
        logger.info(f"Manual archive process initiated by user {current_user.id}")
        
        result = await AssignedInfluencerArchiveService.process_auto_archive(
            db,
            batch_size=batch_size,
            hours_threshold=48,  # Use default values
            tolerance_hours=0.5
        )
        
        return ArchiveProcessResponse(**result)
        
    except Exception as e:
        logger.error(f"Error processing manual archive: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing archive"
        )

@router.get("/candidates")
async def get_archive_candidates(
    limit: int = Query(10, ge=1, le=100, description="Number of candidates to return"),
    current_user: User = Depends(has_permission("admin:read")),
    db: Session = Depends(get_db)
):
    """
    Get a preview of influencers that would be archived
    """
    try:
        # Get candidates (limited for preview)
        candidates = await AssignedInfluencerArchiveService.find_influencers_to_archive(db)
        
        # Return limited set for preview
        preview_candidates = candidates[:limit]
        
        candidate_info = []
        for candidate in preview_candidates:
            candidate_info.append({
                "id": str(candidate.id),
                "campaign_influencer_id": str(candidate.campaign_influencer_id),
                "agent_assignment_id": str(candidate.agent_assignment_id),
                "attempts_made": candidate.attempts_made,
                "last_contacted_at": candidate.last_contacted_at.isoformat() if candidate.last_contacted_at else None,
                "assigned_at": candidate.assigned_at.isoformat() if candidate.assigned_at else None,
                "type": candidate.type
            })
        
        return {
            "total_candidates": len(candidates),
            "preview_count": len(preview_candidates),
            "candidates": candidate_info
        }
        
    except Exception as e:
        logger.error(f"Error getting archive candidates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving archive candidates"
        )

@router.put("/settings")
async def update_archive_settings(
    settings: ArchiveSettingsUpdate,
    current_user: User = Depends(has_role(["platform_admin"])),
):
    """
    Update automatic archive settings (Platform Admin only)
    """
    try:
        logger.info(f"Archive settings updated by user {current_user.id}: {settings.model_dump()}")
        
        # Update scheduler settings
        daily_reset_scheduler.update_archive_settings(
            enabled=settings.enabled,
            batch_size=settings.batch_size,
            hours_threshold=settings.hours_threshold,
            tolerance_hours=settings.tolerance_hours
        )
        
        return {
            "success": True,
            "message": "Archive settings updated successfully",
            "settings": settings.model_dump()
        }
        
    except Exception as e:
        logger.error(f"Error updating archive settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating archive settings"
        )

@router.get("/settings")
async def get_archive_settings(
    current_user: User = Depends(has_permission("admin:read")),
):
    """
    Get current archive settings
    """
    try:
        scheduler_status = daily_reset_scheduler.get_scheduler_status()
        return {
            "success": True,
            "settings": scheduler_status.get("archive_settings", {}),
            "scheduler_status": scheduler_status.get("status", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Error getting archive settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving archive settings"
        )

@router.post("/test-query")
async def test_archive_query(
    hours_threshold: int = Query(48, ge=1, description="Hours threshold to test"),
    tolerance_hours: float = Query(0.5, ge=0.1, le=24, description="Tolerance hours to test"),
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """
    Test the archive query with custom parameters (Platform Admin only)
    """
    try:
        logger.info(f"Testing archive query with threshold={hours_threshold}, tolerance={tolerance_hours}")
        
        # Get count with custom parameters
        candidates_count = await AssignedInfluencerArchiveService.get_archive_candidates_count(
            db, hours_threshold, tolerance_hours
        )
        
        # Get sample candidates
        candidates = await AssignedInfluencerArchiveService.find_influencers_to_archive(
            db, hours_threshold, tolerance_hours
        )
        
        sample_candidates = []
        for candidate in candidates[:5]:  # Show first 5 as sample
            sample_candidates.append({
                "id": str(candidate.id),
                "attempts_made": candidate.attempts_made,
                "last_contacted_at": candidate.last_contacted_at.isoformat() if candidate.last_contacted_at else None,
                "type": candidate.type,
                "archived_at": candidate.archived_at
            })
        
        return {
            "success": True,
            "parameters": {
                "hours_threshold": hours_threshold,
                "tolerance_hours": tolerance_hours
            },
            "results": {
                "total_candidates": candidates_count,
                "sample_candidates": sample_candidates
            }
        }
        
    except Exception as e:
        logger.error(f"Error testing archive query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error testing archive query"
        )