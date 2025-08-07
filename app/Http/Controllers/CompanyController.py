# app/Http/Controllers/CompanyController.py
from sqlalchemy.orm import Session
import uuid

from app.Models.auth_models import User
from app.Schemas.company import (
    CompanyCreate, CompanyUpdate, CompanyResponse,
    CompanyUserCreate, CompanyUserUpdate, CompanyUserResponse,
    CompanyContactCreate, CompanyContactUpdate, CompanyContactResponse
)
from app.Services.CompanyService import CompanyService
from app.Utils.Logger import logger

class CompanyController:
    """Controller for company-related endpoints"""
    
    @staticmethod
    async def create_company(
        company_data: CompanyCreate,
        current_user: User,
        db: Session
    ):
        """Create a new company"""
        try:
            company = await CompanyService.create_company(
                company_data.dict(),
                current_user.id,
                db
            )
            return CompanyResponse.from_orm(company)
        except Exception as e:
            logger.error(f"Error in create_company controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_company(
        company_id: uuid.UUID,
        db: Session
    ):
        """Get a company by ID"""
        try:
            company = await CompanyService.get_company_by_id(company_id, db)
            return CompanyResponse.from_orm(company)
        except Exception as e:
            logger.error(f"Error in get_company controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_company(
        company_id: uuid.UUID,
        company_data: CompanyUpdate,
        db: Session
    ):
        """Update a company"""
        try:
            company = await CompanyService.update_company(
                company_id,
                company_data.dict(exclude_unset=True),
                db
            )
            return CompanyResponse.from_orm(company)
        except Exception as e:
            logger.error(f"Error in update_company controller: {str(e)}")
            raise
    
    @staticmethod
    async def delete_company(
        company_id: uuid.UUID,
        db: Session
    ):
        """Delete a company"""
        try:
            await CompanyService.delete_company(company_id, db)
            return {"message": "Company deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_company controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_company_users(
        company_id: uuid.UUID,
        db: Session
    ):
        """Get all users of a company"""
        try:
            company_users = await CompanyService.get_company_users(company_id, db)
            return [CompanyUserResponse.from_orm(user) for user in company_users]
        except Exception as e:
            logger.error(f"Error in get_company_users controller: {str(e)}")
            raise
    
    @staticmethod
    async def add_company_user(
        company_id: uuid.UUID,
        user_data: CompanyUserCreate,
        db: Session
    ):
        """Add a user to a company"""
        try:
            user_data_dict = user_data.dict()
            user_data_dict['company_id'] = company_id
            company_user = await CompanyService.add_user_to_company(
                company_id,
                user_data_dict,
                db
            )
            return CompanyUserResponse.from_orm(company_user)
        except Exception as e:
            logger.error(f"Error in add_company_user controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_company_user(
        company_user_id: uuid.UUID,
        user_data: CompanyUserUpdate,
        db: Session
    ):
        """Update a company user association"""
        try:
            company_user = await CompanyService.update_company_user(
                company_user_id,
                user_data.dict(exclude_unset=True),
                db
            )
            return CompanyUserResponse.from_orm(company_user)
        except Exception as e:
            logger.error(f"Error in update_company_user controller: {str(e)}")
            raise
    
    @staticmethod
    async def remove_company_user(
        company_user_id: uuid.UUID,
        db: Session
    ):
        """Remove a user from a company"""
        try:
            await CompanyService.remove_user_from_company(company_user_id, db)
            return {"message": "User removed from company successfully"}
        except Exception as e:
            logger.error(f"Error in remove_company_user controller: {str(e)}")
            raise
    
    @staticmethod
    async def add_company_contact(
        company_id: uuid.UUID,
        contact_data: CompanyContactCreate,
        db: Session
    ):
        """Add a contact to a company"""
        try:
            contact_data_dict = contact_data.dict()
            contact_data_dict['company_id'] = company_id
            contact = await CompanyService.add_company_contact(
                company_id,
                contact_data_dict,
                db
            )
            return CompanyContactResponse.from_orm(contact)
        except Exception as e:
            logger.error(f"Error in add_company_contact controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_company_contact(
        contact_id: uuid.UUID,
        contact_data: CompanyContactUpdate,
        db: Session
    ):
        """Update a company contact"""
        try:
            contact = await CompanyService.update_company_contact(
                contact_id,
                contact_data.dict(exclude_unset=True),
                db
            )
            return CompanyContactResponse.from_orm(contact)
        except Exception as e:
            logger.error(f"Error in update_company_contact controller: {str(e)}")
            raise
    
    @staticmethod
    async def delete_company_contact(
        contact_id: uuid.UUID,
        db: Session
    ):
        """Delete a company contact"""
        try:
            await CompanyService.delete_company_contact(contact_id, db)
            return {"message": "Company contact deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_company_contact controller: {str(e)}")
            raise