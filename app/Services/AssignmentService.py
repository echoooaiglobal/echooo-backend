# app/Services/AssignmentService.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status
import uuid

from app.Models.campaign_models import ListAssignment, Agent, Campaign, CampaignList
from app.Models.campaign_list_members import CampaignListMember
from app.Models.influencer_models import SocialAccount
from app.Models.support_models import Platform
from app.Utils.Logger import logger

class AssignmentService:
    """Service for managing assignments and related data"""

    @staticmethod
    async def get_user_assignments(user_id: uuid.UUID, db: Session) -> List[ListAssignment]:
        """
        Get all assignments for a user by finding their agents
        
        Args:
            user_id: ID of the user
            db: Database session
            
        Returns:
            List[ListAssignment]: List of assignments with related data
        """
        try:
            # Get all agents assigned to this user
            user_agents = db.query(Agent).filter(Agent.assigned_to_user_id == user_id).all()
            
            if not user_agents:
                return []
            
            # Get agent IDs
            agent_ids = [agent.id for agent in user_agents]
            
            # Get all assignments for these agents with related data
            assignments = db.query(ListAssignment).options(
                joinedload(ListAssignment.agent).joinedload(Agent.platform),
                joinedload(ListAssignment.agent).joinedload(Agent.status),
                joinedload(ListAssignment.list).joinedload(CampaignList.campaign),
                joinedload(ListAssignment.status)
            ).filter(ListAssignment.agent_id.in_(agent_ids)).all()
            
            return assignments
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting user assignments: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving assignments"
            ) from e

    @staticmethod
    async def get_all_assignments(db: Session) -> List[ListAssignment]:
        """
        Get all assignments (for platform admin)
        
        Args:
            db: Database session
            
        Returns:
            List[ListAssignment]: List of all assignments with related data
        """
        try:
            assignments = db.query(ListAssignment).options(
                joinedload(ListAssignment.agent).joinedload(Agent.platform),
                joinedload(ListAssignment.agent).joinedload(Agent.status),
                joinedload(ListAssignment.list).joinedload(CampaignList.campaign),
                joinedload(ListAssignment.status)
            ).all()
            
            return assignments
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting all assignments: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving assignments"
            ) from e

    @staticmethod
    async def get_assignment_members(
        assignment_id: uuid.UUID, 
        page: int = 1, 
        page_size: int = 10,
        db: Session = None
    ) -> Tuple[List[CampaignListMember], int, ListAssignment]:
        """
        Get paginated members for a specific assignment
        
        Args:
            assignment_id: ID of the assignment
            page: Page number (1-based)
            page_size: Number of items per page
            db: Database session
            
        Returns:
            Tuple[List[CampaignListMember], int, ListAssignment]: Members, total count, and assignment details
        """
        try:
            # First, get the assignment and verify it exists
            assignment = db.query(ListAssignment).options(
                joinedload(ListAssignment.agent),
                joinedload(ListAssignment.list).joinedload(CampaignList.campaign),
                joinedload(ListAssignment.status)
            ).filter(ListAssignment.id == assignment_id).first()
            
            if not assignment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignment not found"
                )
            
            # Get the list_id from the assignment
            list_id = assignment.list_id
            
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Get total count
            total_count = db.query(CampaignListMember).filter(
                CampaignListMember.list_id == list_id
            ).count()
            
            # Get paginated members with eager loading relationships
            members = db.query(CampaignListMember).options(
                joinedload(CampaignListMember.social_account).joinedload(SocialAccount.platform),
                joinedload(CampaignListMember.status),
                joinedload(CampaignListMember.platform)
            ).filter(
                CampaignListMember.list_id == list_id
            ).offset(offset).limit(page_size).all()
            
            return members, total_count, assignment
            
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error getting assignment members: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving assignment members"
            ) from e

    @staticmethod
    async def verify_user_assignment_access(
        user_id: uuid.UUID, 
        assignment_id: uuid.UUID, 
        db: Session
    ) -> bool:
        """
        Verify that a user has access to a specific assignment
        
        Args:
            user_id: ID of the user
            assignment_id: ID of the assignment
            db: Database session
            
        Returns:
            bool: True if user has access, False otherwise
        """
        try:
            # Check if the assignment belongs to any of the user's agents
            assignment = db.query(ListAssignment).join(
                Agent, 
                ListAssignment.agent_id == Agent.id
            ).filter(
                ListAssignment.id == assignment_id,
                Agent.assigned_to_user_id == user_id
            ).first()
            
            return assignment is not None
            
        except SQLAlchemyError as e:
            logger.error(f"Error verifying assignment access: {str(e)}")
            return False