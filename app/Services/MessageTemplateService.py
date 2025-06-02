# app/Services/MessageTemplateService.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
import uuid

from app.Models.campaign_models import Campaign
from app.Models.message_templates import MessageTemplate
from app.Models.company_models import Company
from app.Utils.Logger import logger

from app.Models.campaign_models import CampaignList, Status, Agent, ListAssignment

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
        Create a new message template and optionally assign agent to list
        
        Args:
            template_data: Template data (can include auto_assign_agent: bool)
            created_by: ID of the user creating the template
            db: Database session
            
        Returns:
            Dict: The created message template and assignment info
        """
        try:
            # Set creator
            template_data['created_by'] = created_by
            
            # Extract auto_assign_agent flag (for "Start Outreach" flow)
            auto_assign_agent = template_data.pop('auto_assign_agent', False)
            target_list_id = template_data.pop('target_list_id', None)
            
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
            campaign = None
            if campaign_id:
                campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
                if not campaign:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Campaign not found"
                    )
                
                # Verify campaign belongs to company
                if campaign.company_id != uuid.UUID(company_id):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Campaign does not belong to the specified company"
                    )
            
            # Create template
            template = MessageTemplate(**template_data)
            db.add(template)
            db.flush()  # Get template ID without committing
            
            assignment_info = None
            
            # If auto_assign_agent is True, create list assignment
            if auto_assign_agent and campaign:
                assignment_info = await MessageTemplateService._create_auto_assignment(
                    campaign, target_list_id, template.id, db
                )
            
            db.commit()
            db.refresh(template)
            
            # Return both template and assignment info
            result = {
                "template": template,
                "assignment": assignment_info
            }
            
            return result
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating message template: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating message template"
            ) from e
    
    @staticmethod
    async def _create_auto_assignment(campaign: Campaign, target_list_id: Optional[uuid.UUID], template_id: uuid.UUID, db: Session):
        """
        Automatically assign an available agent to a campaign list
        
        Args:
            campaign: Campaign object
            target_list_id: Specific list ID (optional)
            template_id: Created template ID
            db: Database session
            
        Returns:
            Dict: Assignment information
        """
        try:
            # Find the target list
            if target_list_id:
                # Use specific list
                target_list = db.query(CampaignList).filter(
                    CampaignList.id == target_list_id,
                    CampaignList.campaign_id == campaign.id
                ).first()
            else:
                # Use the first/default list of the campaign
                target_list = db.query(CampaignList).filter(
                    CampaignList.campaign_id == campaign.id
                ).first()
            
            if not target_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No influencer list found for this campaign"
                )
            
            # Update the list to use the new message template
            target_list.message_template_id = template_id
            
            # Find an available agent for the primary platform of the campaign
            # (You might need to determine platform based on list members or campaign settings)
            available_agent = db.query(Agent).filter(
                Agent.is_available == True,
                Agent.current_assignment_id == None
            ).first()
            
            if not available_agent:
                logger.warning("No available agents found for auto-assignment")
                return {
                    "status": "template_created",
                    "message": "Template created but no available agents for assignment",
                    "list_id": str(target_list.id),
                    "assignment_id": None
                }
            
            # Get pending status for assignment
            pending_status = db.query(Status).filter(
                Status.model == "list_assignment",
                Status.name == "pending"
            ).first()
            
            if not pending_status:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Pending status not found for list assignments"
                )
            
            # Create the assignment
            assignment = ListAssignment(
                list_id=target_list.id,
                agent_id=available_agent.id,
                status_id=pending_status.id
            )
            
            db.add(assignment)
            db.flush()  # Get assignment ID
            
            # Update agent status
            available_agent.current_assignment_id = assignment.id
            available_agent.is_available = False
            
            return {
                "status": "assigned",
                "message": "Template created and agent assigned successfully",
                "list_id": str(target_list.id),
                "assignment_id": str(assignment.id),
                "agent_id": str(available_agent.id),
                "agent_name": available_agent.name
            }
            
        except Exception as e:
            logger.error(f"Error in auto-assignment: {str(e)}")
            # Don't fail the template creation if assignment fails
            return {
                "status": "template_created",
                "message": f"Template created but assignment failed: {str(e)}",
                "list_id": str(target_list.id) if 'target_list' in locals() else None,
                "assignment_id": None
            }
    
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
            from app.Models.campaign_models import CampaignList
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