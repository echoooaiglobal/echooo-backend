# app/Services/InfluencerService.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
import uuid

from app.Models.influencers import Influencer
from app.Models.social_accounts import SocialAccount
from app.Models.influencer_contacts import InfluencerContact
from app.Models.auth_models import User
from app.Utils.Logger import logger

class InfluencerService:
    """Service for managing influencers and related data"""
    
    @staticmethod
    async def create_influencer_profile(user_id: uuid.UUID, db: Session):
        """
        Create a new influencer profile for a user
        
        Args:
            user_id: ID of the user
            db: Database session
            
        Returns:
            Influencer: The created influencer profile
        """
        try:
            # Check if user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check if influencer profile already exists
            existing_profile = db.query(Influencer).filter(Influencer.user_id == user_id).first()
            if existing_profile:
                return existing_profile
            
            # Create influencer profile
            influencer = Influencer(user_id=user_id)
            
            db.add(influencer)
            db.commit()
            db.refresh(influencer)
            
            return influencer
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating influencer profile: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating influencer profile"
            ) from e
    
    @staticmethod
    async def get_influencer_by_id(influencer_id: uuid.UUID, db: Session):
        """
        Get an influencer by ID
        
        Args:
            influencer_id: ID of the influencer
            db: Database session
            
        Returns:
            Influencer: The influencer if found, None otherwise
        """
        influencer = db.query(Influencer).filter(Influencer.id == influencer_id).first()
        
        if not influencer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Influencer not found"
            )
            
        return influencer
    
    @staticmethod
    async def get_influencer_by_user_id(user_id: uuid.UUID, db: Session):
        """
        Get an influencer by user ID
        
        Args:
            user_id: ID of the user
            db: Database session
            
        Returns:
            Influencer: The influencer if found, None otherwise
        """
        influencer = db.query(Influencer).filter(Influencer.user_id == user_id).first()
        
        if not influencer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Influencer profile not found for this user"
            )
            
        return influencer
    
    @staticmethod
    async def update_influencer(influencer_id: uuid.UUID, update_data: Dict[str, Any], db: Session):
        """
        Update an influencer profile
        
        Args:
            influencer_id: ID of the influencer
            update_data: Data to update
            db: Database session
            
        Returns:
            Influencer: The updated influencer
        """
        try:
            influencer = db.query(Influencer).filter(Influencer.id == influencer_id).first()
            
            if not influencer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Influencer not found"
                )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(influencer, key) and value is not None:
                    setattr(influencer, key, value)
            
            db.commit()
            db.refresh(influencer)
            
            return influencer
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating influencer: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating influencer"
            ) from e
    
    @staticmethod
    async def delete_influencer(influencer_id: uuid.UUID, db: Session):
        """
        Delete an influencer profile
        
        Args:
            influencer_id: ID of the influencer
            db: Database session
            
        Returns:
            bool: True if successful
        """
        try:
            influencer = db.query(Influencer).filter(Influencer.id == influencer_id).first()
            
            if not influencer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Influencer not found"
                )
            
            db.delete(influencer)
            db.commit()
            
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting influencer: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting influencer"
            ) from e
    
    @staticmethod
    async def add_social_account(influencer_id: uuid.UUID, account_data: Dict[str, Any], db: Session):
        """
        Add a social account to an influencer
        
        Args:
            influencer_id: ID of the influencer
            account_data: Social account data
            db: Database session
            
        Returns:
            SocialAccount: The created social account
        """
        try:
            # Check if influencer exists
            influencer = db.query(Influencer).filter(Influencer.id == influencer_id).first()
            if not influencer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Influencer not found"
                )
            
            # Check if account already exists for this platform
            platform_id = account_data.get('platform_id')
            existing_account = db.query(SocialAccount).filter(
                SocialAccount.influencer_id == influencer_id,
                SocialAccount.platform_id == platform_id
            ).first()
            
            if existing_account:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Social account for this platform already exists"
                )
            
            # Create social account
            account_data['influencer_id'] = influencer_id
            social_account = SocialAccount(**account_data)
            
            db.add(social_account)
            db.commit()
            db.refresh(social_account)
            
            return social_account
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error adding social account: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error adding social account"
            ) from e
    
    @staticmethod
    async def update_social_account(account_id: uuid.UUID, update_data: Dict[str, Any], db: Session):
        """
        Update a social account
        
        Args:
            account_id: ID of the social account
            update_data: Data to update
            db: Database session
            
        Returns:
            SocialAccount: The updated social account
        """
        try:
            social_account = db.query(SocialAccount).filter(
                SocialAccount.id == account_id
            ).first()
            
            if not social_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Social account not found"
                )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(social_account, key) and value is not None:
                    setattr(social_account, key, value)
            
            db.commit()
            db.refresh(social_account)
            
            return social_account
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating social account: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating social account"
            ) from e
    
    @staticmethod
    async def delete_social_account(account_id: uuid.UUID, db: Session):
        """
        Delete a social account
        
        Args:
            account_id: ID of the social account
            db: Database session
            
        Returns:
            bool: True if successful
        """
        try:
            social_account = db.query(SocialAccount).filter(
                SocialAccount.id == account_id
            ).first()
            
            if not social_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Social account not found"
                )
            
            db.delete(social_account)
            db.commit()
            
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting social account: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting social account"
            ) from e
    
    @staticmethod
    async def add_contact(influencer_id: uuid.UUID, contact_data: Dict[str, Any], db: Session):
        """
        Add a contact to an influencer
        
        Args:
            influencer_id: ID of the influencer
            contact_data: Contact data
            db: Database session
            
        Returns:
            InfluencerContact: The created contact
        """
        try:
            # Check if influencer exists
            influencer = db.query(Influencer).filter(Influencer.id == influencer_id).first()
            if not influencer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Influencer not found"
                )
            
            # Create contact
            contact_data['influencer_id'] = influencer_id
            contact = InfluencerContact(**contact_data)
            
            db.add(contact)
            db.commit()
            db.refresh(contact)
            
            return contact
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error adding contact: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error adding contact"
            ) from e
    
    @staticmethod
    async def update_contact(contact_id: uuid.UUID, update_data: Dict[str, Any], db: Session):
        """
        Update a contact
        
        Args:
            contact_id: ID of the contact
            update_data: Data to update
            db: Database session
            
        Returns:
            InfluencerContact: The updated contact
        """
        try:
            contact = db.query(InfluencerContact).filter(
                InfluencerContact.id == contact_id
            ).first()
            
            if not contact:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Contact not found"
                )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(contact, key) and value is not None:
                    setattr(contact, key, value)
            
            db.commit()
            db.refresh(contact)
            
            return contact
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating contact: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating contact"
            ) from e
    
    @staticmethod
    async def delete_contact(contact_id: uuid.UUID, db: Session):
        """
        Delete a contact
        
        Args:
            contact_id: ID of the contact
            db: Database session
            
        Returns:
            bool: True if successful
        """
        try:
            contact = db.query(InfluencerContact).filter(
                InfluencerContact.id == contact_id
            ).first()
            
            if not contact:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Contact not found"
                )
            
            db.delete(contact)
            db.commit()
            
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting contact: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting contact"
            ) from e