# routes/api/v0/categories.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.Http.Controllers.CategoryController import CategoryController
from app.Models.auth_models import User
from app.Schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryWithSubsResponse
)
from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission
)
from config.database import get_db

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/", response_model=List[CategoryResponse])
async def get_all_categories(
    db: Session = Depends(get_db)
):
    """Get all categories"""
    return await CategoryController.get_all_categories(db)

@router.get("/root", response_model=List[CategoryResponse])
async def get_root_categories(
    db: Session = Depends(get_db)
):
    """Get all root-level categories (categories without parents)"""
    return await CategoryController.get_root_categories(db)

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get a category by ID"""
    return await CategoryController.get_category(category_id, db)

@router.post("/", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(has_role(["platform_admin", "platform_user"])),
    db: Session = Depends(get_db)
):
    """Create a new category"""
    return await CategoryController.create_category(category_data, db)

@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    category_data: CategoryUpdate,
    current_user: User = Depends(has_role(["platform_admin", "platform_user"])),
    db: Session = Depends(get_db)
):
    """Update a category"""
    return await CategoryController.update_category(category_id, category_data, db)

@router.delete("/{category_id}")
async def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Delete a category (only platform admins can delete)"""
    return await CategoryController.delete_category(category_id, db)

@router.get("/{category_id}/subcategories", response_model=List[CategoryResponse])
async def get_subcategories(
    category_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get all subcategories of a category"""
    return await CategoryController.get_subcategories(category_id, db)