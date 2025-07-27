# routes/api/v0/scheduler.py

"""
API endpoints for managing the daily reset scheduler
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from app.Models.auth_models import User
from app.Utils.scheduler import daily_reset_scheduler
from app.Utils.Helpers import has_role
from app.Utils.Logger import logger
from config.database import get_db

router = APIRouter(prefix="/scheduler", tags=["Scheduler Management"])

class TimezoneRequest(BaseModel):
    timezone: str

class SchedulerStatusResponse(BaseModel):
    status: str
    total_jobs: int
    jobs: List[Dict[str, Any]]

@router.get("/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(
    current_user: User = Depends(has_role(["platform_admin"]))
):
    """
    Get current scheduler status and job information (Admin only)
    """
    try:
        status_info = daily_reset_scheduler.get_scheduler_status()
        return SchedulerStatusResponse(**status_info)
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting scheduler status"
        )

@router.post("/timezones/add")
async def add_timezone(
    timezone_request: TimezoneRequest,
    current_user: User = Depends(has_role(["platform_admin"]))
):
    """
    Add a new timezone for daily reset (Admin only)
    
    Example timezones:
    - UTC
    - US/Eastern
    - Europe/London
    - Asia/Karachi
    - Asia/Tokyo
    """
    try:
        success = daily_reset_scheduler.add_custom_timezone(timezone_request.timezone)
        
        if success:
            return {
                "message": f"Timezone {timezone_request.timezone} added successfully",
                "timezone": timezone_request.timezone,
                "reset_time": "00:00 (12:00 AM / Midnight)"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to add timezone {timezone_request.timezone}"
            )
            
    except Exception as e:
        logger.error(f"Error adding timezone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding timezone"
        )

@router.delete("/timezones/remove")
async def remove_timezone(
    timezone_request: TimezoneRequest,
    current_user: User = Depends(has_role(["platform_admin"]))
):
    """
    Remove a timezone from daily reset (Admin only)
    """
    try:
        success = daily_reset_scheduler.remove_timezone(timezone_request.timezone)
        
        if success:
            return {
                "message": f"Timezone {timezone_request.timezone} removed successfully",
                "timezone": timezone_request.timezone
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to remove timezone {timezone_request.timezone}"
            )
            
    except Exception as e:
        logger.error(f"Error removing timezone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error removing timezone"
        )

@router.post("/restart")
async def restart_scheduler(
    current_user: User = Depends(has_role(["platform_admin"]))
):
    """
    Restart the daily reset scheduler (Admin only)
    """
    try:
        # Stop current scheduler
        daily_reset_scheduler.stop_scheduler()
        
        # Start scheduler again
        daily_reset_scheduler.start_scheduler()
        
        return {
            "message": "Scheduler restarted successfully",
            "status": "running"
        }
        
    except Exception as e:
        logger.error(f"Error restarting scheduler: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error restarting scheduler"
        )

@router.post("/manual-reset")
async def manual_daily_reset(
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """
    Manually trigger daily reset (Admin only)
    This is a backup method if automatic reset fails
    """
    try:
        from app.Services.OutreachAgentService import OutreachAgentService
        
        # Manual reset
        await OutreachAgentService.reset_daily_counters(db)
        
        return {
            "message": "Daily counters reset manually",
            "reset_time": "now"
        }
        
    except Exception as e:
        logger.error(f"Error in manual daily reset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error performing manual reset"
        )

@router.get("/next-resets")
async def get_next_reset_times(
    current_user: User = Depends(has_role(["platform_admin"]))
):
    """
    Get next reset times for all configured timezones (Admin only)
    """
    try:
        status_info = daily_reset_scheduler.get_scheduler_status()
        
        # Extract next run times
        next_resets = []
        for job in status_info.get("jobs", []):
            if job.get("next_run"):
                next_resets.append({
                    "timezone": job.get("timezone", "Unknown"),
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

# Add this to your main.py:
"""
# In main.py, add this import:
from routes.api.v0 import scheduler

# Add this router:
app.include_router(scheduler.router, prefix=settings.API_V0_STR)
"""