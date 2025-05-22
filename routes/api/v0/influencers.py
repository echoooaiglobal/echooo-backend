# routes/api/v0/influencers.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.Http.Controllers.InfluencerController import InfluencerController
from app.Models.auth_models import User
from app.Schemas.influencer import (
    InfluencerCreate, InfluencerUpdate, InfluencerResponse,
    SocialAccountCreate, SocialAccountUpdate, SocialAccountResponse,
    InfluencerContactCreate, InfluencerContactUpdate, InfluencerContactResponse
)
from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission, is_influencer
)
from config.database import get_db

router = APIRouter(prefix="/influencers", tags=["Influencers"])

# Influencer profile endpoints
@router.post("/", response_model=InfluencerResponse)
async def create_influencer(
    influencer_data: InfluencerCreate,
    current_user: User = Depends(has_permission("influencer:create")),
    db: Session = Depends(get_db)
):
    """Create a new influencer profile"""
    return await InfluencerController.create_influencer(influencer_data, db)

@router.get("/{influencer_id}", response_model=InfluencerResponse)
async def get_influencer(
    influencer_id: uuid.UUID,
    current_user: User = Depends(has_permission("influencer:read")),
    db: Session = Depends(get_db)
):
    """Get an influencer by ID"""
    return await InfluencerController.get_influencer(influencer_id, db)

@router.get("/user/{user_id}", response_model=InfluencerResponse)
async def get_influencer_by_user(
    user_id: uuid.UUID,
    current_user: User = Depends(has_permission("influencer:read")),
    db: Session = Depends(get_db)
):
    """Get an influencer by user ID"""
    return await InfluencerController.get_influencer_by_user(user_id, db)

@router.get("/me", response_model=InfluencerResponse)
async def get_my_profile(
    current_user: User = Depends(is_influencer),
    db: Session = Depends(get_db)
):
    """Get current user's influencer profile"""
    return await InfluencerController.get_influencer_by_user(current_user.id, db)

@router.put("/{influencer_id}", response_model=InfluencerResponse)
async def update_influencer(
    influencer_id: uuid.UUID,
    influencer_data: InfluencerUpdate,
    current_user: User = Depends(has_permission("influencer:update")),
    db: Session = Depends(get_db)
):
    """Update an influencer profile"""
    return await InfluencerController.update_influencer(influencer_id, influencer_data, db)

@router.delete("/{influencer_id}")
async def delete_influencer(
    influencer_id: uuid.UUID,
    current_user: User = Depends(has_permission("influencer:delete")),
    db: Session = Depends(get_db)
):
    """Delete an influencer profile"""
    return await InfluencerController.delete_influencer(influencer_id, db)

# Influencer social account endpoints
@router.post("/{influencer_id}/social-accounts", response_model=SocialAccountResponse)
async def add_social_account(
    influencer_id: uuid.UUID,
    account_data: SocialAccountCreate,
    current_user: User = Depends(has_permission("influencer:update")),
    db: Session = Depends(get_db)
):
    """Add a social account to an influencer"""
    return await InfluencerController.add_social_account(influencer_id, account_data, db)

@router.put("/social-accounts/{account_id}", response_model=SocialAccountResponse)
async def update_social_account(
    account_id: uuid.UUID,
    account_data: SocialAccountUpdate,
    current_user: User = Depends(has_permission("influencer:update")),
    db: Session = Depends(get_db)
):
    """Update an influencer's social account"""
    return await InfluencerController.update_social_account(account_id, account_data, db)

@router.delete("/social-accounts/{account_id}")
async def delete_social_account(
    account_id: uuid.UUID,
    current_user: User = Depends(has_permission("influencer:update")),
    db: Session = Depends(get_db)
):
    """Delete an influencer's social account"""
    return await InfluencerController.delete_social_account(account_id, db)

# Influencer contact endpoints
@router.post("/{influencer_id}/contacts", response_model=InfluencerContactResponse)
async def add_influencer_contact(
    influencer_id: uuid.UUID,
    contact_data: InfluencerContactCreate,
    current_user: User = Depends(has_permission("influencer:update")),
    db: Session = Depends(get_db)
):
    """Add a contact to an influencer"""
    return await InfluencerController.add_influencer_contact(influencer_id, contact_data, db)

@router.put("/contacts/{contact_id}", response_model=InfluencerContactResponse)
async def update_influencer_contact(
    contact_id: uuid.UUID,
    contact_data: InfluencerContactUpdate,
    current_user: User = Depends(has_permission("influencer:update")),
    db: Session = Depends(get_db)
):
    """Update an influencer contact"""
    return await InfluencerController.update_influencer_contact(contact_id, contact_data, db)

@router.delete("/contacts/{contact_id}")
async def delete_influencer_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(has_permission("influencer:update")),
    db: Session = Depends(get_db)
):
    """Delete an influencer contact"""
    return await InfluencerController.delete_influencer_contact(contact_id, db)