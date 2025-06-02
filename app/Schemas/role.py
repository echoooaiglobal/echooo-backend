# app/Schemas/role.py
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime
import uuid

# Permission Schemas
class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class PermissionResponse(PermissionBase):
    id: str
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Role Schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permission_ids: List[str] = []  # List of permission UUIDs

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class RoleResponse(RoleBase):
    id: str
    
    model_config = {"from_attributes": True}
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class RoleDetailResponse(RoleResponse):
    permissions: List[PermissionResponse] = []

class RolePermissionUpdate(BaseModel):
    permission_ids: List[str]  # List of permission UUIDs to assign to role

# User Role Assignment Schemas
class UserRoleAssignment(BaseModel):
    role_ids: List[str]  # List of role UUIDs to assign to user

class BulkUserRoleAssignment(BaseModel):
    user_ids: List[str]  # List of user UUIDs
    role_ids: List[str]  # List of role UUIDs to assign to all users

class UserRoleResponse(BaseModel):
    user_id: str
    roles: List[RoleResponse]
    
    @field_validator('user_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

# Permission Management Schemas
class PermissionGroupResponse(BaseModel):
    """Group permissions by category for better UI organization"""
    category: str
    permissions: List[PermissionResponse]

class RolePermissionMatrix(BaseModel):
    """Show all roles and their permissions in a matrix format"""
    roles: List[RoleDetailResponse]
    all_permissions: List[PermissionResponse]