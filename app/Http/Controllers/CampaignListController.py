# app/Http/Controllers/CampaignListController.py - Fixed imports
from sqlalchemy.orm import Session
import uuid

from app.Models.auth_models import User
from app.Schemas.campaign_lists import (  # Fixed import
    CampaignListCreate, CampaignListUpdate, CampaignListResponse
)

from app.Services.CampaignListService import CampaignListService
from app.Utils.Logger import logger

class CampaignListController:
    """Controller for campaign list-related endpoints"""
    
    @staticmethod
    async def get_all_campaign_lists(db: Session):
        """Get all campaign lists"""
        try:
            lists = await CampaignListService.get_all_lists(db)
            return [CampaignListResponse.model_validate(list_obj) for list_obj in lists]
        except Exception as e:
            logger.error(f"Error in get_all_campaign_lists controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_campaign_lists_by_campaign(campaign_id: uuid.UUID, db: Session):
        """Get all campaign lists for a specific campaign"""
        try:
            lists = await CampaignListService.get_campaign_lists(campaign_id, db)
            return [CampaignListResponse.model_validate(list_obj) for list_obj in lists]
        except Exception as e:
            logger.error(f"Error in get_campaign_lists_by_campaign controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_campaign_list(list_id: uuid.UUID, db: Session):
        """Get a campaign list by ID"""
        try:
            list_obj = await CampaignListService.get_list_by_id(list_id, db)
            return CampaignListResponse.model_validate(list_obj)
        except Exception as e:
            logger.error(f"Error in get_campaign_list controller: {str(e)}")
            raise

    @staticmethod
    async def create_campaign_list(
        list_data: CampaignListCreate,
        current_user: User,
        db: Session
    ):
        """Create a new campaign list"""
        try:
            list_obj = await CampaignListService.create_list(
                list_data.model_dump(exclude_unset=True),
                current_user.id,
                db
            )
            return CampaignListResponse.model_validate(list_obj)
        except Exception as e:
            logger.error(f"Error in create_campaign_list controller: {str(e)}")
            raise

    @staticmethod
    async def create_campaign_list_for_campaign(
        campaign_id: uuid.UUID,
        list_data: CampaignListCreate,
        current_user: User,
        db: Session
    ):
        """Create a new campaign list for a specific campaign"""
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
            logger.error(f"Error in create_campaign_list_for_campaign controller: {str(e)}")
            raise

    @staticmethod
    async def update_campaign_list(
        list_id: uuid.UUID,
        list_data: CampaignListUpdate,
        db: Session
    ):
        """Update a campaign list"""
        try:
            list_obj = await CampaignListService.update_list(
                list_id,
                list_data.model_dump(exclude_unset=True),
                db
            )
            return CampaignListResponse.model_validate(list_obj)
        except Exception as e:
            logger.error(f"Error in update_campaign_list controller: {str(e)}")
            raise

    @staticmethod
    async def delete_campaign_list(list_id: uuid.UUID, db: Session):
        """Delete a campaign list"""
        try:
            await CampaignListService.delete_list(list_id, db)
            return {"message": "Campaign list deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_campaign_list controller: {str(e)}")
            raise

    @staticmethod
    async def get_campaign_list_stats(list_id: uuid.UUID, db: Session):
        """Get statistics for a campaign list"""
        try:
            stats = await CampaignListService.get_list_stats(list_id, db)
            return stats
        except Exception as e:
            logger.error(f"Error in get_campaign_list_stats controller: {str(e)}")
            raise

    @staticmethod
    async def duplicate_campaign_list(
        list_id: uuid.UUID,
        new_name: str,
        current_user: User,
        db: Session
    ):
        """Duplicate a campaign list"""
        try:
            list_obj = await CampaignListService.duplicate_list(list_id, new_name, current_user.id, db)
            return CampaignListResponse.model_validate(list_obj)
        except Exception as e:
            logger.error(f"Error in duplicate_campaign_list controller: {str(e)}")
            raise

    @staticmethod
    async def search_campaign_lists(
        search_term: str,
        campaign_id: uuid.UUID = None,
        db: Session = None
    ):
        """Search campaign lists"""
        try:
            lists = await CampaignListService.search_lists(search_term, campaign_id, db)
            return [CampaignListResponse.model_validate(list_obj) for list_obj in lists]
        except Exception as e:
            logger.error(f"Error in search_campaign_lists controller: {str(e)}")
            raise