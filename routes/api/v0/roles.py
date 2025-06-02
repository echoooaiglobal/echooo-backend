# routes/api/v0/roles.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
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
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Get all roles with their permissions"""
    return await RoleController.get_all_roles(db)

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