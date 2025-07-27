# app/Http/Controllers/CategoryController.py
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

from app.Schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryWithSubsResponse
)
from app.Services.CategoryService import CategoryService
from app.Utils.Logger import logger

class CategoryController:
    """Controller for category-related endpoints"""
    
    @staticmethod
    async def get_all_categories(db: Session):
        """Get all categories"""
        try:
            categories = await CategoryService.get_all_categories(db)
            return [CategoryResponse.model_validate(cat) for cat in categories]
        except Exception as e:
            logger.error(f"Error in get_all_categories controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_root_categories(db: Session):
        """Get all root-level categories"""
        try:
            categories = await CategoryService.get_root_categories(db)
            return [CategoryResponse.model_validate(cat) for cat in categories]
        except Exception as e:
            logger.error(f"Error in get_root_categories controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_category(
        category_id: uuid.UUID,
        db: Session
    ):
        """Get a category by ID"""
        try:
            category = await CategoryService.get_category_by_id(category_id, db)
            return CategoryResponse.model_validate(category)
        except Exception as e:
            logger.error(f"Error in get_category controller: {str(e)}")
            raise
    
    @staticmethod
    async def create_category(
        category_data: CategoryCreate,
        db: Session
    ):
        """Create a new category"""
        try:
            category = await CategoryService.create_category(
                category_data.model_dump(exclude_unset=True),
                db
            )
            return CategoryResponse.model_validate(category)
        except Exception as e:
            logger.error(f"Error in create_category controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_category(
        category_id: uuid.UUID,
        category_data: CategoryUpdate,
        db: Session
    ):
        """Update a category"""
        try:
            category = await CategoryService.update_category(
                category_id,
                category_data.model_dump(exclude_unset=True),
                db
            )
            return CategoryResponse.model_validate(category)
        except Exception as e:
            logger.error(f"Error in update_category controller: {str(e)}")
            raise
    
    @staticmethod
    async def delete_category(
        category_id: uuid.UUID,
        db: Session
    ):
        """Delete a category"""
        try:
            await CategoryService.delete_category(category_id, db)
            return {"message": "Category deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_category controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_subcategories(
        category_id: uuid.UUID,
        db: Session
    ):
        """Get all subcategories of a category"""
        try:
            subcategories = await CategoryService.get_subcategories(category_id, db)
            return [CategoryResponse.model_validate(cat) for cat in subcategories]
        except Exception as e:
            logger.error(f"Error in get_subcategories controller: {str(e)}")
            raise