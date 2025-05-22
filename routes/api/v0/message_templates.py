# routes/api/v0/message_templates.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

from app.Http.Controllers.MessageTemplateController import MessageTemplateController
from app.Models.auth_models import User
from app.Schemas.campaign import MessageTemplateCreate, MessageTemplateUpdate, MessageTemplateResponse
from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission
)
from config.database import get_db

router = APIRouter(prefix="/message-templates", tags=["Message Templates"])

@router.get("/", response_model=List[MessageTemplateResponse])
async def get_all_templates(
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all message templates"""
    return await MessageTemplateController.get_all_templates(db)

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

@router.post("/", response_model=MessageTemplateResponse)
async def create_template(
    template_data: MessageTemplateCreate,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Create a new message template"""
    return await MessageTemplateController.create_template(template_data, current_user, db)

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