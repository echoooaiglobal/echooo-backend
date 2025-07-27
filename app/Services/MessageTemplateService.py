# app/Services/MessageTemplateService.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
import uuid

from app.Models.campaigns import Campaign
from app.Models.agent_assignments import AgentAssignment
from app.Models.campaign_lists import CampaignList
from app.Models.outreach_agents import OutreachAgent
from app.Models.message_templates import MessageTemplate
from app.Models.company_models import Company
from app.Utils.Logger import logger
from app.Models.statuses import Status

class MessageTemplateService:
    """Service for managing message templates"""

    @staticmethod
    async def get_all_templates(db: Session):
        """
        Get all message templates
        
        Args:
            db: Database session
            
        Returns:
            List[MessageTemplate]: List of all message templates
        """
        return db.query(MessageTemplate).all()
    
    @staticmethod
    async def get_campaign_templates(campaign_id: uuid.UUID, db: Session):
        """
        Get all message templates for a specific campaign
        
        Args:
            campaign_id: ID of the campaign
            db: Database session
            
        Returns:
            List[MessageTemplate]: List of campaign message templates
        """
        # Verify campaign exists
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        return db.query(MessageTemplate).filter(
            MessageTemplate.campaign_id == campaign_id
        ).all()
    
    @staticmethod
    async def get_company_templates(company_id: uuid.UUID, db: Session):
        """
        Get all message templates for a specific company
        
        Args:
            company_id: ID of the company
            db: Database session
            
        Returns:
            List[MessageTemplate]: List of company message templates
        """
        # Verify company exists
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        return db.query(MessageTemplate).filter(
            MessageTemplate.company_id == company_id
        ).all()
    
    @staticmethod
    async def get_template_by_id(template_id: uuid.UUID, db: Session):
        """
        Get a message template by ID
        
        Args:
            template_id: ID of the message template
            db: Database session
            
        Returns:
            MessageTemplate: The message template if found
        """
        template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message template not found"
            )
            
        return template
    
    @staticmethod
    async def create_template(template_data: Dict[str, Any], created_by: uuid.UUID, db: Session):
        """
        Create a new message template
        
        Args:
            template_data: Template data dictionary
            created_by: ID of the user creating the template
            db: Database session
            
        Returns:
            MessageTemplate: The created message template object
        """
        try:
            # Set creator
            template_data['created_by'] = created_by
            
            # Verify company exists
            company_id = template_data.get('company_id')
            if company_id:
                company = db.query(Company).filter(Company.id == company_id).first()
                if not company:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Company not found"
                    )
            
            # Verify campaign exists
            campaign_id = template_data.get('campaign_id')
            if campaign_id:
                campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
                if not campaign:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Campaign not found"
                    )
            
            # Validate parent template exists for follow-ups
            parent_template_id = template_data.get('parent_template_id')
            if parent_template_id:
                parent_template = db.query(MessageTemplate).filter(
                    MessageTemplate.id == parent_template_id
                ).first()
                if not parent_template:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Parent template not found"
                    )
            
            # Create the message template
            new_template = MessageTemplate(**template_data)
            db.add(new_template)
            db.commit()
            db.refresh(new_template)
            
            logger.info(f"Message template created successfully: {new_template.id}")
            return new_template
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error creating message template: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error creating message template"
            ) from e
        except HTTPException:
            # Re-raise HTTP exceptions (like 404 for company/campaign not found)
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error creating message template: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating message template"
            ) from e
    
    @staticmethod
    async def update_template(template_id: uuid.UUID, update_data: Dict[str, Any], db: Session):
        """
        Update a message template
        
        Args:
            template_id: ID of the message template
            update_data: Data to update
            db: Database session
            
        Returns:
            MessageTemplate: The updated message template
        """
        try:
            template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
            
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Message template not found"
                )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(template, key) and value is not None:
                    setattr(template, key, value)
            
            db.commit()
            db.refresh(template)
            
            return template
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating message template: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating message template"
            ) from e
    
    @staticmethod
    async def delete_template(template_id: uuid.UUID, db: Session):
        """
        Delete a message template
        
        Args:
            template_id: ID of the message template
            db: Database session
            
        Returns:
            bool: True if successful
        """
        try:
            template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
            
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Message template not found"
                )
            
            # Check if template is used by any influencer lists
            lists_using_template = db.query(CampaignList).filter(
                CampaignList.message_template_id == template_id
            ).count()
            
            if lists_using_template > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete template that is being used by {lists_using_template} influencer lists"
                )
            
            db.delete(template)
            db.commit()
            
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting message template: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting message template"
            ) from e
    
    @staticmethod
    async def render_template(template_id: uuid.UUID, context: Dict[str, Any], db: Session):
        """
        Render a message template with context data
        
        Args:
            template_id: ID of the message template
            context: Context data for rendering
            db: Database session
            
        Returns:
            str: The rendered message
        """
        try:
            template = await MessageTemplateService.get_template_by_id(template_id, db)
            
            # Simple placeholder replacement - you could use a more sophisticated template engine like Jinja2
            content = template.content
            
            # Replace placeholders in format {{variable}}
            import re
            for match in re.finditer(r'{{(.*?)}}', content):
                placeholder = match.group(0)
                variable_path = match.group(1).strip()
                
                # Navigate nested objects using the path
                parts = variable_path.split('.')
                value = context
                for part in parts:
                    if part in value:
                        value = value[part]
                    else:
                        # If path not found, leave placeholder unchanged
                        value = placeholder
                        break
                
                # Replace placeholder with value
                if value != placeholder:
                    content = content.replace(placeholder, str(value))
            
            return content
        except Exception as e:
            logger.error(f"Error rendering template: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error rendering template"
            ) from e