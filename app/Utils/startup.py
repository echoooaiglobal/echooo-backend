# app/Utils/startup.py

"""
Startup utilities for initializing background services
"""

from app.Utils.scheduler import daily_reset_scheduler
from app.Utils.Logger import logger

async def initialize_background_services():
    """
    Initialize all background services when the application starts
    """
    try:
        logger.info("Initializing background services...")
        
        # Start the daily reset scheduler
        daily_reset_scheduler.start_scheduler()
        
        # Add other background services here as needed
        # await initialize_other_services()
        
        logger.info("Background services initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing background services: {str(e)}")
        raise

async def shutdown_background_services():
    """
    Shutdown all background services when the application stops
    """
    try:
        logger.info("Shutting down background services...")
        
        # Stop the daily reset scheduler
        daily_reset_scheduler.stop_scheduler()
        
        # Shutdown other background services here as needed
        # await shutdown_other_services()
        
        logger.info("Background services shutdown complete")
        
    except Exception as e:
        logger.error(f"Error shutting down background services: {str(e)}")