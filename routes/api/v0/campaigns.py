# routes/api/v0/campaigns.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.Http.Controllers.CampaignController import CampaignController
from app.Models.auth_models import User
from app.Schemas.campaign import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    CampaignListCreate, CampaignListUpdate, CampaignListResponse
)

from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission
)
from config.database import get_db

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

# Campaign endpoints
@router.get("/", response_model=List[CampaignResponse])
async def get_all_campaigns(
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all campaigns"""
    return await CampaignController.get_all_campaigns(db)

@router.get("/company/{company_id}", response_model=List[CampaignResponse])
async def get_company_campaigns(
    company_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all campaigns for a specific company"""
    return await CampaignController.get_company_campaigns(company_id, db)

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get a campaign by ID"""
    return await CampaignController.get_campaign(campaign_id, db)

@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: User = Depends(has_permission("campaign:create")),
    db: Session = Depends(get_db)
):
    """Create a new campaign"""
    return await CampaignController.create_campaign(campaign_data, current_user, db)

@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: uuid.UUID,
    campaign_data: CampaignUpdate,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Update a campaign"""
    return await CampaignController.update_campaign(campaign_id, campaign_data, db)

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:delete")),
    db: Session = Depends(get_db)
):
    """Delete a campaign"""
    return await CampaignController.delete_campaign(campaign_id, db)

# Influencer List endpoints
@router.get("/{campaign_id}/lists", response_model=List[CampaignListResponse])
async def get_campaign_lists(
    campaign_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all campaign lists for a campaign"""
    return await CampaignController.get_campaign_lists(campaign_id, db)

@router.post("/{campaign_id}/lists", response_model=CampaignListResponse)
async def create_list(
    campaign_id: uuid.UUID,
    list_data: CampaignListCreate,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Create a new campaign list for a campaign"""
    return await CampaignController.create_list(campaign_id, list_data, current_user, db)
