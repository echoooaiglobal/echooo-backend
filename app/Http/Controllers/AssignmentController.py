# app/Http/Controllers/AssignmentController.py
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import math

from app.Models.auth_models import User
from app.Models.campaign_models import ListAssignment, Agent
from app.Schemas.assignment import AssignmentResponse, AssignmentsResponse, AgentBrief, CampaignBrief, CampaignListBrief, StatusBrief
from app.Schemas.campaign_list_member import CampaignListMemberResponse, CampaignListMembersPaginatedResponse, PaginationInfo, SocialAccountBrief, StatusBrief as MemberStatusBrief, PlatformBrief
from app.Services.AssignmentService import AssignmentService
from app.Utils.Logger import logger

class AssignmentController:
    """Controller for assignment-related endpoints"""
    
    @staticmethod
    async def get_assignments(
        current_user: User,
        user_id: Optional[uuid.UUID] = None,
        db: Session = None
    ):
        """
        Get assignments for current user or specific user (admin only)
        
        Args:
            current_user: Current authenticated user
            user_id: Optional user ID for admin to view specific agent's assignments
            db: Database session
            
        Returns:
            AssignmentsResponse: Assignments with related data
        """
        try:
            # Check if platform admin
            is_platform_admin = any(role.name == "platform_admin" for role in current_user.roles)
            
            if user_id:
                # Admin requesting specific user's assignments
                if not is_platform_admin:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only platform admins can view other users' assignments"
                    )
                target_user_id = user_id
            else:
                # Current user's assignments
                target_user_id = current_user.id
            
            # Get assignments
            if is_platform_admin and not user_id:
                # Platform admin requesting all assignments
                assignments = await AssignmentService.get_all_assignments(db)
                agent_info = None
            else:
                # Specific user assignments
                assignments = await AssignmentService.get_user_assignments(target_user_id, db)
                
                # Get agent info if requesting specific user
                if user_id:
                    user_agents = db.query(Agent).filter(Agent.assigned_to_user_id == target_user_id).all()
                    agent_info = AgentBrief.model_validate(user_agents[0]) if user_agents else None
                else:
                    agent_info = None
            
            # Format assignments
            formatted_assignments = []
            for assignment in assignments:
                assignment_data = AssignmentController._format_assignment_response(assignment)
                formatted_assignments.append(assignment_data)
            
            return AssignmentsResponse(
                assignments=formatted_assignments,
                total_assignments=len(formatted_assignments),
                agent_info=agent_info
            )
            
        except Exception as e:
            logger.error(f"Error in get_assignments controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_assignment_members(
        assignment_id: uuid.UUID,
        page: int = 1,
        page_size: int = 10,
        current_user: User = None,
        db: Session = None
    ):
        """
        Get paginated members for a specific assignment
        
        Args:
            assignment_id: ID of the assignment
            page: Page number
            page_size: Items per page
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            CampaignListMembersPaginatedResponse: Paginated members
        """
        try:
            # Check if platform admin
            is_platform_admin = any(role.name == "platform_admin" for role in current_user.roles)
            
            # Verify access if not platform admin
            if not is_platform_admin:
                has_access = await AssignmentService.verify_user_assignment_access(
                    current_user.id, assignment_id, db
                )
                if not has_access:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You don't have access to this assignment"
                    )
            
            # Get assignment members
            members, total_count, assignment = await AssignmentService.get_assignment_members(
                assignment_id, page, page_size, db
            )
            
            # Format the response
            formatted_members = []
            for member in members:
                member_data = AssignmentController._format_member_response(member)
                formatted_members.append(member_data)
            
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
            logger.error(f"Error in get_assignment_members controller: {str(e)}")
            raise
    
    @staticmethod
    def _format_assignment_response(assignment: ListAssignment) -> AssignmentResponse:
        """Format an assignment object into a consistent response"""
        response = AssignmentResponse.model_validate(assignment)
        
        # Add agent details
        if assignment.agent:
            response.agent = AgentBrief.model_validate(assignment.agent)
        
        # Add campaign list details
        if assignment.list:
            response.campaign_list = CampaignListBrief.model_validate(assignment.list)
            
            # Add campaign details
            if assignment.list.campaign:
                response.campaign = CampaignBrief.model_validate(assignment.list.campaign)
        
        # Add status details
        if assignment.status:
            response.status = StatusBrief.model_validate(assignment.status)
        
        return response
    
    @staticmethod
    def _format_member_response(member) -> CampaignListMemberResponse:
        """Format a member object into a consistent response"""
        response = CampaignListMemberResponse.model_validate(member)
        
        # Add status details if available
        if member.status:
            response.status = MemberStatusBrief.model_validate(member.status)
        
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
                "platform_account_id": member.social_account.platform_account_id,
                "is_verified": member.social_account.is_verified,
                "profile_pic_url": member.social_account.profile_pic_url,
                "account_url": member.social_account.account_url,
                "is_private": member.social_account.is_private,
                "is_business": member.social_account.is_business,
                "media_count": member.social_account.media_count,
                "following_count": member.social_account.following_count,
                "subscribers_count": member.social_account.subscribers_count,
                "likes_count": member.social_account.likes_count,
            }
            
            response.social_account = SocialAccountBrief(**social_account_data)
        
        return response