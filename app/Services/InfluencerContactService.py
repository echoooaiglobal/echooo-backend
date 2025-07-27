# app/Services/InfluencerContactService.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
import uuid

from app.Models.influencer_contacts import InfluencerContact
from app.Models.social_accounts import SocialAccount
from app.Models.platforms import Platform
from app.Models.auth_models import Role
from app.Utils.Logger import logger

class InfluencerContactService:
    """Service for managing influencer contacts"""

    @staticmethod
    async def get_all_contacts(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        social_account_id: Optional[uuid.UUID] = None,
        contact_type: Optional[str] = None,
        platform_id: Optional[uuid.UUID] = None,
        is_primary: Optional[bool] = None
    ):
        """
        Get all influencer contacts with optional filtering
        """
        try:
            # Base query with eager loading
            query = db.query(InfluencerContact).options(
                joinedload(InfluencerContact.social_account),
                joinedload(InfluencerContact.platform),
                joinedload(InfluencerContact.role)
            )
            
            # Apply filters
            if social_account_id:
                query = query.filter(InfluencerContact.social_account_id == social_account_id)
            
            if contact_type:
                query = query.filter(InfluencerContact.contact_type == contact_type.lower())
            
            if platform_id:
                query = query.filter(InfluencerContact.platform_id == platform_id)
            
            if is_primary is not None:
                query = query.filter(InfluencerContact.is_primary == is_primary)
            
            # Apply pagination
            contacts = query.offset(skip).limit(limit).all()
            
            return contacts
        except Exception as e:
            logger.error(f"Error fetching influencer contacts: {str(e)}")
            raise

    @staticmethod
    async def get_contact_by_id(contact_id: uuid.UUID, db: Session):
        """
        Get an influencer contact by ID
        """
        try:
            contact = db.query(InfluencerContact).options(
                joinedload(InfluencerContact.social_account),
                joinedload(InfluencerContact.platform),
                joinedload(InfluencerContact.role)
            ).filter(InfluencerContact.id == contact_id).first()
            
            if not contact:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Influencer contact not found"
                )
            
            return contact
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching contact by ID: {str(e)}")
            raise

    @staticmethod
    async def get_contacts_by_social_account(social_account_id: uuid.UUID, db: Session):
        """
        Get all contacts for a specific social account
        """
        try:
            # Verify social account exists
            social_account = db.query(SocialAccount).filter(SocialAccount.id == social_account_id).first()
            if not social_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Social account not found"
                )
            
            contacts = db.query(InfluencerContact).options(
                joinedload(InfluencerContact.social_account),
                joinedload(InfluencerContact.platform),
                joinedload(InfluencerContact.role)
            ).filter(InfluencerContact.social_account_id == social_account_id).all()
            
            return contacts
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching contacts by social account: {str(e)}")
            raise

    @staticmethod
    async def create_contact(contact_data: Dict[str, Any], db: Session):
        """
        Create a new influencer contact
        """
        try:
            # Verify social account exists
            social_account_id = contact_data.get('social_account_id')
            if social_account_id:
                social_account = db.query(SocialAccount).filter(
                    SocialAccount.id == social_account_id
                ).first()
                if not social_account:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Social account not found"
                    )
            
            # Verify platform exists if provided
            platform_id = contact_data.get('platform_id')
            if platform_id:
                platform = db.query(Platform).filter(Platform.id == platform_id).first()
                if not platform:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Platform not found"
                    )
            
            # Verify role exists if provided
            role_id = contact_data.get('role_id')
            if role_id:
                role = db.query(Role).filter(Role.id == role_id).first()
                if not role:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Role not found"
                    )
            
            # Check for duplicate contact (same social account + contact type + contact value)
            existing_contact = db.query(InfluencerContact).filter(
                InfluencerContact.social_account_id == social_account_id,
                InfluencerContact.contact_type == contact_data.get('contact_type', '').lower(),
                InfluencerContact.contact_value == contact_data.get('contact_value')
            ).first()
            
            if existing_contact:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Contact with this type and value already exists for this social account"
                )
            
            # If this is marked as primary, unset other primary contacts of the same type
            if contact_data.get('is_primary', False):
                await InfluencerContactService._unset_primary_contacts(
                    social_account_id, 
                    contact_data.get('contact_type', '').lower(),
                    db
                )
            
            # Create contact
            contact = InfluencerContact(**contact_data)
            db.add(contact)
            db.commit()
            db.refresh(contact)
            
            # Load relationships for response
            contact = await InfluencerContactService.get_contact_by_id(contact.id, db)
            
            return contact
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating influencer contact: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating influencer contact"
            ) from e

    @staticmethod
    async def update_contact(contact_id: uuid.UUID, update_data: Dict[str, Any], db: Session):
        """
        Update an influencer contact
        """
        try:
            contact = db.query(InfluencerContact).filter(InfluencerContact.id == contact_id).first()
            
            if not contact:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Influencer contact not found"
                )
            
            # Verify platform exists if being updated
            platform_id = update_data.get('platform_id')
            if platform_id:
                platform = db.query(Platform).filter(Platform.id == platform_id).first()
                if not platform:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Platform not found"
                    )
            
            # Verify role exists if being updated
            role_id = update_data.get('role_id')
            if role_id:
                role = db.query(Role).filter(Role.id == role_id).first()
                if not role:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Role not found"
                    )
            
            # Check for duplicate if contact type or value is being updated
            if 'contact_type' in update_data or 'contact_value' in update_data:
                new_type = update_data.get('contact_type', contact.contact_type).lower()
                new_value = update_data.get('contact_value', contact.contact_value)
                
                existing_contact = db.query(InfluencerContact).filter(
                    InfluencerContact.social_account_id == contact.social_account_id,
                    InfluencerContact.contact_type == new_type,
                    InfluencerContact.contact_value == new_value,
                    InfluencerContact.id != contact_id
                ).first()
                
                if existing_contact:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Contact with this type and value already exists for this social account"
                    )
            
            # If setting as primary, unset other primary contacts of the same type
            if update_data.get('is_primary', False) and not contact.is_primary:
                contact_type = update_data.get('contact_type', contact.contact_type).lower()
                await InfluencerContactService._unset_primary_contacts(
                    contact.social_account_id, 
                    contact_type,
                    db,
                    exclude_contact_id=contact_id
                )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(contact, key) and value is not None:
                    if key == 'contact_type':
                        setattr(contact, key, value.lower())
                    else:
                        setattr(contact, key, value)
            
            db.commit()
            db.refresh(contact)
            
            # Load relationships for response
            contact = await InfluencerContactService.get_contact_by_id(contact.id, db)
            
            return contact
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating influencer contact: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating influencer contact"
            ) from e

    @staticmethod
    async def delete_contact(contact_id: uuid.UUID, db: Session):
        """
        Delete an influencer contact
        """
        try:
            contact = db.query(InfluencerContact).filter(InfluencerContact.id == contact_id).first()
            
            if not contact:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Influencer contact not found"
                )
            
            db.delete(contact)
            db.commit()
            
            return True
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting influencer contact: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting influencer contact"
            ) from e

    @staticmethod
    async def bulk_create_contacts(social_account_id: uuid.UUID, contacts_data: List[Dict[str, Any]], db: Session):
        """
        Create multiple contacts for a social account
        """
        try:
            # Verify social account exists
            social_account = db.query(SocialAccount).filter(SocialAccount.id == social_account_id).first()
            if not social_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Social account not found"
                )
            
            created_contacts = []
            failed_contacts = []
            
            for contact_data in contacts_data:
                try:
                    contact_data['social_account_id'] = str(social_account_id)
                    contact = await InfluencerContactService.create_contact(contact_data, db)
                    created_contacts.append(contact)
                except Exception as e:
                    failed_contacts.append({
                        "contact_data": contact_data,
                        "error": str(e)
                    })
                    logger.warning(f"Failed to create contact: {str(e)}")
            
            return {
                "created_contacts": created_contacts,
                "failed_contacts": failed_contacts
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in bulk contact creation: {str(e)}")
            raise

    @staticmethod
    async def _unset_primary_contacts(
        social_account_id: uuid.UUID, 
        contact_type: str, 
        db: Session,
        exclude_contact_id: Optional[uuid.UUID] = None
    ):
        """
        Unset primary flag for existing contacts of the same type
        """
        try:
            query = db.query(InfluencerContact).filter(
                InfluencerContact.social_account_id == social_account_id,
                InfluencerContact.contact_type == contact_type,
                InfluencerContact.is_primary == True
            )
            
            if exclude_contact_id:
                query = query.filter(InfluencerContact.id != exclude_contact_id)
            
            primary_contacts = query.all()
            
            for contact in primary_contacts:
                contact.is_primary = False
            
            db.flush()  # Flush changes without committing
        except Exception as e:
            logger.error(f"Error unsetting primary contacts: {str(e)}")
            raise