# app/Services/CampaignListService.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
import uuid

from app.Models.campaign_models import CampaignList
from app.Models.campaign_list_members import CampaignListMember
from app.Utils.Logger import logger

class CampaignListService:
    """Service for managing campaign lists and members"""

    @staticmethod
    async def get_all_lists(db: Session):
        """
        Get all campaign lists
        
        Args:
            db: Database session
            
        Returns:
            List[CampaignList]: List of all campaign lists
        """
        return db.query(CampaignList).all()
    
    @staticmethod
    async def get_campaign_lists(campaign_id: uuid.UUID, db: Session):
        """
        Get all campaign lists for a specific campaign
        
        Args:
            campaign_id: ID of the campaign
            db: Database session
            
        Returns:
            List[CampaignList]: List of campaign's campaign lists
        """
        return db.query(CampaignList).filter(CampaignList.campaign_id == campaign_id).all()
    
    @staticmethod
    async def get_list_by_id(list_id: uuid.UUID, db: Session):
        """
        Get a campaign list by ID
        
        Args:
            list_id: ID of the campaign list
            db: Database session
            
        Returns:
            CampaignList: The campaign list if found
        """
        list_obj = db.query(CampaignList).filter(CampaignList.id == list_id).first()
        
        if not list_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign list not found"
            )
            
        return list_obj
    
    @staticmethod
    async def create_list(
        list_data: Dict[str, Any],
        created_by: uuid.UUID,
        db: Session
    ):
        """
        Create a new campaign list
        
        Args:
            list_data: List data
            created_by: ID of the user creating the list
            db: Database session
            
        Returns:
            CampaignList: The created campaign list
        """
        try:
            list_data['created_by'] = created_by
            
            # Create campaign list
            campaign_list = CampaignList(**list_data)
            
            db.add(campaign_list)
            db.commit()
            db.refresh(campaign_list)
            
            return campaign_list
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating campaign list: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating campaign list"
            ) from e
    
    @staticmethod
    async def update_list(
        list_id: uuid.UUID,
        update_data: Dict[str, Any],
        db: Session
    ):
        """
        Update a campaign list
        
        Args:
            list_id: ID of the campaign list
            update_data: Data to update
            db: Database session
            
        Returns:
            CampaignList: The updated campaign list
        """
        try:
            list_obj = db.query(CampaignList).filter(CampaignList.id == list_id).first()
            
            if not list_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign list not found"
                )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(list_obj, key) and value is not None:
                    setattr(list_obj, key, value)
            
            db.commit()
            db.refresh(list_obj)
            
            return list_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating campaign list: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating campaign list"
            ) from e
    
    @staticmethod
    async def delete_list(list_id: uuid.UUID, db: Session):
        """
        Delete a campaign list
        
        Args:
            list_id: ID of the campaign list
            db: Database session
            
        Returns:
            bool: True if successful
        """
        try:
            list_obj = db.query(CampaignList).filter(CampaignList.id == list_id).first()
            
            if not list_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign list not found"
                )
            
            db.delete(list_obj)
            db.commit()
            
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting campaign list: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting campaign list"
            ) from e
    
    @staticmethod
    async def get_list_members(list_id: uuid.UUID, db: Session):
        """
        Get all members of an campaign list
        
        Args:
            list_id: ID of the campaign list
            db: Database session
            
        Returns:
            List[CampaignListMember]: List of members
        """
        return db.query(CampaignListMember).filter(CampaignListMember.list_id == list_id).all()
    


    @staticmethod
    async def add_member(
        member_data: Dict[str, Any],
        db: Session
    ):
        """
        Add a member to a campaign list
        
        Args:
            member_data: Member data
            db: Database session
            
        Returns:
            CampaignListMember: The created list member
        """
        try:
            # Check if member with same social account and list already exists
            existing_member = db.query(CampaignListMember).filter(
                CampaignListMember.list_id == member_data['list_id'],
                CampaignListMember.social_account_id == member_data['social_account_id']
            ).first()
            
            if existing_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Social account is already a member of this list"
                )
            
            # Create list member
            list_member = CampaignListMember(**member_data)
            
            db.add(list_member)
            db.commit()
            db.refresh(list_member)
            
            return list_member
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error adding list member: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error adding list member"
            ) from e
    
    @staticmethod
    async def update_member(
        member_id: uuid.UUID,
        update_data: Dict[str, Any],
        db: Session
    ):
        """
        Update a list member
        
        Args:
            member_id: ID of the list member
            update_data: Data to update
            db: Database session
            
        Returns:
            CampaignListMember: The updated list member
        """
        try:
            member = db.query(CampaignListMember).filter(CampaignListMember.id == member_id).first()
            
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="List member not found"
                )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(member, key) and value is not None:
                    setattr(member, key, value)
            
            db.commit()
            db.refresh(member)
            
            return member
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating list member: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating list member"
            ) from e
    
    @staticmethod
    async def remove_member(member_id: uuid.UUID, db: Session):
        """
        Remove a member from a campaign list
        
        Args:
            member_id: ID of the list member
            db: Database session
            
        Returns:
            bool: True if successful
        """
        try:
            member = db.query(CampaignListMember).filter(CampaignListMember.id == member_id).first()
            
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="List member not found"
                )
            
            db.delete(member)
            db.commit()
            
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error removing list member: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error removing list member"
            ) from e