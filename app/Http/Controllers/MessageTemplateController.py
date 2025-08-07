# app/Http/Controllers/MessageTemplateController.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import uuid

from app.Models.auth_models import User
from app.Schemas.message_templates import MessageTemplateUpdate, MessageTemplateResponse
from app.Services.MessageTemplateService import MessageTemplateService
from app.Utils.Logger import logger

class MessageTemplateController:
    """Controller for message template-related endpoints"""
    
    @staticmethod
    async def get_all_templates(db: Session):
        """Get all message templates"""
        try:
            templates = await MessageTemplateService.get_all_templates(db)
            return [MessageTemplateResponse.model_validate(template) for template in templates]
        except Exception as e:
            logger.error(f"Error in get_all_templates controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_campaign_templates(campaign_id: uuid.UUID, db: Session):
        """Get all message templates for a specific campaign"""
        try:
            templates = await MessageTemplateService.get_campaign_templates(campaign_id, db)
            return [MessageTemplateResponse.model_validate(template) for template in templates]
        except Exception as e:
            logger.error(f"Error in get_campaign_templates controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_company_templates(company_id: uuid.UUID, db: Session):
        """Get all message templates for a specific company"""
        try:
            templates = await MessageTemplateService.get_company_templates(company_id, db)
            return [MessageTemplateResponse.model_validate(template) for template in templates]
        except Exception as e:
            logger.error(f"Error in get_company_templates controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_template(template_id: uuid.UUID, db: Session):
        """Get a message template by ID"""
        try:
            template = await MessageTemplateService.get_template_by_id(template_id, db)
            return MessageTemplateResponse.model_validate(template)
        except Exception as e:
            logger.error(f"Error in get_template controller: {str(e)}")
            raise
    
    @staticmethod
    async def create_template(
        template_data: Dict[str, Any],
        current_user: User,
        db: Session
    ) -> MessageTemplateResponse:
        """Create a new message template"""
        try:
            # Service now only creates the template, no assignment logic
            template = await MessageTemplateService.create_template(template_data, current_user.id, db)
            
            # Convert SQLAlchemy object to Pydantic response model
            return MessageTemplateResponse.model_validate(template)
            
        except HTTPException:
            # Re-raise HTTP exceptions from service
            raise
        except Exception as e:
            logger.error(f"Error in create_template controller: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating message template"
            )
    
    @staticmethod
    async def update_template(
        template_id: uuid.UUID,
        template_data: MessageTemplateUpdate,
        db: Session
    ):
        """Update a message template"""
        try:
            template = await MessageTemplateService.update_template(
                template_id,
                template_data.model_dump(exclude_unset=True),
                db
            )
            return MessageTemplateResponse.model_validate(template)
        except Exception as e:
            logger.error(f"Error in update_template controller: {str(e)}")
            raise
    
    @staticmethod
    async def delete_template(template_id: uuid.UUID, db: Session):
        """Delete a message template"""
        try:
            await MessageTemplateService.delete_template(template_id, db)
            return {"message": "Message template deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_template controller: {str(e)}")
            raise
    
    @staticmethod
    async def render_template(template_id: uuid.UUID, context: Dict[str, Any], db: Session):
        """Render a message template with context data"""
        try:
            rendered_content = await MessageTemplateService.render_template(template_id, context, db)
            return {"rendered_content": rendered_content}
        except Exception as e:
            logger.error(f"Error in render_template controller: {str(e)}")
            raise