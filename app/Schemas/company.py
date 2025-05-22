# app/Schemas/company.py
from pydantic import BaseModel, ConfigDict, validator, Field
from typing import List, Optional
from datetime import datetime
import uuid

class CompanyContactBase(BaseModel):
    role: Optional[str] = None
    name: Optional[str] = None
    contact_type: str
    contact_value: str
    is_primary: bool = False

class CompanyContactCreate(CompanyContactBase):
    company_id: uuid.UUID
    company_user_id: Optional[uuid.UUID] = None

class CompanyContactUpdate(CompanyContactBase):
    company_user_id: Optional[uuid.UUID] = None

class CompanyContactResponse(CompanyContactBase):
    id: uuid.UUID
    company_id: uuid.UUID
    company_user_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CompanyUserBase(BaseModel):
    user_id: uuid.UUID
    role_id: uuid.UUID
    is_primary: bool = False

class CompanyUserCreate(CompanyUserBase):
    company_id: uuid.UUID

class CompanyUserUpdate(BaseModel):
    role_id: Optional[uuid.UUID] = None
    is_primary: Optional[bool] = None

class CompanyUserResponse(CompanyUserBase):
    id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CompanyBase(BaseModel):
    name: str
    domain: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None

class CompanyResponse(CompanyBase):
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    users: List[CompanyUserResponse] = []
    contacts: List[CompanyContactResponse] = []

    model_config = ConfigDict(from_attributes=True)