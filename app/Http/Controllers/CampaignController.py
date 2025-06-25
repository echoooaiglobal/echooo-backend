# app/Http/Controllers/CampaignController.py
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

from app.Models.auth_models import User
from app.Models.campaign_models import Campaign, CampaignList
from app.Schemas.campaign import (
    CampaignCreate, CampaignUpdate, CampaignResponse, CategoryBrief, StatusBrief,
    CampaignListCreate, CampaignListResponse, CampaignListUpdate, CampaignListBrief,ListAssignmentBrief
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

    # Helper method to format campaign responses consistently
    @staticmethod
    def _format_campaign_response(campaign: Campaign) -> CampaignResponse:
        """Format a campaign object into a consistent response"""
        response = CampaignResponse.model_validate(campaign)
        
        # Add category details if available
        if campaign.category:
            response.category = CategoryBrief.model_validate(campaign.category)
        
        # Add status details if available
        if campaign.status:
            response.status = StatusBrief.model_validate(campaign.status)
        
        # Add campaign lists if available
        if campaign.campaign_lists:
            response.campaign_lists = [
                CampaignListBrief.model_validate(list_obj) 
                for list_obj in campaign.campaign_lists
            ]
        
        # Add message templates if available
        if campaign.message_templates:
            from app.Schemas.campaign import MessageTemplatesBrief
            response.message_templates = [
                MessageTemplatesBrief.model_validate(template) 
                for template in campaign.message_templates
            ]
        
        # Add list assignments - collect from all campaign lists
        list_assignments = []
        if campaign.campaign_lists:
            for campaign_list in campaign.campaign_lists:
                if campaign_list.assignments:
                    for assignment in campaign_list.assignments:
                        assignment_brief = ListAssignmentBrief.model_validate(assignment)
                        
                        # Add status details if available
                        if assignment.status:
                            assignment_brief.status = StatusBrief.model_validate(assignment.status)
                        
                        list_assignments.append(assignment_brief)
        
        response.list_assignments = list_assignments
        
        return response
    
    @staticmethod
    async def delete_campaign(campaign_id: uuid.UUID, current_user: User, db: Session):
        """Soft delete a campaign"""
        try:
            await CampaignService.delete_campaign(campaign_id, current_user.id, db)  # Pass user ID for deleted_by
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

    # Campaign List methods
    @staticmethod
    async def get_campaign_lists(campaign_id: uuid.UUID, db: Session):
        """Get all campaign lists for a campaign"""
        try:
            lists = await CampaignListService.get_campaign_lists(campaign_id, db)
            return [CampaignListResponse.model_validate(list_obj) for list_obj in lists]
        except Exception as e:
            logger.error(f"Error in get_campaign_lists controller: {str(e)}")
            raise

    @staticmethod
    async def create_list(
        campaign_id: uuid.UUID,
        list_data: CampaignListCreate,
        current_user: User,
        db: Session
    ):
        """Create a new campaign list for a campaign"""
        try:
            list_data_dict = list_data.model_dump(exclude_unset=True)
            list_data_dict['campaign_id'] = str(campaign_id)
            
            list_obj = await CampaignListService.create_list(
                list_data_dict,
                current_user.id,
                db
            )
            return CampaignListResponse.model_validate(list_obj)
        except Exception as e:
            logger.error(f"Error in create_list controller: {str(e)}")
            raise