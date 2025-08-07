# app/Http/Controllers/CampaignController.py - Updated version
from sqlalchemy.orm import Session, object_session
import uuid

from app.Models.auth_models import User
from app.Schemas.campaign import (
    CampaignCreate, CampaignUpdate, CampaignResponse, CategoryBrief, StatusBrief,
    CampaignListResponse, CampaignListBrief, ListAssignmentBrief, MessageTemplatesBrief
)

from app.Services.CampaignService import CampaignService
from app.Services.CampaignListService import CampaignListService
from app.Utils.Logger import logger

class CampaignController:
    """Controller for campaign-related endpoints"""
    
    @staticmethod
    async def get_all_campaigns(db: Session):
        """Get all campaigns"""
        try:
            campaigns = await CampaignService.get_all_campaigns(db)
            return [
                CampaignController._format_campaign_response(campaign) 
                for campaign in campaigns
            ]
        except Exception as e:
            logger.error(f"Error in get_all_campaigns controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_company_campaigns(company_id: uuid.UUID, db: Session):
        """Get all campaigns for a specific company"""
        try:
            campaigns = await CampaignService.get_company_campaigns(company_id, db)
            return [
                CampaignController._format_campaign_response(campaign)
                for campaign in campaigns
            ]
        except Exception as e:
            logger.error(f"Error in get_company_campaigns controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_campaign(campaign_id: uuid.UUID, db: Session):
        """Get a campaign by ID"""
        try:
            campaign = await CampaignService.get_campaign_by_id(campaign_id, db)
            return CampaignController._format_campaign_response(campaign)
        except Exception as e:
            logger.error(f"Error in get_campaign controller: {str(e)}")
            raise

    @staticmethod
    async def get_company_deleted_campaigns(company_id: uuid.UUID, db: Session):
        """Get all deleted campaigns for a specific company"""
        try:
            campaigns = await CampaignService.get_company_deleted_campaigns(company_id, db)
            return [
                CampaignController._format_campaign_response(campaign)
                for campaign in campaigns
            ]
        except Exception as e:
            logger.error(f"Error in get_company_deleted_campaigns controller: {str(e)}")
            raise

    @staticmethod
    async def get_all_deleted_campaigns(db: Session):
        """Get all deleted campaigns (for platform admins)"""
        try:
            campaigns = await CampaignService.get_all_deleted_campaigns(db)
            return [
                CampaignController._format_campaign_response(campaign)
                for campaign in campaigns
            ]
        except Exception as e:
            logger.error(f"Error in get_all_deleted_campaigns controller: {str(e)}")
            raise

    @staticmethod
    async def create_campaign(
        campaign_data: CampaignCreate,
        current_user: User,
        db: Session
    ):
        """Create a new campaign"""
        try:
            campaign = await CampaignService.create_campaign(
                campaign_data.model_dump(exclude_unset=True),
                current_user.id,
                db
            )
            return CampaignController._format_campaign_response(campaign)
        except Exception as e:
            logger.error(f"Error in create_campaign controller: {str(e)}")
            raise

    @staticmethod
    async def update_campaign(
        campaign_id: uuid.UUID,
        campaign_data: CampaignUpdate,
        db: Session
    ):
        """Update a campaign"""
        try:
            campaign = await CampaignService.update_campaign(
                campaign_id,
                campaign_data.model_dump(exclude_unset=True),
                db
            )
            return CampaignController._format_campaign_response(campaign)
        except Exception as e:
            logger.error(f"Error in update_campaign controller: {str(e)}")
            raise

    @staticmethod
    async def delete_campaign(campaign_id: uuid.UUID, current_user: User, db: Session):
        """Soft delete a campaign"""
        try:
            await CampaignService.delete_campaign(campaign_id, current_user.id, db)
            return {"message": "Campaign deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_campaign controller: {str(e)}")
            raise

    @staticmethod
    async def restore_campaign(campaign_id: uuid.UUID, db: Session):
        """Restore a soft deleted campaign"""
        try:
            campaign = await CampaignService.restore_campaign(campaign_id, db)
            return CampaignController._format_campaign_response(campaign)
        except Exception as e:
            logger.error(f"Error in restore_campaign controller: {str(e)}")
            raise

    @staticmethod
    async def hard_delete_campaign(campaign_id: uuid.UUID, db: Session):
        """Permanently delete a campaign"""
        try:
            await CampaignService.hard_delete_campaign(campaign_id, db)
            return {"message": "Campaign permanently deleted"}
        except Exception as e:
            logger.error(f"Error in hard_delete_campaign controller: {str(e)}")
            raise

    # Campaign List methods - Keep these for backward compatibility
    @staticmethod
    async def get_campaign_lists(campaign_id: uuid.UUID, db: Session):
        """Get all campaign lists for a campaign"""
        try:
            lists = await CampaignListService.get_campaign_lists(campaign_id, db)
            return [CampaignListResponse.model_validate(list_obj) for list_obj in lists]
        except Exception as e:
            logger.error(f"Error in get_campaign_lists controller: {str(e)}")
            raise

    # Helper method to format campaign responses consistently
    @staticmethod
    def _format_campaign_response(campaign):
        """Format campaign response with related data"""
        try:
            from sqlalchemy import func
            from app.Models.campaign_influencers import CampaignInfluencer
            
            # Get database session from campaign object
            db = object_session(campaign)
            
            # Format campaign lists with detailed influencer statistics
            campaign_lists_data = []
            for campaign_list in campaign.campaign_lists:
                # Count total influencers for this campaign list
                total_influencers = db.query(func.count(CampaignInfluencer.id)).filter(
                    CampaignInfluencer.campaign_list_id == campaign_list.id,
                    CampaignInfluencer.deleted_at.is_(None)  # Exclude soft deleted
                ).scalar() or 0
                
                # Count onboarded influencers for this list
                onboarded_count = db.query(func.count(CampaignInfluencer.id)).filter(
                    CampaignInfluencer.campaign_list_id == campaign_list.id,
                    CampaignInfluencer.is_ready_for_onboarding == True,
                    CampaignInfluencer.deleted_at.is_(None)
                ).scalar() or 0
                
                # Count contacted influencers for this list
                contacted_count = db.query(func.count(CampaignInfluencer.id)).filter(
                    CampaignInfluencer.campaign_list_id == campaign_list.id,
                    CampaignInfluencer.total_contact_attempts > 0,
                    CampaignInfluencer.deleted_at.is_(None)
                ).scalar() or 0
                
                # Average collaboration price for this list
                avg_price = db.query(func.avg(CampaignInfluencer.collaboration_price)).filter(
                    CampaignInfluencer.campaign_list_id == campaign_list.id,
                    CampaignInfluencer.collaboration_price.isnot(None),
                    CampaignInfluencer.deleted_at.is_(None)
                ).scalar()
                
                # Last activity date for this list
                last_activity = db.query(func.max(CampaignInfluencer.updated_at)).filter(
                    CampaignInfluencer.campaign_list_id == campaign_list.id,
                    CampaignInfluencer.deleted_at.is_(None)
                ).scalar()
                
                # Calculate completion percentage for this list
                list_completion_percentage = (
                    (onboarded_count / total_influencers * 100) 
                    if total_influencers > 0 else 0.0
                )
                
                # Calculate days since list creation
                from datetime import datetime, timezone
                list_days_since_created = (datetime.now(timezone.utc) - campaign_list.created_at).days
                
                # Create campaign list brief with detailed statistics
                list_data = {
                    "id": str(campaign_list.id),
                    "name": campaign_list.name,
                    "description": campaign_list.description,
                    "total_influencers_count": total_influencers,
                    "total_onboarded_count": onboarded_count,
                    "total_contacted_count": contacted_count,
                    "avg_collaboration_price": float(avg_price) if avg_price else None,
                    "completion_percentage": round(list_completion_percentage, 1),
                    "days_since_created": list_days_since_created,
                    "last_activity_date": last_activity
                }
                campaign_lists_data.append(CampaignListBrief.model_validate(list_data))

            # Format other related data (existing code)
            category_brief = None
            if campaign.category:
                category_brief = CategoryBrief.model_validate(campaign.category)

            status_brief = None
            if campaign.status:
                status_brief = StatusBrief.model_validate(campaign.status)

            message_templates_data = []
            for template in campaign.message_templates:
                message_templates_data.append(MessageTemplatesBrief.model_validate(template))

            list_assignments_data = []
            # Get assignments through campaign_lists -> agent_assignments relationship
            if hasattr(campaign, 'campaign_lists') and campaign.campaign_lists:
                for campaign_list in campaign.campaign_lists:
                    if hasattr(campaign_list, 'agent_assignments') and campaign_list.agent_assignments:
                        for assignment in campaign_list.agent_assignments:
                            # Use original field names to match AgentAssignment model
                            assignment_data = {
                                "id": str(assignment.id),
                                "campaign_list_id": str(assignment.campaign_list_id),  # Keep original field name
                                "outreach_agent_id": str(assignment.outreach_agent_id),  # Keep original field name
                                "status_id": str(assignment.status_id),
                                "created_at": assignment.created_at,
                                "updated_at": assignment.updated_at
                            }
                            
                            status_data = None
                            if assignment.status:
                                status_data = StatusBrief.model_validate(assignment.status)
                            assignment_data["status"] = status_data
                            
                            list_assignments_data.append(ListAssignmentBrief.model_validate(assignment_data))

            # Create campaign response (frontend will calculate totals from campaign_lists)
            campaign_data = {
                "id": str(campaign.id),
                "company_id": str(campaign.company_id),
                "name": campaign.name,
                "description": campaign.description,
                "brand_name": campaign.brand_name,
                "budget": campaign.budget,
                "category_id": str(campaign.category_id) if campaign.category_id else None,
                "status_id": str(campaign.status_id) if campaign.status_id else None,
                "created_by": str(campaign.created_by),
                "default_filters": campaign.default_filters,
                "is_deleted": campaign.is_deleted,
                "deleted_at": campaign.deleted_at,
                "deleted_by": str(campaign.deleted_by) if campaign.deleted_by else None,
                "created_at": campaign.created_at,
                "updated_at": campaign.updated_at,
                "category": category_brief,
                "status": status_brief,
                "campaign_lists": campaign_lists_data,  # Includes detailed stats per list
                "message_templates": message_templates_data,
                "list_assignments": list_assignments_data
            }

            return CampaignResponse.model_validate(campaign_data)
            
        except Exception as e:
            logger.error(f"Error formatting campaign response: {str(e)}")
            raise