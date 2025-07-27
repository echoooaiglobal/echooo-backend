# app/Services/CampaignListService.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_, or_
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
import uuid

from app.Models.campaign_lists import CampaignList
from app.Models.campaign_influencers import CampaignInfluencer
from app.Models.campaigns import Campaign
from app.Utils.Logger import logger

class CampaignListService:
    """Service for managing campaign lists"""

    @staticmethod
    async def get_all_lists(db: Session) -> List[CampaignList]:
        """
        Get all campaign lists with their related data
        
        Args:
            db: Database session
            
        Returns:
            List[CampaignList]: List of all campaign lists
        """
        try:
            return db.query(CampaignList).options(
                joinedload(CampaignList.campaign),
                joinedload(CampaignList.creator),
                joinedload(CampaignList.message_template)
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching all campaign lists: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching campaign lists"
            ) from e
    
    @staticmethod
    async def get_campaign_lists(campaign_id: uuid.UUID, db: Session) -> List[CampaignList]:
        """
        Get all campaign lists for a specific campaign
        
        Args:
            campaign_id: ID of the campaign
            db: Database session
            
        Returns:
            List[CampaignList]: List of campaign's campaign lists
        """
        try:
            return db.query(CampaignList).options(
                joinedload(CampaignList.creator),
                joinedload(CampaignList.message_template)
            ).filter(CampaignList.campaign_id == campaign_id).all()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching campaign lists for campaign {campaign_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching campaign lists"
            ) from e
    
    @staticmethod
    async def get_list_by_id(list_id: uuid.UUID, db: Session) -> CampaignList:
        """
        Get a campaign list by ID with related data
        
        Args:
            list_id: ID of the campaign list
            db: Database session
            
        Returns:
            CampaignList: The campaign list
        """
        try:
            list_obj = db.query(CampaignList).options(
                joinedload(CampaignList.campaign),
                joinedload(CampaignList.creator),
                joinedload(CampaignList.message_template),
                joinedload(CampaignList.campaign_influencers)
            ).filter(CampaignList.id == list_id).first()
            
            if not list_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign list not found"
                )
            
            return list_obj
        except SQLAlchemyError as e:
            logger.error(f"Error fetching campaign list {list_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching campaign list"
            ) from e
    
    @staticmethod
    async def create_list(
        list_data: Dict[str, Any],
        created_by: uuid.UUID,
        db: Session
    ) -> CampaignList:
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
            # Validate campaign exists
            campaign_id = list_data.get('campaign_id')
            if campaign_id:
                campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
                if not campaign:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Campaign not found"
                    )
            
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
    ) -> CampaignList:
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
    async def delete_list(list_id: uuid.UUID, db: Session) -> bool:
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
    async def get_list_stats(list_id: uuid.UUID, db: Session) -> Dict[str, Any]:
        """
        Get statistics for a campaign list
        
        Args:
            list_id: ID of the campaign list
            db: Database session
            
        Returns:
            Dict: Statistics about the campaign list
        """
        try:
            # Verify list exists
            list_obj = db.query(CampaignList).filter(CampaignList.id == list_id).first()
            if not list_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign list not found"
                )

            # Get total influencers count
            total_influencers = db.query(CampaignInfluencer).filter(
                CampaignInfluencer.campaign_list_id == list_id
            ).count()

            # Get influencers by status
            status_counts = db.query(
                CampaignInfluencer.status_id,
                func.count(CampaignInfluencer.id).label('count')
            ).filter(
                CampaignInfluencer.campaign_list_id == list_id
            ).group_by(CampaignInfluencer.status_id).all()

            # Get onboarded count
            onboarded_count = db.query(CampaignInfluencer).filter(
                and_(
                    CampaignInfluencer.campaign_list_id == list_id,
                    CampaignInfluencer.is_ready_for_onboarding == True
                )
            ).count()

            # Get average contact attempts
            avg_contact_attempts = db.query(
                func.avg(CampaignInfluencer.total_contact_attempts)
            ).filter(
                CampaignInfluencer.campaign_list_id == list_id
            ).scalar() or 0

            # Get collaboration price stats
            price_stats = db.query(
                func.min(CampaignInfluencer.collaboration_price).label('min_price'),
                func.max(CampaignInfluencer.collaboration_price).label('max_price'),
                func.avg(CampaignInfluencer.collaboration_price).label('avg_price')
            ).filter(
                and_(
                    CampaignInfluencer.campaign_list_id == list_id,
                    CampaignInfluencer.collaboration_price.isnot(None)
                )
            ).first()

            return {
                "list_id": str(list_id),
                "total_influencers": total_influencers,
                "onboarded_count": onboarded_count,
                "avg_contact_attempts": float(avg_contact_attempts),
                "status_breakdown": [
                    {"status_id": str(status.status_id), "count": status.count}
                    for status in status_counts
                ],
                "price_stats": {
                    "min_price": float(price_stats.min_price) if price_stats.min_price else None,
                    "max_price": float(price_stats.max_price) if price_stats.max_price else None,
                    "avg_price": float(price_stats.avg_price) if price_stats.avg_price else None
                }
            }
        except SQLAlchemyError as e:
            logger.error(f"Error getting campaign list stats: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching campaign list statistics"
            ) from e

    @staticmethod
    async def duplicate_list(
        list_id: uuid.UUID,
        new_name: str,
        created_by: uuid.UUID,
        db: Session
    ) -> CampaignList:
        """
        Duplicate a campaign list with a new name
        
        Args:
            list_id: ID of the campaign list to duplicate
            new_name: Name for the new list
            created_by: ID of the user creating the list
            db: Database session
            
        Returns:
            CampaignList: The duplicated campaign list
        """
        try:
            # Get the original list
            original_list = db.query(CampaignList).filter(
                CampaignList.id == list_id
            ).first()
            
            if not original_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign list not found"
                )

            # Create new list with copied data
            new_list = CampaignList(
                campaign_id=original_list.campaign_id,
                name=new_name,
                description=f"Copy of {original_list.name}",
                message_template_id=original_list.message_template_id,
                created_by=created_by,
                notes=original_list.notes
            )
            
            db.add(new_list)
            db.commit()
            db.refresh(new_list)
            
            # Copy influencers from original list
            original_influencers = db.query(CampaignInfluencer).filter(
                CampaignInfluencer.campaign_list_id == list_id
            ).all()
            
            for influencer in original_influencers:
                new_influencer = CampaignInfluencer(
                    campaign_list_id=new_list.id,
                    social_account_id=influencer.social_account_id,
                    status_id=influencer.status_id,
                    total_contact_attempts=0,  # Reset contact attempts
                    collaboration_price=influencer.collaboration_price,
                    is_ready_for_onboarding=False,  # Reset onboarding status
                    notes=influencer.notes
                )
                db.add(new_influencer)
            
            db.commit()
            
            return new_list
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error duplicating campaign list: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error duplicating campaign list"
            ) from e

    @staticmethod
    async def search_lists(
        search_term: str,
        campaign_id: Optional[uuid.UUID] = None,
        db: Session = None
    ) -> List[CampaignList]:
        """
        Search campaign lists by name or description
        
        Args:
            search_term: Term to search for
            campaign_id: Optional campaign ID to filter by
            db: Database session
            
        Returns:
            List[CampaignList]: Matching campaign lists
        """
        try:
            query = db.query(CampaignList).filter(
                or_(
                    CampaignList.name.ilike(f"%{search_term}%"),
                    CampaignList.description.ilike(f"%{search_term}%")
                )
            )
            
            if campaign_id:
                query = query.filter(CampaignList.campaign_id == campaign_id)
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching campaign lists: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error searching campaign lists"
            ) from e