# app/Utils/schedulers/scheduler_manager.py

"""
Central manager for all schedulers
Provides unified interface for managing multiple scheduler types
"""

import asyncio
import pytz
from datetime import datetime
from typing import List, Dict, Any, Optional, Type
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.asyncio import AsyncIOExecutor

from .base_scheduler import BaseScheduler
from .daily_reset_scheduler import DailyResetScheduler
from .archive_scheduler import ArchiveScheduler
from app.Utils.Logger import logger


class SchedulerManager:
    """
    Central manager for all application schedulers
    
    Provides unified interface for:
    - Starting/stopping all schedulers
    - Managing individual scheduler instances
    - Monitoring overall scheduler health
    - Centralized configuration and logging
    """
    
    def __init__(self):
        """Initialize the scheduler manager"""
        self.scheduler = None
        self.schedulers: Dict[str, BaseScheduler] = {}
        self.is_running = False
        self.start_time = None
        
        # Initialize default schedulers
        self._initialize_default_schedulers()
    
    def _initialize_default_schedulers(self):
        """Initialize default scheduler instances"""
        try:
            # Add daily reset scheduler
            daily_reset = DailyResetScheduler()
            self.add_scheduler(daily_reset)
            
            # Add archive scheduler
            archive = ArchiveScheduler()
            self.add_scheduler(archive)
            
            logger.info(f"Initialized {len(self.schedulers)} default schedulers")
            
        except Exception as e:
            logger.error(f"Error initializing default schedulers: {str(e)}")
    
    def add_scheduler(self, scheduler: BaseScheduler) -> bool:
        """
        Add a scheduler to the manager
        
        Args:
            scheduler: BaseScheduler instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not isinstance(scheduler, BaseScheduler):
                logger.error(f"Invalid scheduler type: {type(scheduler)}")
                return False
            
            if scheduler.name in self.schedulers:
                logger.warning(f"Scheduler '{scheduler.name}' already exists, replacing")
            
            # Initialize the scheduler
            if scheduler.initialize():
                self.schedulers[scheduler.name] = scheduler
                logger.info(f"Added scheduler: {scheduler.name}")
                
                # If main scheduler is running, register jobs immediately
                if self.is_running and self.scheduler:
                    self._register_scheduler_jobs(scheduler)
                
                return True
            else:
                logger.error(f"Failed to initialize scheduler: {scheduler.name}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding scheduler {scheduler.name}: {str(e)}")
            return False
    
    def remove_scheduler(self, scheduler_name: str) -> bool:
        """
        Remove a scheduler from the manager
        
        Args:
            scheduler_name: Name of scheduler to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if scheduler_name not in self.schedulers:
                logger.warning(f"Scheduler '{scheduler_name}' not found")
                return False
            
            scheduler = self.schedulers[scheduler_name]
            
            # Remove jobs from main scheduler if running
            if self.is_running and self.scheduler:
                for job_id in scheduler.jobs_registered:
                    try:
                        self.scheduler.remove_job(job_id)
                    except:
                        pass  # Job might not exist
            
            # Cleanup scheduler
            scheduler.cleanup()
            
            # Remove from manager
            del self.schedulers[scheduler_name]
            logger.info(f"Removed scheduler: {scheduler_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing scheduler {scheduler_name}: {str(e)}")
            return False
    
    def get_scheduler(self, scheduler_name: str) -> Optional[BaseScheduler]:
        """Get a specific scheduler by name"""
        return self.schedulers.get(scheduler_name)
    
    def start_all_schedulers(self) -> bool:
        """
        Start all schedulers
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.is_running:
                logger.warning("Schedulers are already running")
                return True
            
            logger.info("Starting all schedulers...")
            
            # Create main APScheduler instance
            if self.scheduler is None:
                executors = {
                    'default': AsyncIOExecutor()
                }
                
                self.scheduler = AsyncIOScheduler(
                    executors=executors,
                    timezone=pytz.UTC
                )
            
            # Register jobs from all schedulers
            total_jobs = 0
            for scheduler in self.schedulers.values():
                jobs_registered = self._register_scheduler_jobs(scheduler)
                total_jobs += len(jobs_registered)
            
            # Start the main scheduler
            self.scheduler.start()
            self.is_running = True
            self.start_time = datetime.utcnow()
            
            logger.info(f"All schedulers started successfully with {total_jobs} total jobs")
            self._log_scheduled_jobs()
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting schedulers: {str(e)}")
            self.is_running = False
            return False
    
    def _register_scheduler_jobs(self, scheduler: BaseScheduler) -> List[str]:
        """Register jobs for a specific scheduler"""
        try:
            jobs_registered = scheduler.register_jobs(self.scheduler)
            logger.info(f"Registered {len(jobs_registered)} jobs for scheduler '{scheduler.name}'")
            return jobs_registered
            
        except Exception as e:
            logger.error(f"Error registering jobs for scheduler '{scheduler.name}': {str(e)}")
            return []
    
    def stop_all_schedulers(self) -> bool:
        """
        Stop all schedulers
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.is_running:
                logger.warning("Schedulers are not running")
                return True
            
            logger.info("Stopping all schedulers...")
            
            # Stop the main scheduler
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown(wait=False)
            
            # Cleanup all schedulers
            for scheduler in self.schedulers.values():
                try:
                    scheduler.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up scheduler '{scheduler.name}': {str(e)}")
            
            self.is_running = False
            logger.info("All schedulers stopped successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping schedulers: {str(e)}")
            return False
    
    def restart_all_schedulers(self) -> bool:
        """
        Restart all schedulers
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Restarting all schedulers...")
            
            if not self.stop_all_schedulers():
                return False
            
            # Small delay to ensure complete shutdown
            import time
            time.sleep(1)
            
            return self.start_all_schedulers()
            
        except Exception as e:
            logger.error(f"Error restarting schedulers: {str(e)}")
            return False
    
    def get_overall_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all schedulers"""
        try:
            scheduler_statuses = {}
            total_jobs = 0
            healthy_schedulers = 0
            
            for name, scheduler in self.schedulers.items():
                status = scheduler.get_status()
                scheduler_statuses[name] = status
                total_jobs += status.get("jobs_count", 0)
                
                if status.get("is_initialized", False) and not status.get("last_error"):
                    healthy_schedulers += 1
            
            # Get main scheduler job info
            main_scheduler_jobs = []
            if self.scheduler:
                for job in self.scheduler.get_jobs():
                    main_scheduler_jobs.append({
                        "id": job.id,
                        "name": job.name,
                        "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                        "timezone": str(job.trigger.timezone) if hasattr(job.trigger, 'timezone') else None
                    })
            
            return {
                "manager_status": "running" if self.is_running else "stopped",
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0,
                "schedulers_count": len(self.schedulers),
                "healthy_schedulers": healthy_schedulers,
                "total_jobs": total_jobs,
                "main_scheduler_jobs": main_scheduler_jobs,
                "scheduler_details": scheduler_statuses
            }
            
        except Exception as e:
            logger.error(f"Error getting overall status: {str(e)}")
            return {
                "manager_status": "error",
                "error": str(e),
                "schedulers_count": len(self.schedulers)
            }
    
    def _log_scheduled_jobs(self):
        """Log information about all scheduled jobs"""
        try:
            if self.scheduler:
                jobs = self.scheduler.get_jobs()
                logger.info(f"Total scheduled jobs: {len(jobs)}")
                
                for job in jobs:
                    next_run = job.next_run_time
                    if next_run:
                        logger.info(f"  - {job.name} (ID: {job.id}): Next run at {next_run}")
        except Exception as e:
            logger.error(f"Error logging scheduled jobs: {str(e)}")
    
    def get_scheduler_names(self) -> List[str]:
        """Get list of all scheduler names"""
        return list(self.schedulers.keys())
    
    def get_job_summary(self) -> Dict[str, Any]:
        """Get summary of jobs by scheduler"""
        summary = {}
        
        for name, scheduler in self.schedulers.items():
            job_defs = scheduler.get_job_definitions()
            summary[name] = {
                "job_count": len(job_defs),
                "jobs": [{"id": job["id"], "name": job["name"], "schedule": job.get("schedule", "unknown")} 
                        for job in job_defs]
            }
        
        return summary
    
    def execute_scheduler_method(self, scheduler_name: str, method_name: str, *args, **kwargs) -> Any:
        """
        Execute a method on a specific scheduler
        
        Args:
            scheduler_name: Name of the scheduler
            method_name: Method name to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Method result or None if error
        """
        try:
            scheduler = self.get_scheduler(scheduler_name)
            if not scheduler:
                logger.error(f"Scheduler '{scheduler_name}' not found")
                return None
            
            if not hasattr(scheduler, method_name):
                logger.error(f"Method '{method_name}' not found on scheduler '{scheduler_name}'")
                return None
            
            method = getattr(scheduler, method_name)
            return method(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error executing method '{method_name}' on scheduler '{scheduler_name}': {str(e)}")
            return None
    
    def add_custom_scheduler(self, scheduler_class: Type[BaseScheduler], *args, **kwargs) -> bool:
        """
        Add a custom scheduler class
        
        Args:
            scheduler_class: Class that inherits from BaseScheduler
            *args: Arguments for scheduler constructor
            **kwargs: Keyword arguments for scheduler constructor
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not issubclass(scheduler_class, BaseScheduler):
                logger.error(f"Scheduler class must inherit from BaseScheduler")
                return False
            
            scheduler_instance = scheduler_class(*args, **kwargs)
            return self.add_scheduler(scheduler_instance)
            
        except Exception as e:
            logger.error(f"Error adding custom scheduler: {str(e)}")
            return False
    
    def __str__(self):
        return f"SchedulerManager(schedulers={len(self.schedulers)}, running={self.is_running})"
    
    def __repr__(self):
        return (f"SchedulerManager(schedulers={list(self.schedulers.keys())}, "
                f"running={self.is_running}, jobs={sum(len(s.jobs_registered) for s in self.schedulers.values())})")