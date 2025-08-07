# app/Services/StatusService.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any
from fastapi import HTTPException, status
import uuid

from app.Models.statuses import Status
from app.Utils.Logger import logger

class StatusService:
    """Service for managing statuses"""

    @staticmethod
    async def get_all_statuses(db: Session):
        """
        Get all statuses
        
        Args:
            db: Database session
            
        Returns:
            List[Status]: List of all statuses
        """
        return db.query(Status).all()
    
    @staticmethod
    async def get_statuses_by_model(model: str, db: Session):
        """
        Get all statuses for a specific model
        
        Args:
            model: The model name (e.g., "list_member", "outreach")
            db: Database session
            
        Returns:
            List[Status]: List of statuses for the specified model
        """
        return db.query(Status).filter(Status.model == model).all()
    
    @staticmethod
    async def get_status_by_id(status_id: uuid.UUID, db: Session):
        """
        Get a status by ID
        
        Args:
            status_id: ID of the status
            db: Database session
            
        Returns:
            Status: The status if found
        """
        status_obj = db.query(Status).filter(Status.id == status_id).first()
        
        if not status_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Status not found"
            )
            
        return status_obj
    
    @staticmethod
    async def create_status(status_data: Dict[str, Any], db: Session):
        """
        Create a new status
        
        Args:
            status_data: Status data
            db: Database session
            
        Returns:
            Status: The created status
        """
        try:
            # Check if status with same model and name already exists
            existing_status = db.query(Status).filter(
                Status.model == status_data['model'],
                Status.name == status_data['name']
            ).first()
            
            if existing_status:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Status with model '{status_data['model']}' and name '{status_data['name']}' already exists"
                )
            
            # Create status
            status_obj = Status(**status_data)
            
            db.add(status_obj)
            db.commit()
            db.refresh(status_obj)
            
            return status_obj
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating status"
            ) from e
    
    @staticmethod
    async def update_status(
        status_id: uuid.UUID,
        update_data: Dict[str, Any],
        db: Session
    ):
        """
        Update a status
        
        Args:
            status_id: ID of the status
            update_data: Data to update
            db: Database session
            
        Returns:
            Status: The updated status
        """
        try:
            status_obj = db.query(Status).filter(Status.id == status_id).first()
            
            if not status_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Status not found"
                )
            
            # Check for unique constraint if model or name is being updated
            if ('model' in update_data and update_data['model'] != status_obj.model) or \
               ('name' in update_data and update_data['name'] != status_obj.name):
                
                model = update_data.get('model', status_obj.model)
                name = update_data.get('name', status_obj.name)
                
                existing_status = db.query(Status).filter(
                    Status.model == model,
                    Status.name == name,
                    Status.id != status_id
                ).first()
                
                if existing_status:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Status with model '{model}' and name '{name}' already exists"
                    )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(status_obj, key) and value is not None:
                    setattr(status_obj, key, value)
            
            db.commit()
            db.refresh(status_obj)
            
            return status_obj
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating status"
            ) from e
    
    @staticmethod
    async def delete_status(status_id: uuid.UUID, db: Session):
        """
        Delete a status
        
        Args:
            status_id: ID of the status
            db: Database session
            
        Returns:
            bool: True if successful
        """
        try:
            status_obj = db.query(Status).filter(Status.id == status_id).first()
            
            if not status_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Status not found"
                )
            
            # Check if status is in use
            # You may need to add checks here to prevent deletion of statuses in use
            
            db.delete(status_obj)
            db.commit()
            
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting status"
            ) from e