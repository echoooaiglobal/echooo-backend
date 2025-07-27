# routes/api/v0/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.Http.Controllers.UserController import UserController
from app.Models.auth_models import User
from app.Schemas.auth import UserResponse, UserDetailResponse, UserUpdate
from app.Schemas.role import UserRoleAssignment, BulkUserRoleAssignment, UserRoleResponse
from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission
)
from config.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=List[UserDetailResponse])
async def get_all_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    user_type: Optional[str] = Query(None, description="Filter by user type (platform, b2c, influencer)"),
    status: Optional[str] = Query(None, description="Filter by user status (active, inactive, pending, suspended)"),
    search: Optional[str] = Query(None, description="Search users by name or email"),
    current_user: User = Depends(has_permission("user:read")),
    db: Session = Depends(get_db)
):
    """Get all users with optional filtering and pagination"""
    return await UserController.get_all_users(
        skip=skip, 
        limit=limit, 
        user_type=user_type,
        status=status,
        search=search,
        db=db
    )

@router.get("/platform-users", response_model=List[UserDetailResponse])
async def get_platform_users(
    current_user: User = Depends(has_role(["platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
):
    """Get all platform users"""
    return await UserController.get_users_by_type("platform", db)

@router.get("/b2c-users", response_model=List[UserDetailResponse])  # Changed endpoint path
async def get_b2c_users(  # Changed function name
    current_user: User = Depends(has_permission("user:read")),
    db: Session = Depends(get_db)
):
    """Get all b2c users"""  # Changed docstring
    return await UserController.get_users_by_type("b2c", db)  # Changed parameter

@router.get("/influencers", response_model=List[UserDetailResponse])
async def get_influencer_users(
    current_user: User = Depends(has_permission("user:read")),
    db: Session = Depends(get_db)
):
    """Get all influencer users"""
    return await UserController.get_users_by_type("influencer", db)

@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(has_role(["platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
):
    """Get user statistics"""
    return await UserController.get_user_stats(db)

@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(has_permission("user:read")),
    db: Session = Depends(get_db)
):
    """Get a user by ID"""
    return await UserController.get_user_by_id(user_id, db)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    current_user: User = Depends(has_permission("user:update")),
    db: Session = Depends(get_db)
):
    """Update a user (admin only)"""
    return await UserController.update_user(user_id, user_data, current_user, db)

@router.put("/{user_id}/status")
async def update_user_status(
    user_id: uuid.UUID, 
    new_status: str,
    current_user: User = Depends(has_role(["platform_super_admin", "platform_admin"])),
    db: Session = Depends(get_db)
):
    """Update user status (activate/deactivate/suspend)"""
    return await UserController.update_user_status(user_id, new_status, db)

# ============= NEW ROLE ASSIGNMENT ENDPOINTS =============

@router.get("/{user_id}/roles", response_model=UserRoleResponse)
async def get_user_roles(
    user_id: uuid.UUID,
    current_user: User = Depends(has_permission("user:read")),
    db: Session = Depends(get_db)
):
    """Get all roles assigned to a specific user"""
    return await UserController.get_user_roles(user_id, db)

@router.put("/{user_id}/roles", response_model=UserRoleResponse)
async def assign_roles_to_user(
    user_id: uuid.UUID,
    role_assignment: UserRoleAssignment,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Assign roles to a user (replaces existing roles)"""
    return await UserController.assign_roles_to_user(user_id, role_assignment.role_ids, db)

@router.post("/{user_id}/roles/add", response_model=UserRoleResponse)
async def add_roles_to_user(
    user_id: uuid.UUID,
    role_assignment: UserRoleAssignment,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Add roles to a user (keeps existing roles)"""
    return await UserController.add_roles_to_user(user_id, role_assignment.role_ids, db)

@router.delete("/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Remove a specific role from a user"""
    return await UserController.remove_role_from_user(user_id, role_id, db)

@router.post("/bulk-assign-roles")
async def bulk_assign_roles(
    bulk_assignment: BulkUserRoleAssignment,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Assign roles to multiple users at once"""
    return await UserController.bulk_assign_roles(bulk_assignment, db)

# ============= EXISTING ENDPOINTS =============

@router.put("/{user_id}/roles")
async def update_user_roles(
    user_id: uuid.UUID,
    role_ids: List[uuid.UUID],
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Update user roles (DEPRECATED - use PUT /{user_id}/roles instead)"""
    return await UserController.update_user_roles(user_id, role_ids, db)

@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Delete a user (platform admin only)"""
    return await UserController.delete_user(user_id, current_user, db)

@router.post("/{user_id}/verify-email")
async def verify_user_email(
    user_id: uuid.UUID,
    current_user: User = Depends(has_role(["platform_admin", "platform_manager"])),
    db: Session = Depends(get_db)
):
    """Manually verify a user's email"""
    return await UserController.verify_user_email(user_id, db)

@router.post("/{user_id}/reset-password")
async def admin_reset_password(
    user_id: uuid.UUID,
    new_password: str,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Admin reset user password"""
    return await UserController.admin_reset_password(user_id, new_password, db)