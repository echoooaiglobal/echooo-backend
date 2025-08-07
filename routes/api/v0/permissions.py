# routes/api/v0/permissions.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.Http.Controllers.PermissionController import PermissionController
from app.Models.auth_models import User
from app.Schemas.role import (
    PermissionCreate, PermissionUpdate, PermissionResponse,
    PermissionGroupResponse, RolePermissionMatrix
)
from app.Utils.Helpers import has_role
from config.database import get_db

router = APIRouter(prefix="/permissions", tags=["Permissions"])

@router.get("/", response_model=List[PermissionResponse])
async def get_all_permissions(
    current_user: User = Depends(has_role(["platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
):
    """Get all permissions"""
    return await PermissionController.get_all_permissions(db)

@router.get("/grouped", response_model=List[PermissionGroupResponse])
async def get_permissions_grouped(
    current_user: User = Depends(has_role(["platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
):
    """Get permissions grouped by category for better UI organization"""
    return await PermissionController.get_permissions_grouped(db)

@router.get("/matrix", response_model=RolePermissionMatrix)
async def get_role_permission_matrix(
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Get role-permission matrix for admin dashboard"""
    return await PermissionController.get_role_permission_matrix(db)

@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: uuid.UUID,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Get a permission by ID"""
    return await PermissionController.get_permission_by_id(permission_id, db)

@router.post("/", response_model=PermissionResponse)
async def create_permission(
    permission_data: PermissionCreate,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Create a new permission"""
    return await PermissionController.create_permission(permission_data, db)

@router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: uuid.UUID,
    permission_data: PermissionUpdate,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Update a permission"""
    return await PermissionController.update_permission(permission_id, permission_data, db)

@router.delete("/{permission_id}")
async def delete_permission(
    permission_id: uuid.UUID,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Delete a permission"""
    return await PermissionController.delete_permission(permission_id, db)