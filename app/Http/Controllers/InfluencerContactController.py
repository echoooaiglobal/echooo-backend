# app/Http/Controllers/InfluencerContactController.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid
from app.Schemas.influencer_contact import (
    InfluencerContactCreate, InfluencerContactUpdate, InfluencerContactResponse,
    SocialAccountBrief, PlatformBrief, RoleBrief,
    InfluencerContactBulkCreate, InfluencerContactBulkResponse
)
from app.Services.InfluencerContactService import InfluencerContactService
from app.Utils.Logger import logger

class InfluencerContactController:
    """Controller for influencer contact-related endpoints"""
    
    @staticmethod
    async def get_all_contacts(
        skip: int = 0,
        limit: int = 100,
        social_account_id: Optional[str] = None,
        contact_type: Optional[str] = None,
        platform_id: Optional[str] = None,
        is_primary: Optional[bool] = None,
        db: Session = None
    ):
        """Get all influencer contacts with optional filtering"""
        try:
            # Convert string UUIDs to UUID objects
            social_account_uuid = uuid.UUID(social_account_id) if social_account_id else None
            platform_uuid = uuid.UUID(platform_id) if platform_id else None
            
            contacts = await InfluencerContactService.get_all_contacts(
                db=db,
                skip=skip,
                limit=limit,
                social_account_id=social_account_uuid,
                contact_type=contact_type,
                platform_id=platform_uuid,
                is_primary=is_primary
            )
            
            return [
                InfluencerContactController._format_contact_response(contact)
                for contact in contacts
            ]
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid UUID format: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error in get_all_contacts controller: {str(e)}")
            raise

    @staticmethod
    async def get_contact_by_id(contact_id: uuid.UUID, db: Session):
        """Get an influencer contact by ID"""
        try:
            contact = await InfluencerContactService.get_contact_by_id(contact_id, db)
            return InfluencerContactController._format_contact_response(contact)
        except Exception as e:
            logger.error(f"Error in get_contact_by_id controller: {str(e)}")
            raise

    @staticmethod
    async def get_contacts_by_social_account(social_account_id: uuid.UUID, db: Session):
        """Get all contacts for a specific social account"""
        try:
            contacts = await InfluencerContactService.get_contacts_by_social_account(social_account_id, db)
            return [
                InfluencerContactController._format_contact_response(contact)
                for contact in contacts
            ]
        except Exception as e:
            logger.error(f"Error in get_contacts_by_social_account controller: {str(e)}")
            raise

    @staticmethod
    async def create_contact(contact_data: InfluencerContactCreate, db: Session):
        """Create a new influencer contact"""
        try:
            contact_dict = contact_data.model_dump(exclude_unset=True)
            
            # Convert string UUIDs to UUID objects
            if 'social_account_id' in contact_dict:
                contact_dict['social_account_id'] = uuid.UUID(contact_dict['social_account_id'])
            if 'platform_id' in contact_dict and contact_dict['platform_id']:
                contact_dict['platform_id'] = uuid.UUID(contact_dict['platform_id'])
            if 'role_id' in contact_dict and contact_dict['role_id']:
                contact_dict['role_id'] = uuid.UUID(contact_dict['role_id'])
            
            contact = await InfluencerContactService.create_contact(contact_dict, db)
            return InfluencerContactController._format_contact_response(contact)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid UUID format: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error in create_contact controller: {str(e)}")
            raise

    @staticmethod
    async def update_contact(
        contact_id: uuid.UUID,
        contact_data: InfluencerContactUpdate,
        db: Session
    ):
        """Update an influencer contact"""
        try:
            update_dict = contact_data.model_dump(exclude_unset=True)
            
            # Convert string UUIDs to UUID objects
            if 'platform_id' in update_dict and update_dict['platform_id']:
                update_dict['platform_id'] = uuid.UUID(update_dict['platform_id'])
            if 'role_id' in update_dict and update_dict['role_id']:
                update_dict['role_id'] = uuid.UUID(update_dict['role_id'])
            
            contact = await InfluencerContactService.update_contact(contact_id, update_dict, db)
            return InfluencerContactController._format_contact_response(contact)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid UUID format: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error in update_contact controller: {str(e)}")
            raise

    @staticmethod
    async def delete_contact(contact_id: uuid.UUID, db: Session):
        """Delete an influencer contact"""
        try:
            await InfluencerContactService.delete_contact(contact_id, db)
            return {"message": "Contact deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_contact controller: {str(e)}")
            raise

    @staticmethod
    async def bulk_create_contacts(
        bulk_data: InfluencerContactBulkCreate,
        db: Session
    ):
        """Create multiple contacts for a social account"""
        try:
            social_account_id = uuid.UUID(bulk_data.social_account_id)
            
            # Convert contact data to dictionaries
            contacts_data = []
            for contact in bulk_data.contacts:
                contact_dict = contact.model_dump(exclude_unset=True)
                
                # Convert UUIDs
                if 'platform_id' in contact_dict and contact_dict['platform_id']:
                    contact_dict['platform_id'] = uuid.UUID(contact_dict['platform_id'])
                if 'role_id' in contact_dict and contact_dict['role_id']:
                    contact_dict['role_id'] = uuid.UUID(contact_dict['role_id'])
                
                contacts_data.append(contact_dict)
            
            result = await InfluencerContactService.bulk_create_contacts(
                social_account_id, contacts_data, db
            )
            
            # Format responses
            formatted_created = [
                InfluencerContactController._format_contact_response(contact)
                for contact in result["created_contacts"]
            ]
            
            return InfluencerContactBulkResponse(
                created_contacts=formatted_created,
                failed_contacts=result["failed_contacts"]
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid UUID format: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error in bulk_create_contacts controller: {str(e)}")
            raise

    @staticmethod
    def _format_contact_response(contact):
        """Format a contact object into a consistent response"""
        response = InfluencerContactResponse.model_validate(contact)
        
        # Add social account details if available
        if contact.social_account:
            response.social_account = SocialAccountBrief.model_validate(contact.social_account)
        
        # Add platform details if available
        if contact.platform:
            response.platform = PlatformBrief.model_validate(contact.platform)
        
        # Add role details if available
        if contact.role:
            response.role = RoleBrief.model_validate(contact.role)
        
        return response