# routes/api/v0/campaigns.py - Updated version
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.Http.Controllers.CampaignController import CampaignController
from app.Models.auth_models import User
from app.Schemas.campaign import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    CampaignListResponse
)

from app.Utils.Helpers import (
    has_role, has_permission
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
    """Soft delete a campaign"""
    return await CampaignController.delete_campaign(campaign_id, current_user, db)

@router.patch("/{campaign_id}/restore", response_model=CampaignResponse)
async def restore_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:delete")),  # Same permission as delete
    db: Session = Depends(get_db)
):
    """Restore a soft deleted campaign"""
    return await CampaignController.restore_campaign(campaign_id, db)

@router.delete("/{campaign_id}/permanent")
async def hard_delete_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(has_role(["company_admin"])),
    db: Session = Depends(get_db)
):
    """Permanently delete a campaign (irreversible)"""
    return await CampaignController.hard_delete_campaign(campaign_id, db)

@router.get("/company/{company_id}/deleted", response_model=List[CampaignResponse])
async def get_company_deleted_campaigns(
    company_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all soft deleted campaigns for a specific company"""
    return await CampaignController.get_company_deleted_campaigns(company_id, db)

@router.get("/deleted", response_model=List[CampaignResponse])
async def get_all_deleted_campaigns(
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all soft deleted campaigns (for platform admins)"""
    return await CampaignController.get_all_deleted_campaigns(db)

# Campaign List endpoints - Keep for backward compatibility
@router.get("/{campaign_id}/lists", response_model=List[CampaignListResponse])
async def get_campaign_lists(
    campaign_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all campaign lists for a campaign"""
    return await CampaignController.get_campaign_lists(campaign_id, db)