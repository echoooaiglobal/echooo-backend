# routes/api/v0/results.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.Http.Controllers.ResultController import ResultController
from app.Models.auth_models import User
from app.Schemas.results import (
    ResultCreate, ResultUpdate, ResultResponse, ResultListResponse,
    CampaignResultsResponse, BulkUpdateRequest, BulkUpdateResponse
)
from app.Utils.Helpers import (
    get_current_active_user, has_permission, has_role
)
from config.database import get_db

router = APIRouter(prefix="/results", tags=["Results"])

# Get all results with pagination and sorting
@router.get("/", response_model=ResultListResponse)
async def get_all_results(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    sort_by: str = Query("created_at", description="Column to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(has_permission("result:read")),
    db: Session = Depends(get_db)
):
    """Get all results with pagination and sorting"""
    return await ResultController.get_all_results(db, page, per_page, sort_by, sort_order)

# Get a specific result by ID
@router.get("/{result_id}", response_model=ResultResponse)
async def get_result(
    result_id: uuid.UUID,
    current_user: User = Depends(has_permission("result:read")),
    db: Session = Depends(get_db)
):
    """Get a result by ID"""
    return await ResultController.get_result(result_id, db)

# Create a new result
@router.post("/", response_model=ResultResponse)
async def create_result(
    result_data: ResultCreate,
    # current_user: User = Depends(has_permission("result:create")),
    db: Session = Depends(get_db)
):
    """Create a new result"""
    return await ResultController.create_result(result_data, db)

# Update a result
@router.put("/{result_id}", response_model=ResultResponse)
async def update_result(
    result_id: uuid.UUID,
    result_data: ResultUpdate,
    # current_user: User = Depends(has_permission("result:update")),
    db: Session = Depends(get_db)
):
    """Update a result"""
    return await ResultController.update_result(result_id, result_data, db)

# Delete a result
@router.delete("/{result_id}", response_model=ResultResponse)
async def delete_result(
    result_id: uuid.UUID,
    # current_user: User = Depends(has_permission("result:delete")),
    db: Session = Depends(get_db)
):
    """Delete a result"""
    return await ResultController.delete_result(result_id, db)

# Get results by campaign
@router.get("/campaign/{campaign_id}", response_model=CampaignResultsResponse)
async def get_campaign_results(
    campaign_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    # current_user: User = Depends(has_permission("result:read")),
    db: Session = Depends(get_db)
):
    """Get all results for a specific campaign"""
    return await ResultController.get_campaign_results(campaign_id, db, page, per_page)

# Get results by influencer username
@router.get("/influencer/{influencer_username}", response_model=ResultListResponse)
async def get_influencer_results(
    influencer_username: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    current_user: User = Depends(has_permission("result:read")),
    db: Session = Depends(get_db)
):
    """Get all results for a specific influencer"""
    return await ResultController.get_influencer_results(influencer_username, db, page, per_page)

# Bulk create results
@router.post("/bulk", response_model=dict)
async def bulk_create_results(
    results_data: List[ResultCreate],
    current_user: User = Depends(has_permission("result:create")),
    db: Session = Depends(get_db)
):
    """Create multiple results in bulk"""
    return await ResultController.bulk_create_results(results_data, db)

# Bulk update results for a specific campaign
@router.put("/campaign/{campaign_id}/update-all", response_model=BulkUpdateResponse)
async def bulk_update_campaign_results(
    campaign_id: uuid.UUID,
    bulk_update_request: BulkUpdateRequest,
    # current_user: User = Depends(has_permission("result:update")),
    db: Session = Depends(get_db)
):
    """Bulk update multiple results in a campaign using result IDs"""
    return await ResultController.bulk_update_campaign_results(campaign_id, bulk_update_request, db)

# Get results statistics
@router.get("/stats/summary", response_model=dict)
async def get_results_stats(
    current_user: User = Depends(has_permission("result:read")),
    db: Session = Depends(get_db)
):
    """Get statistics about results"""
    return await ResultController.get_results_stats(db)