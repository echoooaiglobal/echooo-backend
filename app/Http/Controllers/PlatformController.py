# app/Http/Controllers/PlatformController.py
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

# from app.Models.influencer_models import Platform, Category
from app.Schemas.influencer import (
    PlatformCreate, PlatformUpdate, PlatformResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse
)
from app.Services.PlatformService import PlatformService
from app.Utils.Logger import logger

class PlatformController:
    """Controller for platform and category endpoints"""
    
    @staticmethod
    async def get_all_platforms(db: Session):
        """Get all platforms"""
        try:
            platforms = await PlatformService.get_all_platforms(db)
            return [PlatformResponse.from_orm(platform) for platform in platforms]
        except Exception as e:
            logger.error(f"Error in get_all_platforms controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_platform(platform_id: uuid.UUID, db: Session):
        """Get a platform by ID"""
        try:
            platform = await PlatformService.get_platform_by_id(platform_id, db)
            return PlatformResponse.from_orm(platform)
        except Exception as e:
            logger.error(f"Error in get_platform controller: {str(e)}")
            raise
    
    @staticmethod
    async def create_platform(platform_data: PlatformCreate, db: Session):
        """Create a new platform"""
        try:
            platform = await PlatformService.create_platform(platform_data.dict(), db)
            return PlatformResponse.from_orm(platform)
        except Exception as e:
            logger.error(f"Error in create_platform controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_platform(platform_id: uuid.UUID, platform_data: PlatformUpdate, db: Session):
        """Update a platform"""
        try:
            platform = await PlatformService.update_platform(
                platform_id,
                platform_data.dict(exclude_unset=True),
                db
            )
            return PlatformResponse.from_orm(platform)
        except Exception as e:
            logger.error(f"Error in update_platform controller: {str(e)}")
            raise
    
    @staticmethod
    async def delete_platform(platform_id: uuid.UUID, db: Session):
        """Delete a platform"""
        try:
            await PlatformService.delete_platform(platform_id, db)
            return {"message": "Platform deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_platform controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_all_categories(db: Session):
        """Get all categories"""
        try:
            categories = await PlatformService.get_all_categories(db)
            return [CategoryResponse.from_orm(category) for category in categories]
        except Exception as e:
            logger.error(f"Error in get_all_categories controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_category(category_id: uuid.UUID, db: Session):
        """Get a category by ID"""
        try:
            category = await PlatformService.get_category_by_id(category_id, db)
            return CategoryResponse.from_orm(category)
        except Exception as e:
            logger.error(f"Error in get_category controller: {str(e)}")
            raise
    
    @staticmethod
    async def create_category(category_data: CategoryCreate, db: Session):
        """Create a new category"""
        try:
            category = await PlatformService.create_category(category_data.dict(), db)
            return CategoryResponse.from_orm(category)
        except Exception as e:
            logger.error(f"Error in create_category controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_category(category_id: uuid.UUID, category_data: CategoryUpdate, db: Session):
        """Update a category"""
        try:
            category = await PlatformService.update_category(
                category_id,
                category_data.dict(exclude_unset=True),
                db
            )
            return CategoryResponse.from_orm(category)
        except Exception as e:
            logger.error(f"Error in update_category controller: {str(e)}")
            raise
    
    @staticmethod
    async def delete_category(category_id: uuid.UUID, db: Session):
        """Delete a category"""
        try:
            await PlatformService.delete_category(category_id, db)
            return {"message": "Category deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_category controller: {str(e)}")
            raise