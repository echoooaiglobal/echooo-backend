# app/Http/Controllers/ListAssignmentController.py
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

from app.Models.auth_models import User
from app.Schemas.campaign import (
    ListAssignmentCreate, ListAssignmentUpdate, ListAssignmentResponse
)
from app.Services.ListAssignmentService import ListAssignmentService
from app.Utils.Logger import logger

class ListAssignmentController:
    """Controller for list assignment-related endpoints"""
    
    @staticmethod
    async def get_all_assignments(db: Session):
        """Get all list assignments"""
        try:
            assignments = await ListAssignmentService.get_all_assignments(db)
            return [ListAssignmentResponse.model_validate(assignment) for assignment in assignments]
        except Exception as e:
            logger.error(f"Error in get_all_assignments controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_assignments_by_list(list_id: uuid.UUID, db: Session):
        """Get all assignments for a specific list"""
        try:
            assignments = await ListAssignmentService.get_assignments_by_list(list_id, db)
            return [ListAssignmentResponse.model_validate(assignment) for assignment in assignments]
        except Exception as e:
            logger.error(f"Error in get_assignments_by_list controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_assignments_by_agent(agent_id: uuid.UUID, db: Session):
        """Get all assignments for a specific agent"""
        try:
            assignments = await ListAssignmentService.get_assignments_by_agent(agent_id, db)
            return [ListAssignmentResponse.model_validate(assignment) for assignment in assignments]
        except Exception as e:
            logger.error(f"Error in get_assignments_by_agent controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_assignment(assignment_id: uuid.UUID, db: Session):
        """Get a list assignment by ID"""
        try:
            assignment = await ListAssignmentService.get_assignment_by_id(assignment_id, db)
            return ListAssignmentResponse.model_validate(assignment)
        except Exception as e:
            logger.error(f"Error in get_assignment controller: {str(e)}")
            raise
    
    @staticmethod
    async def create_assignment(
        assignment_data: ListAssignmentCreate,
        current_user: User,
        db: Session
    ):
        """
        Create a new list assignment
        Auto-assigns available agent if agent_id not provided
        """
        try:
            assignment = await ListAssignmentService.create_assignment(
                assignment_data.model_dump(exclude_unset=True),
                db
            )
            return ListAssignmentResponse.model_validate(assignment)
        except Exception as e:
            logger.error(f"Error in create_assignment controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_assignment(
        assignment_id: uuid.UUID,
        assignment_data: ListAssignmentUpdate,
        db: Session
    ):
        """Update a list assignment"""
        try:
            assignment = await ListAssignmentService.update_assignment(
                assignment_id,
                assignment_data.model_dump(exclude_unset=True),
                db
            )
            return ListAssignmentResponse.model_validate(assignment)
        except Exception as e:
            logger.error(f"Error in update_assignment controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_assignment_status(
        assignment_id: uuid.UUID,
        status_id: str,
        db: Session
    ):
        """Update assignment status specifically"""
        try:
            # Convert string to UUID if needed
            # status_uuid = uuid.UUID(status_id) if isinstance(status_id, str) else status_id
            
            assignment = await ListAssignmentService.update_assignment_status(
                assignment_id, status_id, db
            )
            return ListAssignmentResponse.model_validate(assignment)
        except Exception as e:
            logger.error(f"Error in update_assignment_status controller: {str(e)}")
            raise
    
    @staticmethod
    async def activate_assignment(assignment_id: uuid.UUID, db: Session):
        """Activate an assignment (convenience method)"""
        try:
            from app.Models.campaign_models import Status
            
            # Find active status
            active_status = db.query(Status).filter(
                Status.model == "list_assignment",
                Status.name == "active"
            ).first()
            
            if not active_status:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Active status not found for list assignments"
                )
            
            assignment = await ListAssignmentService.update_assignment_status(
                assignment_id, active_status.id, db
            )
            return ListAssignmentResponse.model_validate(assignment)
        except Exception as e:
            logger.error(f"Error in activate_assignment controller: {str(e)}")
            raise
    
    @staticmethod
    async def deactivate_assignment(assignment_id: uuid.UUID, db: Session):
        """Deactivate an assignment (convenience method)"""
        try:
            from app.Models.campaign_models import Status
            
            # Find inactive status
            inactive_status = db.query(Status).filter(
                Status.model == "list_assignment",
                Status.name == "inactive"
            ).first()
            
            if not inactive_status:
                # If inactive status doesn't exist, create it or use pending
                pending_status = db.query(Status).filter(
                    Status.model == "list_assignment",
                    Status.name == "pending"
                ).first()
                
                if not pending_status:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="No suitable inactive/pending status found for list assignments"
                    )
                inactive_status = pending_status
            
            assignment = await ListAssignmentService.update_assignment_status(
                assignment_id, inactive_status.id, db
            )
            return ListAssignmentResponse.model_validate(assignment)
        except Exception as e:
            logger.error(f"Error in deactivate_assignment controller: {str(e)}")
            raise
    
    @staticmethod
    async def complete_assignment(
        assignment_id: uuid.UUID,
        db: Session
    ):
        """Mark an assignment as completed"""
        try:
            assignment = await ListAssignmentService.complete_assignment(assignment_id, db)
            return ListAssignmentResponse.model_validate(assignment)
        except Exception as e:
            logger.error(f"Error in complete_assignment controller: {str(e)}")
            raise
    
    @staticmethod
    async def fail_assignment(
        assignment_id: uuid.UUID,
        reason: str,
        db: Session
    ):
        """Mark an assignment as failed"""
        try:
            assignment = await ListAssignmentService.fail_assignment(assignment_id, reason, db)
            return ListAssignmentResponse.model_validate(assignment)
        except Exception as e:
            logger.error(f"Error in fail_assignment controller: {str(e)}")
            raise
    
    @staticmethod
    async def delete_assignment(
        assignment_id: uuid.UUID,
        db: Session
    ):
        """Delete a list assignment"""
        try:
            await ListAssignmentService.delete_assignment(assignment_id, db)
            return {"message": "Assignment deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_assignment controller: {str(e)}")
            raise