# app/Http/Controllers/PermissionController.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
import uuid

from app.Models.auth_models import Permission, Role, RolePermission
from app.Schemas.role import (
    PermissionCreate, PermissionUpdate, PermissionResponse,
    PermissionGroupResponse, RolePermissionMatrix, RoleDetailResponse
)
from app.Utils.Logger import logger

class PermissionController:
    """Controller for permission management"""
    
    @staticmethod
    async def get_all_permissions(db: Session):
        """Get all permissions"""
        try:
            permissions = db.query(Permission).all()
            return [PermissionResponse.model_validate(perm) for perm in permissions]
        except Exception as e:
            logger.error(f"Error in get_all_permissions controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_permissions_grouped(db: Session):
        """Get permissions grouped by category"""
        try:
            permissions = db.query(Permission).all()
            
            # Group permissions by their prefix (e.g., user:read -> user)
            grouped = {}
            for perm in permissions:
                category = perm.name.split(':')[0] if ':' in perm.name else 'general'
                if category not in grouped:
                    grouped[category] = []
                grouped[category].append(PermissionResponse.model_validate(perm))
            
            # Convert to list of PermissionGroupResponse
            result = []
            for category, perms in grouped.items():
                result.append(PermissionGroupResponse(
                    category=category.title(),
                    permissions=perms
                ))
            
            return sorted(result, key=lambda x: x.category)
        except Exception as e:
            logger.error(f"Error in get_permissions_grouped controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_role_permission_matrix(db: Session):
        """Get role-permission matrix for admin dashboard"""
        try:
            # Get all roles with their permissions
            roles = db.query(Role).options(
                joinedload(Role.permissions).joinedload(RolePermission.permission)
            ).all()
            
            # Get all permissions
            all_permissions = db.query(Permission).all()
            
            # Format roles
            formatted_roles = []
            for role in roles:
                role_data = RoleDetailResponse.model_validate(role)
                role_data.permissions = [
                    PermissionResponse.model_validate(rp.permission) 
                    for rp in role.permissions
                ]
                formatted_roles.append(role_data)
            
            return RolePermissionMatrix(
                roles=formatted_roles,
                all_permissions=[PermissionResponse.model_validate(perm) for perm in all_permissions]
            )
        except Exception as e:
            logger.error(f"Error in get_role_permission_matrix controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_permission_by_id(permission_id: uuid.UUID, db: Session):
        """Get a permission by ID"""
        try:
            permission = db.query(Permission).filter(Permission.id == permission_id).first()
            
            if not permission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Permission not found"
                )
            
            return PermissionResponse.model_validate(permission)
        except Exception as e:
            logger.error(f"Error in get_permission_by_id controller: {str(e)}")
            raise
    
    @staticmethod
    async def create_permission(permission_data: PermissionCreate, db: Session):
        """Create a new permission"""
        try:
            # Check if permission already exists
            existing_perm = db.query(Permission).filter(
                Permission.name == permission_data.name
            ).first()
            
            if existing_perm:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Permission with this name already exists"
                )
            
            permission = Permission(
                name=permission_data.name,
                description=permission_data.description
            )
            
            db.add(permission)
            db.commit()
            db.refresh(permission)
            
            return PermissionResponse.model_validate(permission)
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating permission: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating permission"
            ) from e
    
    @staticmethod
    async def update_permission(
        permission_id: uuid.UUID, 
        permission_data: PermissionUpdate, 
        db: Session
    ):
        """Update a permission"""
        try:
            permission = db.query(Permission).filter(Permission.id == permission_id).first()
            
            if not permission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Permission not found"
                )
            
            # Check for duplicate name if updating
            if permission_data.name and permission_data.name != permission.name:
                existing_perm = db.query(Permission).filter(
                    Permission.name == permission_data.name,
                    Permission.id != permission_id
                ).first()
                
                if existing_perm:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Permission with this name already exists"
                    )
            
            # Update fields
            if permission_data.name is not None:
                permission.name = permission_data.name
            
            if permission_data.description is not None:
                permission.description = permission_data.description
            
            db.commit()
            db.refresh(permission)
            
            return PermissionResponse.model_validate(permission)
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating permission: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating permission"
            ) from e
    
    @staticmethod
    async def delete_permission(permission_id: uuid.UUID, db: Session):
        """Delete a permission"""
        try:
            permission = db.query(Permission).filter(Permission.id == permission_id).first()
            
            if not permission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Permission not found"
                )
            
            # Check if permission is assigned to any roles
            role_count = db.query(RolePermission).filter(
                RolePermission.permission_id == permission_id
            ).count()
            
            if role_count > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete permission that is assigned to {role_count} roles"
                )
            
            # Prevent deletion of system permissions
            system_permissions = [
                "user:create", "user:read", "user:update", "user:delete",
                "company:create", "company:read", "company:update", "company:delete",
                "campaign:create", "campaign:read", "campaign:update", "campaign:delete",
                "influencer:create", "influencer:read", "influencer:update", "influencer:delete"
            ]
            
            if permission.name in system_permissions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete system permissions"
                )
            
            db.delete(permission)
            db.commit()
            
            return {"message": "Permission deleted successfully"}
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting permission: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting permission"
            ) from e