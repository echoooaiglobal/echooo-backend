# routes/api/v0/companies.py
from fastapi import APIRouter
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.Http.Controllers.CompanyController import CompanyController
from app.Models.auth_models import User
from app.Schemas.company import (
    CompanyCreate, CompanyUpdate, CompanyResponse,
    CompanyUserCreate, CompanyUserUpdate, CompanyUserResponse,
    CompanyContactCreate, CompanyContactUpdate, CompanyContactResponse
)
from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission, is_company_admin
)
from config.database import get_db

router = APIRouter(prefix="/companies", tags=["Companies"])

# Company endpoints
@router.post("/", response_model=CompanyResponse)
async def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new company"""
    return await CompanyController.create_company(company_data, current_user, db)

@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: uuid.UUID,
    current_user: User = Depends(has_permission("company:read")),
    db: Session = Depends(get_db)
):
    """Get a company by ID"""
    return await CompanyController.get_company(company_id, db)

@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: uuid.UUID,
    company_data: CompanyUpdate,
    current_user: User = Depends(has_permission("company:update")),
    db: Session = Depends(get_db)
):
    """Update a company"""
    return await CompanyController.update_company(company_id, company_data, db)

@router.delete("/{company_id}")
async def delete_company(
    company_id: uuid.UUID,
    current_user: User = Depends(has_permission("company:delete")),
    db: Session = Depends(get_db)
):
    """Delete a company"""
    return await CompanyController.delete_company(company_id, db)

# Company user endpoints
@router.get("/{company_id}/users", response_model=List[CompanyUserResponse])
async def get_company_users(
    company_id: uuid.UUID,
    current_user: User = Depends(has_permission("company:read")),
    db: Session = Depends(get_db)
):
    """Get all users of a company"""
    return await CompanyController.get_company_users(company_id, db)

@router.post("/{company_id}/users", response_model=CompanyUserResponse)
async def add_company_user(
    company_id: uuid.UUID,
    user_data: CompanyUserCreate,
    current_user: User = Depends(is_company_admin),  # No need to pass company_id
    db: Session = Depends(get_db)
):
    """Add a user to a company"""
    return await CompanyController.add_company_user(company_id, user_data, db)

@router.put("/users/{company_user_id}", response_model=CompanyUserResponse)
async def update_company_user(
    company_user_id: uuid.UUID,
    user_data: CompanyUserUpdate,
    current_user: User = Depends(has_permission("company:update")),
    db: Session = Depends(get_db)
):
    """Update a company user association"""
    return await CompanyController.update_company_user(company_user_id, user_data, db)

@router.delete("/users/{company_user_id}")
async def remove_company_user(
    company_user_id: uuid.UUID,
    current_user: User = Depends(has_permission("company:update")),
    db: Session = Depends(get_db)
):
    """Remove a user from a company"""
    return await CompanyController.remove_company_user(company_user_id, db)

# Company contact endpoints
@router.post("/{company_id}/contacts", response_model=CompanyContactResponse)
async def add_company_contact(
    company_id: uuid.UUID,
    contact_data: CompanyContactCreate,
    current_user: User = Depends(has_permission("company:update")),
    db: Session = Depends(get_db)
):
    """Add a contact to a company"""
    return await CompanyController.add_company_contact(company_id, contact_data, db)

@router.put("/contacts/{contact_id}", response_model=CompanyContactResponse)
async def update_company_contact(
    contact_id: uuid.UUID,
    contact_data: CompanyContactUpdate,
    current_user: User = Depends(has_permission("company:update")),
    db: Session = Depends(get_db)
):
    """Update a company contact"""
    return await CompanyController.update_company_contact(contact_id, contact_data, db)

@router.delete("/contacts/{contact_id}")
async def delete_company_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(has_permission("company:update")),
    db: Session = Depends(get_db)
):
    """Delete a company contact"""
    return await CompanyController.delete_company_contact(contact_id, db)