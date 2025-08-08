# routes/api/v0/message_templates.py - Clean implementation

from fastapi import APIRouter, Depends, HTTPException, status, Body, logger
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid

from app.Http.Controllers.MessageTemplateController import MessageTemplateController
from app.Services.MessageTemplateService import MessageTemplateService
from app.Models.auth_models import User
from app.Schemas.message_templates import (
    MessageTemplateCreate, 
    MessageTemplateUpdate, 
    MessageTemplateResponse,
    MessageTemplateFollowupCreate, 
    CreateTemplateWithFollowupsRequest
)
from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission
)
from config.database import get_db

router = APIRouter(prefix="/message-templates", tags=["Message Templates"])

@router.post("/with-followups", response_model=MessageTemplateResponse)
async def create_template_with_followups(
    request: CreateTemplateWithFollowupsRequest,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """
    Create a message template with AI-generated followups
    
    This endpoint creates a main template and optionally generates followup 
    templates using AI services. The operation is atomic - if followup 
    generation fails, the main template is still created.
    """
    try:
        # Validate AI provider
        if request.ai_provider not in ["openai", "gemini"]:
            raise HTTPException(
                status_code=400, 
                detail="ai_provider must be 'openai' or 'gemini'"
            )
        
        # Convert to template data dictionary
        template_data = {
            "subject": request.subject,
            "content": request.content,
            "company_id": request.company_id,
            "campaign_id": request.campaign_id,
            "template_type": request.template_type,
            "is_global": request.is_global
        }
        
        # Use our enhanced service
        template = await MessageTemplateService.create_template_with_followups(
            template_data, 
            current_user, 
            db,
            generate_followups=request.generate_followups,
            ai_provider=request.ai_provider,
            custom_instructions=request.custom_instructions
        )
        
        # Convert to response format
        return MessageTemplateResponse.model_validate(template)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating template with followups: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{template_id}/regenerate-followups", response_model=List[MessageTemplateResponse])
async def regenerate_followups(
    template_id: uuid.UUID,
    ai_provider: Optional[str] = Body(default="openai", description="AI provider: 'openai' or 'gemini' (defaults to OpenAI)"),
    custom_instructions: Optional[str] = Body(default=None, description="Additional AI instructions"),
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """
    Regenerate followup templates for an existing initial template
    
    This will delete existing followups and create new ones using AI.
    """
    try:
        # Default to OpenAI if no provider specified
        if not ai_provider:
            ai_provider = "openai"
            
        if ai_provider not in ["openai", "gemini"]:
            raise HTTPException(
                status_code=400, 
                detail="ai_provider must be 'openai' or 'gemini' (defaults to 'openai')"
            )
        
        followups = await MessageTemplateService.regenerate_followups(
            template_id,
            db,
            ai_provider=ai_provider,
            custom_instructions=custom_instructions
        )
        
        return [MessageTemplateResponse.model_validate(f) for f in followups]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# Standard CRUD endpoints remain unchanged
@router.post("/", response_model=MessageTemplateResponse) 
async def create_template(
    template_data: MessageTemplateCreate,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Create a message template without followups"""
    try:
        template_dict = template_data.model_dump()
        return await MessageTemplateController.create_template(template_dict, current_user, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=List[MessageTemplateResponse])
async def get_all_templates(
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all message templates"""
    return await MessageTemplateController.get_all_templates(db)

@router.get("/campaign/{campaign_id}/with-followups", response_model=List[MessageTemplateResponse])
async def get_campaign_templates_with_followups(
    campaign_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all templates for a campaign including their followups"""
    templates = await MessageTemplateService.get_campaign_templates_with_followups(campaign_id, db)
    return [MessageTemplateResponse.model_validate(t) for t in templates]

@router.get("/campaign/{campaign_id}", response_model=List[MessageTemplateResponse])
async def get_campaign_templates(
    campaign_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all message templates for a specific campaign"""
    return await MessageTemplateController.get_campaign_templates(campaign_id, db)

@router.get("/company/{company_id}", response_model=List[MessageTemplateResponse])
async def get_company_templates(
    company_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all message templates for a specific company"""
    return await MessageTemplateController.get_company_templates(company_id, db)

@router.get("/{template_id}", response_model=MessageTemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get a message template by ID"""
    return await MessageTemplateController.get_template(template_id, db)

@router.put("/{template_id}", response_model=MessageTemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    template_data: MessageTemplateUpdate,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Update a message template"""
    return await MessageTemplateController.update_template(template_id, template_data, db)

@router.delete("/{template_id}")
async def delete_template(
    template_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Delete a message template"""
    return await MessageTemplateController.delete_template(template_id, db)

@router.post("/{template_id}/render")
async def render_template(
    template_id: uuid.UUID,
    context: Dict[str, Any] = Body(...),
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Render a message template with context data"""
    return await MessageTemplateController.render_template(template_id, context, db)