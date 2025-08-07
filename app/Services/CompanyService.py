# app/Services/CompanyService.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any
from fastapi import HTTPException, status
import uuid

from app.Models.auth_models import User, Role
from app.Models.company_models import Company, CompanyUser, CompanyContact
from app.Utils.Logger import logger

class CompanyService:
    """Service for managing companies and related data"""
    
    @staticmethod
    async def create_company(company_data: Dict[str, Any], created_by: uuid.UUID, db: Session):
        """
        Create a new company
        
        Args:
            company_data: Company data
            created_by: ID of the user creating the company
            db: Database session
            
        Returns:
            Company: The created company
        """
        try:
            # Check if user exists
            user = db.query(User).filter(User.id == created_by).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Create company
            company_data['created_by'] = created_by
            company = Company(**company_data)
            
            db.add(company)
            db.commit()
            db.refresh(company)
            
            # Add creator as a company admin
            b2c_company_owner_role = db.query(Role).filter(Role.name == "b2c_company_owner").first()
            if not b2c_company_owner_role:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="B2C company admin role not found"
                )

            company_user = CompanyUser(
                company_id=company.id,
                user_id=created_by,
                role_id=b2c_company_owner_role.id,
                is_primary=True
            )
            
            db.add(company_user)
            db.commit()
            
            return company
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating company: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating company"
            ) from e
    
    @staticmethod
    async def get_company_by_id(company_id: uuid.UUID, db: Session):
        """
        Get a company by ID
        
        Args:
            company_id: ID of the company
            db: Database session
            
        Returns:
            Company: The company if found
        """
        company = db.query(Company).filter(Company.id == company_id).first()
        
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
            
        return company
    
    @staticmethod
    async def update_company(company_id: uuid.UUID, update_data: Dict[str, Any], db: Session):
        """
        Update a company
        
        Args:
            company_id: ID of the company
            update_data: Data to update
            db: Database session
            
        Returns:
            Company: The updated company
        """
        try:
            company = db.query(Company).filter(Company.id == company_id).first()
            
            if not company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company not found"
                )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(company, key) and value is not None:
                    setattr(company, key, value)
            
            db.commit()
            db.refresh(company)
            
            return company
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating company: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating company"
            ) from e
    
    @staticmethod
    async def delete_company(company_id: uuid.UUID, db: Session):
        """
        Delete a company
        
        Args:
            company_id: ID of the company
            db: Database session
            
        Returns:
            bool: True if successful
        """
        try:
            company = db.query(Company).filter(Company.id == company_id).first()
            
            if not company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company not found"
                )
            
            db.delete(company)
            db.commit()
            
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting company: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting company"
            ) from e
    
    @staticmethod
    async def get_company_users(company_id: uuid.UUID, db: Session):
        """
        Get all users associated with a company
        
        Args:
            company_id: ID of the company
            db: Database session
            
        Returns:
            List[CompanyUser]: List of company users
        """
        company_users = db.query(CompanyUser).filter(
            CompanyUser.company_id == company_id
        ).all()
        
        return company_users
    
    @staticmethod
    async def add_user_to_company(company_id: uuid.UUID, user_data: Dict[str, Any], db: Session):
        """
        Add a user to a company
        
        Args:
            company_id: ID of the company
            user_data: User data including user_id, role_id, is_primary
            db: Database session
            
        Returns:
            CompanyUser: The created company user association
        """
        try:
            # Check if company exists
            company = db.query(Company).filter(Company.id == company_id).first()
            if not company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company not found"
                )
            
            # Check if user exists
            user_id = user_data.get('user_id')
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check if user is already associated with company
            existing_association = db.query(CompanyUser).filter(
                CompanyUser.company_id == company_id,
                CompanyUser.user_id == user_id
            ).first()
            
            if existing_association:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already associated with this company"
                )
            
            # Create company user association
            company_user = CompanyUser(
                company_id=company_id,
                user_id=user_id,
                role_id=user_data.get('role_id'),
                is_primary=user_data.get('is_primary', False)
            )
            
            db.add(company_user)
            db.commit()
            db.refresh(company_user)
            
            return company_user
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error adding user to company: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error adding user to company"
            ) from e
    
    @staticmethod
    async def update_company_user(company_user_id: uuid.UUID, update_data: Dict[str, Any], db: Session):
        """
        Update a company user association
        
        Args:
            company_user_id: ID of the company user association
            update_data: Data to update
            db: Database session
            
        Returns:
            CompanyUser: The updated company user association
        """
        try:
            company_user = db.query(CompanyUser).filter(
                CompanyUser.id == company_user_id
            ).first()
            
            if not company_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company user association not found"
                )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(company_user, key) and value is not None:
                    setattr(company_user, key, value)
            
            db.commit()
            db.refresh(company_user)
            
            return company_user
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating company user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating company user"
            ) from e
    
    @staticmethod
    async def remove_user_from_company(company_user_id: uuid.UUID, db: Session):
        """
        Remove a user from a company
        
        Args:
            company_user_id: ID of the company user association
            db: Database session
            
        Returns:
            bool: True if successful
        """
        try:
            company_user = db.query(CompanyUser).filter(
                CompanyUser.id == company_user_id
            ).first()
            
            if not company_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company user association not found"
                )
            
            db.delete(company_user)
            db.commit()
            
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error removing user from company: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error removing user from company"
            ) from e
    
    @staticmethod
    async def add_company_contact(company_id: uuid.UUID, contact_data: Dict[str, Any], db: Session):
        """
        Add a contact to a company
        
        Args:
            company_id: ID of the company
            contact_data: Contact data
            db: Database session
            
        Returns:
            CompanyContact: The created company contact
        """
        try:
            # Check if company exists
            company = db.query(Company).filter(Company.id == company_id).first()
            if not company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company not found"
                )
            
            # Create contact
            contact_data['company_id'] = company_id
            contact = CompanyContact(**contact_data)
            
            db.add(contact)
            db.commit()
            db.refresh(contact)
            
            return contact
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error adding company contact: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error adding company contact"
            ) from e
    
    @staticmethod
    async def update_company_contact(contact_id: uuid.UUID, update_data: Dict[str, Any], db: Session):
        """
        Update a company contact
        
        Args:
            contact_id: ID of the contact
            update_data: Data to update
            db: Database session
            
        Returns:
            CompanyContact: The updated company contact
        """
        try:
            contact = db.query(CompanyContact).filter(
                CompanyContact.id == contact_id
            ).first()
            
            if not contact:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company contact not found"
                )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(contact, key) and value is not None:
                    setattr(contact, key, value)
            
            db.commit()
            db.refresh(contact)
            
            return contact
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating company contact: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating company contact"
            ) from e
    
    @staticmethod
    async def delete_company_contact(contact_id: uuid.UUID, db: Session):
        """
        Delete a company contact
        
        Args:
            contact_id: ID of the contact
            db: Database session
            
        Returns:
            bool: True if successful
        """
        try:
            contact = db.query(CompanyContact).filter(
                CompanyContact.id == contact_id
            ).first()
            
            if not contact:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company contact not found"
                )
            
            db.delete(contact)
            db.commit()
            
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting company contact: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting company contact"
            ) from e