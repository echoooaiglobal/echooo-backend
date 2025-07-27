# app/Schemas/campaign_lists.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Campaign List schemas
class CampaignListBase(BaseModel):
    campaign_id: str
    name: str
    description: Optional[str] = None
    message_template_id: Optional[str] = None

class CampaignListCreate(CampaignListBase):
    pass

class CampaignListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    message_template_id: Optional[str] = None
    notes: Optional[str] = None

class CampaignListResponse(CampaignListBase):
    id: str
    created_by: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'campaign_id', 'created_by', 'message_template_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Brief schemas for nested responses
class CampaignListBrief(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Campaign List Statistics Response
class CampaignListStatsResponse(BaseModel):
    list_id: str
    total_influencers: int
    onboarded_count: int
    avg_contact_attempts: float
    status_breakdown: List[Dict[str, Any]]
    price_stats: Dict[str, Optional[float]]

# Duplication Response
class CampaignListDuplicateResponse(BaseModel):
    message: str
    original_list_id: str
    new_list_id: str
    new_list_name: str
    influencers_copied: int