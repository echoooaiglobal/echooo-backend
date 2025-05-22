# app/Services/ListAssignmentService.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
import uuid
from app.Models.campaign_models import ListAssignment, CampaignList, Agent
from app.Utils.Logger import logger

class ListAssignmentService:
    """Service for managing list assignments"""

    @staticmethod
    async def get_all_assignments(db: Session):
        """
        Get all list assignments
        
        Args:
            db: Database session
            
        Returns:
            List[ListAssignment]: List of all list assignments
        """
        return db.query(ListAssignment).all()
    
    @staticmethod
    async def get_assignments_by_list(list_id: uuid.UUID, db: Session):
        """
        Get all assignments for a specific list
        
        Args:
            list_id: ID of the list
            db: Database session
            
        Returns:
            List[ListAssignment]: List of list assignments
        """
        return db.query(ListAssignment).filter(ListAssignment.list_id == list_id).all()
    
    @staticmethod
    async def get_assignments_by_agent(agent_id: uuid.UUID, db: Session):
        """
        Get all assignments for a specific agent
        
        Args:
            agent_id: ID of the agent
            db: Database session
            
        Returns:
            List[ListAssignment]: List of list assignments
        """
        return db.query(ListAssignment).filter(ListAssignment.agent_id == agent_id).all()
    
    @staticmethod
    async def get_assignment_by_id(assignment_id: uuid.UUID, db: Session):
        """
        Get an assignment by ID
        
        Args:
            assignment_id: ID of the assignment
            db: Database session
            
        Returns:
            ListAssignment: The assignment if found
        """
        assignment = db.query(ListAssignment).filter(ListAssignment.id == assignment_id).first()
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
            
        return assignment
    
    @staticmethod
    async def create_assignment(assignment_data: Dict[str, Any], db: Session):
        """
        Create a new list assignment
        
        Args:
            assignment_data: Assignment data
            db: Database session
            
        Returns:
            ListAssignment: The created assignment
        """
        try:
            # Validate list exists
            list_id = assignment_data.get('list_id')
            if list_id:
                campaign_list = db.query(CampaignList).filter(CampaignList.id == list_id).first()
                if not campaign_list:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Campaign list not found"
                    )
            
            # Validate agent exists and is available
            agent_id = assignment_data.get('agent_id')
            if agent_id:
                agent = db.query(Agent).filter(Agent.id == agent_id).first()
                if not agent:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Agent not found"
                    )
                
                if not agent.is_available:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Agent is not available for assignment"
                    )
                
                # Check if agent already has an active assignment
                if agent.current_assignment_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Agent already has an active assignment"
                    )
            
            # Create assignment
            assignment = ListAssignment(**assignment_data)
            
            db.add(assignment)
            db.commit()
            
            # Update agent's current assignment
            if agent:
                agent.current_assignment_id = assignment.id
                agent.is_available = False
                db.commit()
            
            db.refresh(assignment)
            
            return assignment
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating list assignment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating list assignment"
            ) from e
    
    @staticmethod
    async def update_assignment(
        assignment_id: uuid.UUID,
        update_data: Dict[str, Any],
        db: Session
    ):
        """
        Update a list assignment
        
        Args:
            assignment_id: ID of the assignment
            update_data: Data to update
            db: Database session
            
        Returns:
            ListAssignment: The updated assignment
        """
        try:
            assignment = db.query(ListAssignment).filter(ListAssignment.id == assignment_id).first()
            
            if not assignment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignment not found"
                )
            
            # Handle status changes
            if 'status_id' in update_data and update_data['status_id'] != assignment.status_id:
                # Get current agent
                agent = db.query(Agent).filter(Agent.id == assignment.agent_id).first()
                
                # If status is being changed to 'completed' or 'failed', free up the agent
                if agent and agent.current_assignment_id == assignment.id:
                    # Check if the new status is 'completed' or 'failed'
                    # This would need to be extended to check specific status IDs or names
                    if 'status_name' in update_data and update_data['status_name'] in ['completed', 'failed']:
                        agent.current_assignment_id = None
                        agent.is_available = True
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(assignment, key) and value is not None:
                    setattr(assignment, key, value)
            
            db.commit()
            db.refresh(assignment)
            
            return assignment
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating list assignment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating list assignment"
            ) from e
    
    @staticmethod
    async def complete_assignment(assignment_id: uuid.UUID, db: Session):
        """
        Mark an assignment as completed and free up the agent
        
        Args:
            assignment_id: ID of the assignment
            db: Database session
            
        Returns:
            ListAssignment: The updated assignment
        """
        try:
            assignment = db.query(ListAssignment).filter(ListAssignment.id == assignment_id).first()
            
            if not assignment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignment not found"
                )
            
            # Get completed status for assignment
            completed_status = db.query('Status').filter(
                'Status.model' == 'list_assignment',
                'Status.name' == 'completed'
            ).first()
            
            if not completed_status:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Completed status not found"
                )
            
            # Update assignment status
            assignment.status_id = completed_status.id
            
            # Free up agent
            agent = db.query(Agent).filter(Agent.id == assignment.agent_id).first()
            if agent and agent.current_assignment_id == assignment.id:
                agent.current_assignment_id = None
                agent.is_available = True
            
            db.commit()
            db.refresh(assignment)
            
            return assignment
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error completing list assignment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error completing list assignment"
            ) from e
    
    @staticmethod
    async def fail_assignment(assignment_id: uuid.UUID, reason: str, db: Session):
        """
        Mark an assignment as failed and free up the agent
        
        Args:
            assignment_id: ID of the assignment
            reason: Reason for failure
            db: Database session
            
        Returns:
            ListAssignment: The updated assignment
        """
        try:
            assignment = db.query(ListAssignment).filter(ListAssignment.id == assignment_id).first()
            
            if not assignment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignment not found"
                )
            
            # Get failed status for assignment
            failed_status = db.query('Status').filter(
                'Status.model' == 'list_assignment',
                'Status.name' == 'failed'
            ).first()
            
            if not failed_status:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed status not found"
                )
            
            # Update assignment status
            assignment.status_id = failed_status.id
            # Add failure reason if model has such field
            if hasattr(assignment, 'failure_reason'):
                assignment.failure_reason = reason
            
            # Free up agent
            agent = db.query(Agent).filter(Agent.id == assignment.agent_id).first()
            if agent and agent.current_assignment_id == assignment.id:
                agent.current_assignment_id = None
                agent.is_available = True
            
            db.commit()
            db.refresh(assignment)
            
            return assignment
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error failing list assignment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error failing list assignment"
            ) from e
    
    @staticmethod
    async def delete_assignment(assignment_id: uuid.UUID, db: Session):
        """
        Delete a list assignment
        
        Args:
            assignment_id: ID of the assignment
            db: Database session
            
        Returns:
            bool: True if successful
        """
        try:
            assignment = db.query(ListAssignment).filter(ListAssignment.id == assignment_id).first()
            
            if not assignment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignment not found"
                )
            
            # Free up agent if this is its current assignment
            agent = db.query(Agent).filter(
                Agent.id == assignment.agent_id,
                Agent.current_assignment_id == assignment.id
            ).first()
            
            if agent:
                agent.current_assignment_id = None
                agent.is_available = True
            
            db.delete(assignment)
            db.commit()
            
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting list assignment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting list assignment"
            ) from e