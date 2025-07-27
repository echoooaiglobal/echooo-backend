# routes/api/v0/oauth.py - UPDATED to use standardized OAuthCallbackResponse
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.Http.Controllers.OAuthController import OAuthController
from app.Models.auth_models import User
from app.Schemas.oauth_schemas import (
    OAuthAuthorizationRequest, OAuthAuthorizationResponse,
    OAuthCallbackResponse, LinkedAccountsResponse, UnlinkAccountResponse,
    OAuthProvidersResponse, OAuthSuccessResponse
)
from app.Utils.Helpers import get_current_user
from config.database import get_db

router = APIRouter(prefix="/auth/oauth", tags=["OAuth Authentication"])

@router.get("/providers", response_model=OAuthProvidersResponse)
async def get_oauth_providers():
    """Get available OAuth providers and their configuration"""
    oauth_controller = OAuthController()
    return await oauth_controller.get_oauth_providers()

@router.get("/{provider}/login", response_model=OAuthAuthorizationResponse)
async def oauth_login(
    provider: str,
    request: Request,
    user_type: Optional[str] = Query(None, description="User type for new registrations (influencer, b2c, platform)")
):
    """
    Initiate OAuth login flow with user type context
    
    The user_type parameter is encoded into the state parameter
    so it survives the OAuth redirect flow.
    """
    oauth_controller = OAuthController()
    return await oauth_controller.initiate_oauth(provider, request, link_mode=False, user_type=user_type)

@router.get("/{provider}/link", response_model=OAuthAuthorizationResponse)
async def oauth_link_account(
    provider: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Link social account to existing user account
    """
    oauth_controller = OAuthController()
    return await oauth_controller.initiate_oauth(provider, request, link_mode=True)

@router.get("/callback/{provider}", response_model=OAuthCallbackResponse)
async def oauth_callback(
    provider: str,
    code: str = Query(..., description="Authorization code from OAuth provider"),
    state: str = Query(..., description="State parameter with encoded user type context"),
    link: Optional[str] = Query(None, description="Link mode indicator"),
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback - NOW RETURNS STANDARDIZED LoginResponse FORMAT
    
    The response now matches the standard LoginResponse structure from auth.py
    with additional OAuth-specific fields for enhanced functionality.
    """
    oauth_controller = OAuthController()
    
    link_mode = link == "true"
    current_user = None
    
    return await oauth_controller.handle_oauth_callback(
        provider, code, state, db, link_mode, current_user
    )

@router.get("/accounts", response_model=LinkedAccountsResponse)
async def get_linked_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's linked OAuth accounts"""
    oauth_controller = OAuthController()
    return await oauth_controller.get_linked_accounts(current_user, db)

@router.delete("/accounts/{account_id}", response_model=UnlinkAccountResponse)
async def unlink_oauth_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unlink a social account"""
    oauth_controller = OAuthController()
    return await oauth_controller.unlink_oauth_account(current_user, account_id, db)

@router.post("/refresh/{account_id}", response_model=OAuthSuccessResponse)
async def refresh_oauth_token(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Refresh OAuth access token"""
    oauth_controller = OAuthController()
    
    try:
        from app.Models.oauth_accounts import OAuthAccount
        from app.Services.OAuthService import OAuthService
        
        oauth_account = db.query(OAuthAccount).filter(
            OAuthAccount.id == account_id,
            OAuthAccount.user_id == current_user.id,
            OAuthAccount.is_active == True
        ).first()
        
        if not oauth_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OAuth account not found"
            )
        
        oauth_service = OAuthService()
        success = await oauth_service.refresh_access_token(oauth_account, db)
        
        if success:
            return OAuthSuccessResponse(
                message=f"{oauth_account.provider.title()} token refreshed successfully",
                data={
                    "account_id": account_id,
                    "provider": oauth_account.provider,
                    "expires_at": oauth_account.expires_at.isoformat() if oauth_account.expires_at else None
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to refresh token. Please reconnect your account."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error refreshing token: {str(e)}"
        )

@router.get("/health")
async def oauth_health_check():
    """Health check endpoint for OAuth functionality"""
    return {
        "status": "healthy",
        "service": "OAuth Authentication API",
        "supported_providers": ["google", "facebook", "instagram", "linkedin"],
        "features": [
            "Social Media Login/Signup",
            "Account Linking", 
            "Token Management",
            "Multi-Provider Support",
            "Standardized LoginResponse Format"
        ],
        "response_format": "Matches standard LoginResponse from /auth/login"
    }