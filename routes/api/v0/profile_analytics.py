# routes/api/v0/profile_analytics.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.Http.Controllers.ProfileAnalyticsController import ProfileAnalyticsController
from app.Models.auth_models import User
from app.Schemas.profile_analytics import (
    ProfileAnalyticsCreate, ProfileAnalyticsUpdate, ProfileAnalyticsResponse,
    ProfileAnalyticsListResponse, ProfileAnalyticsStatsResponse,
    ProfileAnalyticsWithSocialAccountCreate, ProfileAnalyticsWithSocialAccountResponse,
    SocialAccountWithAnalyticsResponse, AnalyticsExistsResponse
)
from app.Utils.Helpers import get_current_active_user
from config.database import get_db

router = APIRouter(prefix="/profile-analytics", tags=["Profile Analytics"])

@router.post("/with-social-account", response_model=ProfileAnalyticsWithSocialAccountResponse)
async def create_analytics_with_social_account(
    data: ProfileAnalyticsWithSocialAccountCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create or update social account and create analytics record
    
    This is the main endpoint for storing profile analytics. It will:
    1. Create a new social account if it doesn't exist (based on platform_id + platform_account_id)
    2. Update existing social account if it exists (keeping influencer_id and platform_account_id unchanged)
    3. Create a new analytics record linked to the social account
    
    Example request:
    ```json
    {
        "social_account_data": {
            "platform_id": "uuid-here",
            "platform_account_id": "instagram_123456",
            "account_handle": "@influencer_name",
            "full_name": "John Doe",
            "profile_pic_url": "https://example.com/pic.jpg",
            "bio": "Lifestyle influencer",
            "is_verified": true,
            "is_private": false
        },
        "analytics": {
            "followers_count": 150000,
            "following_count": 850,
            "posts_count": 1250,
            "engagement_rate": 3.5,
            "avg_likes": 5000,
            "avg_comments": 250,
            "demographics": {
                "age_groups": {"18-24": 35, "25-34": 40, "35-44": 25},
                "gender": {"male": 45, "female": 55}
            }
        }
    }
    ```
    """
    return await ProfileAnalyticsController.create_analytics_with_social_account(data, db)

@router.get("/exists/{platform_account_id}", response_model=AnalyticsExistsResponse)
async def check_analytics_existence(
    platform_account_id: str,
    platform_id: Optional[str] = Query(None, description="Optional platform ID to filter results"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check if analytics exist for a platform account
    
    This endpoint checks whether analytics data exists for a given platform account ID.
    It returns detailed information about the existence status, analytics count, and 
    the date of the latest analytics record.
    
    Path Parameters:
    - platform_account_id: The platform-specific account ID to check
    
    Query Parameters:
    - platform_id: Optional platform ID to filter results (recommended for accuracy)
    
    Response:
    - exists: Boolean indicating if analytics exist
    - platform_account_id: The account ID that was checked
    - platform_id: Platform ID if provided
    - social_account_id: Social account ID if found
    - analytics_count: Number of analytics records found
    - latest_analytics_date: Date of the most recent analytics record
    
    Examples:
    - `/profile-analytics/exists/instagram_123456`
    - `/profile-analytics/exists/instagram_123456?platform_id=uuid-here`
    """
    return await ProfileAnalyticsController.check_analytics_exists(
        platform_account_id, platform_id, db
    )

@router.get("/by-handle/{handle_or_account_id}", response_model=SocialAccountWithAnalyticsResponse)
async def get_analytics_by_handle_or_account_id(
    handle_or_account_id: str,
    platform_id: Optional[str] = Query(None, description="Optional platform ID to filter results"),
    # current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get analytics by user handle or platform account ID
    
    This endpoint searches for a social account by:
    - Account handle (partial match, case-insensitive)
    - Platform account ID (exact match)
    
    Returns the social account details along with all its analytics records (historical data).
    
    Examples:
    - `/profile-analytics/by-handle/@influencer_name`
    - `/profile-analytics/by-handle/instagram_123456?platform_id=uuid-here`
    """
    return await ProfileAnalyticsController.get_analytics_by_handle_or_account_id(
        handle_or_account_id, platform_id, db
    )

@router.post("/", response_model=ProfileAnalyticsResponse)
async def create_profile_analytics_direct(
    analytics_data: ProfileAnalyticsCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create profile analytics directly (social account must already exist)
    
    Use this endpoint when you already have a social account ID and just want to add
    new analytics data. For creating both social account and analytics, use the
    `/with-social-account` endpoint instead.
    """
    return await ProfileAnalyticsController.create_analytics(analytics_data, db)

@router.get("/", response_model=ProfileAnalyticsListResponse)
async def get_all_profile_analytics(
    social_account_id: Optional[str] = Query(None, description="Filter by social account ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of profile analytics with optional filters
    
    Query Parameters:
    - social_account_id: Filter analytics by specific social account
    - page: Page number for pagination (default: 1)
    - per_page: Number of items per page (default: 20, max: 100)
    """
    social_account_uuid = None
    if social_account_id:
        try:
            social_account_uuid = uuid.UUID(social_account_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid social_account_id format"
            )
    
    return await ProfileAnalyticsController.get_all_analytics(
        db, social_account_uuid, page, per_page
    )

@router.get("/stats", response_model=ProfileAnalyticsStatsResponse)
async def get_profile_analytics_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get profile analytics statistics
    
    Returns overview statistics including:
    - Total number of social accounts with analytics
    - Breakdown by platform
    - Recent analytics entries
    - Top platforms by analytics count
    """
    return await ProfileAnalyticsController.get_analytics_stats(db)

@router.get("/{analytics_id}", response_model=ProfileAnalyticsResponse)
async def get_profile_analytics(
    analytics_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific profile analytics record by ID"""
    return await ProfileAnalyticsController.get_analytics_by_id(analytics_id, db)

@router.get("/social-account/{social_account_id}", response_model=List[ProfileAnalyticsResponse])
async def get_analytics_by_social_account(
    social_account_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all analytics records for a specific social account
    
    Returns historical analytics data for the social account, ordered by creation date (newest first).
    """
    return await ProfileAnalyticsController.get_analytics_by_social_account(social_account_id, db)

@router.put("/{analytics_id}", response_model=ProfileAnalyticsResponse)
async def update_profile_analytics(
    analytics_id: uuid.UUID,
    analytics_data: ProfileAnalyticsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update profile analytics
    
    You can update the analytics JSON data. The analytics field will be completely 
    replaced if provided, so make sure to include all data you want to keep.
    """
    return await ProfileAnalyticsController.update_analytics(analytics_id, analytics_data, db)

@router.delete("/{analytics_id}")
async def delete_profile_analytics(
    analytics_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete specific profile analytics record by ID"""
    return await ProfileAnalyticsController.delete_analytics(analytics_id, db)