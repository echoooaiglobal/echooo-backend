# app/Http/Controllers/InfluencerController.py
from sqlalchemy.orm import Session
import uuid

from app.Schemas.influencer import (
    InfluencerCreate, InfluencerUpdate, InfluencerResponse,
    SocialAccountCreate, SocialAccountUpdate, SocialAccountResponse,
    InfluencerContactCreate, InfluencerContactUpdate, InfluencerContactResponse
)
from app.Services.InfluencerService import InfluencerService
from app.Utils.Logger import logger

class InfluencerController:
    """Controller for influencer-related endpoints"""
    
    @staticmethod
    async def create_influencer(
        influencer_data: InfluencerCreate,
        db: Session
    ):
        """Create a new influencer profile"""
        try:
            influencer = await InfluencerService.create_influencer_profile(
                influencer_data.user_id,
                db
            )
            return InfluencerResponse.from_orm(influencer)
        except Exception as e:
            logger.error(f"Error in create_influencer controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_influencer(
        influencer_id: uuid.UUID,
        db: Session
    ):
        """Get an influencer by ID"""
        try:
            influencer = await InfluencerService.get_influencer_by_id(influencer_id, db)
            return InfluencerResponse.from_orm(influencer)
        except Exception as e:
            logger.error(f"Error in get_influencer controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_influencer_by_user(
        user_id: uuid.UUID,
        db: Session
    ):
        """Get an influencer by user ID"""
        try:
            influencer = await InfluencerService.get_influencer_by_user_id(user_id, db)
            return InfluencerResponse.from_orm(influencer)
        except Exception as e:
            logger.error(f"Error in get_influencer_by_user controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_influencer(
        influencer_id: uuid.UUID,
        influencer_data: InfluencerUpdate,
        db: Session
    ):
        """Update an influencer profile"""
        try:
            influencer = await InfluencerService.update_influencer(
                influencer_id,
                influencer_data.dict(exclude_unset=True),
                db
            )
            return InfluencerResponse.from_orm(influencer)
        except Exception as e:
            logger.error(f"Error in update_influencer controller: {str(e)}")
            raise
    
    @staticmethod
    async def delete_influencer(
        influencer_id: uuid.UUID,
        db: Session
    ):
        """Delete an influencer profile"""
        try:
            await InfluencerService.delete_influencer(influencer_id, db)
            return {"message": "Influencer profile deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_influencer controller: {str(e)}")
            raise
    
    @staticmethod
    async def add_social_account(
        influencer_id: uuid.UUID,
        account_data: SocialAccountCreate,
        db: Session
    ):
        """Add a social account to an influencer"""
        try:
            account_data_dict = account_data.dict()
            account_data_dict['influencer_id'] = influencer_id
            social_account = await InfluencerService.add_social_account(
                influencer_id,
                account_data_dict,
                db
            )
            return SocialAccountResponse.from_orm(social_account)
        except Exception as e:
            logger.error(f"Error in add_social_account controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_social_account(
        account_id: uuid.UUID,
        account_data: SocialAccountUpdate,
        db: Session
    ):
        """Update an influencer's social account"""
        try:
            social_account = await InfluencerService.update_social_account(
                account_id,
                account_data.dict(exclude_unset=True),
                db
            )
            return SocialAccountResponse.from_orm(social_account)
        except Exception as e:
            logger.error(f"Error in update_social_account controller: {str(e)}")
            raise
    
    @staticmethod
    async def delete_social_account(
        account_id: uuid.UUID,
        db: Session
    ):
        """Delete an influencer's social account"""
        try:
            await InfluencerService.delete_social_account(account_id, db)
            return {"message": "Social account deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_social_account controller: {str(e)}")
            raise
    
    @staticmethod
    async def add_influencer_contact(
        influencer_id: uuid.UUID,
        contact_data: InfluencerContactCreate,
        db: Session
    ):
        """Add a contact to an influencer"""
        try:
            contact_data_dict = contact_data.dict()
            contact_data_dict['influencer_id'] = influencer_id
            contact = await InfluencerService.add_contact(
                influencer_id,
                contact_data_dict,
                db
            )
            return InfluencerContactResponse.from_orm(contact)
        except Exception as e:
            logger.error(f"Error in add_influencer_contact controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_influencer_contact(
        contact_id: uuid.UUID,
        contact_data: InfluencerContactUpdate,
        db: Session
    ):
        """Update an influencer contact"""
        try:
            contact = await InfluencerService.update_contact(
                contact_id,
                contact_data.dict(exclude_unset=True),
                db
            )
            return InfluencerContactResponse.from_orm(contact)
        except Exception as e:
            logger.error(f"Error in update_influencer_contact controller: {str(e)}")
            raise
    
    @staticmethod
    async def delete_influencer_contact(
        contact_id: uuid.UUID,
        db: Session
    ):
        """Delete an influencer contact"""
        try:
            await InfluencerService.delete_contact(contact_id, db)
            return {"message": "Influencer contact deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_influencer_contact controller: {str(e)}")
            raise