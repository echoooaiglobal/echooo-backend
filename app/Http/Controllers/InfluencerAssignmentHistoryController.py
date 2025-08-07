# app/Http/Controllers/InfluencerAssignmentHistoryController.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import math
from datetime import datetime

from app.Models.influencer_assignment_histories import InfluencerAssignmentHistory
from app.Models.reassignment_reasons import ReassignmentReason
from app.Schemas.influencer_assignment_history import (
    InfluencerAssignmentHistoryResponse, InfluencerAssignmentHistoryListResponse,
    AssignmentHistoryStatsResponse, ReassignmentReasonResponse,
    CampaignInfluencerHistoryBrief, AgentAssignmentHistoryBrief,
    ReassignmentReasonBrief, OutreachAgentBrief, UserBrief
)
from app.Services.InfluencerAssignmentHistoryService import (
    InfluencerAssignmentHistoryService, ReassignmentReasonService
)
from app.Utils.Logger import logger

class InfluencerAssignmentHistoryController:
    """Controller for influencer assignment history-related endpoints"""
    
    @staticmethod
    async def create_assignment_history(
        data: Dict[str, Any],
        db: Session
    ) -> InfluencerAssignmentHistoryResponse:
        """Create a new assignment history record"""
        try:
            history = await InfluencerAssignmentHistoryService.create_assignment_history(data, db)
            return InfluencerAssignmentHistoryController._format_response(history)
        except Exception as e:
            logger.error(f"Error in create_assignment_history controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_assignment_history(
        history_id: uuid.UUID,
        db: Session,
        include_relations: bool = True
    ) -> InfluencerAssignmentHistoryResponse:
        """Get assignment history by ID"""
        try:
            history = await InfluencerAssignmentHistoryService.get_assignment_history_by_id(
                history_id, db, include_relations
            )
            return InfluencerAssignmentHistoryController._format_response(
                history, include_relations
            )
        except Exception as e:
            logger.error(f"Error in get_assignment_history controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_assignment_histories(
        db: Session,
        page: int = 1,
        size: int = 50,
        campaign_influencer_id: Optional[str] = None,
        agent_assignment_id: Optional[str] = None,
        from_agent_id: Optional[str] = None,
        to_agent_id: Optional[str] = None,
        reassignment_reason_id: Optional[str] = None,
        triggered_by: Optional[str] = None,
        reassigned_by: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_relations: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> InfluencerAssignmentHistoryListResponse:
        """Get assignment histories with filtering and pagination"""
        try:
            # Convert string UUIDs to UUID objects
            campaign_influencer_uuid = uuid.UUID(campaign_influencer_id) if campaign_influencer_id else None
            agent_assignment_uuid = uuid.UUID(agent_assignment_id) if agent_assignment_id else None
            from_agent_uuid = uuid.UUID(from_agent_id) if from_agent_id else None
            to_agent_uuid = uuid.UUID(to_agent_id) if to_agent_id else None
            reason_uuid = uuid.UUID(reassignment_reason_id) if reassignment_reason_id else None
            reassigned_by_uuid = uuid.UUID(reassigned_by) if reassigned_by else None
            
            # Calculate skip
            skip = (page - 1) * size
            
            # Get data
            histories, total = await InfluencerAssignmentHistoryService.get_assignment_histories(
                db=db,
                skip=skip,
                limit=size,
                campaign_influencer_id=campaign_influencer_uuid,
                agent_assignment_id=agent_assignment_uuid,
                from_agent_id=from_agent_uuid,
                to_agent_id=to_agent_uuid,
                reassignment_reason_id=reason_uuid,
                triggered_by=triggered_by,
                reassigned_by=reassigned_by_uuid,
                start_date=start_date,
                end_date=end_date,
                include_relations=include_relations,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            # Format responses
            items = [
                InfluencerAssignmentHistoryController._format_response(history, include_relations)
                for history in histories
            ]
            
            # Calculate pagination
            pages = math.ceil(total / size) if total > 0 else 1
            
            return InfluencerAssignmentHistoryListResponse(
                items=items,
                total=total,
                page=page,
                size=size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Error in get_assignment_histories controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_assignment_history(
        history_id: uuid.UUID,
        data: Dict[str, Any],
        db: Session
    ) -> InfluencerAssignmentHistoryResponse:
        """Update assignment history (limited fields)"""
        try:
            history = await InfluencerAssignmentHistoryService.update_assignment_history(
                history_id, data, db
            )
            return InfluencerAssignmentHistoryController._format_response(history)
        except Exception as e:
            logger.error(f"Error in update_assignment_history controller: {str(e)}")
            raise
    
    @staticmethod
    async def bulk_create_assignment_histories(
        histories_data: List[Dict[str, Any]],
        db: Session
    ) -> List[InfluencerAssignmentHistoryResponse]:
        """Bulk create assignment history records"""
        try:
            histories = await InfluencerAssignmentHistoryService.bulk_create_assignment_histories(
                histories_data, db
            )
            return [
                InfluencerAssignmentHistoryController._format_response(history)
                for history in histories
            ]
        except Exception as e:
            logger.error(f"Error in bulk_create_assignment_histories controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_assignment_history_stats(
        db: Session,
        campaign_influencer_id: Optional[str] = None,
        agent_assignment_id: Optional[str] = None,
        from_agent_id: Optional[str] = None,
        to_agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AssignmentHistoryStatsResponse:
        """Get statistics for assignment histories"""
        try:
            # Convert string UUIDs to UUID objects
            campaign_influencer_uuid = uuid.UUID(campaign_influencer_id) if campaign_influencer_id else None
            agent_assignment_uuid = uuid.UUID(agent_assignment_id) if agent_assignment_id else None
            from_agent_uuid = uuid.UUID(from_agent_id) if from_agent_id else None
            to_agent_uuid = uuid.UUID(to_agent_id) if to_agent_id else None
            
            stats = await InfluencerAssignmentHistoryService.get_assignment_history_stats(
                db=db,
                campaign_influencer_id=campaign_influencer_uuid,
                agent_assignment_id=agent_assignment_uuid,
                from_agent_id=from_agent_uuid,
                to_agent_id=to_agent_uuid,
                start_date=start_date,
                end_date=end_date
            )
            
            return AssignmentHistoryStatsResponse(**stats)
        except Exception as e:
            logger.error(f"Error in get_assignment_history_stats controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_by_campaign_influencer(
        campaign_influencer_id: str,
        db: Session,
        page: int = 1,
        size: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> InfluencerAssignmentHistoryListResponse:
        """Get assignment histories for a specific campaign influencer"""
        try:
            return await InfluencerAssignmentHistoryController.get_assignment_histories(
                db=db,
                page=page,
                size=size,
                campaign_influencer_id=campaign_influencer_id,
                include_relations=True,
                sort_by=sort_by,
                sort_order=sort_order
            )
        except Exception as e:
            logger.error(f"Error in get_by_campaign_influencer controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_by_agent(
        agent_id: str,
        db: Session,
        page: int = 1,
        size: int = 50,
        direction: str = "to",  # "to", "from", or "both"
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> InfluencerAssignmentHistoryListResponse:
        """Get assignment histories for a specific agent"""
        try:
            kwargs = {
                "db": db,
                "page": page,
                "size": size,
                "include_relations": True,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
            
            if direction == "to":
                kwargs["to_agent_id"] = agent_id
            elif direction == "from":
                kwargs["from_agent_id"] = agent_id
            elif direction == "both":
                # For "both", we'd need to modify the service to handle OR conditions
                # For now, default to "to"
                kwargs["to_agent_id"] = agent_id
            
            return await InfluencerAssignmentHistoryController.get_assignment_histories(**kwargs)
        except Exception as e:
            logger.error(f"Error in get_by_agent controller: {str(e)}")
            raise
    
    @staticmethod
    def _format_response(
        history: InfluencerAssignmentHistory,
        include_relations: bool = False
    ) -> InfluencerAssignmentHistoryResponse:
        """Format assignment history response"""
        response_data = {
            "id": str(history.id),
            "campaign_influencer_id": str(history.campaign_influencer_id),
            "agent_assignment_id": str(history.agent_assignment_id),
            "from_outreach_agent_id": str(history.from_outreach_agent_id) if history.from_outreach_agent_id else None,
            "to_outreach_agent_id": str(history.to_outreach_agent_id),
            "reassignment_reason_id": str(history.reassignment_reason_id),
            "attempts_before_reassignment": history.attempts_before_reassignment,
            "reassignment_triggered_by": history.reassignment_triggered_by,
            "reassigned_by": str(history.reassigned_by) if history.reassigned_by else None,
            "reassignment_notes": history.reassignment_notes,
            "previous_assignment_data": history.previous_assignment_data,
            "created_at": history.created_at,
            "updated_at": history.updated_at
        }
        
        # Include related objects if requested and available
        if include_relations:
            if hasattr(history, 'campaign_influencer') and history.campaign_influencer:
                response_data["campaign_influencer"] = CampaignInfluencerHistoryBrief(
                    id=str(history.campaign_influencer.id),
                    campaign_list_id=str(history.campaign_influencer.campaign_list_id),
                    social_account_id=str(history.campaign_influencer.social_account_id),
                    status_id=str(history.campaign_influencer.status_id),
                    total_contact_attempts=history.campaign_influencer.total_contact_attempts,
                    collaboration_price=float(history.campaign_influencer.collaboration_price) if history.campaign_influencer.collaboration_price else None,
                    is_ready_for_onboarding=history.campaign_influencer.is_ready_for_onboarding
                )
            
            if hasattr(history, 'agent_assignment') and history.agent_assignment:
                response_data["agent_assignment"] = AgentAssignmentHistoryBrief(
                    id=str(history.agent_assignment.id),
                    outreach_agent_id=str(history.agent_assignment.outreach_agent_id),
                    campaign_list_id=str(history.agent_assignment.campaign_list_id),
                    status_id=str(history.agent_assignment.status_id),
                    assigned_influencers_count=history.agent_assignment.assigned_influencers_count,
                    completed_influencers_count=history.agent_assignment.completed_influencers_count,
                    assigned_at=history.agent_assignment.assigned_at
                )
            
            if hasattr(history, 'reassignment_reason') and history.reassignment_reason:
                response_data["reassignment_reason"] = ReassignmentReasonBrief(
                    id=str(history.reassignment_reason.id),
                    code=history.reassignment_reason.code,
                    name=history.reassignment_reason.name,
                    description=history.reassignment_reason.description,
                    is_system_triggered=history.reassignment_reason.is_system_triggered,
                    is_user_triggered=history.reassignment_reason.is_user_triggered
                )
            
            if hasattr(history, 'from_agent') and history.from_agent:
                response_data["from_agent"] = OutreachAgentBrief(
                    id=str(history.from_agent.id),
                    assigned_user_id=str(history.from_agent.assigned_user_id),
                    is_automation_enabled=history.from_agent.is_automation_enabled,
                    is_available_for_assignment=history.from_agent.is_available_for_assignment,
                    messages_sent_today=history.from_agent.messages_sent_today,
                    last_activity_at=history.from_agent.last_activity_at
                )
            
            if hasattr(history, 'to_agent') and history.to_agent:
                response_data["to_agent"] = OutreachAgentBrief(
                    id=str(history.to_agent.id),
                    assigned_user_id=str(history.to_agent.assigned_user_id),
                    is_automation_enabled=history.to_agent.is_automation_enabled,
                    is_available_for_assignment=history.to_agent.is_available_for_assignment,
                    messages_sent_today=history.to_agent.messages_sent_today,
                    last_activity_at=history.to_agent.last_activity_at
                )
            
            if hasattr(history, 'reassigned_by_user') and history.reassigned_by_user:
                response_data["reassigned_by_user"] = UserBrief(
                    id=str(history.reassigned_by_user.id),
                    email=history.reassigned_by_user.email,
                    first_name=history.reassigned_by_user.first_name,
                    last_name=history.reassigned_by_user.last_name
                )
        
        return InfluencerAssignmentHistoryResponse(**response_data)

class ReassignmentReasonController:
    """Controller for reassignment reason-related endpoints"""
    
    @staticmethod
    async def get_all_reasons(
        db: Session,
        active_only: bool = True,
        triggered_by: Optional[str] = None
    ) -> List[ReassignmentReasonResponse]:
        """Get all reassignment reasons"""
        try:
            reasons = await ReassignmentReasonService.get_all_reasons(
                db, active_only, triggered_by
            )
            return [
                ReassignmentReasonController._format_reason_response(reason)
                for reason in reasons
            ]
        except Exception as e:
            logger.error(f"Error in get_all_reasons controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_reason(
        reason_id: uuid.UUID,
        db: Session
    ) -> ReassignmentReasonResponse:
        """Get reassignment reason by ID"""
        try:
            reason = await ReassignmentReasonService.get_reason_by_id(reason_id, db)
            return ReassignmentReasonController._format_reason_response(reason)
        except Exception as e:
            logger.error(f"Error in get_reason controller: {str(e)}")
            raise
    
    @staticmethod
    async def create_reason(
        data: Dict[str, Any],
        db: Session
    ) -> ReassignmentReasonResponse:
        """Create a new reassignment reason"""
        try:
            reason = await ReassignmentReasonService.create_reason(data, db)
            return ReassignmentReasonController._format_reason_response(reason)
        except Exception as e:
            logger.error(f"Error in create_reason controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_reason(
        reason_id: uuid.UUID,
        data: Dict[str, Any],
        db: Session
    ) -> ReassignmentReasonResponse:
        """Update a reassignment reason"""
        try:
            reason = await ReassignmentReasonService.update_reason(reason_id, data, db)
            return ReassignmentReasonController._format_reason_response(reason)
        except Exception as e:
            logger.error(f"Error in update_reason controller: {str(e)}")
            raise
    
    @staticmethod
    async def delete_reason(
        reason_id: uuid.UUID,
        db: Session
    ) -> Dict[str, str]:
        """Delete (deactivate) a reassignment reason"""
        try:
            await ReassignmentReasonService.delete_reason(reason_id, db)
            return {"message": "Reassignment reason deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_reason controller: {str(e)}")
            raise
    
    @staticmethod
    def _format_reason_response(reason: ReassignmentReason) -> ReassignmentReasonResponse:
        """Format reassignment reason response"""
        return ReassignmentReasonResponse(
            id=str(reason.id),
            code=reason.code,
            name=reason.name,
            description=reason.description,
            is_system_triggered=reason.is_system_triggered,
            is_user_triggered=reason.is_user_triggered,
            is_active=reason.is_active,
            display_order=reason.display_order,
            created_at=reason.created_at,
            updated_at=reason.updated_at
        )