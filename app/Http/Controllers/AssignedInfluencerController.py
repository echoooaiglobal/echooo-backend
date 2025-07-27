# app/Http/Controllers/AssignedInfluencerController.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
import uuid
import math

from app.Models.assigned_influencers import AssignedInfluencer
from app.Schemas.assigned_influencer import (
    AssignedInfluencerResponse, AssignedInfluencerListResponse,
    AssignedInfluencerStatsResponse, CampaignInfluencerBrief,
    AgentAssignmentBrief, StatusBrief, SocialAccountBrief, RecordContactResponse
)
from app.Schemas.common import PaginationInfo
from app.Services.AssignedInfluencerService import AssignedInfluencerService
from app.Utils.Logger import logger

class AssignedInfluencerController:
    """Controller for assigned influencer-related endpoints"""
    
    @staticmethod
    async def create_assigned_influencer(
        data: Dict[str, Any],
        db: Session
    ) -> AssignedInfluencerResponse:
        """Create a new assigned influencer"""
        try:
            assigned_influencer = await AssignedInfluencerService.create_assigned_influencer(data, db)
            return AssignedInfluencerController._format_response(assigned_influencer)
        except Exception as e:
            logger.error(f"Error in create_assigned_influencer controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_assigned_influencer(
        assigned_influencer_id: uuid.UUID,
        db: Session,
        include_relations: bool = True
    ) -> AssignedInfluencerResponse:
        """Get an assigned influencer by ID"""
        try:
            assigned_influencer = await AssignedInfluencerService.get_assigned_influencer_by_id(
                assigned_influencer_id, db, include_relations
            )
            return AssignedInfluencerController._format_response(
                assigned_influencer, include_relations
            )
        except Exception as e:
            logger.error(f"Error in get_assigned_influencer controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_assigned_influencers(
        db: Session,
        page: int = 1,
        size: int = 50,
        agent_assignment_id: Optional[str] = None,
        campaign_influencer_id: Optional[str] = None,
        status_id: Optional[str] = None,
        assignment_type: Optional[str] = None,
        type: Optional[str] = None,  # ADD this line
        include_relations: bool = False,
        sort_by: str = "assigned_at",
        sort_order: str = "desc"
    ) -> AssignedInfluencerListResponse:
        """Get assigned influencers with filtering and pagination"""
        try:
            # Convert string UUIDs to UUID objects
            agent_assignment_uuid = uuid.UUID(agent_assignment_id) if agent_assignment_id else None
            campaign_influencer_uuid = uuid.UUID(campaign_influencer_id) if campaign_influencer_id else None
            status_uuid = uuid.UUID(status_id) if status_id else None
            
            # Calculate skip
            skip = (page - 1) * size
            
            # Get data
            assigned_influencers, total = await AssignedInfluencerService.get_assigned_influencers(
                db=db,
                skip=skip,
                limit=size,
                agent_assignment_id=agent_assignment_uuid,
                campaign_influencer_id=campaign_influencer_uuid,
                status_id=status_uuid,
                assignment_type=assignment_type,
                type=type,  # ADD this line
                include_relations=include_relations,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            # Format responses
            formatted_influencers = [
                AssignedInfluencerController._format_response(ai, include_relations)
                for ai in assigned_influencers
            ]
            
            # Calculate pagination info
            total_pages = math.ceil(total / size) if total > 0 else 1
            
            # Create pagination info object
            pagination_info = PaginationInfo(
                page=page,
                page_size=size,
                total_items=total,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1
            )
            
            # Return with structure
            return AssignedInfluencerListResponse(
                influencers=formatted_influencers,
                pagination=pagination_info
            )
            
        except Exception as e:
            logger.error(f"Error in get_assigned_influencers controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_assigned_influencer(
        assigned_influencer_id: uuid.UUID,
        data: Dict[str, Any],
        db: Session
    ) -> AssignedInfluencerResponse:
        """Update an assigned influencer"""
        try:
            assigned_influencer = await AssignedInfluencerService.update_assigned_influencer(
                assigned_influencer_id, data, db
            )
            return AssignedInfluencerController._format_response(assigned_influencer)
        except Exception as e:
            logger.error(f"Error in update_assigned_influencer controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_status(
        assigned_influencer_id: uuid.UUID,
        status_id: str,
        db: Session
    ) -> AssignedInfluencerResponse:
        """Update only the status of an assigned influencer"""
        try:
            data = {"status_id": status_id}
            assigned_influencer = await AssignedInfluencerService.update_assigned_influencer(
                assigned_influencer_id, data, db
            )
            return AssignedInfluencerController._format_response(assigned_influencer)
        except Exception as e:
            logger.error(f"Error in update_status controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_contact_info(
        assigned_influencer_id: uuid.UUID,
        data: Dict[str, Any],
        db: Session
    ) -> AssignedInfluencerResponse:
        """Update contact information for an assigned influencer"""
        try:
            assigned_influencer = await AssignedInfluencerService.update_contact_info(
                assigned_influencer_id, data, db
            )
            return AssignedInfluencerController._format_response(assigned_influencer)
        except Exception as e:
            logger.error(f"Error in update_contact_info controller: {str(e)}")
            raise
    
    @staticmethod
    async def bulk_update_status(
        influencer_ids: List[str],
        status_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Bulk update status for multiple assigned influencers"""
        try:
            # Convert string UUIDs to UUID objects
            uuid_list = [uuid.UUID(id_str) for id_str in influencer_ids]
            status_uuid = uuid.UUID(status_id)
            
            result = await AssignedInfluencerService.bulk_update_status(
                uuid_list, status_uuid, db
            )
            return result
        except Exception as e:
            logger.error(f"Error in bulk_update_status controller: {str(e)}")
            raise
    
    @staticmethod
    async def transfer_to_agent(
        assigned_influencer_id: uuid.UUID,
        new_agent_assignment_id: str,
        transfer_reason: Optional[str],
        transferred_by_user_id: uuid.UUID,
        db: Session
    ) -> AssignedInfluencerResponse:
        """Transfer an assigned influencer to a different agent"""
        try:
            new_agent_uuid = uuid.UUID(new_agent_assignment_id)
            
            assigned_influencer = await AssignedInfluencerService.transfer_to_agent(
                assigned_influencer_id,
                new_agent_uuid,
                transfer_reason,
                transferred_by_user_id,
                db
            )
            return AssignedInfluencerController._format_response(assigned_influencer)
        except Exception as e:
            logger.error(f"Error in transfer_to_agent controller: {str(e)}")
            raise
    
    @staticmethod
    async def delete_assigned_influencer(
        assigned_influencer_id: uuid.UUID,
        db: Session
    ) -> Dict[str, str]:
        """Delete (archive) an assigned influencer"""
        try:
            await AssignedInfluencerService.delete_assigned_influencer(
                assigned_influencer_id, db
            )
            return {"message": "Assigned influencer archived successfully"}
        except Exception as e:
            logger.error(f"Error in delete_assigned_influencer controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_assigned_influencer_stats(
        db: Session,
        agent_assignment_id: Optional[str] = None,
        campaign_list_id: Optional[str] = None
    ) -> AssignedInfluencerStatsResponse:
        """Get statistics for assigned influencers"""
        try:
            # Convert string UUIDs to UUID objects
            agent_assignment_uuid = uuid.UUID(agent_assignment_id) if agent_assignment_id else None
            campaign_list_uuid = uuid.UUID(campaign_list_id) if campaign_list_id else None
            
            stats = await AssignedInfluencerService.get_assigned_influencer_stats(
                db, agent_assignment_uuid, campaign_list_uuid
            )
            
            return AssignedInfluencerStatsResponse(**stats)
        except Exception as e:
            logger.error(f"Error in get_assigned_influencer_stats controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_by_agent_assignment(
        agent_assignment_id: str,
        db: Session,
        page: int = 1,
        size: int = 50,
        status_id: Optional[str] = None,
        assignment_type: Optional[str] = None,
        type: Optional[str] = None,  # ADD this line
        sort_by: str = "assigned_at",
        sort_order: str = "desc"
    ) -> AssignedInfluencerListResponse:
        """Get assigned influencers for a specific agent assignment"""
        try:
            return await AssignedInfluencerController.get_assigned_influencers(
                db=db,
                page=page,
                size=size,
                agent_assignment_id=agent_assignment_id,
                status_id=status_id,
                assignment_type=assignment_type,
                type=type,  # ADD this line
                include_relations=True,
                sort_by=sort_by,
                sort_order=sort_order
            )
        except Exception as e:
            logger.error(f"Error in get_by_agent_assignment controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_by_campaign_influencer(
        campaign_influencer_id: str,
        db: Session,
        page: int = 1,
        size: int = 50,
        assignment_type: Optional[str] = None
    ) -> AssignedInfluencerListResponse:
        """Get assigned influencers for a specific campaign influencer"""
        try:
            return await AssignedInfluencerController.get_assigned_influencers(
                db=db,
                page=page,
                size=size,
                campaign_influencer_id=campaign_influencer_id,
                assignment_type=assignment_type,
                include_relations=True,
                sort_by="assigned_at",
                sort_order="desc"
            )
        except Exception as e:
            logger.error(f"Error in get_by_campaign_influencer controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_overdue_contacts(
        db: Session,
        page: int = 1,
        size: int = 50,
        agent_assignment_id: Optional[str] = None
    ) -> AssignedInfluencerListResponse:
        """Get assigned influencers with overdue next contact dates"""
        try:
            from datetime import datetime
            from sqlalchemy import and_
            
            # Build query for overdue contacts
            query_filters = {
                "assignment_type": "active",
                "sort_by": "next_contact_at",
                "sort_order": "asc"
            }
            
            if agent_assignment_id:
                query_filters["agent_assignment_id"] = agent_assignment_id
            
            # This would need additional filtering in the service for overdue dates
            # For now, we'll return active assignments and let the frontend filter
            return await AssignedInfluencerController.get_assigned_influencers(
                db=db,
                page=page,
                size=size,
                include_relations=True,
                **query_filters
            )
            
        except Exception as e:
            logger.error(f"Error in get_overdue_contacts controller: {str(e)}")
            raise
    
    @staticmethod
    def _format_response(
        assigned_influencer: AssignedInfluencer,
        include_relations: bool = False
    ) -> AssignedInfluencerResponse:
        """Format assigned influencer response"""
        response_data = {
            "id": str(assigned_influencer.id),
            "campaign_influencer_id": str(assigned_influencer.campaign_influencer_id),
            "agent_assignment_id": str(assigned_influencer.agent_assignment_id),
            "type": assigned_influencer.type,
            "status_id": str(assigned_influencer.status_id),
            "attempts_made": assigned_influencer.attempts_made,
            "last_contacted_at": assigned_influencer.last_contacted_at,
            "next_contact_at": assigned_influencer.next_contact_at,
            "responded_at": assigned_influencer.responded_at,
            "assigned_at": assigned_influencer.assigned_at,
            "archived_at": assigned_influencer.archived_at,
            "notes": assigned_influencer.notes,
            "created_at": assigned_influencer.created_at,
            "updated_at": assigned_influencer.updated_at
        }
        
        # Include related objects if requested and available
        if include_relations:
            if hasattr(assigned_influencer, 'campaign_influencer') and assigned_influencer.campaign_influencer:
                campaign_influencer_data = {
                    "id": str(assigned_influencer.campaign_influencer.id),
                    "campaign_list_id": str(assigned_influencer.campaign_influencer.campaign_list_id),
                    "social_account_id": str(assigned_influencer.campaign_influencer.social_account_id),
                    "status_id": str(assigned_influencer.campaign_influencer.status_id),
                    "total_contact_attempts": assigned_influencer.campaign_influencer.total_contact_attempts,
                    "collaboration_price": float(assigned_influencer.campaign_influencer.collaboration_price) if assigned_influencer.campaign_influencer.collaboration_price else None,
                    "currency": assigned_influencer.campaign_influencer.currency,
                    "is_ready_for_onboarding": assigned_influencer.campaign_influencer.is_ready_for_onboarding,
                    "created_at": assigned_influencer.campaign_influencer.created_at
                }
                
                # ADD campaign influencer status if available
                if hasattr(assigned_influencer.campaign_influencer, 'status') and assigned_influencer.campaign_influencer.status:
                    campaign_influencer_status_data = {
                        "id": str(assigned_influencer.campaign_influencer.status.id),
                        "name": assigned_influencer.campaign_influencer.status.name,
                        "model": assigned_influencer.campaign_influencer.status.model,
                        "description": getattr(assigned_influencer.campaign_influencer.status, 'description', None)
                    }
                    campaign_influencer_data["status"] = StatusBrief.model_validate(campaign_influencer_status_data)
                
                # ADD social account details if available
                if hasattr(assigned_influencer.campaign_influencer, 'social_account') and assigned_influencer.campaign_influencer.social_account:
                    social_account = assigned_influencer.campaign_influencer.social_account
                    social_account_data = {
                        "id": str(social_account.id),
                        "full_name": social_account.full_name,
                        "platform_id": str(social_account.platform_id),
                        "account_handle": social_account.account_handle,
                        "followers_count": social_account.followers_count,
                        "is_verified": social_account.is_verified,
                        "profile_pic_url": social_account.profile_pic_url,
                        "account_url": social_account.account_url
                    }
                    campaign_influencer_data["social_account"] = SocialAccountBrief.model_validate(social_account_data)
                
                response_data["campaign_influencer"] = CampaignInfluencerBrief.model_validate(campaign_influencer_data)
            
            # Add assigned influencer status (this is different from campaign influencer status)
            if hasattr(assigned_influencer, 'status') and assigned_influencer.status:
                response_data["status"] = StatusBrief(
                    id=str(assigned_influencer.status.id),
                    name=assigned_influencer.status.name,
                    model=assigned_influencer.status.model,
                    description=getattr(assigned_influencer.status, 'description', None)
                )
        
        return AssignedInfluencerResponse(**response_data)
    

    @staticmethod
    async def record_contact_attempt(
        assigned_influencer_id: uuid.UUID,
        contact_data: Optional[Dict[str, Any]],
        db: Session
    ) -> RecordContactResponse:
        """
        Record a contact attempt for an assigned influencer
        """
        try:
            result = await AssignedInfluencerService.record_contact_attempt(
                assigned_influencer_id, contact_data, db
            )
            
            # Format the response
            return RecordContactResponse(
                success=result["success"],
                message=result["message"],
                assigned_influencer=AssignedInfluencerController._format_response(
                    result["assigned_influencer"], include_relations=True
                ),
                next_template_info=result["next_template_info"]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in record_contact_attempt controller: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error recording contact attempt"
            )