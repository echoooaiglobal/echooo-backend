# routes/api/v0/auth.py - FIXED with complete-company-registration endpoint
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional

from app.Http.Controllers.AuthController import AuthController
from app.Models.auth_models import User
from app.Schemas.auth import (
    UserCreate, UserResponse, TokenResponse, RefreshTokenRequest, 
    LogoutRequest, UserUpdate, PasswordResetRequest, PasswordReset, UserDetailResponse,
    EmailVerificationToken, EmailVerificationResponse,
    ResendVerificationRequest, ManualVerificationRequest,
    PasswordUpdate, PasswordUpdateResponse
)
from app.Utils.Helpers import get_current_active_user, get_current_user
from config.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    return await AuthController.register(user_data, background_tasks, db)

@router.post("/create-admin", response_model=UserResponse)
async def create_admin(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new platform admin (restricted to existing platform admins)"""
    return await AuthController.create_admin(user_data, db)

@router.post("/login", response_model=None)  # We use None to accept OAuth2PasswordRequestForm
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate a user and return tokens"""
    return await AuthController.login(form_data, db)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Issue a new access token using a refresh token"""
    return await AuthController.refresh_token(refresh_data.refresh_token, db)

@router.post("/logout")
async def logout(
    logout_data: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke a refresh token to logout a user"""
    return await AuthController.logout(logout_data.refresh_token, current_user, db)

@router.post("/password-reset-request")
async def request_password_reset(
    email_data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request a password reset token"""
    return await AuthController.request_password_reset(email_data, background_tasks, db)

@router.post("/password-reset")
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """Reset a user's password using a reset token"""
    return await AuthController.reset_password(reset_data, db)

@router.get("/me", response_model=UserDetailResponse)
async def get_me(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Get current user profile with additional details"""
    return await AuthController.get_me(current_user, db)

@router.put("/me", response_model=UserDetailResponse)
async def update_profile(
    # Form fields (for multipart/form-data)
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    full_name: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    # File upload
    profile_image: Optional[UploadFile] = File(None),
    # Keep current user and db
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile with optional image upload
    
    Accepts multipart/form-data with:
    - Text fields: first_name, last_name, full_name, phone_number
    - File field: profile_image (optional)
    
    Frontend should send as FormData, not JSON
    """
    updated_user = await AuthController.update_profile(
        db=db,
        current_user=current_user,
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        phone_number=phone_number,
        profile_image=profile_image  # This will now work!
    )
    
    return UserDetailResponse.from_orm(updated_user)

# JSON-only version for backward compatibility
@router.patch("/me", response_model=UserDetailResponse)
async def update_profile_json(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile (JSON only - no file upload)
    Use this for text-only updates, use PUT /auth/me for file uploads
    """
    updated_user = await AuthController.update_profile(
        db=db,
        current_user=current_user,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        full_name=user_data.full_name,
        phone_number=user_data.phone_number,
        profile_image=None  # No image upload in JSON endpoint
    )
    
    return UserDetailResponse.from_orm(updated_user)

@router.delete("/me/profile-image")
async def delete_current_user_profile_image(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete current user's profile image"""
    return await AuthController.delete_profile_image(db=db, current_user=current_user)


@router.put("/me/password", response_model=PasswordUpdateResponse)
async def update_password(
    password_data: PasswordUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's password
    
    Requires:
    - current_password: User's current password for verification
    - new_password: New password (must meet complexity requirements)
    - confirm_password: Confirmation of new password
    
    Security features:
    - Verifies current password before allowing change
    - Enforces password complexity requirements
    - Prevents using the same password as current
    - Revokes all refresh tokens (optional security measure)
    """
    return await AuthController.update_password(password_data, current_user, db)

@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    token_data: EmailVerificationToken,
    db: Session = Depends(get_db)
):
    """Verify user's email address using verification token"""
    return await AuthController.verify_email(token_data, db)

@router.post("/resend-verification")
async def resend_verification_email(
    email_data: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Resend email verification link"""
    return await AuthController.resend_verification_email(email_data, background_tasks, db)

@router.get("/verification-status/{user_id}")
async def get_verification_status(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get verification status for a user (admin only or self)"""
    # Check if user is admin or requesting their own status
    is_admin = any(role.name == "platform_admin" for role in current_user.roles)
    if not is_admin and str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own verification status"
        )
    
    return await AuthController.get_verification_status(user_id, db)

# FIX: Add the complete-company-registration endpoint
@router.post("/complete-company-registration")
async def complete_company_registration(
    company_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Complete company registration for OAuth users"""
    return await AuthController.complete_company_registration(company_data, current_user, db)

# Development/Testing endpoints
@router.post("/manual-verify")
async def manual_verify_user(
    verification_data: ManualVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually verify a user (development/admin only)"""
    return await AuthController.manual_verify_user(verification_data, current_user, db)

@router.get("/dev/verification-tokens")
async def list_verification_tokens(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all verification tokens (development only - admin access)"""
    is_admin = any(role.name == "platform_admin" for role in current_user.roles)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    from app.Models.auth_models import EmailVerificationToken
    tokens = db.query(EmailVerificationToken).join(User).all()
    
    return [
        {
            "token": token.token,
            "user_email": token.user.email,
            "user_id": str(token.user.id),
            "expires_at": token.expires_at,
            "is_used": token.is_used,
            "created_at": token.created_at
        }
        for token in tokens
    ]