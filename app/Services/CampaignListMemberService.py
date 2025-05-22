# app/Services/CampaignListMemberService.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status
import uuid
from datetime import datetime
from app.Models.campaign_list_members import CampaignListMember
from app.Models.campaign_models import CampaignList, Status
from app.Models.influencer_models import Influencer, SocialAccount
from app.Models.support_models import Platform
from app.Utils.Logger import logger

class CampaignListMemberService:
    """Service for managing campaign list members"""

    @staticmethod
    async def get_all_members(db: Session):
        """
        Get all list members across all lists
        """
        return db.query(CampaignListMember).options(
            joinedload(CampaignListMember.social_account),
            joinedload(CampaignListMember.status),
            joinedload(CampaignListMember.platform)
        ).all()
    
    @staticmethod
    async def get_list_members_paginated(
        list_id: uuid.UUID, 
        page: int = 1, 
        page_size: int = 10,
        db: Session = None
    ) -> Tuple[List, int]:
        """
        Get paginated members of a campaign list
        
        Args:
            list_id: ID of the campaign list
            page: Page number (1-based)
            page_size: Number of items per page
            db: Database session
            
        Returns:
            Tuple[List[CampaignListMember], int]: List of members and total count
        """
        # Verify list exists
        campaign_list = db.query(CampaignList).filter(CampaignList.id == list_id).first()
        if not campaign_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign list not found"
            )
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count
        total_count = db.query(CampaignListMember).filter(
            CampaignListMember.list_id == list_id
        ).count()
        
        # Get paginated members with eager loading relationships
        members = db.query(CampaignListMember).options(
            joinedload(CampaignListMember.social_account),
            joinedload(CampaignListMember.status),
            joinedload(CampaignListMember.platform)
        ).filter(
            CampaignListMember.list_id == list_id
        ).offset(offset).limit(page_size).all()
        
        return members, total_count
    
    @staticmethod
    async def get_list_members(list_id: uuid.UUID, db: Session):
        """
        Get all members of a campaign list (non-paginated)
        """
        # Use the paginated method with a large page size to get all results
        members, total_count = await CampaignListMemberService.get_list_members_paginated(
            list_id, page=1, page_size=1000, db=db
        )
        return members
    
    @staticmethod
    async def get_all_members_paginated(
        page: int = 1, 
        page_size: int = 10,
        db: Session = None
    ) -> Tuple[List, int]:
        """
        Get paginated members across all lists
        """
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count
        total_count = db.query(CampaignListMember).count()
        
        # Get paginated members
        members = db.query(CampaignListMember).options(
            joinedload(CampaignListMember.social_account),
            joinedload(CampaignListMember.status),
            joinedload(CampaignListMember.platform)
        ).offset(offset).limit(page_size).all()
        
        return members, total_count
    
    @staticmethod
    async def get_member_by_id(member_id: uuid.UUID, db: Session):
        """
        Get a list member by ID
        """
        # Get member with eager loading relationships
        member = db.query(CampaignListMember).options(
            joinedload(CampaignListMember.social_account),
            joinedload(CampaignListMember.status),
            joinedload(CampaignListMember.platform)
        ).filter(CampaignListMember.id == member_id).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="List member not found"
            )
            
        return member

    @staticmethod
    async def add_member_with_social_data(
        list_id: uuid.UUID, 
        platform_id: uuid.UUID, 
        social_data: Dict[str, Any], 
        db: Session
    ):
        """
        Add a member to a campaign list with social account data.
        Finds or creates a social account directly without creating a new influencer.
        """
        try:
            # Verify list exists
            campaign_list = db.query(CampaignList).filter(CampaignList.id == list_id).first()
            if not campaign_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign list not found"
                )
            
            # Verify platform exists
            platform = db.query(Platform).filter(Platform.id == platform_id).first()
            if not platform:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Platform not found"
                )
            
            # Validate required fields in social_data
            if not social_data.get('id'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Social data must include 'id' field"
                )
            
            if not social_data.get('username'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Social data must include 'username' field"
                )
            
            # Try to find existing social account by platform_account_id
            platform_account_id = str(social_data.get('id'))
            existing_account = db.query(SocialAccount).filter(
                SocialAccount.platform_id == platform_id,
                SocialAccount.platform_account_id == platform_account_id
            ).first()
            
            social_account_id = None
            
            # Process followers count value if provided
            followers_count = None
            followers_count_raw = social_data.get('followers', '')
            if followers_count_raw:
                try:
                    if isinstance(followers_count_raw, str):
                        if 'K' in followers_count_raw:
                            followers_count = float(followers_count_raw.replace('K', '')) * 1000
                        elif 'M' in followers_count_raw:
                            followers_count = float(followers_count_raw.replace('M', '')) * 1000000
                        else:
                            followers_count = float(followers_count_raw)
                        followers_count = int(followers_count)
                    else:
                        followers_count = followers_count_raw
                except (ValueError, TypeError):
                    logger.warning(f"Unable to parse followers count: {followers_count_raw}")
            
            # If social account exists, update it
            if existing_account:
                social_account_id = existing_account.id
                account_updated = False
                
                # Update account handle
                if existing_account.account_handle != social_data.get('username', '') and social_data.get('username'):
                    existing_account.account_handle = social_data.get('username')
                    account_updated = True
                
                # Update full name
                if existing_account.full_name != social_data.get('name', '') and social_data.get('name'):
                    existing_account.full_name = social_data.get('name')
                    account_updated = True
                
                # Update profile image
                if existing_account.profile_pic_url != social_data.get('profileImage', '') and social_data.get('profileImage'):
                    existing_account.profile_pic_url = social_data.get('profileImage')
                    account_updated = True
                
                # Update verified status
                if existing_account.is_verified != social_data.get('isVerified', False) and social_data.get('isVerified') is not None:
                    existing_account.is_verified = social_data.get('isVerified')
                    account_updated = True
                
                # Update followers count
                if followers_count is not None and existing_account.followers_count != followers_count:
                    existing_account.followers_count = followers_count
                    account_updated = True
                
                # If any data was updated, commit the changes
                if account_updated:
                    logger.info(f"Updating social account data for {existing_account.account_handle} (ID: {existing_account.id})")
                    db.commit()
                    db.refresh(existing_account)
            else:
                # If no social account exists, check if there's any existing influencer to associate with
                # This is optional - you could look up by username or other criteria
                # For now, we'll just create the social account without an influencer association
                
                # Build social account data
                social_account_data = {
                    # Leave influencer_id as NULL for now
                    "influencer_id": None,  # This field needs to be nullable in the database
                    "platform_id": platform_id,
                    "platform_account_id": platform_account_id,
                    "account_handle": social_data.get('username', ''),
                    "full_name": social_data.get('name', ''),
                    "profile_pic_url": social_data.get('profileImage', ''),
                    "is_verified": social_data.get('isVerified', False)
                }
                
                # Add followers count if available
                if followers_count is not None:
                    social_account_data["followers_count"] = followers_count
                
                # Create social account
                new_social_account = SocialAccount(**social_account_data)
                db.add(new_social_account)
                db.commit()
                db.refresh(new_social_account)
                
                social_account_id = new_social_account.id
            
            # Check if member already exists in this list
            existing_member = db.query(CampaignListMember).filter(
                CampaignListMember.list_id == list_id,
                CampaignListMember.social_account_id == social_account_id
            ).first()
            
            if existing_member:
                logger.info(f"Social account is already a member of this list: list_id={list_id}, social_account_id={social_account_id}")
                return existing_member
            
            # Get default status
            default_status = db.query(Status).filter(
                Status.model == "list_member",
                Status.name == "discovered"
            ).first()
            
            if not default_status:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Default status 'discovered' not found"
                )
            
            # Create list member
            member_data = {
                "list_id": list_id,
                "social_account_id": social_account_id,
                "platform_id": platform_id,
                "status_id": default_status.id,
                "contact_attempts": 0
            }
            
            list_member = CampaignListMember(**member_data)
            db.add(list_member)
            db.commit()
            db.refresh(list_member)
            
            logger.info(f"Created list member: id={list_member.id}, social_account_id={social_account_id}, list_id={list_id}")
            
            # Load relationships for proper response
            list_member = db.query(CampaignListMember).options(
                joinedload(CampaignListMember.social_account),
                joinedload(CampaignListMember.status),
                joinedload(CampaignListMember.platform)
            ).filter(CampaignListMember.id == list_member.id).first()
            
            return list_member
                
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error adding list member with social data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error adding list member: {str(e)}"
            ) from e
    
    @staticmethod
    async def add_member(member_data: Dict[str, Any], db: Session):
        """
        Add a member to a campaign list
        """
        try:
            # Check if social_data is provided
            social_data = member_data.pop('social_data', None)
            
            # If social_data is provided, use the enhanced method
            if social_data:
                list_id = member_data.get('list_id')
                platform_id = member_data.get('platform_id')
                
                if not list_id or not platform_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="List ID and Platform ID are required"
                    )
                
                return await CampaignListMemberService.add_member_with_social_data(
                    uuid.UUID(list_id) if isinstance(list_id, str) else list_id,
                    uuid.UUID(platform_id) if isinstance(platform_id, str) else platform_id,
                    social_data,
                    db
                )
            
            # Original flow for when only member_data is provided
            
            # Verify list exists
            list_id = member_data.get('list_id')
            if not list_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="List ID is required"
                )
            
            campaign_list = db.query(CampaignList).filter(CampaignList.id == list_id).first()
            if not campaign_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign list not found"
                )
            
            # Verify social_account exists
            social_account_id = member_data.get('social_account_id')
            if not social_account_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Social Account ID is required"
                )
            
            social_account = db.query(SocialAccount).filter(SocialAccount.id == social_account_id).first()
            if not social_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Social Account not found"
                )
            
            # Verify platform exists
            platform_id = member_data.get('platform_id')
            if not platform_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Platform ID is required"
                )
            
            platform = db.query(Platform).filter(Platform.id == platform_id).first()
            if not platform:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Platform not found"
                )
            
            # Check if member with same social account and platform already exists in the list
            existing_member = db.query(CampaignListMember).filter(
                CampaignListMember.list_id == list_id,
                CampaignListMember.social_account_id == social_account_id,
                CampaignListMember.platform_id == platform_id
            ).first()
            
            if existing_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Social Account is already a member of this list for this platform"
                )
            
            # Set default status if not provided (discovered)
            if not member_data.get('status_id'):
                default_status = db.query(Status).filter(
                    Status.model == "list_member",
                    Status.name == "discovered"
                ).first()
                
                if default_status:
                    member_data['status_id'] = default_status.id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Default status 'discovered' not found"
                    )
            
            # Set default values for other fields if needed
            if 'contact_attempts' not in member_data:
                member_data['contact_attempts'] = 0
            
            # Create list member
            list_member = CampaignListMember(**member_data)
            
            db.add(list_member)
            db.commit()
            db.refresh(list_member)
            
            return list_member
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error adding list member: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error adding list member: {str(e)}"
            ) from e
    
    @staticmethod
    async def update_member(member_id: uuid.UUID, update_data: Dict[str, Any], db: Session):
        """
        Update a list member
        """
        try:
            member = db.query(CampaignListMember).filter(CampaignListMember.id == member_id).first()
            
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="List member not found"
                )
            
            # Validate status_id if provided
            if 'status_id' in update_data and update_data['status_id']:
                status_obj = db.query(Status).filter(
                    Status.id == update_data['status_id'],
                    Status.model == "list_member"
                ).first()
                
                if not status_obj:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid list member status"
                    )
                
                # If status is changing to "responded", set responded_at timestamp
                if status_obj.name == "responded" and (member.status_id != update_data['status_id']):
                    update_data['responded_at'] = datetime.utcnow()
                
                # If status is changing to "onboarded", set onboarded_at timestamp
                if status_obj.name == "onboarded" and (member.status_id != update_data['status_id']):
                    update_data['onboarded_at'] = datetime.utcnow()
            
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
    
    @staticmethod
    async def record_contact_attempt(member_id: uuid.UUID, db: Session):
        """
        Record a contact attempt for a list member
        """
        try:
            member = db.query(CampaignListMember).filter(CampaignListMember.id == member_id).first()
            
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="List member not found"
                )
            
            # Increment contact attempts
            member.contact_attempts += 1
            
            # Update last contacted timestamp
            member.last_contacted_at = datetime.utcnow()
            
            # If status is still "discovered", update to "contacted"
            if member.status:
                status = db.query(Status).filter(Status.id == member.status_id).first()
                if status and status.name == "discovered":
                    contacted_status = db.query(Status).filter(
                        Status.model == "list_member",
                        Status.name == "contacted"
                    ).first()
                    
                    if contacted_status:
                        member.status_id = contacted_status.id
            
            db.commit()
            db.refresh(member)
            
            return member
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error recording contact attempt: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error recording contact attempt"
            ) from e