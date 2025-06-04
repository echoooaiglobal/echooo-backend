# app/Services/ListAssignmentService.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
import uuid
from app.Models.campaign_models import ListAssignment, CampaignList, Agent, Status
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
    async def find_available_agent(db: Session, platform_id: Optional[uuid.UUID] = None):
        """
        Find an available agent, optionally filtered by platform
        
        Args:
            db: Database session
            platform_id: Optional platform ID to filter agents
            
        Returns:
            Agent: Available agent if found, None otherwise
        """
        query = db.query(Agent).filter(
            Agent.is_available == True,
            Agent.current_assignment_id == None
        )
        
        # If platform_id is provided, filter by platform
        if platform_id:
            query = query.filter(Agent.platform_id == platform_id)
        
        # Return the first available agent
        return query.first()
    
    @staticmethod
    async def create_assignment(assignment_data: Dict[str, Any], db: Session):
        """
        Create a new list assignment
        Auto-assigns available agent if agent_id is not provided
        
        Args:
            assignment_data: Assignment data
            db: Database session
            
        Returns:
            ListAssignment: The created assignment
        """
        try:
            # Validate list exists
            list_id = assignment_data.get('list_id')
            if not list_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="list_id is required"
                )
            
            campaign_list = db.query(CampaignList).filter(CampaignList.id == list_id).first()
            if not campaign_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign list not found"
                )
            
            # Handle agent assignment
            agent_id = assignment_data.get('agent_id')
            agent = None
            
            if agent_id:
                # Specific agent requested
                agent = db.query(Agent).filter(Agent.id == agent_id).first()
                if not agent:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Specified agent not found"
                    )
                
                if not agent.is_available:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Specified agent is not available for assignment"
                    )
                
                if agent.current_assignment_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Specified agent already has an active assignment"
                    )
            else:
                # Auto-assign available agent
                # Try to find agent for the same platform as the campaign list
                # You might need to determine platform from list members or campaign settings
                agent = await ListAssignmentService.find_available_agent(db)
                
                if not agent:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No available agents found for assignment"
                    )
                
                assignment_data['agent_id'] = agent.id
            
            # Set default status if not provided
            if 'status_id' not in assignment_data or not assignment_data['status_id']:
                default_status = db.query(Status).filter(
                    Status.model == "list_assignment",
                    Status.name == "pending"
                ).first()
                
                if not default_status:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Default 'pending' status not found for list assignments"
                    )
                
                assignment_data['status_id'] = default_status.id
            
            # Create assignment
            assignment = ListAssignment(**assignment_data)
            
            db.add(assignment)
            db.commit()
            
            # Update agent's current assignment
            agent.current_assignment_id = assignment.id
            agent.is_available = False
            db.commit()
            
            db.refresh(assignment)
            
            logger.info(f"Assignment created: {assignment.id} for list {list_id} with agent {agent.id}")
            
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
    async def update_assignment_status(
        assignment_id: uuid.UUID,
        status_id: uuid.UUID,
        db: Session
    ):
        """
        Update assignment status
        
        Args:
            assignment_id: ID of the assignment
            status_id: New status ID
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
            
            # Validate status exists and is for list_assignment model
            new_status = db.query(Status).filter(
                Status.id == status_id,
                Status.model == "list_assignment"
            ).first()
            
            if not new_status:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid status for list assignment"
                )
            
            old_status_name = None
            if assignment.status_id:
                old_status = db.query(Status).filter(Status.id == assignment.status_id).first()
                old_status_name = old_status.name if old_status else None
            
            # Update assignment status
            assignment.status_id = status_id
            
            # Handle agent availability based on status change
            agent = db.query(Agent).filter(Agent.id == assignment.agent_id).first()
            
            if agent and agent.current_assignment_id == assignment.id:
                # If status is changing to 'completed' or 'failed', free up the agent
                if new_status.name in ['completed', 'failed']:
                    agent.current_assignment_id = None
                    agent.is_available = True
                    logger.info(f"Agent {agent.id} freed from assignment {assignment.id}")
                
                # If status is changing to 'active' from 'pending' or 'inactive'
                elif new_status.name == 'active' and old_status_name in ['pending', 'inactive']:
                    agent.is_available = False
                    logger.info(f"Agent {agent.id} activated for assignment {assignment.id}")
                
                # If status is changing to 'inactive'
                elif new_status.name == 'inactive':
                    # Keep the assignment but mark agent as available for other tasks
                    agent.is_available = True
                    logger.info(f"Assignment {assignment.id} set to inactive, agent {agent.id} available")
            
            db.commit()
            db.refresh(assignment)
            
            logger.info(f"Assignment {assignment.id} status updated to {new_status.name}")
            
            return assignment
            
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating assignment status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating assignment status"
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
            
            # If status_id is being updated, use the dedicated status update method
            if 'status_id' in update_data and update_data['status_id']:
                status_id = uuid.UUID(update_data['status_id']) if isinstance(update_data['status_id'], str) else update_data['status_id']
                return await ListAssignmentService.update_assignment_status(assignment_id, status_id, db)
            
            # Update other fields
            for key, value in update_data.items():
                if hasattr(assignment, key) and value is not None and key != 'status_id':
                    setattr(assignment, key, value)
            
            db.commit()
            db.refresh(assignment)
            
            return assignment
            
        except HTTPException:
            db.rollback()
            raise
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
            completed_status = db.query(Status).filter(
                Status.model == 'list_assignment',
                Status.name == 'completed'
            ).first()
            
            if not completed_status:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Completed status not found"
                )
            
            return await ListAssignmentService.update_assignment_status(
                assignment_id, completed_status.id, db
            )
            
        except Exception as e:
            logger.error(f"Error completing list assignment: {str(e)}")
            raise
    
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
            failed_status = db.query(Status).filter(
                Status.model == 'list_assignment',
                Status.name == 'failed'
            ).first()
            
            if not failed_status:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed status not found"
                )
            
            # Update the assignment status first
            assignment = await ListAssignmentService.update_assignment_status(
                assignment_id, failed_status.id, db
            )
            
            # Add failure reason if model has such field
            if hasattr(assignment, 'failure_reason'):
                assignment.failure_reason = reason
                db.commit()
                db.refresh(assignment)
            
            return assignment
            
        except Exception as e:
            logger.error(f"Error failing list assignment: {str(e)}")
            raise
    
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
            
            logger.info(f"Assignment {assignment_id} deleted successfully")
            
            return True
            
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting list assignment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting list assignment"
            ) from e