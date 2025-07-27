# routes/api/v0/campaign_influencers.py
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid

from app.Http.Controllers.CampaignInfluencerController import CampaignInfluencerController
from app.Models.auth_models import User
from app.Schemas.campaign_influencer import (
    CampaignInfluencerCreate, CampaignInfluencerUpdate, CampaignInfluencerResponse,
    CampaignInfluencerBulkCreate, CampaignInfluencersPaginatedResponse,
    CampaignInfluencerPriceUpdate,
    CampaignInfluencerStatusUpdate,
    CampaignInfluencerNotesUpdate,
    UpdateSuccessResponse,
)

from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission
)
from config.database import get_db

router = APIRouter(prefix="/campaign-influencers", tags=["Campaign Influencers"])

@router.get("/", response_model=CampaignInfluencersPaginatedResponse)
async def get_all_campaign_influencers(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    campaign_list_id: Optional[uuid.UUID] = Query(None, description="Filter by campaign list ID"),
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """
    Get paginated campaign influencers, optionally filtered by campaign_list_id
    """
    if campaign_list_id:
        return await CampaignInfluencerController.get_list_influencers_paginated(
            campaign_list_id, page, page_size, db
        )
    return await CampaignInfluencerController.get_all_influencers_paginated(page, page_size, db)

@router.post("/", response_model=CampaignInfluencerResponse)
async def create_campaign_influencer(
    influencer_data: CampaignInfluencerCreate,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """
    Create a new campaign influencer
    
    This endpoint supports two flows:
    1. Basic: Provide campaign_list_id, social_account_id
    2. Enhanced: Provide campaign_list_id, platform_id, and social_data (will find or create social account)
    
    Example request for enhanced flow:
    {
        "campaign_list_id": "uuid-here",
        "platform_id": "uuid-here",
        "social_data": {
            "id": "174340276",
            "username": "thegreengentleman",
            "name": "Tyler Vogel",
            "profileImage": "https://example.com/profile.jpg",
            "followers": "1000.0K",
            "isVerified": true
        }
    }
    """
    if hasattr(influencer_data, 'campaign_list_id') and influencer_data.campaign_list_id:
        campaign_list_id = uuid.UUID(influencer_data.campaign_list_id)
        return await CampaignInfluencerController.add_influencer(campaign_list_id, influencer_data, db)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="campaign_list_id is required"
        )

@router.post("/bulk", response_model=List[CampaignInfluencerResponse])
async def create_bulk_campaign_influencers(
    bulk_data: CampaignInfluencerBulkCreate,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """
    Create multiple campaign influencers in a single API call
    
    Example:
    {
        "campaign_list_id": "uuid-here",
        "platform_id": "uuid-here",
        "influencers": [
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
    return await CampaignInfluencerController.add_bulk_influencers(
        uuid.UUID(bulk_data.campaign_list_id),
        uuid.UUID(bulk_data.platform_id),
        bulk_data.influencers,
        db
    )

@router.get("/{influencer_id}", response_model=CampaignInfluencerResponse)
async def get_campaign_influencer(
    influencer_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get a campaign influencer by ID"""
    return await CampaignInfluencerController.get_influencer(influencer_id, db)

@router.put("/{influencer_id}", response_model=CampaignInfluencerResponse)
async def update_campaign_influencer(
    influencer_id: uuid.UUID,
    influencer_data: CampaignInfluencerUpdate,
    current_user: User = Depends(has_permission("campaign_influencer:update")),
    db: Session = Depends(get_db)
):
    """Update a campaign influencer"""
    return await CampaignInfluencerController.update_influencer(influencer_id, influencer_data, db)

@router.delete("/{influencer_id}")
async def delete_campaign_influencer(
    influencer_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Remove an influencer from a campaign list"""
    return await CampaignInfluencerController.remove_influencer(influencer_id, db)

# Additional endpoints for specific campaign list operations
@router.get("/list/{campaign_list_id}", response_model=CampaignInfluencersPaginatedResponse)
async def get_campaign_list_influencers(
    campaign_list_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all influencers for a specific campaign list with pagination"""
    return await CampaignInfluencerController.get_list_influencers_paginated(
        campaign_list_id, page, page_size, db
    )

@router.post("/list/{campaign_list_id}", response_model=CampaignInfluencerResponse)
async def add_influencer_to_list(
    campaign_list_id: uuid.UUID,
    influencer_data: CampaignInfluencerCreate,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Add an influencer to a specific campaign list"""
    return await CampaignInfluencerController.add_influencer(campaign_list_id, influencer_data, db)

@router.post("/list/{campaign_list_id}/bulk", response_model=List[CampaignInfluencerResponse])
async def add_bulk_influencers_to_list(
    campaign_list_id: uuid.UUID,
    platform_id: uuid.UUID = Query(..., description="Platform ID for all influencers"),
    influencers: List[Dict[str, Any]] = Body(..., description="List of influencer data"),
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Add multiple influencers to a specific campaign list"""
    return await CampaignInfluencerController.add_bulk_influencers(
        campaign_list_id, platform_id, influencers, db
    )

# Status Management APIs
@router.patch("/bulk-status-update", response_model=List[CampaignInfluencerResponse])
async def bulk_update_influencer_status(
    influencer_ids: List[uuid.UUID] = Body(...),
    status_id: uuid.UUID = Body(...),
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Bulk update status for multiple campaign influencers"""
    return await CampaignInfluencerController.bulk_update_status(
        influencer_ids, status_id, db
    )

# Contact Management APIs
@router.patch("/{influencer_id}/contact-attempts", response_model=CampaignInfluencerResponse)
async def update_contact_attempts(
    influencer_id: uuid.UUID,
    increment: int = Body(1, embed=True),
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Update contact attempts for a campaign influencer"""
    return await CampaignInfluencerController.update_contact_attempts(
        influencer_id, increment, db
    )

@router.get("/{influencer_id}/contact-history")
async def get_contact_history(
    influencer_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get contact history for a campaign influencer"""
    return await CampaignInfluencerController.get_contact_history(influencer_id, db)

# Onboarding Management APIs
@router.patch("/{influencer_id}/ready-for-onboarding", response_model=CampaignInfluencerResponse)
async def mark_ready_for_onboarding(
    influencer_id: uuid.UUID,
    is_ready: bool = Body(..., embed=True),
    collaboration_price: Optional[float] = Body(None, embed=True),
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Mark influencer as ready/not ready for onboarding"""
    update_data = CampaignInfluencerUpdate(
        is_ready_for_onboarding=is_ready,
        collaboration_price=collaboration_price
    )
    return await CampaignInfluencerController.update_influencer(influencer_id, update_data, db)

@router.get("/onboarding-pipeline")
async def get_onboarding_pipeline(
    campaign_list_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get influencers in the onboarding pipeline"""
    return await CampaignInfluencerController.get_onboarding_pipeline(campaign_list_id, db)

# Analytics & Reporting APIs
@router.get("/list/{campaign_list_id}/stats")
async def get_list_influencer_stats(
    campaign_list_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get detailed statistics for influencers in a campaign list"""
    return await CampaignInfluencerController.get_list_influencer_stats(campaign_list_id, db)

@router.get("/list/{campaign_list_id}/price-analytics")
async def get_price_analytics(
    campaign_list_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get collaboration price analytics for a campaign list"""
    return await CampaignInfluencerController.get_price_analytics(campaign_list_id, db)

# Advanced Search & Filter APIs
@router.get("/search", response_model=CampaignInfluencersPaginatedResponse)
async def advanced_search_influencers(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    campaign_list_id: Optional[uuid.UUID] = Query(None),
    status_id: Optional[uuid.UUID] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    is_ready_for_onboarding: Optional[bool] = Query(None),
    min_contact_attempts: Optional[int] = Query(None),
    max_contact_attempts: Optional[int] = Query(None),
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Advanced search for campaign influencers with multiple filters"""
    return await CampaignInfluencerController.advanced_search(
        page, page_size, campaign_list_id, status_id, min_price, max_price,
        is_ready_for_onboarding, min_contact_attempts, max_contact_attempts, db
    )

@router.get("/filter/price-range", response_model=CampaignInfluencersPaginatedResponse)
async def filter_by_price_range(
    min_price: float = Query(...),
    max_price: float = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    campaign_list_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Filter influencers by collaboration price range"""
    return await CampaignInfluencerController.advanced_search(
        page, page_size, campaign_list_id, None, min_price, max_price,
        None, None, None, db
    )

# Batch Operations APIs
@router.delete("/batch-remove")
async def batch_remove_influencers(
    influencer_ids: List[uuid.UUID] = Body(...),
    current_user: User = Depends(has_permission("campaign:delete")),
    db: Session = Depends(get_db)
):
    """Remove multiple influencers from campaign lists"""
    return await CampaignInfluencerController.batch_remove_influencers(influencer_ids, db)

# Migration & Transfer APIs
@router.post("/{influencer_id}/transfer")
async def transfer_influencer_to_list(
    influencer_id: uuid.UUID,
    target_list_id: uuid.UUID = Body(..., embed=True),
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Transfer an influencer to a different campaign list"""
    return await CampaignInfluencerController.transfer_influencer_to_list(
        influencer_id, target_list_id, db
    )

@router.post("/list/{campaign_list_id}/copy-to")
async def copy_influencers_to_list(
    campaign_list_id: uuid.UUID,
    target_list_id: uuid.UUID = Body(..., embed=True),
    influencer_ids: Optional[List[uuid.UUID]] = Body(None),
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Copy influencers from one list to another"""
    return await CampaignInfluencerController.copy_influencers_to_list(
        campaign_list_id, target_list_id, influencer_ids, db
    )


# ================================
# COLLABORATION PRICE & CURRENCY UPDATE
# ================================

@router.patch("/{influencer_id}/price", response_model=UpdateSuccessResponse)
async def update_collaboration_price(
    influencer_id: uuid.UUID,
    price_data: CampaignInfluencerPriceUpdate,
    current_user: User = Depends(has_permission("campaign_influencer:update")),
    db: Session = Depends(get_db)
):
    try:
        
        # Pass the Pydantic model directly to controller
        await CampaignInfluencerController.update_collaboration_price(
            influencer_id, price_data, db  # Pass price_data, not update_data
        )
        
        # Create success message
        updated_fields = []
        if price_data.collaboration_price is not None:
            updated_fields.append(f"price to {price_data.collaboration_price}")
        if price_data.currency is not None:
            updated_fields.append(f"currency to {price_data.currency}")
            
        message = f"Successfully updated collaboration price"
        
        return UpdateSuccessResponse(
            message=message,
            influencer_id=str(influencer_id)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating collaboration price: {str(e)}"
        )

# ================================
# STATUS UPDATE
# ================================

@router.patch("/{influencer_id}/status", response_model=UpdateSuccessResponse)
async def update_influencer_status(
    influencer_id: uuid.UUID,
    status_data: CampaignInfluencerStatusUpdate,
    current_user: User = Depends(has_permission("campaign_influencer:update")),
    db: Session = Depends(get_db)
):
    try:
        # Call controller method
        await CampaignInfluencerController.update_status(
            influencer_id, 
            status_data.status_id, 
            status_data.assigned_influencer_id,
            db
        )
        
        # Create dynamic message based on what was updated
        message = "Successfully updated campaign influencer status"
        
        # Check if the status being set is 'completed' and assigned_influencer_id is provided
        if status_data.assigned_influencer_id:
            from app.Models.statuses import Status
            status = db.query(Status).filter(
                Status.id == status_data.status_id,
                Status.model == 'campaign_influencer'  # Filter by model
            ).first()
            if status and status.name.lower() == 'completed':
                message += " and assigned influencer status & type to completed"
        
        return UpdateSuccessResponse(
            message=message,
            influencer_id=str(influencer_id)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating status: {str(e)}"
        )

# ================================
# NOTES UPDATE
# ================================

@router.patch("/{influencer_id}/notes", response_model=UpdateSuccessResponse)
async def update_influencer_notes(
    influencer_id: uuid.UUID,
    notes_data: CampaignInfluencerNotesUpdate,
    current_user: User = Depends(has_permission("campaign_influencer:update")),
    db: Session = Depends(get_db)
):
    """
    Update notes for a campaign influencer
    
    Args:
        influencer_id: ID of the campaign influencer
        notes_data: Notes update data
        
    Returns:
        Success response with confirmation message
    """
    try:
        update_data = {"notes": notes_data.notes}
        
        # Perform the update
        await CampaignInfluencerController.update_influencer(
            influencer_id, update_data, db
        )
        
        notes_preview = notes_data.notes[:50] + "..." if notes_data.notes and len(notes_data.notes) > 50 else notes_data.notes
        message = f"Successfully updated notes" + (f": {notes_preview}" if notes_data.notes else " (cleared)")
        
        return UpdateSuccessResponse(
            message=message,
            influencer_id=str(influencer_id)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating notes: {str(e)}"
        )