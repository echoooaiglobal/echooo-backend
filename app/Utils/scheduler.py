# app/Utils/scheduler.py

import asyncio
import pytz
from datetime import datetime, time
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.asyncio import AsyncIOExecutor

from config.database import get_db
from app.Services.OutreachAgentService import OutreachAgentService
from app.Utils.Logger import logger

class DailyResetScheduler:
    """
    Automatic scheduler for resetting daily counters at 11:00 PM in multiple time zones
    """
    
    def __init__(self):
        self.scheduler = None
        
        # Define time zones for reset (you can add more as needed)
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
        
        # Reset time (12:00 AM / Midnight)
        self.reset_hour = 0
        self.reset_minute = 0
        
    def start_scheduler(self):
        """Start the background scheduler"""
        try:
            if self.scheduler is None:
                # Configure scheduler with async executor
                executors = {
                    'default': AsyncIOExecutor()
                }
                
                self.scheduler = AsyncIOScheduler(
                    executors=executors,
                    timezone=pytz.UTC
                )
                
                # Add jobs for each timezone
                self._add_timezone_jobs()
                
                # Start the scheduler
                self.scheduler.start()
                logger.info("Daily reset scheduler started successfully")
                
                # Log next scheduled runs
                self._log_scheduled_jobs()
                
        except Exception as e:
            logger.error(f"Error starting daily reset scheduler: {str(e)}")
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown(wait=False)
                logger.info("Daily reset scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping daily reset scheduler: {str(e)}")
    
    def _add_timezone_jobs(self):
        """Add reset jobs for each timezone"""
        for timezone_str in self.reset_timezones:
            try:
                # Create cron trigger for 11:00 PM in this timezone
                trigger = CronTrigger(
                    hour=self.reset_hour,
                    minute=self.reset_minute,
                    timezone=pytz.timezone(timezone_str)
                )
                
                # Add job to scheduler
                job_id = f"daily_reset_{timezone_str.replace('/', '_')}"
                self.scheduler.add_job(
                    func=self._reset_daily_counters_for_timezone,
                    trigger=trigger,
                    args=[timezone_str],
                    id=job_id,
                    name=f"Daily Reset - {timezone_str}",
                    replace_existing=True,
                    max_instances=1  # Prevent concurrent runs
                )
                
                logger.info(f"Added daily reset job for {timezone_str} at {self.reset_hour:02d}:{self.reset_minute:02d} (midnight)")
                
            except Exception as e:
                logger.error(f"Error adding job for timezone {timezone_str}: {str(e)}")
    
    async def _reset_daily_counters_for_timezone(self, timezone_str: str):
        """Reset daily counters for a specific timezone"""
        try:
            current_time = datetime.now(pytz.timezone(timezone_str))
            logger.info(f"Starting daily reset for {timezone_str} at {current_time}")
            
            # Get database session
            db = next(get_db())
            
            try:
                # Reset counters using the service
                await OutreachAgentService.reset_daily_counters(db)
                
                # Log success with timezone info
                logger.info(f"Daily counters reset successfully for {timezone_str}")
                
                # Optional: Reset other daily counters here
                await self._reset_additional_daily_counters(db, timezone_str)
                
            except Exception as e:
                logger.error(f"Error resetting counters for {timezone_str}: {str(e)}")
                db.rollback()
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in daily reset job for {timezone_str}: {str(e)}")
    
    async def _reset_additional_daily_counters(self, db: Session, timezone_str: str):
        """Reset additional daily counters (extend as needed)"""
        try:
            # Example: Reset other daily metrics
            # You can add more reset operations here
            
            # Reset automation session daily counters
            # await AutomationSessionService.reset_daily_counters(db)
            
            # Reset communication channel daily counters
            # await CommunicationChannelService.reset_daily_counters(db)
            
            logger.info(f"Additional daily counters reset for {timezone_str}")
            
        except Exception as e:
            logger.error(f"Error resetting additional counters for {timezone_str}: {str(e)}")
    
    def _log_scheduled_jobs(self):
        """Log information about scheduled jobs"""
        try:
            if self.scheduler:
                jobs = self.scheduler.get_jobs()
                logger.info(f"Scheduled {len(jobs)} daily reset jobs:")
                
                for job in jobs:
                    next_run = job.next_run_time
                    if next_run:
                        logger.info(f"  - {job.name}: Next run at {next_run}")
        except Exception as e:
            logger.error(f"Error logging scheduled jobs: {str(e)}")
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        try:
            if not self.scheduler:
                return {"status": "not_initialized", "jobs": []}
            
            jobs_info = []
            for job in self.scheduler.get_jobs():
                jobs_info.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "timezone": str(job.trigger.timezone) if hasattr(job.trigger, 'timezone') else None
                })
            
            return {
                "status": "running" if self.scheduler.running else "stopped",
                "total_jobs": len(jobs_info),
                "jobs": jobs_info
            }
            
        except Exception as e:
            logger.error(f"Error getting scheduler status: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def add_custom_timezone(self, timezone_str: str):
        """Add a custom timezone for daily reset"""
        try:
            if timezone_str not in self.reset_timezones:
                self.reset_timezones.append(timezone_str)
                
                # Add job if scheduler is running
                if self.scheduler and self.scheduler.running:
                    trigger = CronTrigger(
                        hour=self.reset_hour,
                        minute=self.reset_minute,
                        timezone=pytz.timezone(timezone_str)
                    )
                    
                    job_id = f"daily_reset_{timezone_str.replace('/', '_')}"
                    self.scheduler.add_job(
                        func=self._reset_daily_counters_for_timezone,
                        trigger=trigger,
                        args=[timezone_str],
                        id=job_id,
                        name=f"Daily Reset - {timezone_str}",
                        replace_existing=True,
                        max_instances=1
                    )
                    
                logger.info(f"Added custom timezone {timezone_str} for daily reset")
                return True
                
        except Exception as e:
            logger.error(f"Error adding custom timezone {timezone_str}: {str(e)}")
            return False
    
    def remove_timezone(self, timezone_str: str):
        """Remove a timezone from daily reset"""
        try:
            if timezone_str in self.reset_timezones:
                self.reset_timezones.remove(timezone_str)
                
                # Remove job if scheduler is running
                if self.scheduler and self.scheduler.running:
                    job_id = f"daily_reset_{timezone_str.replace('/', '_')}"
                    self.scheduler.remove_job(job_id)
                    
                logger.info(f"Removed timezone {timezone_str} from daily reset")
                return True
                
        except Exception as e:
            logger.error(f"Error removing timezone {timezone_str}: {str(e)}")
            return False

# Global scheduler instance
daily_reset_scheduler = DailyResetScheduler()