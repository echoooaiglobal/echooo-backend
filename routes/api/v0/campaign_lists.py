# routes/api/v0/campaign_lists.py - Fixed imports
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid

from app.Http.Controllers.CampaignListController import CampaignListController
from app.Models.auth_models import User
from app.Schemas.campaign_lists import (  # Fixed import
    CampaignListCreate, CampaignListUpdate, CampaignListResponse
)

from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission
)
from config.database import get_db

router = APIRouter(prefix="/campaign-lists", tags=["Campaign Lists"])

# Basic CRUD operations
@router.get("/", response_model=List[CampaignListResponse])
async def get_all_campaign_lists(
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all campaign lists"""
    return await CampaignListController.get_all_campaign_lists(db)

@router.get("/{list_id}", response_model=CampaignListResponse)
async def get_campaign_list(
    list_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get a campaign list by ID"""
    return await CampaignListController.get_campaign_list(list_id, db)

@router.post("/", response_model=CampaignListResponse)
async def create_campaign_list(
    list_data: CampaignListCreate,
    current_user: User = Depends(has_permission("campaign:create")),
    db: Session = Depends(get_db)
):
    """Create a new campaign list"""
    return await CampaignListController.create_campaign_list(list_data, current_user, db)

@router.put("/{list_id}", response_model=CampaignListResponse)
async def update_campaign_list(
    list_id: uuid.UUID,
    list_data: CampaignListUpdate,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Update a campaign list"""
    return await CampaignListController.update_campaign_list(list_id, list_data, db)

@router.delete("/{list_id}")
async def delete_campaign_list(
    list_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:delete")),
    db: Session = Depends(get_db)
):
    """Delete a campaign list"""
    return await CampaignListController.delete_campaign_list(list_id, db)

# Campaign-specific list operations
@router.get("/campaign/{campaign_id}", response_model=List[CampaignListResponse])
async def get_campaign_lists_by_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all campaign lists for a specific campaign"""
    return await CampaignListController.get_campaign_lists_by_campaign(campaign_id, db)

@router.post("/campaign/{campaign_id}", response_model=CampaignListResponse)
async def create_campaign_list_for_campaign(
    campaign_id: uuid.UUID,
    list_data: CampaignListCreate,
    current_user: User = Depends(has_permission("campaign:create")),
    db: Session = Depends(get_db)
):
    """Create a new campaign list for a specific campaign"""
    return await CampaignListController.create_campaign_list_for_campaign(
        campaign_id, list_data, current_user, db
    )

# Additional utility endpoints
@router.get("/{list_id}/stats")
async def get_campaign_list_stats(
    list_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get statistics for a campaign list"""
    return await CampaignListController.get_campaign_list_stats(list_id, db)

@router.post("/{list_id}/duplicate", response_model=CampaignListResponse)
async def duplicate_campaign_list(
    list_id: uuid.UUID,
    new_name: str = Body(..., embed=True),
    current_user: User = Depends(has_permission("campaign:create")),
    db: Session = Depends(get_db)
):
    """Duplicate a campaign list with a new name"""
    return await CampaignListController.duplicate_campaign_list(
        list_id, new_name, current_user, db
    )

@router.get("/search/", response_model=List[CampaignListResponse])
async def search_campaign_lists(
    q: str = Query(..., description="Search term"),
    campaign_id: Optional[uuid.UUID] = Query(None, description="Filter by campaign ID"),
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Search campaign lists by name or description"""
    return await CampaignListController.search_campaign_lists(q, campaign_id, db)