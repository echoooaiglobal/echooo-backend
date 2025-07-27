# app/Services/AgentAssignmentService.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func, desc, asc
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status
import uuid
import math

from app.Models.agent_assignments import AgentAssignment
from app.Models.outreach_agents import OutreachAgent
from app.Models.campaign_lists import CampaignList
from app.Models.statuses import Status
from app.Utils.Logger import logger
from app.Models.influencer_outreach import InfluencerOutreach
from app.Services.InfluencerOutreachService import InfluencerOutreachService
from app.Models.message_templates import MessageTemplate
from app.Models.campaigns import Campaign

class AgentAssignmentService:
    """Service for managing agent assignments"""

    @staticmethod
    async def get_all_assignments(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        agent_id: Optional[uuid.UUID] = None,
        campaign_list_id: Optional[uuid.UUID] = None,
        include_deleted: bool = False
    ) -> Tuple[List[AgentAssignment], int]:
        """
        Get all agent assignments with optional filtering and pagination
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            status_filter: Optional status filter
            agent_id: Optional agent ID filter
            campaign_list_id: Optional campaign list ID filter
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            Tuple[List[AgentAssignment], int]: Assignments and total count
        """
        try:
            # Build query with relationships
            query = db.query(AgentAssignment).options(
                joinedload(AgentAssignment.agent),
                joinedload(AgentAssignment.campaign_list),
                joinedload(AgentAssignment.status)
            )
            
            # Apply filters
            if not include_deleted:
                query = query.filter(AgentAssignment.deleted_at.is_(None))
            
            if status_filter:
                query = query.join(Status).filter(Status.name == status_filter)
            
            if agent_id:
                query = query.filter(AgentAssignment.outreach_agent_id == agent_id)
            
            if campaign_list_id:
                query = query.filter(AgentAssignment.campaign_list_id == campaign_list_id)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination and ordering
            assignments = query.order_by(desc(AgentAssignment.created_at)).offset(skip).limit(limit).all()
            
            return assignments, total_count
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_all_assignments: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )

    @staticmethod
    async def get_assignment_by_id(assignment_id: uuid.UUID, db: Session) -> AgentAssignment:
        """
        Get a specific agent assignment by ID
        
        Args:
            assignment_id: ID of the assignment
            db: Database session
            
        Returns:
            AgentAssignment: The assignment object
            
        Raises:
            HTTPException: If assignment not found
        """
        try:
            assignment = db.query(AgentAssignment).options(
                joinedload(AgentAssignment.agent),
                joinedload(AgentAssignment.campaign_list),
                joinedload(AgentAssignment.status)
            ).filter(
                AgentAssignment.id == assignment_id,
                AgentAssignment.deleted_at.is_(None)
            ).first()
            
            if not assignment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent assignment not found"
                )
            
            return assignment
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_assignment_by_id: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )

    @staticmethod
    async def create_assignment(assignment_data: Dict[str, Any], db: Session) -> AgentAssignment:
        """
        Create a new agent assignment
        
        Args:
            assignment_data: Assignment data dictionary
            db: Database session
            
        Returns:
            AgentAssignment: Created assignment
            
        Raises:
            HTTPException: If creation fails or validation errors
        """
        try:
            # Validate that agent and campaign list exist
            agent_id = uuid.UUID(assignment_data['outreach_agent_id'])
            list_id = uuid.UUID(assignment_data['campaign_list_id'])
            status_id = uuid.UUID(assignment_data['status_id'])
            
            # Check if agent exists and is available
            agent = db.query(OutreachAgent).filter(
                OutreachAgent.id == agent_id,
                OutreachAgent.deleted_at.is_(None)
            ).first()
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Outreach agent not found"
                )
            
            # Check if campaign list exists
            campaign_list = db.query(CampaignList).filter(
                CampaignList.id == list_id,
                CampaignList.deleted_at.is_(None)
            ).first()
            
            if not campaign_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign list not found"
                )
            
            # Check if status exists
            status_obj = db.query(Status).filter(Status.id == status_id).first()
            if not status_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Status not found"
                )
            
            # Check for existing assignment
            existing = db.query(AgentAssignment).filter(
                and_(
                    AgentAssignment.outreach_agent_id == agent_id,
                    AgentAssignment.campaign_list_id == list_id,
                    AgentAssignment.deleted_at.is_(None)
                )
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Assignment already exists for this agent and campaign list"
                )
            
            # Create assignment
            assignment = AgentAssignment(**assignment_data)
            db.add(assignment)
            db.commit()
            db.refresh(assignment)
            
            # Load relationships
            assignment = await AgentAssignmentService.get_assignment_by_id(assignment.id, db)
            
            return assignment
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid UUID format: {str(e)}"
            )
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in create_assignment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )

    @staticmethod
    async def update_assignment(
        assignment_id: uuid.UUID,
        assignment_data: Dict[str, Any],
        db: Session
    ) -> AgentAssignment:
        """
        Update an agent assignment
        
        Args:
            assignment_id: ID of the assignment to update
            assignment_data: Updated assignment data
            db: Database session
            
        Returns:
            AgentAssignment: Updated assignment
            
        Raises:
            HTTPException: If assignment not found or update fails
        """
        try:
            # Get existing assignment
            assignment = await AgentAssignmentService.get_assignment_by_id(assignment_id, db)
            
            # Validate referenced entities if they're being updated
            if 'outreach_agent_id' in assignment_data:
                agent_id = uuid.UUID(assignment_data['outreach_agent_id'])
                agent = db.query(OutreachAgent).filter(
                    OutreachAgent.id == agent_id,
                    OutreachAgent.deleted_at.is_(None)
                ).first()
                if not agent:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Outreach agent not found"
                    )
            
            if 'campaign_list_id' in assignment_data:
                list_id = uuid.UUID(assignment_data['campaign_list_id'])
                campaign_list = db.query(CampaignList).filter(
                    CampaignList.id == list_id,
                    CampaignList.deleted_at.is_(None)
                ).first()
                if not campaign_list:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Campaign list not found"
                    )
            
            if 'status_id' in assignment_data:
                status_id = uuid.UUID(assignment_data['status_id'])
                status_obj = db.query(Status).filter(Status.id == status_id).first()
                if not status_obj:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Status not found"
                    )
            
            # Update assignment
            for key, value in assignment_data.items():
                if hasattr(assignment, key):
                    setattr(assignment, key, value)
            
            db.commit()
            db.refresh(assignment)
            
            # Reload with relationships
            assignment = await AgentAssignmentService.get_assignment_by_id(assignment_id, db)
            
            return assignment
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid UUID format: {str(e)}"
            )
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in update_assignment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )

    @staticmethod
    async def delete_assignment(assignment_id: uuid.UUID, db: Session, soft_delete: bool = True) -> AgentAssignment:
        """
        Delete an agent assignment (soft delete by default)
        
        Args:
            assignment_id: ID of the assignment to delete
            db: Database session
            soft_delete: Whether to soft delete (default) or hard delete
            
        Returns:
            AgentAssignment: Deleted assignment
            
        Raises:
            HTTPException: If assignment not found or deletion fails
        """
        try:
            assignment = await AgentAssignmentService.get_assignment_by_id(assignment_id, db)
            
            if soft_delete:
                assignment.deleted_at = func.now()
                db.commit()
                db.refresh(assignment)
            else:
                db.delete(assignment)
                db.commit()
            
            return assignment
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in delete_assignment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )

    @staticmethod
    async def get_assignments_by_agent(
        agent_id: uuid.UUID,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[AgentAssignment], int]:
        """Get assignments with dynamically calculated counts"""
        try:
            from app.Models.assigned_influencers import AssignedInfluencer
            from sqlalchemy import case, func
            
            # Query with calculated counts using subqueries
            query = db.query(
                AgentAssignment,
                func.count(AssignedInfluencer.id).label('assigned_count'),
                func.sum(case((AssignedInfluencer.type == 'completed', 1), else_=0)).label('completed_count'),
                func.sum(case((AssignedInfluencer.type == 'active', 1), else_=0)).label('pending_count'),
                func.sum(case((AssignedInfluencer.type == 'archived', 1), else_=0)).label('archived_count')
            ).outerjoin(
                AssignedInfluencer, 
                AssignedInfluencer.agent_assignment_id == AgentAssignment.id
            ).options(
                joinedload(AgentAssignment.agent),
                joinedload(AgentAssignment.campaign_list).joinedload(CampaignList.campaign).joinedload(Campaign.message_templates),
                joinedload(AgentAssignment.status)
            ).filter(
                AgentAssignment.outreach_agent_id == agent_id,
                AgentAssignment.deleted_at.is_(None)
            ).group_by(AgentAssignment.id)
            
            # Get total count and paginated results
            total_count = query.count()
            results = query.offset(skip).limit(limit).all()
            
            # Format results with calculated counts
            assignments = []
            for assignment, assigned_count, completed_count, pending_count, archived_count in results:
                # Add calculated counts as attributes
                assignment.assigned_influencers_count = assigned_count or 0
                assignment.completed_influencers_count = completed_count or 0
                assignment.pending_influencers_count = pending_count or 0
                assignment.archived_influencers_count = archived_count or 0
                assignments.append(assignment)
            
            return assignments, total_count
            
        except Exception as e:
            logger.error(f"Error in get_assignments_by_agent: {str(e)}")
            raise


    @staticmethod
    async def get_assignments_by_campaign_list(
        campaign_list_id: uuid.UUID,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[AgentAssignment], int]:
        """
        Get all assignments for a specific campaign list
        
        Args:
            campaign_list_id: ID of the campaign list
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple[List[AgentAssignment], int]: Assignments and total count
        """
        return await AgentAssignmentService.get_all_assignments(
            db=db,
            skip=skip,
            limit=limit,
            campaign_list_id=campaign_list_id
        )

    @staticmethod
    async def get_assignment_stats(db: Session) -> Dict[str, Any]:
        """
        Get assignment statistics
        
        Args:
            db: Database session
            
        Returns:
            Dict[str, Any]: Assignment statistics
        """
        try:
            # Base query for active assignments
            base_query = db.query(AgentAssignment).filter(AgentAssignment.deleted_at.is_(None))
            
            # Basic counts
            total_assignments = base_query.count()
            
            # Status-based counts (assuming status names)
            active_assignments = base_query.join(Status).filter(Status.name.in_(['active', 'in_progress'])).count()
            completed_assignments = base_query.join(Status).filter(Status.name == 'completed').count()
            pending_assignments = base_query.join(Status).filter(Status.name == 'pending').count()
            
            # Influencer counts
            totals = base_query.with_entities(
                func.sum(AgentAssignment.assigned_influencers_count).label('total_assigned'),
                func.sum(AgentAssignment.completed_influencers_count).label('total_completed'),
                func.sum(AgentAssignment.pending_influencers_count).label('total_pending')
            ).first()
            
            total_assigned_influencers = totals.total_assigned or 0
            total_completed_influencers = totals.total_completed or 0
            total_pending_influencers = totals.total_pending or 0
            
            # Calculate completion rate
            avg_completion_rate = 0.0
            if total_assigned_influencers > 0:
                avg_completion_rate = (total_completed_influencers / total_assigned_influencers) * 100
            
            return {
                "total_assignments": total_assignments,
                "active_assignments": active_assignments,
                "completed_assignments": completed_assignments,
                "pending_assignments": pending_assignments,
                "total_assigned_influencers": total_assigned_influencers,
                "total_completed_influencers": total_completed_influencers,
                "total_pending_influencers": total_pending_influencers,
                "avg_completion_rate": round(avg_completion_rate, 2)
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_assignment_stats: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        
    # Static methods for outreach records related to assignments
    @staticmethod
    async def get_outreach_records_for_assignment(
        agent_assignment_id: uuid.UUID,
        db: Session
    ) -> List[InfluencerOutreach]:
        """Get all outreach records for an agent assignment"""
        try:

            outreach_records = db.query(InfluencerOutreach).filter(
                InfluencerOutreach.agent_assignment_id == agent_assignment_id
            ).order_by(InfluencerOutreach.created_at.desc()).all()
            
            return outreach_records
            
        except Exception as e:
            logger.error(f"Error fetching outreach records for assignment {agent_assignment_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching outreach records for assignment"
            )

    @staticmethod
    async def get_assignment_outreach_stats(
        agent_assignment_id: uuid.UUID,
        db: Session
    ) -> Dict[str, Any]:
        """Get outreach statistics for an assignment"""
        try:
            
            stats = await InfluencerOutreachService.get_outreach_statistics(
                agent_assignment_id=agent_assignment_id,
                db=db
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error fetching outreach stats for assignment {agent_assignment_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching outreach statistics"
            )