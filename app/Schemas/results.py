# app/Schemas/results.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, Union
from datetime import datetime
from decimal import Decimal
import uuid

class ResultBase(BaseModel):
    campaign_id: str = Field(..., description="Campaign ID (UUID as string)")
    user_ig_id: Optional[str] = Field(None, max_length=255, description="Instagram user ID")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name of the influencer")
    influencer_username: str = Field(..., min_length=1, max_length=255, description="Influencer username")
    profile_pic_url: Optional[str] = Field(None, description="Profile picture URL")
    post_id: Optional[str] = Field(None, max_length=255, description="Social media post ID")
    title: Optional[str] = Field(None, description="Post title or caption")
    views_count: Optional[int] = Field(None, ge=0, description="Number of views")
    likes_count: Optional[int] = Field(None, ge=0, description="Number of likes")
    plays_count: Optional[int] = Field(None, ge=0, description="Number of plays")
    comments_count: Optional[int] = Field(None, ge=0, description="Number of comments")
    media_preview: Optional[str] = Field(None, description="Media preview URL")
    duration: Optional[Union[float, Decimal]] = Field(None, ge=0, description="Duration in seconds (supports decimal values)")
    thumbnail: Optional[str] = Field(None, description="Thumbnail URL")
    post_created_at: Optional[datetime] = Field(None, description="When the post was created")
    post_result_obj: Optional[Dict[str, Any]] = Field(None, description="Complete post object as JSON")

class ResultCreate(ResultBase):
    pass

class ResultUpdate(BaseModel):
    campaign_id: Optional[str] = Field(None, description="Campaign ID (UUID as string)")
    user_ig_id: Optional[str] = Field(None, max_length=255, description="Instagram user ID")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name of the influencer")
    influencer_username: Optional[str] = Field(None, min_length=1, max_length=255, description="Influencer username")
    profile_pic_url: Optional[str] = Field(None, description="Profile picture URL")
    post_id: Optional[str] = Field(None, max_length=255, description="Social media post ID")
    title: Optional[str] = Field(None, description="Post title or caption")
    views_count: Optional[int] = Field(None, ge=0, description="Number of views")
    likes_count: Optional[int] = Field(None, ge=0, description="Number of likes")
    plays_count: Optional[int] = Field(None, ge=0, description="Number of plays")
    comments_count: Optional[int] = Field(None, ge=0, description="Number of comments")
    media_preview: Optional[str] = Field(None, description="Media preview URL")
    duration: Optional[Union[float, Decimal]] = Field(None, ge=0, description="Duration in seconds (supports decimal values)")
    thumbnail: Optional[str] = Field(None, description="Thumbnail URL")
    post_created_at: Optional[datetime] = Field(None, description="When the post was created")
    post_result_obj: Optional[Dict[str, Any]] = Field(None, description="Complete post object as JSON")

class ResultResponse(ResultBase):
    id: str = Field(..., description="Result ID (UUID as string)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'campaign_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class ResultBrief(BaseModel):
    """Brief result info for use in other responses"""
    id: str
    influencer_username: str
    post_id: Optional[str]
    title: Optional[str]
    views_count: Optional[int]
    duration: Optional[Union[float, Decimal]]
    created_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class ResultListResponse(BaseModel):
    """Response for paginated result lists"""
    results: list[ResultResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class CampaignResultsResponse(BaseModel):
    """Response for campaign-specific results"""
    campaign_id: str
    results: list[ResultResponse]
    total_results: int
    
    @field_validator('campaign_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class ResultsStatsResponse(BaseModel):
    """Response for results statistics"""
    total_results: int
    total_views: Optional[int]
    total_likes: Optional[int]
    total_plays: Optional[int]
    total_comments: Optional[int]
    results_by_campaign: Dict[str, int]
    top_influencers: list[Dict[str, Any]]
    recent_results: list[ResultBrief]

class IndividualResultUpdate(BaseModel):
    """Individual result update with custom data"""
    result_id: str = Field(..., description="Result ID to update")
    update_data: ResultUpdate = Field(..., description="Data to update for this specific result")

class BulkUpdateRequest(BaseModel):
    """Request for bulk updating multiple results with individual data"""
    updates: list[IndividualResultUpdate] = Field(..., description="List of individual result updates")

class BulkUpdateResponse(BaseModel):
    """Response for bulk update operation"""
    success: bool
    updated_count: int
    failed_count: int
    message: str
    updated_results: list[ResultResponse] = []
    errors: list[Dict[str, str]] = []