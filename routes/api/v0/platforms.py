# routes/api/v0/platforms.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.Http.Controllers.PlatformController import PlatformController
from app.Models.auth_models import User
from app.Schemas.influencer import (
    PlatformCreate, PlatformUpdate, PlatformResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse
)
from app.Utils.Helpers import (
    has_role
)
from config.database import get_db

router = APIRouter(prefix="/platforms", tags=["Platforms"])

# Platform endpoints
@router.get("/", response_model=List[PlatformResponse])
async def get_all_platforms(
    db: Session = Depends(get_db)
):
    """Get all platforms"""
    return await PlatformController.get_all_platforms(db)

@router.get("/platforms/{platform_id}", response_model=PlatformResponse)
async def get_platform(
    platform_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get a platform by ID"""
    return await PlatformController.get_platform(platform_id, db)

@router.post("/platforms", response_model=PlatformResponse)
async def create_platform(
    platform_data: PlatformCreate,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Create a new platform"""
    return await PlatformController.create_platform(platform_data, db)

@router.put("/platforms/{platform_id}", response_model=PlatformResponse)
async def update_platform(
    platform_id: uuid.UUID,
    platform_data: PlatformUpdate,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Update a platform"""
    return await PlatformController.update_platform(platform_id, platform_data, db)

@router.delete("/platforms/{platform_id}")
async def delete_platform(
    platform_id: uuid.UUID,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Delete a platform"""
    return await PlatformController.delete_platform(platform_id, db)

# Category endpoints
@router.get("/categories", response_model=List[CategoryResponse])
async def get_all_categories(
    db: Session = Depends(get_db)
):
    """Get all categories"""
    return await PlatformController.get_all_categories(db)

@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get a category by ID"""
    return await PlatformController.get_category(category_id, db)

@router.post("/categories", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(has_role(["platform_admin", "platform_user"])),
    db: Session = Depends(get_db)
):
    """Create a new category"""
    return await PlatformController.create_category(category_data, db)

@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    category_data: CategoryUpdate,
    current_user: User = Depends(has_role(["platform_admin", "platform_user"])),
    db: Session = Depends(get_db)
):
    """Update a category"""
    return await PlatformController.update_category(category_id, category_data, db)

@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Delete a category"""
    return await PlatformController.delete_category(category_id, db)