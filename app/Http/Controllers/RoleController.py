# app/Http/Controllers/RoleController.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from typing import List, Dict, Any
import uuid

from app.Models.auth_models import Role, Permission, RolePermission
from app.Schemas.role import (
    RoleCreate, RoleUpdate, RoleResponse, RoleDetailResponse,
    PermissionResponse, RolePermissionUpdate
)
from app.Utils.Logger import logger

class RoleController:
    """Controller for role and permission management"""
    
    @staticmethod
    async def get_all_roles(db: Session):
        """Get all roles with their permissions"""
        try:
            roles = db.query(Role).options(
                joinedload(Role.permissions).joinedload(RolePermission.permission)
            ).all()
            
            result = []
            for role in roles:
                try:
                    # Create role data first
                    role_data = RoleDetailResponse.model_validate(role)
                    
                    # Handle permissions properly
                    permissions = []
                    if hasattr(role, 'permissions') and role.permissions:
                        for role_permission in role.permissions:
                            if hasattr(role_permission, 'permission') and role_permission.permission:
                                perm_response = PermissionResponse.model_validate(role_permission.permission)
                                permissions.append(perm_response)
                    
                    role_data.permissions = permissions
                    result.append(role_data)
                    
                except Exception as validation_error:
                    logger.error(f"Error validating role {role.name}: {str(validation_error)}")
                    # Create a minimal role response if validation fails
                    role_data = RoleDetailResponse(
                        id=str(role.id),
                        name=role.name,
                        description=role.description or "",
                        permissions=[]
                    )
                    result.append(role_data)
            
            return result
        except Exception as e:
            logger.error(f"Error in get_all_roles controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_roles_by_user_type(user_type: str, db: Session):
        """Get roles filtered by user type"""
        try:
            # Define role patterns for each user type
            role_patterns = {
                "platform": ["platform_admin", "platform_user", "platform_manager", 
                           "platform_accountant", "platform_developer", "platform_customer_support", 
                           "platform_content_moderator", "platform_agent"],
                "company": ["company_admin", "company_user", "company_manager", 
                          "company_accountant", "company_marketer", "company_content_creator"],
                "influencer": ["influencer", "influencer_manager"]
            }
            
            if user_type not in role_patterns:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid user_type: {user_type}"
                )
            
            role_names = role_patterns[user_type]
            
            # Build query with OR conditions for role name patterns
            query = db.query(Role).options(
                joinedload(Role.permissions).joinedload(RolePermission.permission)
            )
            
            # Create filter conditions using role names or LIKE patterns
            conditions = []
            for role_name in role_names:
                conditions.append(Role.name == role_name)
            
            # Also add LIKE patterns for user_type prefix
            conditions.append(Role.name.like(f"{user_type}_%"))
            
            # Apply OR conditions
            if conditions:
                from sqlalchemy import or_
                query = query.filter(or_(*conditions))
            
            roles = query.all()
            
            result = []
            for role in roles:
                try:
                    # Create role data first
                    role_data = RoleDetailResponse.model_validate(role)
                    
                    # Handle permissions properly
                    permissions = []
                    if hasattr(role, 'permissions') and role.permissions:
                        for role_permission in role.permissions:
                            if hasattr(role_permission, 'permission') and role_permission.permission:
                                perm_response = PermissionResponse.model_validate(role_permission.permission)
                                permissions.append(perm_response)
                    
                    role_data.permissions = permissions
                    result.append(role_data)
                    
                except Exception as validation_error:
                    logger.error(f"Error validating role {role.name}: {str(validation_error)}")
                    # Create a minimal role response if validation fails
                    role_data = RoleDetailResponse(
                        id=str(role.id),
                        name=role.name,
                        description=role.description or "",
                        permissions=[]
                    )
                    result.append(role_data)
            
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_roles_by_user_type controller: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving roles by user type"
            )
    
    @staticmethod
    async def get_user_types_with_role_counts(db: Session):
        """Get user types with their role counts"""
        try:
            # Define role patterns for each user type
            user_types = {
                "platform": ["platform_%"],
                "company": ["company_%"], 
                "influencer": ["influencer", "influencer_%"]
            }
            
            result = []
            
            for user_type, patterns in user_types.items():
                # Count roles for this user type
                conditions = []
                for pattern in patterns:
                    if pattern.endswith('%'):
                        conditions.append(Role.name.like(pattern))
                    else:
                        conditions.append(Role.name == pattern)
                
                if conditions:
                    from sqlalchemy import or_
                    count = db.query(Role).filter(or_(*conditions)).count()
                else:
                    count = 0
                
                result.append({
                    "user_type": user_type,
                    "role_count": count,
                    "description": {
                        "platform": "Platform-specific roles for system administration and management",
                        "company": "Company-specific roles for business users and teams",
                        "influencer": "Influencer-specific roles for content creators"
                    }.get(user_type, f"{user_type.title()} roles")
                })
            
            return {
                "user_types": result,
                "total_roles": db.query(Role).count()
            }
        except Exception as e:
            logger.error(f"Error in get_user_types_with_role_counts controller: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving user types statistics"
            )
    
    @staticmethod
    async def get_all_permissions(db: Session):
        """Get all available permissions"""
        try:
            permissions = db.query(Permission).all()
            return [PermissionResponse.model_validate(perm) for perm in permissions]
        except Exception as e:
            logger.error(f"Error in get_all_permissions controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_role_by_id(role_id: uuid.UUID, db: Session):
        """Get a role by ID with its permissions"""
        try:
            role = db.query(Role).options(
                joinedload(Role.permissions).joinedload(RolePermission.permission)
            ).filter(Role.id == role_id).first()
            
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Role not found"
                )
            
            try:
                # Create role data first
                role_data = RoleDetailResponse.model_validate(role)
                
                # Handle permissions properly
                permissions = []
                if hasattr(role, 'permissions') and role.permissions:
                    for role_permission in role.permissions:
                        if hasattr(role_permission, 'permission') and role_permission.permission:
                            perm_response = PermissionResponse.model_validate(role_permission.permission)
                            permissions.append(perm_response)
                
                role_data.permissions = permissions
                return role_data
                
            except Exception as validation_error:
                logger.error(f"Error validating role {role.name}: {str(validation_error)}")
                # Create a minimal role response if validation fails
                return RoleDetailResponse(
                    id=str(role.id),
                    name=role.name,
                    description=role.description or "",
                    permissions=[]
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_role_by_id controller: {str(e)}")
            raise
    
    @staticmethod
    async def create_role(role_data: RoleCreate, db: Session):
        """Create a new role"""
        try:
            # Check if role with same name already exists
            existing_role = db.query(Role).filter(Role.name == role_data.name).first()
            if existing_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Role with this name already exists"
                )
            
            # Create role
            role = Role(
                name=role_data.name,
                description=role_data.description
            )
            
            db.add(role)
            db.flush()  # Get the ID without committing
            
            # Add permissions if provided
            if role_data.permission_ids:
                permission_uuids = [uuid.UUID(pid) for pid in role_data.permission_ids]
                permissions = db.query(Permission).filter(Permission.id.in_(permission_uuids)).all()
                
                if len(permissions) != len(permission_uuids):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="One or more permissions not found"
                    )
                
                # Create role-permission associations
                for permission in permissions:
                    role_permission = RolePermission(
                        role_id=role.id,
                        permission_id=permission.id
                    )
                    db.add(role_permission)
            
            db.commit()
            db.refresh(role)
            
            return RoleResponse.model_validate(role)
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating role: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating role"
            ) from e
    
    @staticmethod
    async def update_role(role_id: uuid.UUID, role_data: RoleUpdate, db: Session):
        """Update a role"""
        try:
            role = db.query(Role).filter(Role.id == role_id).first()
            
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Role not found"
                )
            
            # Check if updating name would create duplicate
            if role_data.name and role_data.name != role.name:
                existing_role = db.query(Role).filter(
                    Role.name == role_data.name,
                    Role.id != role_id
                ).first()
                
                if existing_role:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Role with this name already exists"
                    )
            
            # Update fields
            if role_data.name is not None:
                role.name = role_data.name
            
            if role_data.description is not None:
                role.description = role_data.description
            
            db.commit()
            db.refresh(role)
            
            return RoleResponse.model_validate(role)
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating role: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating role"
            ) from e
    
    @staticmethod
    async def update_role_permissions(
        role_id: uuid.UUID, 
        permission_data: RolePermissionUpdate, 
        db: Session
    ):
        """Update role permissions"""
        try:
            role = db.query(Role).filter(Role.id == role_id).first()
            
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Role not found"
                )
            
            # Get permissions
            permission_uuids = [uuid.UUID(pid) for pid in permission_data.permission_ids]
            permissions = db.query(Permission).filter(Permission.id.in_(permission_uuids)).all()
            
            if len(permissions) != len(permission_uuids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more permissions not found"
                )
            
            # Remove existing role-permission associations
            db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
            
            # Add new associations
            for permission in permissions:
                role_permission = RolePermission(
                    role_id=role_id,
                    permission_id=permission.id
                )
                db.add(role_permission)
            
            db.commit()
            
            return {
                "message": "Role permissions updated successfully",
                "permissions": [perm.name for perm in permissions]
            }
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating role permissions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating role permissions"
            ) from e
    
    @staticmethod
    async def delete_role(role_id: uuid.UUID, db: Session):
        """Delete a role"""
        try:
            role = db.query(Role).filter(Role.id == role_id).first()
            
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Role not found"
                )
            
            # Check if role is assigned to any users
            if role.users:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete role that is assigned to {len(role.users)} users"
                )
            
            # Prevent deletion of system roles
            system_roles = [
                "platform_admin", "platform_user", "company_admin", 
                "company_user", "influencer"
            ]
            
            if role.name in system_roles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete system roles"
                )
            
            db.delete(role)
            db.commit()
            
            return {"message": "Role deleted successfully"}
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting role: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting role"
            ) from e