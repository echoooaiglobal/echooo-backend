# app/Http/Controllers/UserController.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional
import uuid

from app.Models.auth_models import User, Role, UserStatus
from app.Models.company_models import CompanyUser
from app.Schemas.auth import (
    UserResponse, UserDetailResponse, UserUpdate, 
    RoleResponse, CompanyBriefResponse
)
from app.Utils.Logger import logger
from app.Http.Controllers.AuthController import AuthController

class UserController:
    """Controller for user management endpoints"""
    
    @staticmethod
    async def get_all_users(
        skip: int = 0,
        limit: int = 100,
        user_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        db: Session = None
    ):
        """Get all users with filtering and pagination"""
        try:
            # Base query with eager loading
            query = db.query(User).options(
                joinedload(User.roles),
                joinedload(User.company_associations).joinedload(CompanyUser.company)
            )
            
            # Apply filters
            if user_type:
                query = query.filter(User.user_type == user_type)
            
            if status:
                query = query.filter(User.status == status)
            
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        User.full_name.ilike(search_term),
                        User.email.ilike(search_term)
                    )
                )
            
            # Apply pagination
            users = query.offset(skip).limit(limit).all()
            
            # Format response
            result = []
            for user in users:
                user_data = UserDetailResponse.model_validate(user)
                user_data.roles = [RoleResponse.model_validate(role) for role in user.roles]
                
                # Add company info for b2c users
                if user.user_type == "b2c" and user.company_associations:
                    company_association = user.company_associations[0]  # Get first company
                    if company_association.company:
                        user_data.company = CompanyBriefResponse.model_validate(company_association.company)
                
                result.append(user_data)
            
            return result
        except Exception as e:
            logger.error(f"Error in get_all_users controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_users_by_type(user_type: str, db: Session):
        """Get users by type (platform, company, influencer)"""
        try:
            users = db.query(User).options(
                joinedload(User.roles),
                joinedload(User.company_associations).joinedload(CompanyUser.company)
            ).filter(User.user_type == user_type).all()
            
            result = []
            for user in users:
                user_data = UserDetailResponse.model_validate(user)
                user_data.roles = [RoleResponse.model_validate(role) for role in user.roles]
                
                # Add company info for b2c users
                if user.user_type == "b2c" and user.company_associations:
                    company_association = user.company_associations[0]
                    if company_association.company:
                        user_data.company = CompanyBriefResponse.model_validate(company_association.company)
                                
                result.append(user_data)
            
            return result
        except Exception as e:
            logger.error(f"Error in get_users_by_type controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_user_stats(db: Session):
        """Get user statistics"""
        try:
            # Total users
            total_users = db.query(User).count()
            
            # Users by type
            platform_users = db.query(User).filter(User.user_type == "platform").count()
            company_users = db.query(User).filter(User.user_type == "b2c").count()
            influencer_users = db.query(User).filter(User.user_type == "influencer").count()
            
            # Users by status
            active_users = db.query(User).filter(User.status == UserStatus.ACTIVE.value).count()
            pending_users = db.query(User).filter(User.status == UserStatus.PENDING.value).count()
            inactive_users = db.query(User).filter(User.status == UserStatus.INACTIVE.value).count()
            suspended_users = db.query(User).filter(User.status == UserStatus.SUSPENDED.value).count()
            
            # Recent registrations (last 30 days)
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_registrations = db.query(User).filter(
                User.created_at >= thirty_days_ago
            ).count()
            
            return {
                "total_users": total_users,
                "users_by_type": {
                    "platform": platform_users,
                    "b2c": company_users,
                    "influencer": influencer_users
                },
                "users_by_status": {
                    "active": active_users,
                    "pending": pending_users,
                    "inactive": inactive_users,
                    "suspended": suspended_users
                },
                "recent_registrations": recent_registrations
            }
        except Exception as e:
            logger.error(f"Error in get_user_stats controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_user_by_id(user_id: uuid.UUID, db: Session):
        """Get a user by ID"""
        try:
            user = db.query(User).options(
                joinedload(User.roles),
                joinedload(User.company_associations).joinedload(CompanyUser.company)
            ).filter(User.id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user_data = UserDetailResponse.model_validate(user)
            user_data.roles = [RoleResponse.model_validate(role) for role in user.roles]
            
            # Add company info for company users
            if user.user_type == "b2c" and user.company_associations:
                company_association = user.company_associations[0]
                if company_association.company:
                    user_data.company = CompanyBriefResponse.model_validate(company_association.company)
            
            return user_data
        except Exception as e:
            logger.error(f"Error in get_user_by_id controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_user(
        user_id: uuid.UUID,
        user_data: UserUpdate,
        current_user: User,
        db: Session
    ):
        """Update a user"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check if current user can update this user
            # Platform admins can update anyone
            # Users can update themselves
            can_update = (
                any(role.name == "platform_admin" for role in current_user.roles) or
                current_user.id == user_id
            )
            
            if not can_update:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to update this user"
                )
            
            # Update allowed fields
            if user_data.full_name is not None:
                user.full_name = user_data.full_name
            
            if user_data.phone_number is not None:
                user.phone_number = user_data.phone_number
                
            if user_data.profile_image_url is not None:
                user.profile_image_url = user_data.profile_image_url
            
            db.commit()
            db.refresh(user)
            
            return UserResponse.model_validate(user)
        except Exception as e:
            logger.error(f"Error in update_user controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_user_status(user_id: uuid.UUID, new_status: str, db: Session):
        """Update user status"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Validate status
            valid_statuses = [status.value for status in UserStatus]
            if new_status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
            
            user.status = new_status
            db.commit()
            db.refresh(user)
            
            return {"message": f"User status updated to {new_status}"}
        except Exception as e:
            logger.error(f"Error in update_user_status controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_user_roles(user_id: uuid.UUID, role_ids: List[uuid.UUID], db: Session):
        """Update user roles"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Get roles
            roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
            
            if len(roles) != len(role_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more roles not found"
                )
            
            # Update user roles
            user.roles = roles
            db.commit()
            db.refresh(user)
            
            return {
                "message": "User roles updated successfully",
                "roles": [role.name for role in roles]
            }
        except Exception as e:
            logger.error(f"Error in update_user_roles controller: {str(e)}")
            raise
    
    @staticmethod
    async def delete_user(user_id: uuid.UUID, current_user: User, db: Session):
        """Delete a user"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Prevent deletion of self
            if current_user.id == user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete your own account"
                )
            
            # Check if user has any important associations
            # Add business logic here to prevent deletion of users with important data
            
            db.delete(user)
            db.commit()
            
            return {"message": "User deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_user controller: {str(e)}")
            raise
    
    @staticmethod
    async def verify_user_email(user_id: uuid.UUID, db: Session):
        """Manually verify a user's email"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user.email_verified = True
            if user.status == UserStatus.PENDING.value:
                user.status = UserStatus.ACTIVE.value
            
            db.commit()
            db.refresh(user)
            
            return {"message": "User email verified successfully"}
        except Exception as e:
            logger.error(f"Error in verify_user_email controller: {str(e)}")
            raise
    
    @staticmethod
    async def admin_reset_password(user_id: uuid.UUID, new_password: str, db: Session):
        """Admin reset user password"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Hash new password
            user.hashed_password = AuthController.get_password_hash(new_password)
            
            # Revoke all refresh tokens for this user
            from app.Models.auth_models import RefreshToken
            db.query(RefreshToken).filter(RefreshToken.user_id == user_id).update({"is_revoked": True})
            
            db.commit()
            
            return {"message": "Password reset successfully"}
        except Exception as e:
            logger.error(f"Error in admin_reset_password controller: {str(e)}")
            raise
    
    # ============= NEW ROLE ASSIGNMENT METHODS =============
    
    @staticmethod
    async def get_user_roles(user_id: uuid.UUID, db: Session):
        """Get all roles assigned to a user"""
        try:
            user = db.query(User).options(
                joinedload(User.roles)
            ).filter(User.id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            from app.Schemas.role import UserRoleResponse, RoleResponse
            
            return UserRoleResponse(
                user_id=str(user.id),
                roles=[RoleResponse.model_validate(role) for role in user.roles]
            )
        except Exception as e:
            logger.error(f"Error in get_user_roles controller: {str(e)}")
            raise
    
    @staticmethod
    async def assign_roles_to_user(user_id: uuid.UUID, role_ids: List[str], db: Session):
        """Assign roles to a user (replaces existing roles)"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Convert string UUIDs to UUID objects and get roles
            role_uuids = [uuid.UUID(role_id) for role_id in role_ids]
            roles = db.query(Role).filter(Role.id.in_(role_uuids)).all()
            
            if len(roles) != len(role_uuids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more roles not found"
                )
            
            # Replace all roles
            user.roles = roles
            db.commit()
            db.refresh(user)
            
            from app.Schemas.role import UserRoleResponse, RoleResponse
            
            return UserRoleResponse(
                user_id=str(user.id),
                roles=[RoleResponse.model_validate(role) for role in user.roles]
            )
        except Exception as e:
            logger.error(f"Error in assign_roles_to_user controller: {str(e)}")
            raise
    
    @staticmethod
    async def add_roles_to_user(user_id: uuid.UUID, role_ids: List[str], db: Session):
        """Add roles to a user (keeps existing roles)"""
        try:
            user = db.query(User).options(
                joinedload(User.roles)
            ).filter(User.id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Convert string UUIDs to UUID objects and get roles
            role_uuids = [uuid.UUID(role_id) for role_id in role_ids]
            new_roles = db.query(Role).filter(Role.id.in_(role_uuids)).all()
            
            if len(new_roles) != len(role_uuids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more roles not found"
                )
            
            # Get existing role IDs
            existing_role_ids = {role.id for role in user.roles}
            
            # Add only new roles (avoid duplicates)
            for role in new_roles:
                if role.id not in existing_role_ids:
                    user.roles.append(role)
            
            db.commit()
            db.refresh(user)
            
            from app.Schemas.role import UserRoleResponse, RoleResponse
            
            return UserRoleResponse(
                user_id=str(user.id),
                roles=[RoleResponse.model_validate(role) for role in user.roles]
            )
        except Exception as e:
            logger.error(f"Error in add_roles_to_user controller: {str(e)}")
            raise
    
    @staticmethod
    async def remove_role_from_user(user_id: uuid.UUID, role_id: uuid.UUID, db: Session):
        """Remove a specific role from a user"""
        try:
            user = db.query(User).options(
                joinedload(User.roles)
            ).filter(User.id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Find the role to remove
            role_to_remove = None
            for role in user.roles:
                if role.id == role_id:
                    role_to_remove = role
                    break
            
            if not role_to_remove:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Role not assigned to this user"
                )
            
            # Prevent removal of critical roles that would lock out the user
            if role_to_remove.name == "platform_admin" and len(user.roles) == 1:
                # Check if this is the last platform admin
                admin_count = db.query(User).join(User.roles).filter(
                    Role.name == "platform_admin"
                ).count()
                
                if admin_count <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot remove the last platform admin role"
                    )
            
            # Remove the role
            user.roles.remove(role_to_remove)
            db.commit()
            db.refresh(user)
            
            return {"message": f"Role '{role_to_remove.name}' removed from user successfully"}
        except Exception as e:
            logger.error(f"Error in remove_role_from_user controller: {str(e)}")
            raise
    
    @staticmethod
    async def bulk_assign_roles(bulk_assignment, db: Session):
        """Assign roles to multiple users at once"""
        try:
            from app.Schemas.role import BulkUserRoleAssignment
            
            # Convert string UUIDs to UUID objects
            user_uuids = [uuid.UUID(user_id) for user_id in bulk_assignment.user_ids]
            role_uuids = [uuid.UUID(role_id) for role_id in bulk_assignment.role_ids]
            
            # Get users and roles
            users = db.query(User).filter(User.id.in_(user_uuids)).all()
            roles = db.query(Role).filter(Role.id.in_(role_uuids)).all()
            
            if len(users) != len(user_uuids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more users not found"
                )
            
            if len(roles) != len(role_uuids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more roles not found"
                )
            
            # Assign roles to all users
            updated_users = []
            for user in users:
                user.roles = roles
                updated_users.append({
                    "user_id": str(user.id),
                    "user_name": user.full_name,
                    "roles": [role.name for role in roles]
                })
            
            db.commit()
            
            return {
                "message": f"Roles assigned to {len(users)} users successfully",
                "updated_users": updated_users
            }
        except Exception as e:
            logger.error(f"Error in bulk_assign_roles controller: {str(e)}")
            raise