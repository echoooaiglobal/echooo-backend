# app/Http/Controllers/AgentAssignmentController.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any, Optional, Tuple
import uuid
import math
from sqlalchemy import func, desc

from app.Models.auth_models import User
from app.Models.agent_assignments import AgentAssignment
from app.Schemas.agent_assignment import (
    AgentAssignmentResponse, AgentAssignmentsPaginatedResponse,
    AgentAssignmentStatsResponse, CampaignListBrief, StatusBrief, CampaignBrief
)
from app.Schemas.common import PaginationInfo
from app.Models.outreach_agents import OutreachAgent
from app.Services.AgentAssignmentService import AgentAssignmentService
from app.Utils.Logger import logger
from app.Schemas.agent_assignment import MessageTemplateBrief

class AgentAssignmentController:
    """Controller for agent assignment-related endpoints"""
    
    @staticmethod
    async def get_all_assignments(
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        agent_id: Optional[str] = None,
        campaign_list_id: Optional[str] = None,
        include_deleted: bool = False,
        current_user: User = None,
        db: Session = None
    ) -> AgentAssignmentsPaginatedResponse:
        """
        Get all agent assignments with pagination and filtering
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status_filter: Optional status filter
            agent_id: Optional agent ID filter
            campaign_list_id: Optional campaign list ID filter
            include_deleted: Whether to include soft-deleted records
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            AgentAssignmentsPaginatedResponse: Paginated assignments
        """
        try:
            # Convert string UUIDs to UUID objects if provided
            agent_uuid = None
            if agent_id:
                try:
                    agent_uuid = uuid.UUID(agent_id)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid agent ID format"
                    )
            
            campaign_list_uuid = None
            if campaign_list_id:
                try:
                    campaign_list_uuid = uuid.UUID(campaign_list_id)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid campaign list ID format"
                    )
            
            # Get assignments
            assignments, total_count = await AgentAssignmentService.get_all_assignments(
                db=db,
                skip=skip,
                limit=limit,
                status_filter=status_filter,
                agent_id=agent_uuid,
                campaign_list_id=campaign_list_uuid,
                include_deleted=include_deleted
            )
            
            # Format the response
            formatted_assignments = []
            for assignment in assignments:
                assignment_data = AgentAssignmentController._format_assignment_response(assignment)
                formatted_assignments.append(assignment_data)
            
            # Calculate pagination info
            total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
            page = (skip // limit) + 1
            
            pagination_info = PaginationInfo(
                page=page,
                page_size=limit,
                total_items=total_count,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1
            )

            return AgentAssignmentsPaginatedResponse(
                assignments=formatted_assignments,
                pagination=pagination_info
            )
            
        except Exception as e:
            logger.error(f"Error in get_all_assignments controller: {str(e)}")
            raise

    @staticmethod
    async def get_my_assignments(
        skip: int = 0,
        limit: int = 100,
        current_user: User = None,
        db: Session = None
    ) -> AgentAssignmentsPaginatedResponse:
        """
        Get assignments for the current user's outreach agent
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            AgentAssignmentsPaginatedResponse: Paginated assignments for the user's agent
        """
        try:
            # First, find the outreach agent for the current user
            outreach_agent = db.query(OutreachAgent).filter(
                OutreachAgent.assigned_user_id == current_user.id,
                OutreachAgent.deleted_at.is_(None)
            ).first()
            
            if not outreach_agent:
                # User is not an outreach agent, return empty response
                return AgentAssignmentsPaginatedResponse(
                    assignments=[],
                    page=1,
                    page_size=limit,
                    total_items=0,
                    total_pages=0,
                    has_next=False,
                    has_previous=False
                )
            
            # Get assignments for this agent
            assignments, total_count = await AgentAssignmentService.get_assignments_by_agent(
                outreach_agent.id, db, skip, limit
            )
            
            # Format the response
            formatted_assignments = []
            for assignment in assignments:
                assignment_data = AgentAssignmentController._format_assignment_response(assignment)
                formatted_assignments.append(assignment_data)
            
            # Calculate pagination info
            total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
            page = (skip // limit) + 1
            
            pagination_info = PaginationInfo(
                page=page,
                page_size=limit,
                total_items=total_count,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1
            )

            return AgentAssignmentsPaginatedResponse(
                assignments=formatted_assignments,
                pagination=pagination_info
            )
            
        except Exception as e:
            logger.error(f"Error in get_my_assignments controller: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving assignments"
            )

    @staticmethod
    async def get_assignment(
        assignment_id: str,
        current_user: User = None,
        db: Session = None
    ) -> AgentAssignmentResponse:
        """
        Get a specific agent assignment by ID
        
        Args:
            assignment_id: ID of the assignment
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            AgentAssignmentResponse: Assignment details
        """
        try:
            # Convert string UUID to UUID object
            try:
                assignment_uuid = uuid.UUID(assignment_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid assignment ID format"
                )
            
            # Get assignment
            assignment = await AgentAssignmentService.get_assignment_by_id(assignment_uuid, db)
            
            # Format and return response
            return AgentAssignmentController._format_assignment_response(assignment)
            
        except Exception as e:
            logger.error(f"Error in delete_assignment controller: {str(e)}")
            raise

    @staticmethod
    async def get_assignments_by_agent(
        agent_id: str,
        skip: int = 0,
        limit: int = 100,
        current_user: User = None,
        db: Session = None
    ) -> AgentAssignmentsPaginatedResponse:
        """
        Get all assignments for a specific agent
        
        Args:
            agent_id: ID of the agent
            skip: Number of records to skip
            limit: Maximum number of records to return
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            AgentAssignmentsPaginatedResponse: Paginated assignments for the agent
        """
        try:
            # Convert string UUID to UUID object
            try:
                agent_uuid = uuid.UUID(agent_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid agent ID format"
                )
            
            # Get assignments
            assignments, total_count = await AgentAssignmentService.get_assignments_by_agent(
                agent_uuid, db, skip, limit
            )
            
            # Format the response
            formatted_assignments = []
            for assignment in assignments:
                assignment_data = AgentAssignmentController._format_assignment_response(assignment)
                formatted_assignments.append(assignment_data)
            
            # Calculate pagination info
            total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
            page = (skip // limit) + 1
            
            pagination_info = PaginationInfo(
                page=page,
                page_size=limit,
                total_items=total_count,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1
            )

            return AgentAssignmentsPaginatedResponse(
                assignments=formatted_assignments,
                pagination=pagination_info
            )
            
        except Exception as e:
            logger.error(f"Error in get_assignments_by_agent controller: {str(e)}")
            raise

    @staticmethod
    async def get_assignments_by_campaign_list(
        campaign_list_id: str,
        skip: int = 0,
        limit: int = 100,
        current_user: User = None,
        db: Session = None
    ) -> AgentAssignmentsPaginatedResponse:
        """
        Get all assignments for a specific campaign list
        
        Args:
            campaign_list_id: ID of the campaign list
            skip: Number of records to skip
            limit: Maximum number of records to return
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            AgentAssignmentsPaginatedResponse: Paginated assignments for the campaign list
        """
        try:
            # Convert string UUID to UUID object
            try:
                campaign_list_uuid = uuid.UUID(campaign_list_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid campaign list ID format"
                )
            
            # Get assignments
            assignments, total_count = await AgentAssignmentService.get_assignments_by_campaign_list(
                campaign_list_uuid, db, skip, limit
            )
            
            # Format the response
            formatted_assignments = []
            for assignment in assignments:
                assignment_data = AgentAssignmentController._format_assignment_response(assignment)
                formatted_assignments.append(assignment_data)
            
            # Calculate pagination info
            total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
            page = (skip // limit) + 1
            
            pagination_info = PaginationInfo(
                page=page,
                page_size=limit,
                total_items=total_count,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1
            )

            return AgentAssignmentsPaginatedResponse(
                assignments=formatted_assignments,
                pagination=pagination_info
            )
            
        except Exception as e:
            logger.error(f"Error in get_assignments_by_campaign_list controller: {str(e)}")
            raise

    @staticmethod
    async def update_assignment_status(
        assignment_id: str,
        status_id: str,
        current_user: User = None,
        db: Session = None
    ) -> AgentAssignmentResponse:
        """
        Update assignment status specifically
        
        Args:
            assignment_id: ID of the assignment
            status_id: New status ID
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            AgentAssignmentResponse: Updated assignment
        """
        try:
            # Update using the regular update method
            assignment_data = {"status_id": status_id}
            return await AgentAssignmentController.update_assignment(
                assignment_id, assignment_data, current_user, db
            )
            
        except Exception as e:
            logger.error(f"Error in update_assignment_status controller: {str(e)}")
            raise

    @staticmethod
    async def update_assignment_counts(
        assignment_id: str,
        counts_data: Dict[str, int],
        current_user: User = None,
        db: Session = None
    ) -> AgentAssignmentResponse:
        """
        Update assignment influencer counts
        
        Args:
            assignment_id: ID of the assignment
            counts_data: Dictionary containing count updates
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            AgentAssignmentResponse: Updated assignment
        """
        try:
            # Update using the regular update method
            return await AgentAssignmentController.update_assignment(
                assignment_id, counts_data, current_user, db
            )
            
        except Exception as e:
            logger.error(f"Error in update_assignment_counts controller: {str(e)}")
            raise

    @staticmethod
    async def get_assignment_stats(
        current_user: User = None,
        db: Session = None
    ) -> AgentAssignmentStatsResponse:
        """
        Get assignment statistics
        
        Args:
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            AgentAssignmentStatsResponse: Assignment statistics
        """
        try:
            # Get stats from service
            stats = await AgentAssignmentService.get_assignment_stats(db)
            
            return AgentAssignmentStatsResponse(**stats)
            
        except Exception as e:
            logger.error(f"Error in get_assignment_stats controller: {str(e)}")
            raise

    @staticmethod
    def _format_assignment_response(assignment: AgentAssignment) -> AgentAssignmentResponse:
        """Format an assignment object into a consistent response"""
        try:
            # Create assignment data (UNCHANGED)
            assignment_data = {
                'id': str(assignment.id),
                'outreach_agent_id': str(assignment.outreach_agent_id),
                'campaign_list_id': str(assignment.campaign_list_id),
                'status_id': str(assignment.status_id),
                'assigned_influencers_count': assignment.assigned_influencers_count or 0,
                'completed_influencers_count': assignment.completed_influencers_count or 0,
                'pending_influencers_count': assignment.pending_influencers_count or 0,
                'archived_influencers_count': assignment.archived_influencers_count or 0,
                'assigned_at': assignment.assigned_at,
                'completed_at': assignment.completed_at,
                'created_at': assignment.created_at,
                'updated_at': assignment.updated_at,
                'deleted_at': assignment.deleted_at
            }
            
            response = AgentAssignmentResponse.model_validate(assignment_data)
            
            # Add campaign_list details (UNCHANGED)
            if hasattr(assignment, 'campaign_list') and assignment.campaign_list:
                response.campaign_list = CampaignListBrief.model_validate(assignment.campaign_list)
                
                # Add campaign details with message templates (UPDATED)
                if hasattr(assignment.campaign_list, 'campaign') and assignment.campaign_list.campaign:
                    campaign = assignment.campaign_list.campaign
                    campaign_data = {
                        'id': str(campaign.id),
                        'name': campaign.name,
                        'brand_name': campaign.brand_name,
                        'description': campaign.description,
                        'status_id': str(campaign.status_id) if campaign.status_id else None,
                        'start_date': campaign.start_date,
                        'end_date': campaign.end_date
                    }
                    
                    # ADD message templates if available
                    if hasattr(campaign, 'message_templates') and campaign.message_templates:
                        message_templates_data = []
                        for template in campaign.message_templates:
                            template_data = {
                                'id': str(template.id),
                                'subject': template.subject,  # Can be None for follow-ups
                                'content': template.content,
                                'template_type': template.template_type,  # NEW FIELD
                                'followup_sequence': template.followup_sequence,  # NEW FIELD
                                'followup_delay_hours': template.followup_delay_hours  # NEW FIELD
                            }
                            message_templates_data.append(MessageTemplateBrief.model_validate(template_data))
                        campaign_data['message_templates'] = message_templates_data
                    
                    response.campaign = CampaignBrief.model_validate(campaign_data)
            
            # Add status details (UNCHANGED)
            if hasattr(assignment, 'status') and assignment.status:
                response.status = StatusBrief.model_validate(assignment.status)
            
            return response
            
        except Exception as e:
            logger.error(f"Error formatting assignment response for assignment {assignment.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error formatting assignment data"
            )

    @staticmethod
    async def verify_user_assignment_access(
        user_id: uuid.UUID,
        assignment_id: uuid.UUID,
        db: Session
    ) -> bool:
        """
        Verify if a user has access to a specific assignment
        
        Args:
            user_id: ID of the user
            assignment_id: ID of the assignment
            db: Database session
            
        Returns:
            bool: True if user has access, False otherwise
        """
        try:
            # Check if user has any agents assigned to this assignment
            assignment = db.query(AgentAssignment).options(
                joinedload(AgentAssignment.agent)
            ).filter(
                AgentAssignment.id == assignment_id,
                AgentAssignment.deleted_at.is_(None)
            ).first()
            
            if not assignment or not assignment.agent:
                return False
            
            return assignment.agent.assigned_user_id == user_id
            
        except Exception as e:
            logger.error(f"Error in verify_user_assignment_access: {str(e)}")
            return False

    @staticmethod
    async def get_user_assignments(
        user_id: uuid.UUID,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None
    ) -> Tuple[List[AgentAssignment], int]:
        """
        Get assignments for a specific user through their agents
        
        Args:
            user_id: ID of the user
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            status_filter: Optional status filter
            
        Returns:
            Tuple[List[AgentAssignment], int]: User's assignments and total count
        """
        try:
            # Get user's agents first
            from app.Models.outreach_agents import OutreachAgent
            user_agents = db.query(OutreachAgent).filter(
                OutreachAgent.assigned_user_id == user_id,
                OutreachAgent.deleted_at.is_(None)
            ).all()
            
            if not user_agents:
                return [], 0
            
            agent_ids = [agent.id for agent in user_agents]
            
            # Build query for assignments
            query = db.query(AgentAssignment).options(
                joinedload(AgentAssignment.agent),
                joinedload(AgentAssignment.campaign_list),
                joinedload(AgentAssignment.status)
            ).filter(
                AgentAssignment.outreach_agent_id.in_(agent_ids),
                AgentAssignment.deleted_at.is_(None)
            )
            
            # Apply status filter if provided
            if status_filter:
                from app.Models.statuses import Status
                query = query.join(Status).filter(Status.name == status_filter)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination and ordering
            assignments = query.order_by(desc(AgentAssignment.created_at)).offset(skip).limit(limit).all()
            
            return assignments, total_count
            
        except Exception as e:
            logger.error(f"Error in get_user_assignments: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving user assignments"
            )

    @staticmethod
    async def bulk_update_assignments(
        assignment_ids: List[str],
        update_data: Dict[str, Any],
        current_user: User = None,
        db: Session = None
    ) -> List[AgentAssignmentResponse]:
        """
        Bulk update multiple assignments
        
        Args:
            assignment_ids: List of assignment IDs to update
            update_data: Data to update for all assignments
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            List[AgentAssignmentResponse]: Updated assignments
        """
        try:
            updated_assignments = []
            
            for assignment_id in assignment_ids:
                try:
                    assignment = await AgentAssignmentController.update_assignment(
                        assignment_id, update_data, current_user, db
                    )
                    updated_assignments.append(assignment)
                except Exception as e:
                    logger.error(f"Error updating assignment {assignment_id}: {str(e)}")
                    # Continue with other assignments
                    continue
            
            return updated_assignments
            
        except Exception as e:
            logger.error(f"Error in bulk_update_assignments: {str(e)}")
            raise

    @staticmethod
    async def bulk_delete_assignments(
        assignment_ids: List[str],
        soft_delete: bool = True,
        current_user: User = None,
        db: Session = None
    ) -> List[AgentAssignmentResponse]:
        """
        Bulk delete multiple assignments
        
        Args:
            assignment_ids: List of assignment IDs to delete
            soft_delete: Whether to soft delete or hard delete
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            List[AgentAssignmentResponse]: Deleted assignments
        """
        try:
            deleted_assignments = []
            
            for assignment_id in assignment_ids:
                try:
                    assignment = await AgentAssignmentController.delete_assignment(
                        assignment_id, soft_delete, current_user, db
                    )
                    deleted_assignments.append(assignment)
                except Exception as e:
                    logger.error(f"Error deleting assignment {assignment_id}: {str(e)}")
                    # Continue with other assignments
                    continue
            
            return deleted_assignments
            
        except Exception as e:
            logger.error(f"Error in bulk_delete_assignments: {str(e)}")
            raise

    @staticmethod
    async def get_assignment_history(
        assignment_id: str,
        current_user: User = None,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        Get assignment history/audit trail
        
        Args:
            assignment_id: ID of the assignment
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            List[Dict[str, Any]]: Assignment history records
        """
        try:
            # Convert string UUID to UUID object
            try:
                assignment_uuid = uuid.UUID(assignment_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid assignment ID format"
                )
            
            # Verify assignment exists
            assignment = await AgentAssignmentService.get_assignment_by_id(assignment_uuid, db)
            
            # Get assignment histories
            from app.Models.influencer_assignment_histories import InfluencerAssignmentHistory
            histories = db.query(InfluencerAssignmentHistory).filter(
                InfluencerAssignmentHistory.agent_assignment_id == assignment_uuid
            ).order_by(desc(InfluencerAssignmentHistory.created_at)).all()
            
            # Format history records
            formatted_histories = []
            for history in histories:
                history_data = {
                    "id": str(history.id),
                    "campaign_influencer_id": str(history.campaign_influencer_id),
                    "from_agent_id": str(history.from_outreach_agent_id) if history.from_outreach_agent_id else None,
                    "to_agent_id": str(history.to_outreach_agent_id),
                    "reassignment_reason_id": str(history.reassignment_reason_id),
                    "attempts_before_reassignment": history.attempts_before_reassignment,
                    "reassignment_triggered_by": history.reassignment_triggered_by,
                    "reassigned_by": str(history.reassigned_by) if history.reassigned_by else None,
                    "reassignment_notes": history.reassignment_notes,
                    "previous_assignment_data": history.previous_assignment_data,
                    "created_at": history.created_at,
                    "updated_at": history.updated_at
                }
                formatted_histories.append(history_data)
            
            return formatted_histories
            
        except Exception as e:
            logger.error(f"Error in get_assignment_history: {str(e)}")
            raise

    @staticmethod
    async def assign_influencers_to_agent(
        assignment_id: str,
        influencer_ids: List[str],
        current_user: User = None,
        db: Session = None
    ) -> AgentAssignmentResponse:
        """
        Assign specific influencers to an agent assignment
        
        Args:
            assignment_id: ID of the assignment
            influencer_ids: List of influencer IDs to assign
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            AgentAssignmentResponse: Updated assignment
        """
        try:
            # Convert string UUID to UUID object
            try:
                assignment_uuid = uuid.UUID(assignment_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid assignment ID format"
                )
            
            # Get assignment
            assignment = await AgentAssignmentService.get_assignment_by_id(assignment_uuid, db)
            
            # Convert influencer IDs to UUIDs
            influencer_uuids = []
            for inf_id in influencer_ids:
                try:
                    influencer_uuids.append(uuid.UUID(inf_id))
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid influencer ID format: {inf_id}"
                    )
            
            # Here you would implement the logic to create AssignedInfluencer records
            # This depends on your specific business logic and models
            
            # Update assignment counts
            new_assigned_count = assignment.assigned_influencers_count + len(influencer_ids)
            new_pending_count = assignment.pending_influencers_count + len(influencer_ids)
            
            update_data = {
                "assigned_influencers_count": new_assigned_count,
                "pending_influencers_count": new_pending_count
            }
            
            # Update assignment
            updated_assignment = await AgentAssignmentService.update_assignment(
                assignment_uuid, update_data, db
            )
            
            return AgentAssignmentController._format_assignment_response(updated_assignment)
            
        except Exception as e:
            logger.error(f"Error in assign_influencers_to_agent: {str(e)}")
            raise

    @staticmethod
    async def complete_influencer_outreach(
        assignment_id: str,
        influencer_id: str,
        current_user: User = None,
        db: Session = None
    ) -> AgentAssignmentResponse:
        """
        Mark an influencer's outreach as completed for an assignment
        
        Args:
            assignment_id: ID of the assignment
            influencer_id: ID of the influencer
            completion_notes: Optional notes about completion
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            AgentAssignmentResponse: Updated assignment
        """
        try:
            # Convert string UUIDs to UUID objects
            try:
                assignment_uuid = uuid.UUID(assignment_id)
                influencer_uuid = uuid.UUID(influencer_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid ID format"
                )
            
            # Get assignment
            assignment = await AgentAssignmentService.get_assignment_by_id(assignment_uuid, db)
            
            # Here you would implement the logic to mark the specific influencer as completed
            # This might involve updating AssignedInfluencer records or creating completion records
            
            # Update assignment counts
            update_data = {
                "completed_influencers_count": assignment.completed_influencers_count + 1,
                "pending_influencers_count": max(0, assignment.pending_influencers_count - 1)
            }
            
            # Check if all influencers are completed
            if update_data["pending_influencers_count"] == 0 and assignment.assigned_influencers_count > 0:
                # Get "completed" status
                from app.Models.statuses import Status
                completed_status = db.query(Status).filter(Status.name == "completed").first()
                if completed_status:
                    update_data["status_id"] = str(completed_status.id)
                    update_data["completed_at"] = func.now()
            
            # Update assignment
            updated_assignment = await AgentAssignmentService.update_assignment(
                assignment_uuid, update_data, db
            )
            
            return AgentAssignmentController._format_assignment_response(updated_assignment)
            
        except Exception as e:
            logger.error(f"Error in complete_influencer_outreach: {str(e)}")
            raise

    @staticmethod
    async def reassign_influencer(
        assignment_id: str,
        influencer_id: str,
        new_agent_id: str,
        reassignment_reason: str,
        current_user: User = None,
        db: Session = None
    ) -> AgentAssignmentResponse:
        """
        Reassign an influencer from one agent to another
        
        Args:
            assignment_id: ID of the current assignment
            influencer_id: ID of the influencer to reassign
            new_agent_id: ID of the new agent
            reassignment_reason: Reason for reassignment
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            AgentAssignmentResponse: Updated assignment
        """
        try:
            # Convert string UUIDs to UUID objects
            try:
                assignment_uuid = uuid.UUID(assignment_id)
                influencer_uuid = uuid.UUID(influencer_id)
                new_agent_uuid = uuid.UUID(new_agent_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid ID format"
                )
            
            # Get current assignment
            assignment = await AgentAssignmentService.get_assignment_by_id(assignment_uuid, db)
            
            # Verify new agent exists
            from app.Models.outreach_agents import OutreachAgent
            new_agent = db.query(OutreachAgent).filter(
                OutreachAgent.id == new_agent_uuid,
                OutreachAgent.deleted_at.is_(None)
            ).first()
            
            if not new_agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="New agent not found"
                )
            
            # Here you would implement the reassignment logic
            # This might involve:
            # 1. Creating a new assignment for the new agent
            # 2. Removing the influencer from the current assignment
            # 3. Creating a reassignment history record
            # 4. Updating counts for both assignments
            
            # Update current assignment counts
            update_data = {
                "assigned_influencers_count": max(0, assignment.assigned_influencers_count - 1),
                "pending_influencers_count": max(0, assignment.pending_influencers_count - 1)
            }
            
            # Update assignment
            updated_assignment = await AgentAssignmentService.update_assignment(
                assignment_uuid, update_data, db
            )
            
            return AgentAssignmentController._format_assignment_response(updated_assignment)
            
        except Exception as e:
            logger.error(f"Error in reassign_influencer: {str(e)}")
            raise

    @staticmethod
    async def create_assignment(
        assignment_data: Dict[str, Any],
        current_user: User = None,
        db: Session = None
    ) -> AgentAssignmentResponse:
        """
        Create a new agent assignment
        
        Args:
            assignment_data: Assignment data dictionary
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            AgentAssignmentResponse: Created assignment
        """
        try:
            # Create assignment
            assignment = await AgentAssignmentService.create_assignment(assignment_data, db)
            
            # Format and return response
            return AgentAssignmentController._format_assignment_response(assignment)
            
        except Exception as e:
            logger.error(f"Error in create_assignment controller: {str(e)}")
            raise

    @staticmethod
    async def update_assignment(
        assignment_id: str,
        assignment_data: Dict[str, Any],
        current_user: User = None,
        db: Session = None
    ) -> AgentAssignmentResponse:
        """
        Update an agent assignment
        
        Args:
            assignment_id: ID of the assignment to update
            assignment_data: Updated assignment data
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            AgentAssignmentResponse: Updated assignment
        """
        try:
            # Convert string UUID to UUID object
            try:
                assignment_uuid = uuid.UUID(assignment_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid assignment ID format"
                )
            
            # Update assignment
            assignment = await AgentAssignmentService.update_assignment(
                assignment_uuid, assignment_data, db
            )
            
            # Format and return response
            return AgentAssignmentController._format_assignment_response(assignment)
            
        except Exception as e:
            logger.error(f"Error in update_assignment controller: {str(e)}")
            raise

    @staticmethod
    async def delete_assignment(
        assignment_id: str,
        soft_delete: bool = True,
        current_user: User = None,
        db: Session = None
    ) -> AgentAssignmentResponse:
        """
        Delete an agent assignment
        
        Args:
            assignment_id: ID of the assignment to delete
            soft_delete: Whether to soft delete (default) or hard delete
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            AgentAssignmentResponse: Deleted assignment
        """
        try:
            # Convert string UUID to UUID object
            try:
                assignment_uuid = uuid.UUID(assignment_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid assignment ID format"
                )
            
            # Delete assignment
            assignment = await AgentAssignmentService.delete_assignment(
                assignment_uuid, db, soft_delete
            )
            
            # Format and return response
            return AgentAssignmentController._format_assignment_response(assignment)
            
        except Exception as e:
            logger.error(f"Error in delete_assignment controller: {str(e)}")
            raise