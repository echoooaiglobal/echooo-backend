# routes/api/v0/scheduler_management.py

"""
Comprehensive API endpoints for managing the modular scheduler system
INCLUDES ALL APIS from previous versions to ensure no regression
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from app.Models.auth_models import User
from app.Utils.schedulers import scheduler_manager
from app.Utils.Helpers import has_role, has_permission, get_current_active_user
from app.Utils.Logger import logger
from config.database import get_db

# Import archive service for manual testing
from app.Services.AssignedInfluencerArchiveService import AssignedInfluencerArchiveService

router = APIRouter(prefix="/scheduler-management", tags=["Scheduler Management"])

# ================================
# REQUEST/RESPONSE MODELS
# ================================

class SchedulerStatusResponse(BaseModel):
    manager_status: str
    start_time: Optional[str] = None
    uptime_seconds: float
    schedulers_count: int
    healthy_schedulers: int
    total_jobs: int
    main_scheduler_jobs: List[Dict[str, Any]]
    scheduler_details: Dict[str, Any]

class TimezoneRequest(BaseModel):
    timezone: str = Field(..., description="Timezone string (e.g., 'US/Eastern', 'Asia/Karachi')")

class ArchiveSettingsUpdate(BaseModel):
    enabled: bool = Field(description="Enable/disable automatic archiving")
    batch_size: int = Field(ge=1, le=10000, description="Maximum records to process per run")
    hours_threshold: int = Field(ge=1, description="Hours after last contact to archive")
    tolerance_hours: float = Field(ge=0.1, le=24, description="Tolerance window in hours")
    run_minute: int = Field(ge=0, le=59, description="Minute of hour to run (0-59)")
    # Backlog management settings
    enable_backlog_processing: bool = Field(default=True, description="Enable backlog processing")
    max_backlog_age_days: int = Field(default=30, ge=1, le=365, description="Maximum age for backlog processing")
    aggressive_mode: bool = Field(default=False, description="Process all eligible records regardless of age")

class BasicResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ArchiveTestRequest(BaseModel):
    batch_size: int = Field(default=10, ge=1, le=100, description="Test batch size")
    dry_run: bool = Field(default=True, description="If true, only count candidates without archiving")

# NEW: Backlog management models
class BacklogAnalysisResponse(BaseModel):
    total_candidates: int
    brackets: List[Dict[str, Any]]
    oldest_record: Optional[Dict[str, Any]]
    analysis_timestamp: str

class EmergencyCleanupRequest(BaseModel):
    max_age_days: int = Field(default=90, ge=1, le=365, description="Maximum age in days for emergency cleanup")
    batch_size: int = Field(default=2000, ge=100, le=5000, description="Batch size for emergency processing")
    confirm_emergency: bool = Field(description="Must be true to confirm emergency operation")

class RangeArchiveRequest(BaseModel):
    min_hours: float = Field(ge=1, description="Minimum hours since last contact")
    max_hours: int = Field(ge=2, description="Maximum hours since last contact")
    batch_size: int = Field(default=1000, ge=1, le=10000, description="Batch size for processing")
    tolerance_hours: float = Field(default=0.5, ge=0.1, le=24, description="Tolerance window")

# Legacy response models for backward compatibility
class LegacySchedulerStatusResponse(BaseModel):
    status: str
    total_jobs: int
    jobs: List[Dict[str, Any]]

# ================================
# OVERALL SCHEDULER MANAGEMENT
# ================================

@router.get("/status", response_model=SchedulerStatusResponse)
async def get_overall_status(
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"]))
):
    """
    Get comprehensive status of all schedulers (Admin only)
    
    Returns detailed information about:
    - Overall system status
    - Individual scheduler health
    - Job information and next run times
    - Performance statistics
    """
    try:
        status_info = scheduler_manager.get_overall_status()
        return SchedulerStatusResponse(**status_info)
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting scheduler status"
        )

@router.post("/restart-all")
async def restart_all_schedulers(
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"]))
) -> BasicResponse:
    """
    Restart all schedulers (Platform Admin only)
    
    This will:
    1. Stop all currently running schedulers
    2. Wait for graceful shutdown
    3. Restart all schedulers with current configuration
    """
    try:
        logger.info(f"Scheduler restart initiated by user {current_user.id}")
        
        if scheduler_manager.restart_all_schedulers():
            return BasicResponse(
                success=True,
                message="All schedulers restarted successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to restart schedulers"
            )
    except Exception as e:
        logger.error(f"Error restarting schedulers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error restarting schedulers"
        )

@router.get("/job-summary")
async def get_job_summary(
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"]))
) -> Dict[str, Any]:
    """
    Get summary of all jobs by scheduler
    
    Returns organized view of:
    - Jobs per scheduler
    - Schedule information
    - Current status
    """
    try:
        return scheduler_manager.get_job_summary()
    except Exception as e:
        logger.error(f"Error getting job summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting job summary"
        )

@router.get("/health")
async def scheduler_health_check(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Health check endpoint for scheduler system
    
    Can be used by:
    - Load balancers for health checks
    - Monitoring systems
    - Admin dashboards
    """
    try:
        status = scheduler_manager.get_overall_status()
        
        # Determine overall health
        is_healthy = (
            status.get("manager_status") == "running" and
            status.get("healthy_schedulers", 0) == status.get("schedulers_count", 0) and
            status.get("total_jobs", 0) > 0
        )
        
        return {
            "healthy": is_healthy,
            "status": status.get("manager_status", "unknown"),
            "schedulers_healthy": f"{status.get('healthy_schedulers', 0)}/{status.get('schedulers_count', 0)}",
            "total_jobs": status.get("total_jobs", 0),
            "uptime_seconds": status.get("uptime_seconds", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in scheduler health check: {str(e)}")
        return {
            "healthy": False,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# ================================
# DAILY RESET SCHEDULER MANAGEMENT
# ================================

@router.get("/daily-reset/status")
async def get_daily_reset_status(
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"]))
) -> Dict[str, Any]:
    """
    Get detailed status of daily reset scheduler
    
    Includes:
    - Configured timezones
    - Next reset times for each timezone
    - Job registration status
    """
    try:
        daily_reset = scheduler_manager.get_scheduler("daily_reset")
        if not daily_reset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Daily reset scheduler not found"
            )
        
        return daily_reset.get_status()
    except Exception as e:
        logger.error(f"Error getting daily reset status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting daily reset status"
        )

@router.post("/daily-reset/add-timezone")
async def add_timezone_to_daily_reset(
    timezone_request: TimezoneRequest,
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"]))
) -> BasicResponse:
    """
    Add a timezone to daily reset scheduler (Platform Admin only)
    
    Examples of valid timezones:
    - 'UTC'
    - 'US/Eastern', 'US/Pacific'
    - 'Europe/London', 'Europe/Paris'
    - 'Asia/Karachi', 'Asia/Tokyo'
    """
    try:
        result = scheduler_manager.execute_scheduler_method(
            "daily_reset", 
            "add_custom_timezone", 
            timezone_request.timezone,
            scheduler_manager.scheduler
        )
        
        if result:
            return BasicResponse(
                success=True,
                message=f"Timezone '{timezone_request.timezone}' added successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to add timezone '{timezone_request.timezone}'. Check if timezone is valid."
            )
    except Exception as e:
        logger.error(f"Error adding timezone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding timezone"
        )

@router.delete("/daily-reset/remove-timezone")
async def remove_timezone_from_daily_reset(
    timezone: str = Query(..., description="Timezone to remove"),
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"]))
) -> BasicResponse:
    """
    Remove a timezone from daily reset scheduler (Platform Admin only)
    """
    try:
        result = scheduler_manager.execute_scheduler_method(
            "daily_reset", 
            "remove_timezone", 
            timezone,
            scheduler_manager.scheduler
        )
        
        if result:
            return BasicResponse(
                success=True,
                message=f"Timezone '{timezone}' removed successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to remove timezone '{timezone}'. Check if timezone exists."
            )
    except Exception as e:
        logger.error(f"Error removing timezone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error removing timezone"
        )

@router.get("/daily-reset/timezones")
async def get_daily_reset_timezones(
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"]))
) -> Dict[str, Any]:
    """
    Get configured timezones and their next reset times
    """
    try:
        timezones = scheduler_manager.execute_scheduler_method(
            "daily_reset", 
            "get_timezone_list"
        )
        
        next_times = scheduler_manager.execute_scheduler_method(
            "daily_reset", 
            "get_next_reset_times"
        )
        
        return {
            "timezones": timezones or [],
            "next_reset_times": next_times or {},
            "total_timezones": len(timezones or [])
        }
    except Exception as e:
        logger.error(f"Error getting daily reset timezones: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting timezone information"
        )

# ================================
# ARCHIVE SCHEDULER MANAGEMENT
# ================================

@router.get("/archive/status")
async def get_archive_status(
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"]))
) -> Dict[str, Any]:
    """
    Get comprehensive status of archive scheduler
    
    Includes:
    - Current configuration
    - Processing statistics
    - Last run information
    - Next scheduled run
    - Backlog processing settings
    """
    try:
        archive_scheduler = scheduler_manager.get_scheduler("archive_scheduler")
        if not archive_scheduler:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Archive scheduler not found"
            )
        
        return archive_scheduler.get_status()
    except Exception as e:
        logger.error(f"Error getting archive status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting archive status"
        )

@router.put("/archive/settings")
async def update_archive_settings(
    settings: ArchiveSettingsUpdate,
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"]))
) -> BasicResponse:
    """
    Update archive scheduler settings (Platform Admin only)
    
    Settings include:
    - enabled: Enable/disable automatic archiving
    - batch_size: Maximum records per run (1-10000)
    - hours_threshold: Hours after last contact to archive
    - tolerance_hours: Time window tolerance (±)
    - run_minute: Minute of hour to run (0-59)
    - enable_backlog_processing: Enable backlog handling
    - max_backlog_age_days: Maximum age for backlog processing
    - aggressive_mode: Process all eligible records regardless of age
    """
    try:
        logger.info(f"Archive settings update by user {current_user.id}: {settings.model_dump()}")
        
        result = scheduler_manager.execute_scheduler_method(
            "archive_scheduler",
            "update_settings",
            enabled=settings.enabled,
            batch_size=settings.batch_size,
            hours_threshold=settings.hours_threshold,
            tolerance_hours=settings.tolerance_hours,
            run_minute=settings.run_minute,
            enable_backlog_processing=settings.enable_backlog_processing,
            max_backlog_age_days=settings.max_backlog_age_days,
            aggressive_mode=settings.aggressive_mode,
            scheduler=scheduler_manager.scheduler
        )
        
        if result:
            return BasicResponse(
                success=True,
                message="Archive settings updated successfully",
                data=settings.model_dump()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update archive settings. Check parameter values."
            )
    except Exception as e:
        logger.error(f"Error updating archive settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating archive settings"
        )

@router.get("/archive/statistics")
async def get_archive_statistics(
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"]))
) -> Dict[str, Any]:
    """
    Get detailed archive processing statistics
    
    Returns:
    - Total records processed and archived
    - Backlog processing statistics
    - Error counts and last error information
    - Last run details and performance metrics
    - Current configuration
    """
    try:
        stats = scheduler_manager.execute_scheduler_method(
            "archive_scheduler",
            "get_statistics"
        )
        
        if stats is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Archive scheduler not found"
            )
        
        return stats
    except Exception as e:
        logger.error(f"Error getting archive statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting archive statistics"
        )

@router.post("/archive/reset-statistics")
async def reset_archive_statistics(
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"]))
) -> BasicResponse:
    """
    Reset archive processing statistics (Platform Admin only)
    
    This clears:
    - Total processed/archived counters
    - Backlog processing counters
    - Error counts
    - Last run information
    """
    try:
        scheduler_manager.execute_scheduler_method(
            "archive_scheduler",
            "reset_statistics"
        )
        
        return BasicResponse(
            success=True,
            message="Archive statistics reset successfully"
        )
    except Exception as e:
        logger.error(f"Error resetting archive statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resetting archive statistics"
        )

@router.get("/archive/candidates-count")
async def get_archive_candidates_count(
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get count of influencers eligible for archiving
    """
    try:
        count = await AssignedInfluencerArchiveService.get_archive_candidates_count(db)
        
        return {
            "candidates_count": count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting candidates count: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting candidates count"
        )

@router.get("/archive/candidates")
async def get_archive_candidates(
    limit: int = Query(10, ge=1, le=100, description="Number of candidates to return"),
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"])),
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

@router.post("/archive/process-now")
async def process_archive_now(
    batch_size: int = Query(1000, ge=1, le=10000, description="Override batch size for this run"),
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Manually trigger archive processing immediately (Platform Admin only)
    
    This bypasses the normal schedule and processes archives now.
    Useful for:
    - Testing archive functionality
    - Manual cleanup after configuration changes
    - Emergency archiving
    """
    try:
        logger.info(f"Manual archive process initiated by user {current_user.id} with batch_size={batch_size}")
        
        result = await AssignedInfluencerArchiveService.process_auto_archive(
            db,
            batch_size=batch_size,
            hours_threshold=48,
            tolerance_hours=0.5
        )
        
        return result
    except Exception as e:
        logger.error(f"Error processing manual archive: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing archive"
        )

# ================================
# NEW: BACKLOG MANAGEMENT APIS
# ================================

@router.get("/archive/backlog-analysis", response_model=BacklogAnalysisResponse)
async def get_backlog_analysis(
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
) -> BacklogAnalysisResponse:
    """
    Analyze backlog of records that should have been archived
    
    This endpoint helps you understand:
    - How many records are waiting to be archived
    - Age distribution of unarchived records
    - Oldest record that should be archived
    - Impact of server downtime on archiving
    """
    try:
        analysis = await AssignedInfluencerArchiveService.get_backlog_analysis(db)
        return BacklogAnalysisResponse(**analysis)
    except Exception as e:
        logger.error(f"Error getting backlog analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error analyzing archive backlog"
        )

@router.post("/archive/process-range")
async def process_range_archive(
    range_request: RangeArchiveRequest,
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Process archiving for records within a specific time range (Platform Admin only)
    
    This is useful for:
    - Processing backlog after server downtime
    - Cleaning up specific age groups of records
    - Custom archiving scenarios
    
    Example: Archive records that are 7-30 days old
    """
    try:
        logger.info(f"Range archive initiated by user {current_user.id}: {range_request.model_dump()}")
        
        # Validate range
        if range_request.min_hours >= range_request.max_hours:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="min_hours must be less than max_hours"
            )
        
        result = await AssignedInfluencerArchiveService.process_range_archive(
            db,
            min_hours=range_request.min_hours,
            max_hours=range_request.max_hours,
            batch_size=range_request.batch_size,
            tolerance_hours=range_request.tolerance_hours
        )
        
        return result
    except Exception as e:
        logger.error(f"Error processing range archive: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing range archive"
        )

@router.post("/archive/emergency-cleanup")
async def emergency_cleanup(
    cleanup_request: EmergencyCleanupRequest,
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Emergency cleanup for very old unarchived records (Platform Admin only)
    
    ⚠️ WARNING: This is an emergency operation for cleaning up large backlogs
    
    Use this when:
    - Server was down for extended periods
    - Archive scheduler failed for days/weeks
    - You have thousands of old unarchived records
    
    This will process ALL records older than specified age regardless of normal rules.
    """
    try:
        # Safety check
        if not cleanup_request.confirm_emergency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must set confirm_emergency=true for emergency operations"
            )
        
        logger.warning(f"EMERGENCY CLEANUP initiated by user {current_user.id}: {cleanup_request.model_dump()}")
        
        result = await AssignedInfluencerArchiveService.emergency_cleanup(
            db,
            max_age_days=cleanup_request.max_age_days,
            batch_size=cleanup_request.batch_size
        )
        
        return result
    except Exception as e:
        logger.error(f"Error in emergency cleanup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in emergency cleanup"
        )

@router.get("/archive/candidates-by-age")
async def get_candidates_by_age(
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get breakdown of archive candidates by age groups
    
    Shows distribution of unarchived records across different age brackets.
    Useful for understanding the scope of backlog issues.
    
    FIXED: Now properly filters by attempts_made >= 3
    """
    try:
        # Define age brackets
        brackets = [
            {"name": "Ready (48-72h)", "min": 48, "max": 72},
            {"name": "Overdue (3-7d)", "min": 72, "max": 168},
            {"name": "Very Overdue (1-4w)", "min": 168, "max": 672},
            {"name": "Critical (1m+)", "min": 672, "max": 8760}
        ]
        
        results = []
        total_candidates = 0
        
        for bracket in brackets:
            # FIXED: Use the corrected method that filters by attempts_made >= 3
            count = await AssignedInfluencerArchiveService.count_influencers_in_range(
                db, bracket["min"], bracket["max"]
            )
            
            results.append({
                "name": bracket["name"],
                "count": count,
                "age_range": f"{bracket['min']/24:.1f} - {bracket['max']/24:.1f} days",
                "min_hours": bracket["min"],
                "max_hours": bracket["max"]
            })
            
            total_candidates += count
        
        return {
            "total_candidates": total_candidates,
            "age_brackets": results,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Only includes records with attempts_made >= 3"  # ADDED: Clarification note
        }
        
    except Exception as e:
        logger.error(f"Error getting candidates by age: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting candidates by age"
        )

@router.post("/archive/trigger-backlog-processing")
async def trigger_backlog_processing(
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Manually trigger backlog processing (Platform Admin only)
    
    This runs the same logic as the scheduled backlog processor:
    - Processes extended backlog (48h-7d old records)
    - Processes old backlog if aggressive mode is enabled
    - Uses larger batch sizes for efficiency
    """
    try:
        logger.info(f"Manual backlog processing triggered by user {current_user.id}")
        
        archive_scheduler = scheduler_manager.get_scheduler("archive_scheduler")
        if not archive_scheduler:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Archive scheduler not found"
            )
        
        # Execute backlog processing directly
        await archive_scheduler._execute_backlog_process()
        
        return {
            "success": True,
            "message": "Backlog processing completed",
            "triggered_by": str(current_user.id),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error triggering backlog processing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error triggering backlog processing"
        )

# ================================
# INDIVIDUAL SCHEDULER MANAGEMENT
# ================================

@router.get("/schedulers")
async def list_schedulers(
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"]))
) -> List[str]:
    """
    Get list of all registered schedulers
    """
    try:
        return scheduler_manager.get_scheduler_names()
    except Exception as e:
        logger.error(f"Error listing schedulers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing schedulers"
        )

@router.get("/schedulers/{scheduler_name}/status")
async def get_scheduler_status(
    scheduler_name: str,
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"]))
) -> Dict[str, Any]:
    """
    Get detailed status of a specific scheduler
    """
    try:
        scheduler = scheduler_manager.get_scheduler(scheduler_name)
        if not scheduler:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheduler '{scheduler_name}' not found"
            )
        
        return scheduler.get_status()
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting scheduler status"
        )

# ================================
# ADVANCED SCHEDULER OPERATIONS
# ================================

@router.post("/schedulers/{scheduler_name}/execute-method")
async def execute_scheduler_method(
    scheduler_name: str,
    method_name: str = Query(..., description="Method name to execute"),
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"]))
) -> Dict[str, Any]:
    """
    Execute a method on a specific scheduler (Platform Admin only)
    
    This is an advanced endpoint for debugging and administration.
    Use with caution as it can execute any public method on the scheduler.
    """
    try:
        # Whitelist of safe methods that can be executed
        safe_methods = [
            "get_status", "get_statistics", "get_job_definitions",
            "get_timezone_list", "get_next_reset_times"
        ]
        
        if method_name not in safe_methods:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Method '{method_name}' is not allowed for execution"
            )
        
        result = scheduler_manager.execute_scheduler_method(
            scheduler_name, method_name
        )
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Method execution failed or scheduler not found"
            )
        
        return {
            "success": True,
            "scheduler": scheduler_name,
            "method": method_name,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error executing scheduler method: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error executing scheduler method"
        )

# ================================
# LEGACY COMPATIBILITY ENDPOINTS
# ================================

@router.get("/next-resets")
async def get_next_reset_times(
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"]))
):
    """
    Get next reset times for all configured timezones (Admin only)
    
    Legacy endpoint for backward compatibility with original scheduler.py
    """
    try:
        daily_reset = scheduler_manager.get_scheduler("daily_reset")
        if not daily_reset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Daily reset scheduler not found"
            )
        
        status_info = daily_reset.get_status()
        
        # Extract next run times from main scheduler jobs
        next_resets = []
        overall_status = scheduler_manager.get_overall_status()
        
        for job in overall_status.get("main_scheduler_jobs", []):
            if job.get("id", "").startswith("daily_reset_") and job.get("next_run"):
                # Extract timezone from job name
                timezone_info = job.get("name", "").replace("Daily Reset - ", "")
                next_resets.append({
                    "timezone": timezone_info,
                    "next_reset": job.get("next_run"),
                    "job_name": job.get("name", "Unknown")
                })
        
        # Sort by next run time
        next_resets.sort(key=lambda x: x["next_reset"])
        
        return {
            "total_scheduled_resets": len(next_resets),
            "next_resets": next_resets
        }
        
    except Exception as e:
        logger.error(f"Error getting next reset times: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting next reset times"
        )

@router.post("/manual-reset")
async def manual_daily_reset(
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
):
    """
    Manually trigger daily reset (Admin only)
    
    Legacy endpoint for backward compatibility.
    This is a backup method if automatic reset fails.
    """
    try:
        from app.Services.OutreachAgentService import OutreachAgentService
        
        # Manual reset - direct call to service
        await OutreachAgentService.reset_daily_counters(db)
        
        return {
            "message": "Daily counters reset manually",
            "reset_time": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in manual daily reset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error performing manual reset"
        )

# ================================
# TESTING AND DEVELOPMENT ENDPOINTS
# ================================

@router.post("/test/daily-reset/{timezone}")
async def test_daily_reset(
    timezone: str,
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
) -> BasicResponse:
    """
    Test daily reset for a specific timezone (Platform Admin only)
    
    This manually executes the daily reset logic for testing purposes.
    """
    try:
        logger.info(f"Manual daily reset test initiated for {timezone} by user {current_user.id}")
        
        daily_reset = scheduler_manager.get_scheduler("daily_reset")
        if not daily_reset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Daily reset scheduler not found"
            )
        
        # Execute the reset method directly
        await daily_reset._execute_daily_reset(timezone)
        
        return BasicResponse(
            success=True,
            message=f"Daily reset test completed for timezone: {timezone}"
        )
    except Exception as e:
        logger.error(f"Error testing daily reset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error testing daily reset"
        )

@router.post("/test/archive-process")
async def test_archive_process(
    test_request: ArchiveTestRequest,
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Test archive process with configurable parameters (Platform Admin only)
    
    Options:
    - batch_size: Number of records to process (1-100 for testing)
    - dry_run: If true, only counts candidates without archiving
    """
    try:
        logger.info(f"Archive process test initiated by user {current_user.id}: {test_request.model_dump()}")
        
        if test_request.dry_run:
            # Just count candidates
            count = await AssignedInfluencerArchiveService.get_archive_candidates_count(db)
            return {
                "dry_run": True,
                "candidates_count": count,
                "message": f"Found {count} candidates that would be archived"
            }
        else:
            # Actually process archives
            result = await AssignedInfluencerArchiveService.process_auto_archive(
                db,
                batch_size=test_request.batch_size,
                hours_threshold=48,
                tolerance_hours=0.5
            )
            result["dry_run"] = False
            return result
            
    except Exception as e:
        logger.error(f"Error testing archive process: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error testing archive process"
        )

@router.post("/test/query-performance")
async def test_query_performance(
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Test query performance for archive operations (Platform Admin only)
    
    This endpoint helps you monitor database performance and
    validate that indexes are working correctly.
    """
    try:
        import time
        
        # Test candidate count query performance
        start_time = time.time()
        count = await AssignedInfluencerArchiveService.get_archive_candidates_count(db)
        count_time = time.time() - start_time
        
        # Test finding candidates query performance
        start_time = time.time()
        candidates = await AssignedInfluencerArchiveService.find_influencers_to_archive(db)
        find_time = time.time() - start_time
        
        return {
            "query_performance": {
                "count_query_ms": round(count_time * 1000, 2),
                "find_query_ms": round(find_time * 1000, 2),
                "total_candidates": count,
                "sample_size": len(candidates),
                "performance_rating": "excellent" if count_time < 0.01 else "good" if count_time < 0.1 else "needs_optimization"
            },
            "recommendations": {
                "count_query_fast": count_time < 0.01,
                "find_query_fast": find_time < 0.1,
                "indexes_working": count_time < 0.01 and find_time < 0.1
            }
        }
    except Exception as e:
        logger.error(f"Error testing query performance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error testing query performance"
        )

@router.post("/test/simulate-server-downtime")
async def simulate_server_downtime_recovery(
    downtime_days: int = Query(3, ge=1, le=30, description="Simulate downtime of N days"),
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Simulate recovery from server downtime (Platform Admin only)
    
    This endpoint helps test backlog processing by:
    1. Analyzing what would happen after N days of downtime
    2. Showing how many records would need backlog processing
    3. Estimating processing time and batches needed
    
    This is a READ-ONLY simulation - no data is modified.
    """
    try:
        logger.info(f"Simulating {downtime_days} days server downtime recovery for user {current_user.id}")
        
        # Calculate time ranges for simulation
        now = datetime.utcnow()
        
        # Records that would accumulate during downtime
        downtime_start = 48  # Normal threshold
        downtime_end = 48 + (downtime_days * 24)  # After N days of downtime
        
        # Count records in different scenarios
        scenarios = [
            {
                "name": "Immediate Backlog",
                "description": f"Records that would be 48h-{downtime_end}h old after {downtime_days} days downtime",
                "min_hours": 48,
                "max_hours": downtime_end
            },
            {
                "name": "Extended Backlog", 
                "description": f"Very old records (7+ days)",
                "min_hours": 168,  # 7 days
                "max_hours": 720   # 30 days
            }
        ]
        
        simulation_results = []
        total_backlog = 0
        
        for scenario in scenarios:
            count = await AssignedInfluencerArchiveService.count_influencers_in_range(
                db, scenario["min_hours"], scenario["max_hours"]
            )
            
            # Estimate processing time (assuming 1000 records per minute)
            est_processing_minutes = count / 1000 if count > 0 else 0
            batches_needed = (count // 1000) + (1 if count % 1000 > 0 else 0)
            
            scenario_result = {
                **scenario,
                "current_count": count,
                "estimated_processing_minutes": round(est_processing_minutes, 1),
                "batches_needed": batches_needed,
                "age_range_days": f"{scenario['min_hours']/24:.1f} - {scenario['max_hours']/24:.1f}"
            }
            
            simulation_results.append(scenario_result)
            total_backlog += count
        
        # Recovery strategy recommendation
        if total_backlog == 0:
            strategy = "No backlog - normal operation can resume"
        elif total_backlog < 1000:
            strategy = "Small backlog - regular processing will catch up quickly"
        elif total_backlog < 10000:
            strategy = "Moderate backlog - enable backlog processing or use range archiving"
        else:
            strategy = "Large backlog - consider emergency cleanup or aggressive mode"
        
        return {
            "simulation": {
                "downtime_days": downtime_days,
                "total_backlog_records": total_backlog,
                "recovery_strategy": strategy,
                "scenarios": simulation_results
            },
            "recommendations": {
                "immediate_action": "Enable backlog processing" if total_backlog > 1000 else "Resume normal operation",
                "use_emergency_cleanup": total_backlog > 10000,
                "estimated_total_recovery_time_minutes": sum(s["estimated_processing_minutes"] for s in simulation_results)
            },
            "timestamp": now.isoformat(),
            "note": "This is a simulation - no records were modified"
        }
        
    except Exception as e:
        logger.error(f"Error simulating server downtime recovery: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error simulating downtime recovery"
        )