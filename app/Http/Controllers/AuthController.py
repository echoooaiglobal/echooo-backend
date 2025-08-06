# app/Http/Controllers/AuthController.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import uuid

from app.Services.EmailVerificationService import EmailVerificationService
from app.Schemas.auth import (
    UserCreate, UserResponse, TokenResponse, TokenData, 
    LoginResponse, RoleResponse, PasswordResetRequest, 
    PasswordReset, UserUpdate, CompanyBriefResponse, UserDetailResponse,
    EmailVerificationRequest, EmailVerificationToken, EmailVerificationResponse,
    ResendVerificationRequest, ManualVerificationRequest,
    PasswordUpdate, PasswordUpdateResponse
)
from app.Schemas.company import CompanyCreate
from app.Models.auth_models import User, Role, RefreshToken, UserStatus
from app.Models.company_models import Company, CompanyUser
from app.Services.InfluencerService import InfluencerService
from config.database import get_db
from app.Utils.Helpers import get_current_user, get_current_active_user
from app.Utils.Logger import logger
from config.settings import settings
from app.Services.CompanyService import CompanyService
from app.Services.GoogleCloudStorageService import gcs_service
from app.Utils.Logger import logger

# Configuration for JWT
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

# Password handling
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v0/auth/login")

# Router
router = APIRouter(tags=["Authentication"])

class AuthController:
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate a hashed password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        
        # Convert any UUID objects to strings
        for key, value in to_encode.items():
            if isinstance(value, uuid.UUID):
                to_encode[key] = str(value)
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(user_id: int, db: Session) -> str:
        """Create a refresh token and store it in the database"""
        refresh_token = RefreshToken.create_token(user_id, expires_in_days=REFRESH_TOKEN_EXPIRE_DAYS)
        db.add(refresh_token)
        db.commit()
        db.refresh(refresh_token)
        return refresh_token.token
    
    @staticmethod
    async def register(user_data: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
        """Register a new user"""
        # Check if email already registered
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        db_user = User(
            email=user_data.email,
            hashed_password=AuthController.get_password_hash(user_data.password),
            full_name=user_data.full_name,
            phone_number=user_data.phone_number,
            status=UserStatus.PENDING.value,
            user_type=user_data.user_type
        )
        
        # Add default role or specific role if provided
        if hasattr(user_data, 'role_name') and user_data.role_name:
            # If specific role requested, check if it exists and matches user type
            role = db.query(Role).filter(Role.name == user_data.role_name).first()
            
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role '{user_data.role_name}' not found"
                )
            
            # Validate role matches user type
            if user_data.user_type == "platform" and not role.name.startswith("platform_"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role '{role.name}' is not a platform role"
                )
            elif user_data.user_type == "b2c" and not role.name.startswith("b2c_"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role '{role.name}' is not a b2c role"
                )
            elif user_data.user_type == "influencer" and not (role.name == "influencer" or role.name == "influencer_manager"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role '{role.name}' is not an influencer role"
                )
        else:
            # Default role assignment
            if user_data.user_type == "platform":
                role = db.query(Role).filter(Role.name == "platform_user").first()
            elif user_data.user_type == "b2c":
                role = db.query(Role).filter(Role.name == "b2c_company_admin").first()
            elif user_data.user_type == "influencer":
                role = db.query(Role).filter(Role.name == "influencer").first()
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid user type"
                )
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Role not found"
            )
        
        db_user.roles.append(role)
        
        # Start transaction
        try:
            # Different flows based on user type
            if user_data.user_type == "platform":
                # For platform users, just save the user
                db.add(db_user)
                db.commit()
                db.refresh(db_user)
                
            elif user_data.user_type == "b2c":
                company_id = getattr(user_data, 'company_id', None)
                company_name = getattr(user_data, 'company_name', None)
                
                # First save the user to get the ID
                db.add(db_user)
                db.commit()
                db.refresh(db_user)
                
                if company_id is not None:
                    # User specified an existing company - associate with it
                    try:
                        # Convert string to UUID
                        company_id_uuid = uuid.UUID(company_id)
                        company = db.query(Company).filter(Company.id == company_id_uuid).first()
                        
                        if not company:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Company not found"
                            )
                        
                        # Create association using CompanyUser model
                        company_user = CompanyUser(
                            company_id=company.id,
                            user_id=db_user.id,
                            role_id=role.id,
                            is_primary=True
                        )
                        
                        db.add(company_user)
                        db.commit()
                    except ValueError:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid company ID format"
                        )
                elif company_name is not None:
                    # User wants to create a new company
                    try:
                        # Create company data dictionary
                        company_data = {
                            "name": company_name,
                            "domain": getattr(user_data, 'company_domain', None)
                        }
                        
                        # Create a new company
                        company = await CompanyService.create_company(
                            company_data,
                            db_user.id,
                            db
                        )
                        
                    except Exception as e:
                        # If company creation fails, rollback and report error
                        logger.error(f"Error creating company during registration: {str(e)}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error creating company: {str(e)}"
                        )
                # If neither company_id nor company_name provided, user will be created
                # without a company association
                    
            elif user_data.user_type == "influencer":
                # For influencers, create user and influencer profile
                db.add(db_user)
                db.commit()
                db.refresh(db_user)
                
                # Create influencer profile
                await InfluencerService.create_influencer_profile(db_user.id, db)
            
            try:
                # Create email verification token
                verification_token = await EmailVerificationService.create_verification_token(db_user.id, db)
                
                # In production, you would send this token via email
                # For development, you can log it or return it in response
                logger.info(f"Email verification token for {db_user.email}: {verification_token}")
                
                # Here you would typically add email sending to background tasks:
                # background_tasks.add_task(send_verification_email, db_user.email, verification_token)
                
            except Exception as e:
                logger.error(f"Error creating verification token during registration: {str(e)}")
                # Don't fail registration if verification token creation fails
            
            # Return the user
            return UserResponse.model_validate(db_user)
        except Exception as e:
            db.rollback()
            logger.error(f"Error registering user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error registering user: {str(e)}"
            )

    @staticmethod
    async def create_admin(user_data: UserCreate, db: Session):
        """Create a new platform admin"""
        # Check if email already registered
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user with admin privileges
        db_user = User(
            email=user_data.email,
            hashed_password=AuthController.get_password_hash(user_data.password),
            full_name=user_data.full_name,
            phone_number=user_data.phone_number,
            status=UserStatus.ACTIVE.value,  # Active immediately
            email_verified=True,  # Verified immediately
            user_type="platform"
        )
        
        # Add platform_admin role
        admin_role = db.query(Role).filter(Role.name == "platform_admin").first()
        if not admin_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Platform admin role not found"
            )
        
        db_user.roles.append(admin_role)
        
        # Start transaction
        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            # Return the new admin user
            return UserResponse.model_validate(db_user)
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating admin: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating admin: {str(e)}"
            )
    
    @staticmethod
    async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
        """Authenticate a user and return tokens"""
        # Find user by email
        user = db.query(User).filter(User.email == form_data.username).first()
        
        # Validate credentials
        if not user or not AuthController.verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if user.status != UserStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is not active",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last login timestamp
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        # Create tokens - convert UUID to string
        user_id_str = str(user.id)  # Ensure user_id is a string
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthController.create_access_token(
            data={"sub": user.email, "user_id": user_id_str},
            expires_delta=access_token_expires
        )
        
        refresh_token = AuthController.create_refresh_token(user.id, db)
        
        # Get user roles
        roles = [RoleResponse.from_orm(role) for role in user.roles]
        
        # Get company info if user is a company user
        company = None
        if user.user_type == "b2c":
            # Find the company through CompanyUser association
            company_user = db.query(CompanyUser).filter(CompanyUser.user_id == user.id).first()
            if company_user:
                company = db.query(Company).filter(Company.id == company_user.company_id).first()
        
        # Return tokens and user info
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
            roles=roles,
            company=CompanyBriefResponse.model_validate(company) if company else None
        )
    
    @staticmethod
    async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
        """Issue a new access token using a refresh token"""
        # Find the refresh token
        token_record = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        ).first()
        
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get the user
        user = db.query(User).filter(User.id == token_record.user_id).first()
        if not user or user.status != UserStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive or not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthController.create_access_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    @staticmethod
    async def logout(refresh_token: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        """Revoke a refresh token to logout a user"""
        # Find and revoke the token
        token_record = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_revoked == False
        ).first()
        
        if token_record:
            token_record.is_revoked = True
            db.commit()
        
        return {"message": "Successfully logged out"}
    
    @staticmethod
    async def request_password_reset(email_data: PasswordResetRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
        """Request a password reset token"""
        user = db.query(User).filter(User.email == email_data.email).first()
        
        # Always return success even if email not found (for security)
        if not user:
            return {"message": "If your email is registered, you will receive a password reset link"}
        
        # Generate reset token
        reset_token = str(uuid.uuid4())
        # Here you would normally store this token with an expiration in your database
        # and associate it with the user
        
        # Send password reset email (background task)
        # background_tasks.add_task(send_password_reset_email, user.email, reset_token)
        return { "token": reset_token, "message": "If your email is registered, you will receive a password reset link" }
        return {"message": "If your email is registered, you will receive a password reset link"}
    
    @staticmethod
    async def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
        """Reset a user's password using a reset token"""
        # Here you would validate the reset token against what's stored in your database
        # For now, this is a placeholder
        
        # Find user by email (in production, you'd find by token)
        user = db.query(User).filter(User.email == reset_data.email).first()
        
        if not user:
            # For security, don't reveal that the email doesn't exist
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Update password
        user.hashed_password = AuthController.get_password_hash(reset_data.new_password)
        
        # Revoke all refresh tokens for this user
        db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update({"is_revoked": True})
        
        db.commit()
        
        return {"message": "Password has been reset successfully"}
    
    @staticmethod
    async def get_me(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
        """Get current user profile with additional details"""
        # Get user roles
        roles = [RoleResponse.model_validate(role) for role in current_user.roles]
        
        # Get company info if user is a company user
        company = None
        if current_user.user_type == "b2c":
            # Find the company through CompanyUser association
            company_user = db.query(CompanyUser).filter(CompanyUser.user_id == current_user.id).first()
            if company_user:
                company = db.query(Company).filter(Company.id == company_user.company_id).first()
        
        # Create response with company info
        response = UserDetailResponse.model_validate(current_user)
        response.roles = roles
        if company:
            response.company = CompanyBriefResponse.model_validate(company)
        
        return response
    
    @staticmethod
    async def update_profile(
        db: Session, 
        current_user,
        # Form data for profile fields
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        full_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        # File upload for profile image
        profile_image: Optional[UploadFile] = None
    ):
        """
        Update user profile with new fields and optional image upload
        Supports both individual field updates and image upload in one call
        """
        try:
            # Check if user is soft deleted
            if current_user.is_deleted:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot modify deleted user profile"
                )
            
            # Track if any changes were made
            changes_made = False
            print(f"profile_image:1", profile_image)
            # Handle profile image upload first (if provided)
            if profile_image and profile_image.filename:
                print(f"profile_image:2", profile_image.filename)
                try:
                    # Upload new image to GCS
                    file_path, public_url = await gcs_service.upload_profile_image(
                        file=profile_image,
                        user_id=str(current_user.id),
                        optimize=True
                    )
                    
                    # Delete old profile image if exists - UNCOMMENT THESE LINES:
                    if current_user.profile_image_url:
                        old_file_path = current_user.profile_image_url.split('/')[-2:]
                        if len(old_file_path) == 2:
                            old_path = f"profile-images/{old_file_path[0]}/{old_file_path[1]}"
                            await gcs_service.delete_profile_image(old_path)
                    
                    # Update profile image URL - UNCOMMENT THESE LINES:
                    current_user.profile_image_url = public_url
                    changes_made = True
                    logger.info(f"Profile image updated for user {current_user.id}")

                except Exception as e:
                    logger.error(f"Failed to upload profile image for user {current_user.id}: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to upload profile image: {str(e)}"
                    )
            
            # Update name fields
            if first_name is not None:
                # Validate and clean first name
                first_name = first_name.strip()
                if first_name and not first_name.replace(' ', '').replace('-', '').replace("'", '').isalpha():
                    raise HTTPException(
                        status_code=400,
                        detail="First name can only contain letters, spaces, hyphens, and apostrophes"
                    )
                current_user.first_name = first_name or None
                changes_made = True
            
            if last_name is not None:
                # Validate and clean last name
                last_name = last_name.strip()
                if last_name and not last_name.replace(' ', '').replace('-', '').replace("'", '').isalpha():
                    raise HTTPException(
                        status_code=400,
                        detail="Last name can only contain letters, spaces, hyphens, and apostrophes"
                    )
                current_user.last_name = last_name or None
                changes_made = True
            
            # Auto-update full_name if first_name or last_name changed
            if first_name is not None or last_name is not None:
                if current_user.first_name and current_user.last_name:
                    current_user.full_name = f"{current_user.first_name} {current_user.last_name}"
                elif current_user.first_name:
                    current_user.full_name = current_user.first_name
                elif current_user.last_name:
                    current_user.full_name = current_user.last_name
                elif full_name:  # Use provided full_name if individual names are empty
                    current_user.full_name = full_name.strip()
                # If all are empty, keep existing full_name (don't make it null due to constraint)
            
            # Update full_name directly if provided (backward compatibility)
            elif full_name is not None:
                current_user.full_name = full_name.strip()
                changes_made = True
            
            # Update phone number
            if phone_number is not None:
                current_user.phone_number = phone_number.strip() or None
                changes_made = True
            print(f"changes_made::", changes_made)
            # Only commit if changes were made
            if changes_made:
                db.commit()
                db.refresh(current_user)
                logger.info(f"Profile updated for user {current_user.id}")
            
            return current_user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating profile for user {current_user.id}: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to update profile"
            )
    
    @staticmethod
    async def delete_profile_image(db: Session, current_user):
        """Delete user's profile image"""
        try:
            # Check if user is soft deleted
            if current_user.is_deleted:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot modify deleted user profile"
                )
            
            if not current_user.profile_image_url:
                raise HTTPException(
                    status_code=400,
                    detail="No profile image to delete"
                )
            
            # Extract file path from URL and delete from GCS
            url_parts = current_user.profile_image_url.split('/')
            if len(url_parts) >= 2:
                file_path = f"profile-images/{url_parts[-2]}/{url_parts[-1]}"
                await gcs_service.delete_profile_image(file_path)
            
            # Update database
            current_user.profile_image_url = None
            db.commit()
            db.refresh(current_user)
            
            logger.info(f"Profile image deleted for user {current_user.id}")
            return {"message": "Profile image deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete profile image for user {current_user.id}: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to delete profile image"
            )
    
    @staticmethod
    async def verify_email(token_data: EmailVerificationToken, db: Session):
        """Verify user's email address"""
        result = await EmailVerificationService.verify_email_token(token_data.token, db)
        return EmailVerificationResponse(**result)
    
    @staticmethod
    async def resend_verification_email(
        email_data: ResendVerificationRequest, 
        background_tasks: BackgroundTasks,
        db: Session
    ):
        """Resend email verification link"""
        try:
            token = await EmailVerificationService.resend_verification_email(email_data.email, db)
            
            # In production, send email via background task
            # background_tasks.add_task(send_verification_email, email_data.email, token)
            
            # For development, log the token
            logger.info(f"New verification token for {email_data.email}: {token}")
            
            return {
                "message": "If the email exists and is not verified, a new verification link has been sent",
                "token": token  # Remove this in production
            }
        except Exception as e:
            logger.error(f"Error resending verification email: {str(e)}")
            return {
                "message": "If the email exists and is not verified, a new verification link has been sent"
            }
    
    @staticmethod
    async def manual_verify_user(
        verification_data: ManualVerificationRequest,
        current_user: User,
        db: Session
    ):
        """Manually verify a user (development only)"""
        # Check if current user is platform admin
        is_admin = any(role.name == "platform_super_admin" or role.name == "platform_admin" for role in current_user.roles)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only platform admins can manually verify users"
            )
        
        try:
            user_id = uuid.UUID(verification_data.user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        result = await EmailVerificationService.manual_verify_user(
            user_id,
            verification_data.verification_type,
            db
        )
        
        return result
    
    @staticmethod
    async def get_verification_status(user_id: str, db: Session):
        """Get verification status for a user"""
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        return await EmailVerificationService.get_verification_status(user_uuid, db)
    
    @staticmethod
    async def complete_company_registration(
        company_data: dict,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Complete company registration for OAuth users"""
        try:
            # FIX: Instead of checking if user is already a company user,
            # check if they already have a complete company setup
            
            # Validate company data
            company_name = company_data.get('company_name', '').strip()
            company_domain = company_data.get('company_domain', '').strip()
            
            if not company_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Company name is required"
                )
            
            if not company_domain:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Company domain is required"
                )
            
            # Check if user already has a fully configured company
            existing_company_user = db.query(CompanyUser).filter(CompanyUser.user_id == current_user.id).first()
            
            if existing_company_user:
                existing_company = db.query(Company).filter(Company.id == existing_company_user.company_id).first()
                
                # If company exists and has both name and domain set, and they're not placeholder values
                if (existing_company and 
                    existing_company.name and 
                    existing_company.domain and
                    not existing_company.name.endswith("'s Company") and  # Not a placeholder
                    existing_company.domain != company_domain):  # Allow updating if domain is different
                    
                    # FIX: Allow updating existing company instead of rejecting
                    logger.info(f"Updating existing company {existing_company.id} for user {current_user.id}")
                    
                    # Update the existing company
                    existing_company.name = company_name
                    existing_company.domain = company_domain
                    existing_company.updated_at = datetime.utcnow()
                    
                    db.commit()
                    db.refresh(existing_company)
                    
                    # Update user type if not already set to b2c
                    if current_user.user_type != "b2c":
                        current_user.user_type = "b2c"
                        db.commit()
                        db.refresh(current_user)
                    
                    return {
                        "message": "Company information updated successfully",
                        "user": UserResponse.model_validate(current_user),
                        "company": CompanyBriefResponse.model_validate(existing_company)
                    }
                
                elif existing_company:
                    # Update placeholder company with real data
                    logger.info(f"Updating placeholder company {existing_company.id} for user {current_user.id}")
                    
                    existing_company.name = company_name
                    existing_company.domain = company_domain
                    existing_company.updated_at = datetime.utcnow()
                    
                    db.commit()
                    db.refresh(existing_company)
                    
                    # Ensure user type is set to b2c
                    if current_user.user_type != "b2c":
                        current_user.user_type = "b2c"
                        db.commit()
                    
                    return {
                        "message": "Company registration completed successfully",
                        "user": UserResponse.model_validate(current_user),
                        "company": CompanyBriefResponse.model_validate(existing_company)
                    }
            
            # No existing company association, create new company and association
            logger.info(f"Creating new company for user {current_user.id}")
            
            # Set user type to b2c if not already set
            if current_user.user_type != "b2c":
                current_user.user_type = "b2c"
            
            # Ensure user has b2c_company_admin role
            b2c_company_admin_role = db.query(Role).filter(Role.name == "b2c_company_admin").first()
            
            if not b2c_company_admin_role:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="B2C company admin role not found"
                )
            
            # Add b2c_company_admin role if not already present
            if b2c_company_admin_role not in current_user.roles:
                # Clear existing roles and add b2c_company_admin role
                current_user.roles.clear()
                current_user.roles.append(b2c_company_admin_role)
            
            # Create company using CompanyService
            from app.Services.CompanyService import CompanyService
            
            company = await CompanyService.create_company(
                {
                    "name": company_name,
                    "domain": company_domain
                },
                current_user.id,
                db
            )
            
            db.commit()
            db.refresh(current_user)
            
            logger.info(f"Successfully completed company registration for user {current_user.id}")
            
            return {
                "message": "Company registration completed successfully",
                "user": UserResponse.model_validate(current_user),
                "company": CompanyBriefResponse.model_validate(company)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error completing company registration: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error completing company registration: {str(e)}"
            )
        
    @staticmethod
    async def update_password(password_data: 'PasswordUpdate', current_user: User, db: Session):
        """Update current user's password"""
        try:
            # Verify current password
            if not AuthController.verify_password(password_data.current_password, current_user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            # Check if new password is different from current password
            if AuthController.verify_password(password_data.new_password, current_user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New password must be different from current password"
                )
            
            # Update password
            current_user.hashed_password = AuthController.get_password_hash(password_data.new_password)
            
            # Optional: Revoke all refresh tokens for security (force re-login on all devices)
            db.query(RefreshToken).filter(RefreshToken.user_id == current_user.id).update({"is_revoked": True})
            
            # Update password changed timestamp (if you have this field)
            # current_user.password_changed_at = datetime.utcnow()
            
            db.commit()
            
            return {"message": "Password updated successfully. Please log in again."}
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Error updating password for user {current_user.id}: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while updating password"
            )