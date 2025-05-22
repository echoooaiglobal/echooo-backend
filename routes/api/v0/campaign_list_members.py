# routes/api/v0/campaign_list_members.py
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid

from app.Http.Controllers.CampaignListMemberController import CampaignListMemberController
from app.Models.auth_models import User
from app.Schemas.campaign_list_member import (
    CampaignListMemberCreate, CampaignListMemberUpdate, CampaignListMemberResponse,
    CampaignListMemberBulkCreate, CampaignListMembersPaginatedResponse
)

from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission
)
from config.database import get_db

main_router = APIRouter(prefix="/campaign-list-members", tags=["Campaign List Members"])

@main_router.get("/", response_model=CampaignListMembersPaginatedResponse)
async def get_all_list_members(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    list_id: Optional[uuid.UUID] = Query(None, description="Filter by list ID"),
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """
    Get paginated list members, optionally filtered by list_id
    """
    if list_id:
        return await CampaignListMemberController.get_list_members_paginated(list_id, page, page_size, db)
    return await CampaignListMemberController.get_all_members_paginated(page, page_size, db)

@main_router.post("/", response_model=CampaignListMemberResponse)
async def create_list_member(
    member_data: CampaignListMemberCreate,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """
    Create a new campaign list member
    
    This endpoint supports two flows:
    1. Basic: Provide list_id, social_account_id, platform_id
    2. Enhanced: Provide list_id, platform_id, and social_data (will find or create social account)
    """
    if hasattr(member_data, 'list_id') and member_data.list_id:
        list_id = member_data.list_id
        return await CampaignListMemberController.add_member(list_id, member_data, db)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="list_id is required"
        )

@main_router.post("/bulk", response_model=List[CampaignListMemberResponse])
async def create_bulk_list_members(
    bulk_data: CampaignListMemberBulkCreate,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """
    Create multiple campaign list members in a single API call
    
    Example:
    {
        "list_id": "uuid-here",
        "platform_id": "uuid-here",
        "members": [
            {
                "id": "174340276",
                "username": "thegreengentleman",
                "name": "Tyler Vogel",
                "profileImage": "https://example.com/profile.jpg",
                "followers": "1000.0K",
                "isVerified": true
            },
            {
                "id": "another-id",
                "username": "another_user",
                "name": "Another Name",
                "profileImage": "https://example.com/another.jpg",
                "followers": "500K",
                "isVerified": false
            }
        ]
    }
    """
    return await CampaignListMemberController.add_bulk_members(
        bulk_data.list_id,
        bulk_data.platform_id,
        bulk_data.members,
        db
    )

@main_router.get("/{member_id}", response_model=CampaignListMemberResponse)
async def get_list_member(
    member_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get a list member by ID"""
    return await CampaignListMemberController.get_member(member_id, db)

@main_router.put("/{member_id}", response_model=CampaignListMemberResponse)
async def update_list_member(
    member_id: uuid.UUID,
    member_data: CampaignListMemberUpdate,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Update a list member"""
    return await CampaignListMemberController.update_member(member_id, member_data, db)

@main_router.delete("/{member_id}")
async def delete_list_member(
    member_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Delete a list member"""
    return await CampaignListMemberController.remove_member(member_id, db)

@main_router.post("/{member_id}/contact", response_model=CampaignListMemberResponse)
async def record_contact_attempt(
    member_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Record a contact attempt for a list member"""
    return await CampaignListMemberController.record_contact_attempt(member_id, db)

# Keep the list-specific routes for backwards compatibility
# This can be deprecated later
legacy_router = APIRouter(prefix="/campaign-lists", tags=["List Members"])

@legacy_router.get("/{list_id}/members", response_model=List[CampaignListMemberResponse])
async def get_list_members(
    list_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all members of a campaign list"""
    return await CampaignListMemberController.get_list_members(list_id, db)



router = APIRouter()
router.include_router(main_router)
router.include_router(legacy_router)