# app/Utils/schedulers/__init__.py

"""
Modular scheduler system for background tasks
"""

from .base_scheduler import BaseScheduler
from .daily_reset_scheduler import DailyResetScheduler
from .archive_scheduler import ArchiveScheduler
from .scheduler_manager import SchedulerManager

# Global scheduler manager instance
scheduler_manager = SchedulerManager()

__all__ = [
    'BaseScheduler',
    'DailyResetScheduler', 
    'ArchiveScheduler',
    'SchedulerManager',
    'scheduler_manager'
]