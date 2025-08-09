# app/Utils/schedulers/base_scheduler.py

"""
Base abstract class for all schedulers
Provides common functionality and enforces interface consistency
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from app.Utils.Logger import logger


class BaseScheduler(ABC):
    """
    Abstract base class for all scheduler implementations
    
    This ensures consistency across all scheduler types and provides
    common functionality like logging, error handling, and status tracking.
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize base scheduler
        
        Args:
            name: Unique name for this scheduler
            description: Human-readable description
        """
        self.name = name
        self.description = description
        self.scheduler_id = str(uuid.uuid4())
        self.is_initialized = False
        self.jobs_registered = []
        self.last_error = None
        self.created_at = datetime.utcnow()
        
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the scheduler and register jobs
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def register_jobs(self, scheduler) -> List[str]:
        """
        Register all jobs for this scheduler
        
        Args:
            scheduler: APScheduler instance
            
        Returns:
            List[str]: List of job IDs that were registered
        """
        pass
    
    @abstractmethod
    def get_job_definitions(self) -> List[Dict[str, Any]]:
        """
        Get definitions for all jobs managed by this scheduler
        
        Returns:
            List[Dict]: List of job definition dictionaries
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of this scheduler
        
        Returns:
            Dict: Status information
        """
        return {
            "name": self.name,
            "description": self.description,
            "scheduler_id": self.scheduler_id,
            "is_initialized": self.is_initialized,
            "jobs_count": len(self.jobs_registered),
            "jobs_registered": self.jobs_registered,
            "last_error": str(self.last_error) if self.last_error else None,
            "created_at": self.created_at.isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.created_at).total_seconds()
        }
    
    def log_info(self, message: str):
        """Log info message with scheduler context"""
        logger.info(f"[{self.name}] {message}")
    
    def log_error(self, message: str, exception: Exception = None):
        """Log error message with scheduler context"""
        self.last_error = exception or message
        if exception:
            logger.error(f"[{self.name}] {message}: {str(exception)}", exc_info=True)
        else:
            logger.error(f"[{self.name}] {message}")
    
    def log_warning(self, message: str):
        """Log warning message with scheduler context"""
        logger.warning(f"[{self.name}] {message}")
    
    def mark_initialized(self, success: bool = True):
        """Mark scheduler as initialized"""
        self.is_initialized = success
        if success:
            self.log_info(f"Scheduler initialized successfully with {len(self.jobs_registered)} jobs")
        else:
            self.log_error("Scheduler initialization failed")
    
    def add_job_id(self, job_id: str):
        """Add a job ID to the registered jobs list"""
        if job_id not in self.jobs_registered:
            self.jobs_registered.append(job_id)
    
    def remove_job_id(self, job_id: str):
        """Remove a job ID from the registered jobs list"""
        if job_id in self.jobs_registered:
            self.jobs_registered.remove(job_id)
    
    def validate_job_definition(self, job_def: Dict[str, Any]) -> bool:
        """
        Validate a job definition has required fields
        
        Args:
            job_def: Job definition dictionary
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ['id', 'name', 'func', 'trigger']
        
        for field in required_fields:
            if field not in job_def:
                self.log_error(f"Job definition missing required field: {field}")
                return False
        
        return True
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about jobs managed by this scheduler
        
        Returns:
            Dict: Job statistics
        """
        return {
            "total_jobs": len(self.jobs_registered),
            "job_ids": self.jobs_registered,
            "scheduler_type": self.__class__.__name__,
            "is_healthy": self.is_initialized and self.last_error is None
        }
    
    @abstractmethod
    def cleanup(self):
        """
        Cleanup resources when scheduler is shut down
        """
        pass
    
    def __str__(self):
        return f"{self.__class__.__name__}(name='{self.name}', jobs={len(self.jobs_registered)})"
    
    def __repr__(self):
        return (f"{self.__class__.__name__}(name='{self.name}', "
                f"description='{self.description}', "
                f"jobs={len(self.jobs_registered)}, "
                f"initialized={self.is_initialized})")