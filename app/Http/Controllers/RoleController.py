# app/Http/Controllers/RoleController.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
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
                role_data = RoleDetailResponse.model_validate(role)
                role_data.permissions = [
                    PermissionResponse.model_validate(rp.permission) 
                    for rp in role.permissions
                ]
                result.append(role_data)
            
            return result
        except Exception as e:
            logger.error(f"Error in get_all_roles controller: {str(e)}")
            raise
    
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
            
            role_data = RoleDetailResponse.model_validate(role)
            role_data.permissions = [
                PermissionResponse.model_validate(rp.permission) 
                for rp in role.permissions
            ]
            
            return role_data
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