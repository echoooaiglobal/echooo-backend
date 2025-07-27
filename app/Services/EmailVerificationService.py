# app/Services/EmailVerificationService.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
import uuid
from datetime import datetime

from app.Models.auth_models import User, EmailVerificationToken, UserStatus
from app.Utils.Logger import logger

class EmailVerificationService:
    """Service for managing email verification"""

    @staticmethod
    async def create_verification_token(user_id: uuid.UUID, db: Session) -> str:
        """
        Create a new email verification token for a user
        
        Args:
            user_id: ID of the user
            db: Database session
            
        Returns:
            str: The verification token
        """
        try:
            # Check if user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check if user is already verified
            if user.email_verified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is already verified"
                )
            
            # Invalidate any existing tokens for this user
            existing_tokens = db.query(EmailVerificationToken).filter(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.is_used == False
            ).all()
            
            for token in existing_tokens:
                token.is_used = True
            
            # Create new verification token
            verification_token = EmailVerificationToken.create_token(user_id)
            db.add(verification_token)
            db.commit()
            db.refresh(verification_token)
            
            return verification_token.token
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating verification token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating verification token"
            ) from e

    @staticmethod
    async def verify_email_token(token: str, db: Session) -> Dict[str, Any]:
        """
        Verify an email verification token
        
        Args:
            token: The verification token
            db: Database session
            
        Returns:
            Dict: Verification result with user info
        """
        try:
            # Find the token
            verification_token = db.query(EmailVerificationToken).filter(
                EmailVerificationToken.token == token
            ).first()
            
            if not verification_token:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invalid verification token"
                )
            
            # Check if token is valid
            if not verification_token.is_valid():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification token has expired or already been used"
                )
            
            # Get the user
            user = db.query(User).filter(User.id == verification_token.user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Mark token as used
            verification_token.is_used = True
            
            # Verify the user's email and activate account
            user.email_verified = True
            user.status = UserStatus.ACTIVE.value
            
            db.commit()
            db.refresh(user)
            
            return {
                "message": "Email verified successfully",
                "user_id": user.id,
                "email_verified": user.email_verified,
                "status": user.status
            }
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error verifying email token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error verifying email"
            ) from e

    @staticmethod
    async def resend_verification_email(email: str, db: Session) -> str:
        """
        Resend verification email to a user
        
        Args:
            email: User's email address
            db: Database session
            
        Returns:
            str: New verification token
        """
        try:
            # Find user by email
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                # Don't reveal if email exists for security
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="If the email exists, a new verification link will be sent"
                )
            
            # Check if already verified
            if user.email_verified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is already verified"
                )
            
            # Create new token
            token = await EmailVerificationService.create_verification_token(user.id, db)
            
            return token
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resending verification email: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error resending verification email"
            ) from e

    @staticmethod
    async def manual_verify_user(user_id: uuid.UUID, verification_type: str, db: Session) -> Dict[str, Any]:
        """
        Manually verify a user (for development purposes)
        
        Args:
            user_id: ID of the user to verify
            verification_type: Type of verification (email, company, influencer)
            db: Database session
            
        Returns:
            Dict: Verification result
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            result = {"user_id": user.id, "verifications": []}
            
            if verification_type == "email":
                user.email_verified = True
                user.status = UserStatus.ACTIVE.value
                result["verifications"].append("email_verified")
                
            elif verification_type == "b2c" and user.user_type == "b2c":
                user.email_verified = True
                user.status = UserStatus.ACTIVE.value
                result["verifications"].append("b2c_verified")
                result["verifications"].append("email_verified")
                
            elif verification_type == "influencer" and user.user_type == "influencer":
                user.email_verified = True
                user.status = UserStatus.ACTIVE.value
                result["verifications"].append("influencer_verified")
                result["verifications"].append("email_verified")
                
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid verification type '{verification_type}' for user type '{user.user_type}'"
                )
            
            db.commit()
            db.refresh(user)
            
            result["message"] = f"User manually verified: {', '.join(result['verifications'])}"
            result["status"] = user.status
            result["email_verified"] = user.email_verified
            
            return result
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error manually verifying user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error verifying user"
            ) from e

    @staticmethod
    async def get_verification_status(user_id: uuid.UUID, db: Session) -> Dict[str, Any]:
        """
        Get verification status for a user
        
        Args:
            user_id: ID of the user
            db: Database session
            
        Returns:
            Dict: User verification status
        """
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "user_id": user.id,
            "email": user.email,
            "email_verified": user.email_verified,
            "status": user.status,
            "user_type": user.user_type,
            "created_at": user.created_at
        }