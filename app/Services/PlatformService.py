# app/Services/PlatformService.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any
from fastapi import HTTPException, status
import uuid

from app.Models.support_models import Platform, Category
from app.Utils.Logger import logger

class PlatformService:
    """Service for managing platforms and categories"""
    
    @staticmethod
    async def get_all_platforms(db: Session):
        """
        Get all platforms
        
        Args:
            db: Database session
            
        Returns:
            List[Platform]: List of all platforms
        """
        return db.query(Platform).all()
    
    @staticmethod
    async def get_platform_by_id(platform_id: uuid.UUID, db: Session):
        """
        Get a platform by ID
        
        Args:
            platform_id: ID of the platform
            db: Database session
            
        Returns:
            Platform: The platform if found
        """
        platform = db.query(Platform).filter(Platform.id == platform_id).first()
        
        if not platform:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Platform not found"
            )
            
        return platform
    
    @staticmethod
    async def create_platform(platform_data: Dict[str, Any], db: Session):
        """
        Create a new platform
        
        Args:
            platform_data: Platform data
            db: Database session
            
        Returns:
            Platform: The created platform
        """
        try:
            # Check if platform with same name already exists
            existing_platform = db.query(Platform).filter(
                Platform.name == platform_data.get('name')
            ).first()
            
            if existing_platform:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Platform with this name already exists"
                )
            
            # Create platform
            platform = Platform(**platform_data)
            
            db.add(platform)
            db.commit()
            db.refresh(platform)
            
            return platform
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating platform: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating platform"
            ) from e
    
    @staticmethod
    async def update_platform(platform_id: uuid.UUID, update_data: Dict[str, Any], db: Session):
        """
        Update a platform
        
        Args:
            platform_id: ID of the platform
            update_data: Data to update
            db: Database session
            
        Returns:
            Platform: The updated platform
        """
        try:
            platform = db.query(Platform).filter(Platform.id == platform_id).first()
            
            if not platform:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Platform not found"
                )
            
            # If name is being updated, check if it already exists
            if 'name' in update_data and update_data['name'] != platform.name:
                existing_platform = db.query(Platform).filter(
                    Platform.name == update_data['name']
                ).first()
                
                if existing_platform:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Platform with this name already exists"
                    )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(platform, key) and value is not None:
                    setattr(platform, key, value)
            
            db.commit()
            db.refresh(platform)
            
            return platform
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating platform: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating platform"
            ) from e
    
    @staticmethod
    async def delete_platform(platform_id: uuid.UUID, db: Session):
        """
        Delete a platform
        
        Args:
            platform_id: ID of the platform
            db: Database session
            
        Returns:
            bool: True if successful
        """
        try:
            platform = db.query(Platform).filter(Platform.id == platform_id).first()
            
            if not platform:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Platform not found"
                )
            
            db.delete(platform)
            db.commit()
            
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting platform: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting platform"
            ) from e
    
    @staticmethod
    async def get_all_categories(db: Session):
        """
        Get all categories
        
        Args:
            db: Database session
            
        Returns:
            List[Category]: List of all categories
        """
        return db.query(Category).all()
    
    @staticmethod
    async def get_category_by_id(category_id: uuid.UUID, db: Session):
        """
        Get a category by ID
        
        Args:
            category_id: ID of the category
            db: Database session
            
        Returns:
            Category: The category if found
        """
        category = db.query(Category).filter(Category.id == category_id).first()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
            
        return category
    
    @staticmethod
    async def create_category(category_data: Dict[str, Any], db: Session):
        """
        Create a new category
        
        Args:
            category_data: Category data
            db: Database session
            
        Returns:
            Category: The created category
        """
        try:
            # Check if category with same name already exists
            existing_category = db.query(Category).filter(
                Category.name == category_data.get('name')
            ).first()
            
            if existing_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category with this name already exists"
                )
            
            # Create category
            category = Category(**category_data)
            
            db.add(category)
            db.commit()
            db.refresh(category)
            
            return category
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating category: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating category"
            ) from e
    
    @staticmethod
    async def update_category(category_id: uuid.UUID, update_data: Dict[str, Any], db: Session):
        """
        Update a category
        
        Args:
            category_id: ID of the category
            update_data: Data to update
            db: Database session
            
        Returns:
            Category: The updated category
        """
        try:
            category = db.query(Category).filter(Category.id == category_id).first()
            
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
            
            # If name is being updated, check if it already exists
            if 'name' in update_data and update_data['name'] != category.name:
                existing_category = db.query(Category).filter(
                    Category.name == update_data['name']
                ).first()
                
                if existing_category:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Category with this name already exists"
                    )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(category, key) and value is not None:
                    setattr(category, key, value)
            
            db.commit()
            db.refresh(category)
            
            return category
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating category: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating category"
            ) from e
    
    @staticmethod
    async def delete_category(category_id: uuid.UUID, db: Session):
        """
        Delete a category
        
        Args:
            category_id: ID of the category
            db: Database session
            
        Returns:
            bool: True if successful
        """
        try:
            category = db.query(Category).filter(Category.id == category_id).first()
            
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
            
            db.delete(category)
            db.commit()
            
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting category: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting category"
            ) from e