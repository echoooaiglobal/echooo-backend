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

# Import our professional AI service
from app.Services.ThirdParty.services.ai_content_service import AIContentService, AIProvider
from app.Services.ThirdParty.exceptions import ThirdPartyAPIError

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
    async def get_template_by_id(template_id: uuid.UUID, db: Session) -> MessageTemplate:
        """Get template by ID with followups"""
        try:
            template = db.query(MessageTemplate).filter(
                MessageTemplate.id == template_id,
                MessageTemplate.is_deleted == False
            ).first()
            
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Message template not found"
                )
            
            return template
            
        except SQLAlchemyError as e:
            logger.error(f"Error fetching template {template_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching message template"
            ) from e
    
    @staticmethod
    async def get_campaign_templates_with_followups(campaign_id: uuid.UUID, db: Session) -> List[MessageTemplate]:
        """Get all templates for a campaign including followups"""
        try:
            # Get only initial templates (followups will be loaded via relationship)
            templates = db.query(MessageTemplate).filter(
                MessageTemplate.campaign_id == campaign_id,
                MessageTemplate.template_type == "initial",
                MessageTemplate.is_deleted == False
            ).all()
            
            return templates
            
        except SQLAlchemyError as e:
            logger.error(f"Error fetching templates for campaign {campaign_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching campaign templates"
            ) from e

    @staticmethod
    async def regenerate_followups(
        template_id: uuid.UUID,
        db: Session,
        ai_provider: str = "openai",
        custom_instructions: Optional[str] = None
    ) -> List[MessageTemplate]:
        """Regenerate followups for an existing template"""
        try:
            # Get main template
            main_template = await MessageTemplateService.get_template_by_id(template_id, db)
            
            if main_template.template_type != "initial":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Can only regenerate followups for initial templates"
                )
            
            # Delete existing followups
            existing_followups = db.query(MessageTemplate).filter(
                MessageTemplate.parent_template_id == template_id,
                MessageTemplate.is_deleted == False
            ).all()
            
            for followup in existing_followups:
                followup.is_deleted = True
            
            db.commit()
            
            # Generate new followups
            ai_service = AIContentService()
            
            followup_templates = await ai_service.generate_followup_messages(
                original_subject=main_template.subject or "Collaboration Opportunity",
                original_message=main_template.content,
                provider=ai_provider,
                count=5,
                custom_instructions=custom_instructions
            )
            
            # Save new followups
            created_followups = []
            for i, followup in enumerate(followup_templates, 1):
                followup_data = {
                    "content": followup["content"],
                    "subject": followup.get("subject"),
                    "company_id": str(main_template.company_id),
                    "campaign_id": str(main_template.campaign_id),
                    "template_type": "followup",
                    "parent_template_id": str(main_template.id),
                    "followup_sequence": i,
                    "followup_delay_hours": followup["delay_hours"],
                    "is_global": main_template.is_global
                }
                
                # Get user from main template
                followup_template = await MessageTemplateService.create_template(
                    followup_data, main_template.creator, db
                )
                created_followups.append(followup_template)
            
            logger.info(f"✅ Regenerated {len(created_followups)} followup templates")
            return created_followups
            
        except ThirdPartyAPIError as e:
            logger.error(f"AI service error regenerating followups: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI service error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error regenerating followups: {str(e)}")
            raise
    
    @staticmethod
    async def create_template_with_followups(
        template_data: Dict[str, Any],
        user,
        db: Session,
        generate_followups: bool = True,
        ai_provider: str = "openai",
        custom_instructions: Optional[str] = None
    ) -> MessageTemplate:
        """
        Create a message template with AI-generated followups
        
        Args:
            template_data: Template data dictionary
            user: Current user
            db: Database session
            generate_followups: Whether to generate followups
            ai_provider: AI provider to use ("openai", "gemini")
            custom_instructions: Additional instructions for AI
            
        Returns:
            Created main template with followups attached
        """
        
        try:
            # Step 1: Create the main template
            main_template = await MessageTemplateService.create_template(template_data, user, db)
            
            # Step 2: Generate followups if requested and it's an initial template
            if (generate_followups and 
                template_data.get("template_type", "initial") == "initial"):
                
                try:
                    logger.info(f"Generating followups using {ai_provider} for template {main_template.id}")
                    
                    # Use our professional AI service
                    ai_service = AIContentService()
                    
                    followup_templates = await ai_service.generate_followup_messages(
                        original_subject=template_data.get("subject", "Collaboration Opportunity"),
                        original_message=template_data["content"],
                        provider=ai_provider,
                        count=5,
                        custom_instructions=custom_instructions
                    )
                    
                    # Step 3: Save followup templates to database
                    created_followups = []
                    for i, followup in enumerate(followup_templates, 1):
                        followup_data = {
                            "content": followup["content"],
                            "subject": followup.get("subject"),
                            "company_id": template_data["company_id"],
                            "campaign_id": template_data["campaign_id"], 
                            "template_type": "followup",
                            "parent_template_id": str(main_template.id),
                            "followup_sequence": i,
                            "followup_delay_hours": followup["delay_hours"],
                            "is_global": template_data.get("is_global", True)
                        }
                        
                        followup_template = await MessageTemplateService.create_template(
                            followup_data, user, db
                        )
                        created_followups.append(followup_template)
                    
                    logger.info(f"✅ Created {len(created_followups)} followup templates")
                    
                    # Attach followups to main template for response
                    main_template.followup_templates = created_followups
                    
                except ThirdPartyAPIError as ai_error:
                    # Log AI error but don't fail the entire operation
                    logger.warning(f"AI followup generation failed: {str(ai_error)}")
                    logger.warning("Continuing without followups...")
                    
                except Exception as e:
                    # Log unexpected errors but don't fail main template creation
                    logger.error(f"Unexpected error during followup generation: {str(e)}")
                    logger.warning("Continuing without followups...")
            
            return main_template
            
        except Exception as e:
            logger.error(f"Error in create_template_with_followups: {str(e)}")
            raise

    @staticmethod
    async def create_template(template_data: Dict[str, Any], user, db: Session) -> MessageTemplate:
        """Create a single message template"""
        try:
            # Convert string IDs to UUIDs if needed
            if isinstance(template_data.get("company_id"), str):
                template_data["company_id"] = uuid.UUID(template_data["company_id"])
            if isinstance(template_data.get("campaign_id"), str):
                template_data["campaign_id"] = uuid.UUID(template_data["campaign_id"])
            if isinstance(template_data.get("parent_template_id"), str):
                template_data["parent_template_id"] = uuid.UUID(template_data["parent_template_id"])
            
            # Create template
            template = MessageTemplate(
                subject=template_data.get("subject"),
                content=template_data["content"],
                company_id=template_data["company_id"],
                campaign_id=template_data["campaign_id"],
                template_type=template_data.get("template_type", "initial"),
                parent_template_id=template_data.get("parent_template_id"),
                followup_sequence=template_data.get("followup_sequence"),
                followup_delay_hours=template_data.get("followup_delay_hours"),
                is_global=template_data.get("is_global", True),
                created_by=user.id
            )
            
            db.add(template)
            db.commit()
            db.refresh(template)
            
            logger.info(f"Created template: {template.id} ({template.template_type})")
            return template
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error creating template: {str(e)}")
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