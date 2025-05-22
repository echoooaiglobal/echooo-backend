# app/Http/Controllers/CampaignListMemberController.py  
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid
import math
from app.Models.auth_models import User
from app.Schemas.campaign_list_member import (
    CampaignListMemberCreate, CampaignListMemberUpdate, CampaignListMemberResponse,
    SocialAccountBrief, StatusBrief, PlatformBrief,
    CampaignListMemberBulkCreate, CampaignListMembersPaginatedResponse, PaginationInfo
)

from app.Services.CampaignListMemberService import CampaignListMemberService
from app.Utils.Logger import logger

class CampaignListMemberController:
    """Controller for campaign list member-related endpoints"""
    
    @staticmethod
    async def get_list_members_paginated(
        list_id: uuid.UUID, 
        page: int = 1, 
        page_size: int = 10,
        db: Session = None
    ):
        """Get paginated members of a campaign list"""
        try:
            members, total_count = await CampaignListMemberService.get_list_members_paginated(
                list_id, page, page_size, db
            )
            
            # Format the response
            formatted_members = [
                CampaignListMemberController._format_member_response(member)
                for member in members
            ]
            
            # Calculate pagination info
            total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
            
            pagination_info = PaginationInfo(
                page=page,
                page_size=page_size,
                total_items=total_count,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1
            )
            
            return CampaignListMembersPaginatedResponse(
                members=formatted_members,
                pagination=pagination_info
            )
            
        except Exception as e:
            logger.error(f"Error in get_list_members_paginated controller: {str(e)}")
            raise

    @staticmethod
    async def get_all_members_paginated(
        page: int = 1, 
        page_size: int = 10,
        db: Session = None
    ):
        """Get paginated members across all lists"""
        try:
            members, total_count = await CampaignListMemberService.get_all_members_paginated(
                page, page_size, db
            )
            
            # Format the response
            formatted_members = [
                CampaignListMemberController._format_member_response(member)
                for member in members
            ]
            
            # Calculate pagination info
            total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
            
            pagination_info = PaginationInfo(
                page=page,
                page_size=page_size,
                total_items=total_count,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1
            )
            
            return CampaignListMembersPaginatedResponse(
                members=formatted_members,
                pagination=pagination_info
            )
            
        except Exception as e:
            logger.error(f"Error in get_all_members_paginated controller: {str(e)}")
            raise

    @staticmethod
    async def get_all_members(db: Session):
        """Get all list members across all lists"""
        try:
            members = await CampaignListMemberService.get_all_members(db)
            return [
                CampaignListMemberController._format_member_response(member)
                for member in members
            ]
        except Exception as e:
            logger.error(f"Error in get_all_members controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_list_members(list_id: uuid.UUID, db: Session):
        """Get all members of a campaign list (non-paginated)"""
        try:
            members = await CampaignListMemberService.get_list_members(list_id, db)
            return [
                CampaignListMemberController._format_member_response(member)
                for member in members
            ]
        except Exception as e:
            logger.error(f"Error in get_list_members controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_member(member_id: uuid.UUID, db: Session):
        """Get a list member by ID"""
        try:
            member = await CampaignListMemberService.get_member_by_id(member_id, db)
            return CampaignListMemberController._format_member_response(member)
        except Exception as e:
            logger.error(f"Error in get_member controller: {str(e)}")
            raise
    
    @staticmethod
    async def add_member(
        list_id: uuid.UUID,
        member_data: Dict[str, Any],
        db: Session
    ):
        """Add a member to a campaign list"""
        try:
            # Convert to dict if it's a Pydantic model
            data_dict = member_data if isinstance(member_data, dict) else member_data.model_dump(exclude_unset=True)
            
            # Ensure list_id from path is used
            data_dict['list_id'] = str(list_id)
            
            # Process the request based on whether social_data or social_account_id is provided
            if 'social_data' in data_dict and data_dict['social_data']:
                # Handle with social data
                platform_id = data_dict.get('platform_id')
                if not platform_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="platform_id is required when using social_data"
                    )
                
                # Call the service method that handles creating or finding the social account
                member = await CampaignListMemberService.add_member_with_social_data(
                    list_id=uuid.UUID(data_dict['list_id']) if isinstance(data_dict['list_id'], str) else data_dict['list_id'],
                    platform_id=uuid.UUID(platform_id) if isinstance(platform_id, str) else platform_id,
                    social_data=data_dict['social_data'],
                    db=db
                )
            else:
                # Handle with social_account_id (traditional flow)
                if 'social_account_id' not in data_dict or not data_dict['social_account_id']:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="social_account_id is required when not using social_data"
                    )
                
                # Call the original method
                member = await CampaignListMemberService.add_member(data_dict, db)
            
            return CampaignListMemberController._format_member_response(member)
        except Exception as e:
            logger.error(f"Error in add_member controller: {str(e)}")
            raise
    
    @staticmethod
    async def add_bulk_members(
        list_id: uuid.UUID,
        platform_id: uuid.UUID,
        members_data: List[Dict[str, Any]],
        db: Session
    ):
        """Add multiple members to a campaign list in bulk"""
        try:
            result_members = []
            
            # Begin transaction for all operations
            for member_data in members_data:
                try:
                    member = await CampaignListMemberService.add_member_with_social_data(
                        list_id=list_id,
                        platform_id=platform_id,
                        social_data=member_data,
                        db=db
                    )
                    result_members.append(
                        CampaignListMemberController._format_member_response(member)
                    )
                except Exception as e:
                    # Log the error for this specific member but continue with others
                    logger.error(f"Error adding member {member_data.get('username', 'unknown')}: {str(e)}")
                    # Don't raise here to allow other members to be processed
            
            return result_members
        except Exception as e:
            logger.error(f"Error in add_bulk_members controller: {str(e)}")
            raise

    # app/Http/Controllers/CampaignListMemberController.py (continued)
    
    @staticmethod
    async def update_member(
        member_id: uuid.UUID,
        member_data: CampaignListMemberUpdate,
        db: Session
    ):
        """Update a list member"""
        try:
            member = await CampaignListMemberService.update_member(
                member_id,
                member_data.model_dump(exclude_unset=True),
                db
            )
            return CampaignListMemberController._format_member_response(member)
        except Exception as e:
            logger.error(f"Error in update_member controller: {str(e)}")
            raise
    
    @staticmethod
    async def remove_member(member_id: uuid.UUID, db: Session):
        """Remove a member from a campaign list"""
        try:
            await CampaignListMemberService.remove_member(member_id, db)
            return {"message": "Member removed successfully"}
        except Exception as e:
            logger.error(f"Error in remove_member controller: {str(e)}")
            raise
    
    @staticmethod
    async def record_contact_attempt(member_id: uuid.UUID, db: Session):
        """Record a contact attempt for a list member"""
        try:
            member = await CampaignListMemberService.record_contact_attempt(member_id, db)
            return CampaignListMemberController._format_member_response(member)
        except Exception as e:
            logger.error(f"Error in record_contact_attempt controller: {str(e)}")
            raise
    
    @staticmethod
    def _format_member_response(member):
        """Format a member object into a consistent response"""
        response = CampaignListMemberResponse.model_validate(member)
        
        # Add status details if available
        if member.status:
            response.status = StatusBrief.model_validate(member.status)
        
        # Add platform details if available
        if member.platform:
            response.platform = PlatformBrief.model_validate(member.platform)
        
        # Add social account details if available
        if member.social_account:
            # Create a brief summary of the social account
            social_account_data = {
                "id": member.social_account.id,
                "full_name": member.social_account.full_name,
                "platform_id": member.social_account.platform_id,
                "account_handle": member.social_account.account_handle,
                "followers_count": member.social_account.followers_count,
                "platform_account_id": member.social_account.platform_account_id,  # Include this field
                "is_verified": member.social_account.is_verified,
                "profile_pic_url": member.social_account.profile_pic_url,
                "is_private": member.social_account.is_private,
                "is_business": member.social_account.is_business,
                "media_count": member.social_account.media_count,
                "following_count": member.social_account.following_count,
                "subscribers_count": member.social_account.subscribers_count,
                "likes_count": member.social_account.likes_count,
            }
            
            response.social_account = SocialAccountBrief(**social_account_data)
        
        return response