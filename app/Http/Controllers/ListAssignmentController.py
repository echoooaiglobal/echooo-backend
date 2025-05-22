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
        """Create a new list assignment"""
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