# app/Utils/startup.py - Updated for modular scheduler system

"""
Startup utilities for initializing background services with modular scheduler system
"""

from app.Utils.schedulers import scheduler_manager
from app.Utils.Logger import logger


async def initialize_background_services():
    """
    Initialize all background services when the application starts
    """
    try:
        logger.info("Initializing background services...")
        
        # Start all schedulers through the manager
        if scheduler_manager.start_all_schedulers():
            logger.info("All schedulers started successfully")
        else:
            logger.error("Failed to start some schedulers")
            raise Exception("Scheduler initialization failed")
        
        # Add other background services here as needed
        # await initialize_message_queue()
        # await initialize_cache_service()
        # await initialize_monitoring_service()
        
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
        
        # Stop all schedulers through the manager
        if scheduler_manager.stop_all_schedulers():
            logger.info("All schedulers stopped successfully")
        else:
            logger.warning("Some schedulers may not have stopped cleanly")
        
        # Shutdown other background services here as needed
        # await shutdown_message_queue()
        # await shutdown_cache_service()
        # await shutdown_monitoring_service()
        
        logger.info("Background services shutdown complete")
        
    except Exception as e:
        logger.error(f"Error shutting down background services: {str(e)}")