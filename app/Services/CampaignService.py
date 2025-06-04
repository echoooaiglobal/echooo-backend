# app/Services/CampaignService.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from app.Models.campaign_models import Campaign, CampaignList, Status, ListAssignment
from app.Models.support_models import Category
from app.Utils.Logger import logger
import uuid
import re

class CampaignService:
    """Service for managing campaigns"""

    @staticmethod
    async def get_all_campaigns(db: Session):
        """
        Get all campaigns with all related data including list assignments
        """
        return db.query(Campaign).options(
            joinedload(Campaign.category),
            joinedload(Campaign.status),
            joinedload(Campaign.campaign_lists),
            joinedload(Campaign.message_templates),
            # Add nested loading for list assignments through campaign lists
            joinedload(Campaign.campaign_lists).joinedload(CampaignList.assignments).joinedload(ListAssignment.status)
        ).all()

    @staticmethod
    async def get_company_campaigns(company_id: uuid.UUID, db: Session):
        """
        Get all campaigns for a specific company with all related data
        """
        return db.query(Campaign).options(
            joinedload(Campaign.category),
            joinedload(Campaign.status),
            joinedload(Campaign.campaign_lists),
            joinedload(Campaign.message_templates),
            # Add nested loading for list assignments
            joinedload(Campaign.campaign_lists).joinedload(CampaignList.assignments).joinedload(ListAssignment.status)
        ).filter(Campaign.company_id == company_id).all()

    @staticmethod
    async def get_campaign_by_id(campaign_id: uuid.UUID, db: Session):
        """
        Get a campaign by ID with all related data
        """
        campaign = db.query(Campaign).options(
            joinedload(Campaign.category),
            joinedload(Campaign.status),
            joinedload(Campaign.campaign_lists),
            joinedload(Campaign.message_templates),
            # Add nested loading for list assignments
            joinedload(Campaign.campaign_lists).joinedload(CampaignList.assignments).joinedload(ListAssignment.status)
        ).filter(Campaign.id == campaign_id).first()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
            
        return campaign
    
    @staticmethod
    async def create_campaign(campaign_data: Dict[str, Any], created_by: uuid.UUID, db: Session):
        """
        Create a new campaign along with a default influencer list
        
        Args:
            campaign_data: Campaign data
            created_by: ID of the user creating the campaign
            db: Database session
            
        Returns:
            Campaign: The created campaign
        """
        try:
            campaign_data['created_by'] = created_by
            
            # Validate category exists if category_id is provided
            if 'category_id' in campaign_data and campaign_data['category_id']:
                try:
                    # If it's a string, convert to UUID
                    if isinstance(campaign_data['category_id'], str):
                        category_id = uuid.UUID(campaign_data['category_id'])
                    else:
                        category_id = campaign_data['category_id']
                    
                    # Check if category exists
                    category = db.query(Category).filter(Category.id == category_id).first()
                    if not category:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Category not found"
                        )
                    
                    # Set the UUID object as category_id
                    campaign_data['category_id'] = category_id
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid category ID format"
                    )
            
            # Validate status exists if status_id is provided, or set default status
            if 'status_id' in campaign_data and campaign_data['status_id']:
                try:
                    # If it's a string, convert to UUID
                    if isinstance(campaign_data['status_id'], str):
                        status_id = uuid.UUID(campaign_data['status_id'])
                    else:
                        status_id = campaign_data['status_id']
                    
                    # Check if status exists
                    status_obj = db.query(Status).filter(Status.id == status_id).first()
                    if not status_obj:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Status not found"
                        )
                    
                    # Set the UUID object as status_id
                    campaign_data['status_id'] = status_id
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid status ID format"
                    )
            else:
                # Set default status if not provided (draft)
                default_status = db.query(Status).filter(
                    Status.model == "campaign",
                    Status.name == "draft"
                ).first()
                
                if default_status:
                    campaign_data['status_id'] = default_status.id
            
            # Create campaign
            campaign = Campaign(**campaign_data)
            
            db.add(campaign)
            db.commit()
            db.refresh(campaign)
            
            # Now create a default influencer list for this campaign
            try:
                # Generate a suitable name for the list
                campaign_name = campaign_data.get('name', 'Campaign')
                list_name = f"{campaign_name} - Target Influencers"
                
                # Create influencer list data
                from app.Models.campaign_models import CampaignList
                
                list_data = {
                    "campaign_id": campaign.id,
                    "name": list_name,
                    "description": f"Default influencer list for the {campaign_name} campaign",
                    "created_by": created_by
                }
                
                # Create the list
                influencer_list = CampaignList(**list_data)
                db.add(influencer_list)
                db.commit()
                
                # Refresh the campaign to get the relationship updated
                db.refresh(campaign)
                
            except Exception as list_error:
                # If list creation fails, log the error but don't fail the campaign creation
                logger.error(f"Error creating default influencer list: {str(list_error)}")
                # We don't raise an exception here to allow the campaign to be created even if list creation fails
            
            return campaign
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating campaign: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating campaign"
            ) from e
    
    @staticmethod
    async def update_campaign(
        campaign_id: uuid.UUID,
        update_data: Dict[str, Any],
        db: Session
    ):
        """
        Update a campaign and optionally update its default influencer list
        
        Args:
            campaign_id: ID of the campaign
            update_data: Data to update
            db: Database session
            
        Returns:
            Campaign: The updated campaign
        """
        try:
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
            
            if not campaign:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign not found"
                )
            
            # Store original name for comparison
            original_name = campaign.name
            name_changed = 'name' in update_data and update_data['name'] != original_name
            
            # Handle category_id conversion and validation
            if 'category_id' in update_data and update_data['category_id'] is not None:
                try:
                    # If it's a string, convert to UUID
                    if isinstance(update_data['category_id'], str):
                        category_id = uuid.UUID(update_data['category_id'])
                    else:
                        category_id = update_data['category_id']
                    
                    # Check if category exists
                    category = db.query(Category).filter(Category.id == category_id).first()
                    if not category:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Category not found"
                        )
                    
                    # Set the UUID object as category_id
                    update_data['category_id'] = category_id
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid category ID format"
                    )
            
            # Handle status_id conversion and validation
            if 'status_id' in update_data and update_data['status_id'] is not None:
                try:
                    # If it's a string, convert to UUID
                    if isinstance(update_data['status_id'], str):
                        status_id = uuid.UUID(update_data['status_id'])
                    else:
                        status_id = update_data['status_id']
                    
                    # Check if status exists and is a campaign status
                    status_obj = db.query(Status).filter(
                        Status.id == status_id,
                        Status.model == "campaign"
                    ).first()
                    
                    if not status_obj:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid campaign status"
                        )
                    
                    # Set the UUID object as status_id
                    update_data['status_id'] = status_id
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid status ID format"
                    )
            
            # Handle other fields validations (budget, currency_code, etc.)
            if 'budget' in update_data and update_data['budget'] is not None:
                # Ensure budget is a numeric value
                try:
                    update_data['budget'] = float(update_data['budget'])
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Budget must be a numeric value"
                    )
            
            if 'currency_code' in update_data and update_data['currency_code'] is not None:
                # Ensure currency code is valid format (3 letters)
                if not re.match(r'^[A-Z]{3}$', update_data['currency_code']):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Currency code must be a 3-letter ISO code (e.g., USD, EUR)"
                    )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(campaign, key) and value is not None:
                    setattr(campaign, key, value)
            
            # Save the campaign changes
            db.commit()
            db.refresh(campaign)
            
            # If the campaign name changed, update the default influencer list
            if name_changed:
                try:
                    # Find the default influencer list for this campaign
                    # Assuming the first list is the default one, or the one with a name matching the pattern
                    campaign_lists = db.query(CampaignList).filter(
                        CampaignList.campaign_id == campaign_id
                    ).all()
                    
                    if campaign_lists:
                        # Try to find the default list by checking name patterns
                        default_list = None
                        for list_obj in campaign_lists:
                            # Check if this looks like a default list (has the original name in it)
                            if original_name in list_obj.name and " - Target Influencers" in list_obj.name:
                                default_list = list_obj
                                break
                        
                        # If no list with pattern found, use the first one
                        if default_list is None and campaign_lists:
                            default_list = campaign_lists[0]
                        
                        # Update the list name if found
                        if default_list:
                            new_list_name = f"{campaign.name} - Target Influencers"
                            default_list.name = new_list_name
                            default_list.description = f"Default influencer list for the {campaign.name} campaign"
                            db.commit()
                except Exception as list_error:
                    # Log the error but don't fail the campaign update
                    logger.error(f"Error updating influencer list name: {str(list_error)}")
                    # We don't raise an exception here to allow the campaign update to succeed
            
            return campaign
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating campaign: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating campaign"
            ) from e
    
    @staticmethod
    async def delete_campaign(campaign_id: uuid.UUID, db: Session):
        """
        Delete a campaign
        
        Args:
            campaign_id: ID of the campaign
            db: Database session
            
        Returns:
            bool: True if successful
        """
        try:
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
            
            if not campaign:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign not found"
                )
            
            db.delete(campaign)
            db.commit()
            
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting campaign: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting campaign"
            ) from e