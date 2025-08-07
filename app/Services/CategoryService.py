# app/Services/CategoryService.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any
from fastapi import HTTPException, status
import uuid

from app.Models.categories import Category
from app.Utils.Logger import logger

class CategoryService:
    """Service for managing categories"""

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
    async def get_root_categories(db: Session):
        """
        Get all root-level categories (those without a parent)
        
        Args:
            db: Database session
            
        Returns:
            List[Category]: List of root categories
        """
        return db.query(Category).filter(Category.parent_id == None).all()
    
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
            # Handle parent ID if provided
            parent_id = category_data.get('parent_id')
            if parent_id and isinstance(parent_id, str):
                try:
                    category_data['parent_id'] = uuid.UUID(parent_id)
                    
                    # Verify parent exists
                    parent = db.query(Category).filter(Category.id == category_data['parent_id']).first()
                    if not parent:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Parent category not found"
                        )
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid parent ID format"
                    )
            
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
        except HTTPException:
            db.rollback()
            raise
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
            
            # Handle parent ID if provided
            parent_id = update_data.get('parent_id')
            if parent_id is not None:
                if parent_id == "":
                    # Set to None (make it a root category)
                    update_data['parent_id'] = None
                elif isinstance(parent_id, str):
                    try:
                        update_data['parent_id'] = uuid.UUID(parent_id)
                        
                        # Verify parent exists and is not this category (prevent circular reference)
                        if update_data['parent_id'] == category_id:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="A category cannot be its own parent"
                            )
                        
                        parent = db.query(Category).filter(Category.id == update_data['parent_id']).first()
                        if not parent:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Parent category not found"
                            )
                    except ValueError:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid parent ID format"
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
        except HTTPException:
            db.rollback()
            raise
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
            
            # Check if category has subcategories
            subcategories = db.query(Category).filter(Category.parent_id == category_id).all()
            if subcategories:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete category with subcategories. Please delete or reassign subcategories first."
                )
            
            # Check if category is used by any social accounts
            if hasattr(category, 'social_accounts') and len(category.social_accounts) > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete category that is used by social accounts"
                )
            
            db.delete(category)
            db.commit()
            
            return True
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting category: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting category"
            ) from e
    
    @staticmethod
    async def get_subcategories(category_id: uuid.UUID, db: Session):
        """
        Get all subcategories of a category
        
        Args:
            category_id: ID of the parent category
            db: Database session
            
        Returns:
            List[Category]: List of subcategories
        """
        # Verify parent exists
        parent = db.query(Category).filter(Category.id == category_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found"
            )
        
        return db.query(Category).filter(Category.parent_id == category_id).all()