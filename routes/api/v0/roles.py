# routes/api/v0/roles.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.Http.Controllers.RoleController import RoleController
from app.Models.auth_models import User
from app.Schemas.role import (
    RoleCreate, RoleUpdate, RoleResponse, RoleDetailResponse,
    PermissionResponse, RolePermissionUpdate
)
from app.Utils.Helpers import has_role
from config.database import get_db

router = APIRouter(prefix="/roles", tags=["Roles & Permissions"])

@router.get("/", response_model=List[RoleDetailResponse])
async def get_all_roles(
    user_type: Optional[str] = Query(None, description="Filter roles by user type (platform, b2c, influencer)"),
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """
    Get all roles with their permissions, optionally filtered by user type
    
    Query Parameters:
    - user_type: Filter roles by user type (platform, b2c, influencer)
      - platform: Returns roles like platform_admin, platform_user, platform_manager, etc.
      - b2c: Returns roles like b2c_company_admin, b2c_campaign_manager, b2c_marketing_director, etc.
      - influencer: Returns roles like influencer, influencer_manager
    """
    if user_type:
        # Validate user_type
        valid_user_types = ["platform", "b2c", "influencer"]
        if user_type.lower() not in valid_user_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user_type. Must be one of: {', '.join(valid_user_types)}"
            )
        return await RoleController.get_roles_by_user_type(user_type.lower(), db)
    
    return await RoleController.get_all_roles(db)

@router.get("/by-type/{user_type}", response_model=List[RoleDetailResponse])
async def get_roles_by_user_type(
    user_type: str,
    current_user: User = Depends(has_role(["platform_admin", "platform_manager", "platform_agent"])),
    db: Session = Depends(get_db)
):
    """
    Get roles specific to a user type
    
    Path Parameters:
    - user_type: The user type (platform, b2c, influencer)
    
    Returns roles filtered by naming convention:
    - platform: platform_admin, platform_user, platform_manager, etc.
    - b2c: b2c_company_admin, b2c_campaign_manager, b2c_marketing_director, etc.
    - influencer: influencer, influencer_manager
    """
    valid_user_types = ["platform", "b2c", "influencer"]
    if user_type.lower() not in valid_user_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user_type. Must be one of: {', '.join(valid_user_types)}"
        )
    
    return await RoleController.get_roles_by_user_type(user_type.lower(), db)

@router.get("/user-types/list")
async def get_user_types(
    current_user: User = Depends(has_role(["platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
):
    """Get list of available user types and their role counts"""
    return await RoleController.get_user_types_with_role_counts(db)

@router.get("/permissions", response_model=List[PermissionResponse])
async def get_all_permissions(
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Get all available permissions"""
    return await RoleController.get_all_permissions(db)

@router.get("/{role_id}", response_model=RoleDetailResponse)
async def get_role(
    role_id: uuid.UUID,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Get a role by ID with its permissions"""
    return await RoleController.get_role_by_id(role_id, db)

@router.post("/", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Create a new role"""
    return await RoleController.create_role(role_data, db)

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: uuid.UUID,
    role_data: RoleUpdate,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Update a role"""
    return await RoleController.update_role(role_id, role_data, db)

@router.put("/{role_id}/permissions")
async def update_role_permissions(
    role_id: uuid.UUID,
    permission_data: RolePermissionUpdate,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Update role permissions"""
    return await RoleController.update_role_permissions(role_id, permission_data, db)

@router.delete("/{role_id}")
async def delete_role(
    role_id: uuid.UUID,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Delete a role"""
    return await RoleController.delete_role(role_id, db)