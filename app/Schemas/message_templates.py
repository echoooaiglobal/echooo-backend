# app/Schemas/message_templates.py - Remove assignment fields
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from enum import Enum

class TemplateTypeEnum(str, Enum):
    initial = "initial"
    followup = "followup"

# Message Template schemas
class MessageTemplateBase(BaseModel):
    subject: Optional[str] = Field(None, description="Subject line (required for initial, optional for follow-ups)")
    content: str = Field(..., description="Message content")
    company_id: str
    campaign_id: str
    template_type: TemplateTypeEnum = Field(default=TemplateTypeEnum.initial)
    parent_template_id: Optional[str] = Field(None, description="Parent template ID for follow-ups")
    followup_sequence: Optional[int] = Field(None, description="Follow-up sequence number (1, 2, 3...)")
    followup_delay_hours: Optional[int] = Field(None, ge=0, description="Hours to wait before sending this follow-up")
    is_global: bool = False

    # ADD this validator to handle UUIDs
    @field_validator('company_id', 'campaign_id', 'parent_template_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    @model_validator(mode='after')
    def validate_template_fields(self):
        """Validate template fields based on type"""
        if self.template_type == TemplateTypeEnum.initial:
            if not self.subject:
                raise ValueError("Subject is required for initial templates")
            if self.parent_template_id:
                raise ValueError("Initial templates cannot have a parent template")
            if self.followup_sequence:
                raise ValueError("Initial templates cannot have a followup sequence")
        
        elif self.template_type == TemplateTypeEnum.followup:
            if not self.parent_template_id:
                raise ValueError("Follow-up templates must have a parent template")
            if not self.followup_sequence:
                raise ValueError("Follow-up templates must have a sequence number")
            if self.followup_sequence < 1:
                raise ValueError("Follow-up sequence must be >= 1")
        
        return self

class MessageTemplateFollowupCreate(BaseModel):
    """Simplified schema for creating follow-up templates"""
    content: str = Field(..., description="Follow-up message content")
    followup_delay_hours: int = Field(..., ge=0, description="Hours to wait before sending")
    subject: Optional[str] = Field(None, description="Optional subject for follow-up")

# REMOVED auto_assign_agent and target_list_id fields
class MessageTemplateCreate(MessageTemplateBase):
    """Schema for creating message templates - NO ASSIGNMENT FIELDS"""
    pass

class MessageTemplateUpdate(BaseModel):
    subject: Optional[str] = None
    content: Optional[str] = None
    is_global: Optional[bool] = None

class MessageTemplateBrief(BaseModel):
    """Brief template info for responses"""
    id: str
    subject: Optional[str] = None
    content: str
    template_type: TemplateTypeEnum
    followup_sequence: Optional[int] = None
    followup_delay_hours: Optional[int] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
class MessageTemplateResponse(MessageTemplateBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    # Include follow-up templates for initial templates
    followup_templates: Optional[List[MessageTemplateBrief]] = None
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'company_id', 'campaign_id', 'created_by', 'parent_template_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    

class MessageTemplateWithFollowupsCreate(BaseModel):
    """Schema for creating message templates with AI-generated followups"""
    subject: str = Field(..., description="Subject line for the initial message")
    content: str = Field(..., description="Message content")
    company_id: str = Field(..., description="Company ID")
    campaign_id: str = Field(..., description="Campaign ID")
    template_type: TemplateTypeEnum = Field(default=TemplateTypeEnum.initial)
    is_global: bool = Field(default=True)
    
    # AI followup generation options
    generate_followups: bool = Field(default=True, description="Whether to generate AI followups")
    ai_provider: Optional[str] = Field(default="openai", description="AI provider: 'openai' or 'gemini'")
    custom_instructions: Optional[str] = Field(default=None, description="Custom instructions for AI")
    
    @field_validator('company_id', 'campaign_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    @field_validator('ai_provider')
    @classmethod
    def validate_ai_provider(cls, v):
        if v and v not in ['openai', 'gemini']:
            raise ValueError("ai_provider must be 'openai' or 'gemini'")
        return v or 'openai'  # Default to openai if None
    
    @model_validator(mode='after')
    def validate_followup_fields(self):
        """Validate that initial template has subject"""
        if self.template_type == TemplateTypeEnum.initial and not self.subject:
            raise ValueError("Subject is required for initial templates")
        return self

class MessageTemplateWithFollowupsResponse(BaseModel):
    """Response schema for template with followups"""
    # Main template fields
    id: str
    subject: Optional[str]
    content: str
    company_id: str
    campaign_id: str
    template_type: TemplateTypeEnum
    is_global: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    # Followup templates
    followup_templates: Optional[List[MessageTemplateBrief]] = None
    
    # Generation metadata
    ai_generation_success: bool = Field(default=True, description="Whether AI generation was successful")
    ai_provider_used: Optional[str] = Field(default=None, description="AI provider that was used")
    followup_count: int = Field(default=0, description="Number of followups generated")
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', 'company_id', 'campaign_id', 'created_by', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Alternative simple request model (if you prefer structured approach)
class CreateTemplateWithFollowupsRequest(BaseModel):
    """Simple request wrapper for the endpoint"""
    subject: str
    content: str  
    company_id: str
    campaign_id: str
    template_type: str = "initial"
    is_global: bool = True
    generate_followups: bool = True
    ai_provider: str = "openai"
    custom_instructions: Optional[str] = None