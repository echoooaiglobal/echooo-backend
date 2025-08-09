# app/Utils/schedulers/daily_reset_scheduler.py

"""
Scheduler for daily counter resets across multiple timezones
"""

import pytz
from datetime import datetime
from typing import List, Dict, Any
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from .base_scheduler import BaseScheduler
from config.database import get_db
from app.Services.OutreachAgentService import OutreachAgentService


class DailyResetScheduler(BaseScheduler):
    """
    Handles daily reset operations for outreach agents across multiple timezones
    
    Resets daily counters at midnight (00:00) in each configured timezone
    """
    
    def __init__(self):
        super().__init__(
            name="daily_reset",
            description="Daily reset of outreach agent counters across multiple timezones"
        )
        
        # Configure timezones for reset operations
        self.reset_timezones = [
            'UTC',                    # UTC/GMT
            'US/Eastern',            # EST/EDT 
            'US/Central',            # CST/CDT
            'US/Mountain',           # MST/MDT
            'US/Pacific',            # PST/PDT
            'Europe/London',         # GMT/BST
            'Europe/Paris',          # CET/CEST
            'Asia/Dubai',            # Gulf Standard Time
            'Asia/Karachi',          # Pakistan Standard Time
            'Asia/Kolkata',          # Indian Standard Time
            'Asia/Singapore',        # Singapore Time
            'Asia/Tokyo',            # Japan Standard Time
            'Australia/Sydney',      # Australian Eastern Time
        ]
        
        # Reset time configuration
        self.reset_hour = 0      # Midnight
        self.reset_minute = 0    # 00 minutes
        
    def initialize(self) -> bool:
        """Initialize the daily reset scheduler"""
        try:
            self.log_info("Initializing daily reset scheduler")
            
            # Validate timezone configurations
            invalid_timezones = []
            for tz in self.reset_timezones:
                try:
                    pytz.timezone(tz)
                except pytz.UnknownTimeZoneError:
                    invalid_timezones.append(tz)
            
            if invalid_timezones:
                self.log_error(f"Invalid timezones found: {invalid_timezones}")
                return False
            
            self.mark_initialized(True)
            return True
            
        except Exception as e:
            self.log_error("Failed to initialize daily reset scheduler", e)
            self.mark_initialized(False)
            return False
    
    def register_jobs(self, scheduler) -> List[str]:
        """Register daily reset jobs for each timezone"""
        registered_jobs = []
        
        try:
            for timezone_str in self.reset_timezones:
                job_id = self._register_timezone_job(scheduler, timezone_str)
                if job_id:
                    registered_jobs.append(job_id)
                    self.add_job_id(job_id)
            
            self.log_info(f"Registered {len(registered_jobs)} daily reset jobs")
            return registered_jobs
            
        except Exception as e:
            self.log_error("Failed to register daily reset jobs", e)
            return registered_jobs
    
    def _register_timezone_job(self, scheduler, timezone_str: str) -> str:
        """Register a daily reset job for a specific timezone"""
        try:
            # Create cron trigger for midnight in this timezone
            trigger = CronTrigger(
                hour=self.reset_hour,
                minute=self.reset_minute,
                timezone=pytz.timezone(timezone_str)
            )
            
            # Generate unique job ID
            job_id = f"daily_reset_{timezone_str.replace('/', '_').replace('-', '_')}"
            
            # Add job to scheduler
            scheduler.add_job(
                func=self._execute_daily_reset,
                trigger=trigger,
                args=[timezone_str],
                id=job_id,
                name=f"Daily Reset - {timezone_str}",
                replace_existing=True,
                max_instances=1  # Prevent concurrent runs
            )
            
            self.log_info(f"Registered daily reset job for {timezone_str} at {self.reset_hour:02d}:{self.reset_minute:02d}")
            return job_id
            
        except Exception as e:
            self.log_error(f"Failed to register job for timezone {timezone_str}", e)
            return None
    
    async def _execute_daily_reset(self, timezone_str: str):
        """Execute daily reset for a specific timezone"""
        try:
            current_time = datetime.now(pytz.timezone(timezone_str))
            self.log_info(f"Starting daily reset for {timezone_str} at {current_time}")
            
            # Get database session
            db = next(get_db())
            
            try:
                # Execute the reset operation - FIXED: Remove timezone_str parameter
                await OutreachAgentService.reset_daily_counters(db)
                self.log_info(f"Daily reset completed successfully for {timezone_str}")
                
                # Optional: Reset other daily counters here
                await self._reset_additional_daily_counters(db, timezone_str)
                
            except Exception as e:
                self.log_error(f"Error during daily reset execution for {timezone_str}", e)
                db.rollback()
            finally:
                db.close()
                
        except Exception as e:
            self.log_error(f"Critical error in daily reset for {timezone_str}", e)
    
    async def _reset_additional_daily_counters(self, db: Session, timezone_str: str):
        """Reset additional daily counters (extend as needed)"""
        try:
            # Example: Reset other daily metrics
            # You can add more reset operations here
            
            # Reset automation session daily counters
            # await AutomationSessionService.reset_daily_counters(db)
            
            # Reset communication channel daily counters
            # await CommunicationChannelService.reset_daily_counters(db)
            
            self.log_info(f"Additional daily counters reset for {timezone_str}")
            
        except Exception as e:
            self.log_error(f"Error resetting additional counters for {timezone_str}", e)
    
    def get_job_definitions(self) -> List[Dict[str, Any]]:
        """Get definitions for all daily reset jobs"""
        job_definitions = []
        
        for timezone_str in self.reset_timezones:
            job_id = f"daily_reset_{timezone_str.replace('/', '_').replace('-', '_')}"
            
            job_definitions.append({
                "id": job_id,
                "name": f"Daily Reset - {timezone_str}",
                "description": f"Reset daily counters at midnight in {timezone_str}",
                "func": self._execute_daily_reset,
                "trigger": {
                    "type": "cron",
                    "hour": self.reset_hour,
                    "minute": self.reset_minute,
                    "timezone": timezone_str
                },
                "args": [timezone_str],
                "max_instances": 1,
                "timezone": timezone_str,
                "schedule": f"{self.reset_hour:02d}:{self.reset_minute:02d} daily"
            })
        
        return job_definitions
    
    def add_custom_timezone(self, timezone_str: str, scheduler=None) -> bool:
        """
        Add a custom timezone for daily reset
        
        Args:
            timezone_str: Timezone string (e.g., 'Asia/Singapore')
            scheduler: Optional scheduler instance to immediately register job
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate timezone
            pytz.timezone(timezone_str)
            
            if timezone_str not in self.reset_timezones:
                self.reset_timezones.append(timezone_str)
                self.log_info(f"Added custom timezone: {timezone_str}")
                
                # If scheduler is provided, register the job immediately
                if scheduler:
                    job_id = self._register_timezone_job(scheduler, timezone_str)
                    if job_id:
                        self.add_job_id(job_id)
                        return True
                    return False
                
                return True
            else:
                self.log_warning(f"Timezone {timezone_str} already exists")
                return True
                
        except pytz.UnknownTimeZoneError:
            self.log_error(f"Invalid timezone: {timezone_str}")
            return False
        except Exception as e:
            self.log_error(f"Error adding custom timezone {timezone_str}", e)
            return False
    
    def remove_timezone(self, timezone_str: str, scheduler=None) -> bool:
        """
        Remove a timezone from daily reset
        
        Args:
            timezone_str: Timezone string to remove
            scheduler: Optional scheduler instance to remove job immediately
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if timezone_str in self.reset_timezones:
                self.reset_timezones.remove(timezone_str)
                job_id = f"daily_reset_{timezone_str.replace('/', '_').replace('-', '_')}"
                
                # Remove from registered jobs list
                self.remove_job_id(job_id)
                
                # If scheduler is provided, remove the job immediately
                if scheduler:
                    try:
                        scheduler.remove_job(job_id)
                        self.log_info(f"Removed job for timezone: {timezone_str}")
                    except:
                        pass  # Job might not exist
                
                self.log_info(f"Removed timezone: {timezone_str}")
                return True
            else:
                self.log_warning(f"Timezone {timezone_str} not found")
                return False
                
        except Exception as e:
            self.log_error(f"Error removing timezone {timezone_str}", e)
            return False
    
    def get_timezone_list(self) -> List[str]:
        """Get list of configured timezones"""
        return self.reset_timezones.copy()
    
    def get_next_reset_times(self) -> Dict[str, str]:
        """Get next reset time for each timezone"""
        next_times = {}
        
        for timezone_str in self.reset_timezones:
            try:
                tz = pytz.timezone(timezone_str)
                now = datetime.now(tz)
                
                # Calculate next midnight
                next_reset = now.replace(hour=self.reset_hour, minute=self.reset_minute, second=0, microsecond=0)
                if next_reset <= now:
                    # If midnight has passed today, next reset is tomorrow
                    next_reset = next_reset.replace(day=next_reset.day + 1)
                
                next_times[timezone_str] = next_reset.isoformat()
                
            except Exception as e:
                self.log_error(f"Error calculating next reset time for {timezone_str}", e)
                next_times[timezone_str] = "error"
        
        return next_times
    
    def cleanup(self):
        """Cleanup resources"""
        self.log_info("Cleaning up daily reset scheduler")
        # No specific cleanup needed for this scheduler
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed status including timezone information"""
        base_status = super().get_status()
        
        base_status.update({
            "timezones_count": len(self.reset_timezones),
            "configured_timezones": self.reset_timezones,
            "reset_schedule": f"{self.reset_hour:02d}:{self.reset_minute:02d}",
            "next_reset_times": self.get_next_reset_times()
        })
        
        return base_status