# routes/api/v0/auth.py
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.Http.Controllers.AuthController import AuthController
from app.Models.auth_models import User
from app.Schemas.auth import (
    UserCreate, UserResponse, TokenResponse, RefreshTokenRequest, 
    LogoutRequest, UserUpdate, PasswordResetRequest, PasswordReset, UserDetailResponse
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

@router.put("/me", response_model=UserResponse)
async def update_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    return await AuthController.update_profile(user_data, current_user, db)