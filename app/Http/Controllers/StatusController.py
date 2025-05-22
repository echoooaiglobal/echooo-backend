# app/Http/Controllers/StatusController.py
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

from app.Models.auth_models import User
from app.Schemas.campaign import (
    StatusCreate, StatusUpdate, StatusResponse
)
from app.Services.StatusService import StatusService
from app.Utils.Logger import logger

class StatusController:
    """Controller for status-related endpoints"""
    
    @staticmethod
    async def get_all_statuses(db: Session):
        """Get all statuses"""
        try:
            statuses = await StatusService.get_all_statuses(db)
            return [StatusResponse.model_validate(status_obj) for status_obj in statuses]
        except Exception as e:
            logger.error(f"Error in get_all_statuses controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_statuses_by_model(model: str, db: Session):
        """Get all statuses for a specific model"""
        try:
            statuses = await StatusService.get_statuses_by_model(model, db)
            return [StatusResponse.model_validate(status_obj) for status_obj in statuses]
        except Exception as e:
            logger.error(f"Error in get_statuses_by_model controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_status(status_id: uuid.UUID, db: Session):
        """Get a status by ID"""
        try:
            status_obj = await StatusService.get_status_by_id(status_id, db)
            return StatusResponse.model_validate(status_obj)
        except Exception as e:
            logger.error(f"Error in get_status controller: {str(e)}")
            raise
    
    @staticmethod
    async def create_status(
        status_data: StatusCreate,
        db: Session
    ):
        """Create a new status"""
        try:
            status_obj = await StatusService.create_status(
                status_data.model_dump(exclude_unset=True),
                db
            )
            return StatusResponse.model_validate(status_obj)
        except Exception as e:
            logger.error(f"Error in create_status controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_status(
        status_id: uuid.UUID,
        status_data: StatusUpdate,
        db: Session
    ):
        """Update a status"""
        try:
            status_obj = await StatusService.update_status(
                status_id,
                status_data.model_dump(exclude_unset=True),
                db
            )
            return StatusResponse.model_validate(status_obj)
        except Exception as e:
            logger.error(f"Error in update_status controller: {str(e)}")
            raise
    
    @staticmethod
    async def delete_status(status_id: uuid.UUID, db: Session):
        """Delete a status"""
        try:
            await StatusService.delete_status(status_id, db)
            return {"message": "Status deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_status controller: {str(e)}")
            raise