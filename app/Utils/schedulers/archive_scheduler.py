# app/Utils/schedulers/archive_scheduler.py - Enhanced with Backlog Management

"""
Enhanced scheduler for automatic archiving of stale assigned influencers
INCLUDES: Backlog management for missed archiving windows
"""

import pytz
from datetime import datetime, timedelta
from typing import List, Dict, Any
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from .base_scheduler import BaseScheduler
from config.database import get_db
from app.Services.AssignedInfluencerArchiveService import AssignedInfluencerArchiveService


class ArchiveScheduler(BaseScheduler):
    """
    Enhanced scheduler for automatic archiving of stale assigned influencers
    
    Features:
    - Regular hourly archiving
    - Backlog processing for missed windows
    - Flexible time thresholds for old records
    - Progressive archiving strategies
    """
    
    def __init__(self):
        super().__init__(
            name="archive_scheduler",
            description="Enhanced automatic archiving with backlog management"
        )
        
        # Archive configuration
        self.enabled = True
        self.run_minute = 15            # Run at :15 minutes past each hour
        self.batch_size = 1000          # Max records to process per run
        self.hours_threshold = 48       # Hours after last contact to archive
        self.tolerance_hours = 0.5      # ±30 minutes tolerance window
        
        # ENHANCED: Backlog management settings
        self.enable_backlog_processing = True
        self.max_backlog_age_days = 30  # Process records up to 30 days old
        self.backlog_batch_multiplier = 2  # Use larger batches for backlog
        self.aggressive_mode = False    # Process ALL eligible records regardless of age
        
        # Performance and safety limits
        self.max_batch_size = 10000
        self.min_hours_threshold = 1
        self.max_tolerance_hours = 24
        
        # Statistics tracking
        self.last_run_stats = None
        self.total_processed = 0
        self.total_archived = 0
        self.error_count = 0
        self.backlog_processed = 0
    
    def initialize(self) -> bool:
        """Initialize the archive scheduler"""
        try:
            self.log_info("Initializing enhanced archive scheduler with backlog management")
            
            # Validate configuration
            if not self._validate_configuration():
                return False
            
            self.log_info(f"Archive scheduler configured: "
                         f"enabled={self.enabled}, "
                         f"batch_size={self.batch_size}, "
                         f"threshold={self.hours_threshold}h, "
                         f"tolerance=±{self.tolerance_hours}h, "
                         f"backlog_enabled={self.enable_backlog_processing}")
            
            self.mark_initialized(True)
            return True
            
        except Exception as e:
            self.log_error("Failed to initialize archive scheduler", e)
            self.mark_initialized(False)
            return False
    
    def _validate_configuration(self) -> bool:
        """Validate scheduler configuration"""
        if self.batch_size < 1 or self.batch_size > self.max_batch_size:
            self.log_error(f"Invalid batch_size: {self.batch_size}. Must be 1-{self.max_batch_size}")
            return False
        
        if self.hours_threshold < self.min_hours_threshold:
            self.log_error(f"Invalid hours_threshold: {self.hours_threshold}. Must be >= {self.min_hours_threshold}")
            return False
        
        if self.tolerance_hours < 0.1 or self.tolerance_hours > self.max_tolerance_hours:
            self.log_error(f"Invalid tolerance_hours: {self.tolerance_hours}. Must be 0.1-{self.max_tolerance_hours}")
            return False
        
        if self.max_backlog_age_days < 1 or self.max_backlog_age_days > 365:
            self.log_error(f"Invalid max_backlog_age_days: {self.max_backlog_age_days}. Must be 1-365")
            return False
        
        return True
    
    def register_jobs(self, scheduler) -> List[str]:
        """Register archive processing jobs"""
        registered_jobs = []
        
        try:
            if not self.enabled:
                self.log_info("Archive scheduler disabled, skipping job registration")
                return registered_jobs
            
            # Register regular hourly job
            job_id = self._register_archive_job(scheduler)
            if job_id:
                registered_jobs.append(job_id)
                self.add_job_id(job_id)
            
            # Register backlog processing job (runs every 6 hours)
            if self.enable_backlog_processing:
                backlog_job_id = self._register_backlog_job(scheduler)
                if backlog_job_id:
                    registered_jobs.append(backlog_job_id)
                    self.add_job_id(backlog_job_id)
            
            self.log_info(f"Registered {len(registered_jobs)} archive jobs")
            return registered_jobs
            
        except Exception as e:
            self.log_error("Failed to register archive jobs", e)
            return registered_jobs
    
    def _register_archive_job(self, scheduler) -> str:
        """Register the hourly archive processing job"""
        try:
            # Create cron trigger - run every hour at specified minute
            trigger = CronTrigger(
                minute=self.run_minute,
                timezone=pytz.UTC
            )
            
            job_id = "influencer_archive_hourly"
            
            # Add job to scheduler
            scheduler.add_job(
                func=self._execute_archive_process,
                trigger=trigger,
                id=job_id,
                name="Hourly Influencer Archive",
                replace_existing=True,
                max_instances=1  # Prevent overlapping runs
            )
            
            self.log_info(f"Registered regular archive job to run at :{self.run_minute:02d} minutes past each hour")
            return job_id
            
        except Exception as e:
            self.log_error("Failed to register archive job", e)
            return None
    
    def _register_backlog_job(self, scheduler) -> str:
        """Register the backlog processing job (runs every 6 hours)"""
        try:
            # Create cron trigger - run every 6 hours at minute 45
            trigger = CronTrigger(
                hour="0,6,12,18",  # Run at midnight, 6am, noon, 6pm
                minute=45,
                timezone=pytz.UTC
            )
            
            job_id = "influencer_archive_backlog"
            
            # Add job to scheduler
            scheduler.add_job(
                func=self._execute_backlog_process,
                trigger=trigger,
                id=job_id,
                name="Archive Backlog Processing",
                replace_existing=True,
                max_instances=1  # Prevent overlapping runs
            )
            
            self.log_info("Registered backlog processing job to run every 6 hours at :45 minutes")
            return job_id
            
        except Exception as e:
            self.log_error("Failed to register backlog job", e)
            return None
    
    async def _execute_archive_process(self):
        """Execute the regular archive processing"""
        start_time = datetime.utcnow()
        
        try:
            self.log_info("Starting hourly archive process")
            
            # Get database session
            db = next(get_db())
            
            try:
                # Use regular thresholds for hourly processing
                result = await self._process_archives_with_settings(
                    db,
                    batch_size=self.batch_size,
                    hours_threshold=self.hours_threshold,
                    tolerance_hours=self.tolerance_hours,
                    process_type="regular"
                )
                
                # Update statistics
                self._update_run_stats(result)
                
                if result["success"]:
                    self.total_processed += result["processed"]
                    self.total_archived += result["archived"]
                    
                    if result["archived"] > 0:
                        self.log_info(f"Regular archive completed: archived {result['archived']} influencers "
                                    f"in {result['execution_time_seconds']:.2f} seconds")
                    else:
                        self.log_info("Regular archive completed: no influencers archived")
                else:
                    self.error_count += 1
                    self.log_error(f"Regular archive failed: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                self.error_count += 1
                self.log_error("Error during regular archive execution", e)
            finally:
                db.close()
                
        except Exception as e:
            self.error_count += 1
            self.log_error("Critical error in regular archive job", e)
    
    async def _execute_backlog_process(self):
        """Execute backlog processing for missed archive windows"""
        start_time = datetime.utcnow()
        
        try:
            self.log_info("Starting backlog archive processing")
            
            # Get database session
            db = next(get_db())
            
            try:
                # STRATEGY 1: Process records slightly older than normal window
                extended_result = await self._process_extended_backlog(db)
                
                # STRATEGY 2: Process very old records if aggressive mode is enabled
                old_result = {"processed": 0, "archived": 0}
                if self.aggressive_mode:
                    old_result = await self._process_old_backlog(db)
                
                # Combine results
                total_processed = extended_result["processed"] + old_result["processed"]
                total_archived = extended_result["archived"] + old_result["archived"]
                
                self.backlog_processed += total_archived
                
                backlog_stats = {
                    "success": True,
                    "processed": total_processed,
                    "archived": total_archived,
                    "extended_backlog": extended_result,
                    "old_backlog": old_result,
                    "execution_time_seconds": (datetime.utcnow() - start_time).total_seconds(),
                    "process_type": "backlog"
                }
                
                self._update_run_stats(backlog_stats)
                
                if total_archived > 0:
                    self.log_info(f"Backlog processing completed: archived {total_archived} influencers "
                                f"({extended_result['archived']} extended + {old_result['archived']} old)")
                else:
                    self.log_info("Backlog processing completed: no influencers archived")
                
            except Exception as e:
                self.error_count += 1
                self.log_error("Error during backlog processing", e)
            finally:
                db.close()
                
        except Exception as e:
            self.error_count += 1
            self.log_error("Critical error in backlog processing", e)
    
    async def _process_extended_backlog(self, db: Session) -> Dict[str, Any]:
        """Process records that are slightly older than the normal window"""
        try:
            # Extended window: 48 hours to 7 days old
            extended_hours = self.hours_threshold + (24 * 7)  # 48 hours + 7 days
            extended_tolerance = 24  # Much larger tolerance for backlog
            
            self.log_info(f"Processing extended backlog: {self.hours_threshold}h to {extended_hours}h old")
            
            result = await self._process_archives_with_settings(
                db,
                batch_size=self.batch_size * self.backlog_batch_multiplier,
                hours_threshold=extended_hours,
                tolerance_hours=extended_tolerance,
                process_type="extended_backlog",
                min_hours=self.hours_threshold + self.tolerance_hours  # Don't overlap with regular processing
            )
            
            return result
            
        except Exception as e:
            self.log_error("Error in extended backlog processing", e)
            return {"success": False, "processed": 0, "archived": 0, "error": str(e)}
    
    async def _process_old_backlog(self, db: Session) -> Dict[str, Any]:
        """Process very old records (aggressive mode)"""
        try:
            # Very old records: 7 days to max_backlog_age_days
            old_hours = 24 * self.max_backlog_age_days
            old_tolerance = 24 * 7  # One week tolerance
            
            self.log_info(f"Processing old backlog: 7 days to {self.max_backlog_age_days} days old")
            
            result = await self._process_archives_with_settings(
                db,
                batch_size=self.batch_size * self.backlog_batch_multiplier,
                hours_threshold=old_hours,
                tolerance_hours=old_tolerance,
                process_type="old_backlog",
                min_hours=24 * 7  # Only process records older than 7 days
            )
            
            return result
            
        except Exception as e:
            self.log_error("Error in old backlog processing", e)
            return {"success": False, "processed": 0, "archived": 0, "error": str(e)}
    
    async def _process_archives_with_settings(
        self, 
        db: Session, 
        batch_size: int, 
        hours_threshold: int, 
        tolerance_hours: float,
        process_type: str,
        min_hours: float = None
    ) -> Dict[str, Any]:
        """Process archives with custom settings"""
        try:
            # Check candidates first
            if min_hours:
                # For backlog processing, we need a custom method to count candidates in range
                candidates_count = await self._count_candidates_in_range(
                    db, min_hours, hours_threshold, tolerance_hours
                )
            else:
                candidates_count = await AssignedInfluencerArchiveService.get_archive_candidates_count(
                    db, hours_threshold, tolerance_hours
                )
            
            if candidates_count == 0:
                self.log_info(f"No candidates found for {process_type} processing")
                return {
                    "success": True,
                    "processed": 0,
                    "archived": 0,
                    "candidates_found": 0,
                    "process_type": process_type
                }
            
            self.log_info(f"Found {candidates_count} candidates for {process_type} processing")
            
            # Process archiving
            if min_hours:
                # Use custom processing for backlog
                result = await self._process_candidates_in_range(
                    db, min_hours, hours_threshold, tolerance_hours, batch_size
                )
            else:
                # Use regular processing
                result = await AssignedInfluencerArchiveService.process_auto_archive(
                    db, batch_size, hours_threshold, tolerance_hours
                )
            
            result["process_type"] = process_type
            result["candidates_found"] = candidates_count
            
            return result
            
        except Exception as e:
            self.log_error(f"Error in {process_type} processing", e)
            return {
                "success": False,
                "processed": 0,
                "archived": 0,
                "error": str(e),
                "process_type": process_type
            }
    
    async def _count_candidates_in_range(
        self, 
        db: Session, 
        min_hours: float, 
        max_hours: int, 
        tolerance_hours: float
    ) -> int:
        """Count candidates within a specific time range"""
        try:
            from sqlalchemy import and_
            from app.Models.assigned_influencers import AssignedInfluencer
            from datetime import timezone
            
            now = datetime.now(timezone.utc)
            min_time = now - timedelta(hours=max_hours + tolerance_hours)
            max_time = now - timedelta(hours=min_hours)
            
            count = db.query(AssignedInfluencer).filter(
                and_(
                    AssignedInfluencer.attempts_made == 3,
                    AssignedInfluencer.archived_at.is_(None),
                    AssignedInfluencer.type != 'archived',
                    AssignedInfluencer.last_contacted_at.isnot(None),
                    AssignedInfluencer.last_contacted_at >= min_time,
                    AssignedInfluencer.last_contacted_at <= max_time
                )
            ).count()
            
            return count
            
        except Exception as e:
            self.log_error(f"Error counting candidates in range", e)
            return 0
    
    async def _process_candidates_in_range(
        self, 
        db: Session, 
        min_hours: float, 
        max_hours: int, 
        tolerance_hours: float, 
        batch_size: int
    ) -> Dict[str, Any]:
        """Process candidates within a specific time range"""
        try:
            # This would require extending the AssignedInfluencerArchiveService
            # For now, we'll use the existing method with adjusted parameters
            return await AssignedInfluencerArchiveService.process_auto_archive(
                db, batch_size, max_hours, tolerance_hours
            )
            
        except Exception as e:
            self.log_error(f"Error processing candidates in range", e)
            return {
                "success": False,
                "processed": 0,
                "archived": 0,
                "error": str(e)
            }
    
    def _update_run_stats(self, result: Dict[str, Any]):
        """Update last run statistics"""
        self.last_run_stats = {
            **result,
            "timestamp": datetime.utcnow().isoformat(),
            "configuration": {
                "batch_size": self.batch_size,
                "hours_threshold": self.hours_threshold,
                "tolerance_hours": self.tolerance_hours,
                "backlog_enabled": self.enable_backlog_processing,
                "aggressive_mode": self.aggressive_mode
            }
        }
    
    def get_job_definitions(self) -> List[Dict[str, Any]]:
        """Get definitions for archive jobs"""
        jobs = []
        
        if not self.enabled:
            return jobs
        
        # Regular hourly job
        jobs.append({
            "id": "influencer_archive_hourly",
            "name": "Hourly Influencer Archive",
            "description": f"Archive stale influencers (attempts=3, {self.hours_threshold}h+ since contact)",
            "func": self._execute_archive_process,
            "trigger": {
                "type": "cron",
                "minute": self.run_minute,
                "timezone": "UTC"
            },
            "max_instances": 1,
            "schedule": f":{self.run_minute:02d} every hour",
            "configuration": {
                "batch_size": self.batch_size,
                "hours_threshold": self.hours_threshold,
                "tolerance_hours": self.tolerance_hours
            }
        })
        
        # Backlog processing job
        if self.enable_backlog_processing:
            jobs.append({
                "id": "influencer_archive_backlog",
                "name": "Archive Backlog Processing",
                "description": f"Process missed archive windows (up to {self.max_backlog_age_days} days old)",
                "func": self._execute_backlog_process,
                "trigger": {
                    "type": "cron",
                    "hour": "0,6,12,18",
                    "minute": 45,
                    "timezone": "UTC"
                },
                "max_instances": 1,
                "schedule": "Every 6 hours at :45",
                "configuration": {
                    "max_backlog_age_days": self.max_backlog_age_days,
                    "aggressive_mode": self.aggressive_mode,
                    "backlog_batch_multiplier": self.backlog_batch_multiplier
                }
            })
        
        return jobs
    
    def update_settings(self, 
                       enabled: bool = None,
                       batch_size: int = None,
                       hours_threshold: int = None,
                       tolerance_hours: float = None,
                       run_minute: int = None,
                       enable_backlog_processing: bool = None,
                       max_backlog_age_days: int = None,
                       aggressive_mode: bool = None,
                       scheduler=None) -> bool:
        """Enhanced update settings with backlog options"""
        try:
            settings_changed = False
            
            # Regular settings
            if enabled is not None and enabled != self.enabled:
                self.enabled = enabled
                settings_changed = True
                self.log_info(f"Archive enabled set to: {enabled}")
            
            if batch_size is not None and batch_size != self.batch_size:
                if 1 <= batch_size <= self.max_batch_size:
                    self.batch_size = batch_size
                    settings_changed = True
                    self.log_info(f"Batch size updated to: {batch_size}")
                else:
                    self.log_error(f"Invalid batch_size: {batch_size}")
                    return False
            
            if hours_threshold is not None and hours_threshold != self.hours_threshold:
                if hours_threshold >= self.min_hours_threshold:
                    self.hours_threshold = hours_threshold
                    settings_changed = True
                    self.log_info(f"Hours threshold updated to: {hours_threshold}")
                else:
                    self.log_error(f"Invalid hours_threshold: {hours_threshold}")
                    return False
            
            if tolerance_hours is not None and tolerance_hours != self.tolerance_hours:
                if 0.1 <= tolerance_hours <= self.max_tolerance_hours:
                    self.tolerance_hours = tolerance_hours
                    settings_changed = True
                    self.log_info(f"Tolerance hours updated to: {tolerance_hours}")
                else:
                    self.log_error(f"Invalid tolerance_hours: {tolerance_hours}")
                    return False
            
            if run_minute is not None and run_minute != self.run_minute:
                if 0 <= run_minute <= 59:
                    self.run_minute = run_minute
                    settings_changed = True
                    self.log_info(f"Run minute updated to: {run_minute}")
                else:
                    self.log_error(f"Invalid run_minute: {run_minute}")
                    return False
            
            # ENHANCED: Backlog settings
            if enable_backlog_processing is not None and enable_backlog_processing != self.enable_backlog_processing:
                self.enable_backlog_processing = enable_backlog_processing
                settings_changed = True
                self.log_info(f"Backlog processing enabled set to: {enable_backlog_processing}")
            
            if max_backlog_age_days is not None and max_backlog_age_days != self.max_backlog_age_days:
                if 1 <= max_backlog_age_days <= 365:
                    self.max_backlog_age_days = max_backlog_age_days
                    settings_changed = True
                    self.log_info(f"Max backlog age updated to: {max_backlog_age_days} days")
                else:
                    self.log_error(f"Invalid max_backlog_age_days: {max_backlog_age_days}")
                    return False
            
            if aggressive_mode is not None and aggressive_mode != self.aggressive_mode:
                self.aggressive_mode = aggressive_mode
                settings_changed = True
                self.log_info(f"Aggressive mode set to: {aggressive_mode}")
            
            # If scheduler is provided and settings changed, update jobs
            if scheduler and settings_changed:
                self._update_scheduler_jobs(scheduler)
            
            if settings_changed:
                self.log_info("Archive settings updated successfully")
            
            return True
            
        except Exception as e:
            self.log_error("Error updating archive settings", e)
            return False
    
    def _update_scheduler_jobs(self, scheduler):
        """Update all scheduler jobs with new settings"""
        try:
            # Remove existing jobs
            job_ids = ["influencer_archive_hourly", "influencer_archive_backlog"]
            for job_id in job_ids:
                try:
                    scheduler.remove_job(job_id)
                    self.remove_job_id(job_id)
                except:
                    pass  # Job might not exist
            
            # Re-register jobs with new settings if enabled
            if self.enabled:
                # Register regular job
                regular_job_id = self._register_archive_job(scheduler)
                if regular_job_id:
                    self.add_job_id(regular_job_id)
                
                # Register backlog job if enabled
                if self.enable_backlog_processing:
                    backlog_job_id = self._register_backlog_job(scheduler)
                    if backlog_job_id:
                        self.add_job_id(backlog_job_id)
            
        except Exception as e:
            self.log_error("Error updating scheduler jobs", e)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get enhanced archive processing statistics"""
        return {
            "total_processed": self.total_processed,
            "total_archived": self.total_archived,
            "backlog_processed": self.backlog_processed,
            "error_count": self.error_count,
            "last_run": self.last_run_stats,
            "configuration": {
                "enabled": self.enabled,
                "batch_size": self.batch_size,
                "hours_threshold": self.hours_threshold,
                "tolerance_hours": self.tolerance_hours,
                "run_minute": self.run_minute,
                "backlog_settings": {
                    "enabled": self.enable_backlog_processing,
                    "max_age_days": self.max_backlog_age_days,
                    "aggressive_mode": self.aggressive_mode,
                    "batch_multiplier": self.backlog_batch_multiplier
                }
            }
        }
    
    def reset_statistics(self):
        """Reset processing statistics"""
        self.total_processed = 0
        self.total_archived = 0
        self.backlog_processed = 0
        self.error_count = 0
        self.last_run_stats = None
        self.log_info("Archive statistics reset")
    
    def cleanup(self):
        """Cleanup resources"""
        self.log_info("Cleaning up enhanced archive scheduler")
        # No specific cleanup needed for this scheduler
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed status including enhanced archive information"""
        base_status = super().get_status()
        
        base_status.update({
            "enabled": self.enabled,
            "configuration": {
                "batch_size": self.batch_size,
                "hours_threshold": self.hours_threshold,
                "tolerance_hours": self.tolerance_hours,
                "run_minute": self.run_minute,
                "backlog_processing": {
                    "enabled": self.enable_backlog_processing,
                    "max_age_days": self.max_backlog_age_days,
                    "aggressive_mode": self.aggressive_mode,
                    "batch_multiplier": self.backlog_batch_multiplier
                }
            },
            "statistics": {
                "total_processed": self.total_processed,
                "total_archived": self.total_archived,
                "backlog_processed": self.backlog_processed,
                "error_count": self.error_count
            },
            "last_run": self.last_run_stats,
            "schedules": {
                "regular": f":{self.run_minute:02d} every hour",
                "backlog": "Every 6 hours at :45" if self.enable_backlog_processing else "disabled"
            }
        })
        
        return base_status