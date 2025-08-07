# routes/api/v0/influencer_contacts.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from sqlalchemy import func
from app.Models.influencer_contacts import InfluencerContact
from app.Http.Controllers.InfluencerContactController import InfluencerContactController
from app.Models.auth_models import User
from app.Schemas.influencer_contact import (
    InfluencerContactCreate, InfluencerContactUpdate, InfluencerContactResponse,
    InfluencerContactBulkCreate, InfluencerContactBulkResponse
)
from app.Utils.Helpers import (
    has_role, has_permission
)
from app.Utils.Logger import logger
from config.database import get_db

router = APIRouter(prefix="/influencer-contacts", tags=["Influencer Contacts"])

@router.get("/", response_model=List[InfluencerContactResponse])
async def get_all_contacts(
    skip: int = Query(0, ge=0, description="Number of contacts to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of contacts to return"),
    social_account_id: Optional[str] = Query(None, description="Filter by social account ID"),
    contact_type: Optional[str] = Query(None, description="Filter by contact type (email, phone, whatsapp, etc.)"),
    platform_id: Optional[str] = Query(None, description="Filter by platform ID"),
    is_primary: Optional[bool] = Query(None, description="Filter by primary contact status"),
    current_user: User = Depends(has_permission("influencer_contact:read")),
    db: Session = Depends(get_db)
):
    """
    Get all influencer contacts with optional filtering and pagination
    
    Supports filtering by:
    - social_account_id: Get contacts for a specific social account
    - contact_type: Filter by contact type (email, phone, whatsapp, telegram, discord, other)
    - platform_id: Get contacts for a specific platform
    - is_primary: Filter by primary contact status
    """
    return await InfluencerContactController.get_all_contacts(
        skip=skip,
        limit=limit,
        social_account_id=social_account_id,
        contact_type=contact_type,
        platform_id=platform_id,
        is_primary=is_primary,
        db=db
    )

@router.get("/social-account/{social_account_id}", response_model=List[InfluencerContactResponse])
async def get_contacts_by_social_account(
    social_account_id: uuid.UUID,
    current_user: User = Depends(has_permission("influencer_contact:read")),
    db: Session = Depends(get_db)
):
    """Get all contacts for a specific social account"""
    return await InfluencerContactController.get_contacts_by_social_account(
        social_account_id, db
    )

@router.get("/{contact_id}", response_model=InfluencerContactResponse)
async def get_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(has_permission("influencer_contact:read")),
    db: Session = Depends(get_db)
):
    """Get an influencer contact by ID"""
    return await InfluencerContactController.get_contact_by_id(contact_id, db)

@router.post("/", response_model=InfluencerContactResponse)
async def create_contact(
    contact_data: InfluencerContactCreate,
    current_user: User = Depends(has_permission("influencer_contact:create")),
    db: Session = Depends(get_db)
):
    """
    Create a new influencer contact
    
    Contact types supported:
    - email: Email address
    - phone: Phone number
    - whatsapp: WhatsApp number
    - telegram: Telegram username/handle
    - discord: Discord username/handle
    - other: Other contact methods
    
    Example:
    ```json
    {
        "social_account_id": "uuid-here",
        "contact_type": "email",
        "contact_value": "influencer@example.com",
        "name": "Business Manager",
        "is_primary": true,
        "platform_specific": false
    }
    ```
    """
    return await InfluencerContactController.create_contact(contact_data, db)

@router.post("/bulk", response_model=InfluencerContactBulkResponse)
async def bulk_create_contacts(
    bulk_data: InfluencerContactBulkCreate,
    current_user: User = Depends(has_permission("influencer_contact:create")),
    db: Session = Depends(get_db)
):
    """
    Create multiple contacts for a social account in a single API call
    
    Example:
    ```json
    {
        "social_account_id": "uuid-here",
        "contacts": [
            {
                "contact_type": "email",
                "contact_value": "manager@example.com",
                "name": "Business Manager",
                "is_primary": true
            },
            {
                "contact_type": "phone",
                "contact_value": "+1234567890",
                "name": "Personal Phone",
                "is_primary": false
            }
        ]
    }
    ```
    """
    return await InfluencerContactController.bulk_create_contacts(bulk_data, db)

@router.put("/{contact_id}", response_model=InfluencerContactResponse)
async def update_contact(
    contact_id: uuid.UUID,
    contact_data: InfluencerContactUpdate,
    current_user: User = Depends(has_permission("influencer_contact:update")),
    db: Session = Depends(get_db)
):
    """
    Update an influencer contact
    
    You can update any field of the contact. When setting is_primary=true,
    other contacts of the same type for the same social account will automatically
    be set to is_primary=false.
    """
    return await InfluencerContactController.update_contact(
        contact_id, contact_data, db
    )

@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(has_permission("influencer_contact:delete")),
    db: Session = Depends(get_db)
):
    """Delete an influencer contact"""
    return await InfluencerContactController.delete_contact(contact_id, db)

# Additional utility endpoints

@router.get("/types/list")
async def get_contact_types(
    current_user: User = Depends(has_permission("influencer_contact:read")),
    db: Session = Depends(get_db)
):
    """Get list of supported contact types"""
    from app.Schemas.influencer_contact import VALID_CONTACT_TYPES
    
    return {
        "contact_types": [
            {
                "value": contact_type,
                "label": contact_type.title(),
                "description": {
                    "email": "Email address for business communications",
                    "phone": "Primary phone number",
                    "whatsapp": "WhatsApp number for messaging",
                    "telegram": "Telegram username or handle",
                    "discord": "Discord username or handle",
                    "other": "Other contact methods"
                }.get(contact_type, f"{contact_type.title()} contact")
            }
            for contact_type in VALID_CONTACT_TYPES
        ]
    }

@router.get("/social-account/{social_account_id}/primary", response_model=List[InfluencerContactResponse])
async def get_primary_contacts(
    social_account_id: uuid.UUID,
    current_user: User = Depends(has_permission("influencer_contact:read")),
    db: Session = Depends(get_db)
):
    """Get all primary contacts for a specific social account"""
    return await InfluencerContactController.get_all_contacts(
        skip=0,
        limit=100,
        social_account_id=str(social_account_id),
        is_primary=True,
        db=db
    )

@router.get("/social-account/{social_account_id}/type/{contact_type}", response_model=List[InfluencerContactResponse])
async def get_contacts_by_type(
    social_account_id: uuid.UUID,
    contact_type: str,
    current_user: User = Depends(has_permission("influencer_contact:read")),
    db: Session = Depends(get_db)
):
    """Get all contacts of a specific type for a social account"""
    # Validate contact type
    from app.Schemas.influencer_contact import VALID_CONTACT_TYPES
    if contact_type.lower() not in VALID_CONTACT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid contact type. Must be one of: {', '.join(VALID_CONTACT_TYPES)}"
        )
    
    return await InfluencerContactController.get_all_contacts(
        skip=0,
        limit=100,
        social_account_id=str(social_account_id),
        contact_type=contact_type.lower(),
        db=db
    )

@router.post("/social-account/{social_account_id}/set-primary/{contact_id}")
async def set_primary_contact(
    social_account_id: uuid.UUID,
    contact_id: uuid.UUID,
    current_user: User = Depends(has_permission("influencer_contact:update")),
    db: Session = Depends(get_db)
):
    """
    Set a contact as the primary contact for its type
    
    This will automatically unset any other primary contacts of the same type
    for the same social account.
    """
    # First get the contact to verify it belongs to the social account
    contact = await InfluencerContactController.get_contact_by_id(contact_id, db)
    
    if str(contact.social_account_id) != str(social_account_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contact does not belong to the specified social account"
        )
    
    # Update the contact to be primary
    from app.Schemas.influencer_contact import InfluencerContactUpdate
    update_data = InfluencerContactUpdate(is_primary=True)
    
    return await InfluencerContactController.update_contact(
        contact_id, update_data, db
    )

# Statistics endpoints for admin/analytics

@router.get("/stats/overview")
async def get_contacts_stats(
    current_user: User = Depends(has_role(["platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
):
    """Get overview statistics for influencer contacts (admin only)"""
    try:
        
        # Total contacts
        total_contacts = db.query(InfluencerContact).count()
        
        # Contacts by type
        contacts_by_type = db.query(
            InfluencerContact.contact_type,
            func.count(InfluencerContact.id).label('count')
        ).group_by(InfluencerContact.contact_type).all()
        
        # Primary contacts count
        primary_contacts = db.query(InfluencerContact).filter(
            InfluencerContact.is_primary == True
        ).count()
        
        # Platform-specific contacts count
        platform_specific_contacts = db.query(InfluencerContact).filter(
            InfluencerContact.platform_specific == True
        ).count()
        
        return {
            "total_contacts": total_contacts,
            "primary_contacts": primary_contacts,
            "platform_specific_contacts": platform_specific_contacts,
            "contacts_by_type": [
                {"type": contact_type, "count": count}
                for contact_type, count in contacts_by_type
            ]
        }
    except Exception as e:
        logger.error(f"Error getting contacts stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving contact statistics"
        )