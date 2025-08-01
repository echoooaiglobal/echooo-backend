# app/Http/Controllers/AgentSocialConnectionController.py
from fastapi import HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import secrets
import json
import base64
import httpx
from datetime import datetime, timedelta

from app.Models.auth_models import User
from app.Models.platforms import Platform
from app.Models.agent_social_connections import AgentSocialConnection
from app.Services.AgentSocialConnectionService import AgentSocialConnectionService
from app.Services.InstagramIntegrationService import InstagramIntegrationService
from app.Schemas.agent_social_connection import (
    AgentSocialConnectionCreate, AgentSocialConnectionUpdate,
    AgentSocialConnectionResponse, AgentSocialConnectionDetailResponse,
    AgentSocialConnectionsPaginatedResponse, UserPlatformConnectionsStatus,
    TokenValidationRequest, TokenValidationResponse,
    AutomationToggleRequest, AutomationStatusResponse,
    ConnectionHealthCheck, SystemHealthReport,
    BulkConnectionUpdate, BulkOperationResponse,
    PlatformConnectionRequest, PlatformConnectionInitiateRequest,
    OAuthInitiateResponse, OAuthCallbackResponse, OAuthStatusResponse
)
from app.Utils.Logger import logger
from config.settings import settings

class AgentSocialConnectionController:
    """Controller for agent social connections endpoints"""

    # =============================================================================
    # OAUTH FLOW METHODS
    # =============================================================================

    @staticmethod
    async def initiate_platform_connection(
        platform_request: PlatformConnectionInitiateRequest,
        current_user: User,
        db: Session
    ) -> OAuthInitiateResponse:
        """Initiate OAuth flow for platform connection"""
        
        try:
            # Get platform info
            platform = db.query(Platform).filter(
                Platform.id == platform_request.platform_id
            ).first()
            
            
            if not platform:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Platform not found"
                )
            
            # Check if user already has connection for this platform
            existing_connection = db.query(AgentSocialConnection).filter(
                AgentSocialConnection.user_id == current_user.id,
                AgentSocialConnection.platform_id == platform_request.platform_id,
                AgentSocialConnection.is_active == True,
                AgentSocialConnection.deleted_at.is_(None)
            ).first()
            
            if existing_connection:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"You already have an active {platform.name} connection"
                )
            
            # Generate secure state for OAuth
            state_data = {
                "user_id": str(current_user.id),
                "platform_id": platform_request.platform_id,
                "timestamp": datetime.utcnow().isoformat(),
                "nonce": secrets.token_urlsafe(16)
            }
            
            encoded_state = base64.b64encode(
                json.dumps(state_data).encode()
            ).decode()
            
            # Platform-specific OAuth configurations
            oauth_configs = {
                "instagram": {
                    "auth_url": "https://api.instagram.com/oauth/authorize",
                    "client_id": settings.INSTAGRAM_APP_ID,
                    "scope": "user_profile,user_media,instagram_basic",
                    "redirect_uri": f"{settings.BASE_URL}/api/v0/agent-social-connections/oauth-callback/instagram"
                },
                "facebook": {
                    "auth_url": "https://www.facebook.com/v19.0/dialog/oauth",
                    "client_id": settings.FACEBOOK_APP_ID,
                    "scope": "pages_manage_posts,pages_messaging,instagram_basic,instagram_manage_messages,pages_read_engagement",
                    "redirect_uri": f"{settings.BASE_URL}/api/v0/agent-social-connections/oauth-callback/facebook"
                },
                "whatsapp": {
                    "auth_url": "https://www.facebook.com/v19.0/dialog/oauth",
                    "client_id": settings.FACEBOOK_APP_ID,
                    "scope": "whatsapp_business_messaging,whatsapp_business_management",
                    "redirect_uri": f"{settings.BASE_URL}/api/v0/agent-social-connections/oauth-callback/whatsapp"
                }
            }
            
            platform_name = platform.name.lower()
            if platform_name not in oauth_configs:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"OAuth not supported for {platform.name}"
                )
            
            config = oauth_configs[platform_name]
            
            # Add additional scopes if provided
            scopes = config['scope']
            if platform_request.additional_scopes:
                scopes += "," + ",".join(platform_request.additional_scopes)
            
            # Build authorization URL
            authorization_url = (
                f"{config['auth_url']}"
                f"?client_id={config['client_id']}"
                f"&redirect_uri={config['redirect_uri']}"
                f"&scope={scopes}"
                f"&response_type=code"
                f"&state={encoded_state}"
            )
            
            logger.info(f"Initiated OAuth flow for user {current_user.id} on platform {platform.name}")
            
            return OAuthInitiateResponse(
                authorization_url=authorization_url,
                state=encoded_state,
                platform=platform.name,
                expires_in=600,  # 10 minutes
                instructions=f"Visit the authorization URL to connect your {platform.name} account"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error initiating OAuth flow: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initiate OAuth flow"
            )

    @staticmethod
    async def handle_oauth_callback(
        platform: str,
        code: str,
        state: str,
        error: Optional[str],
        error_description: Optional[str],
        db: Session
    ) -> RedirectResponse:
        """Handle OAuth callback and create connection"""
        
        try:
            # Handle OAuth errors
            if error:
                error_msg = error_description or error
                logger.error(f"OAuth error for {platform}: {error_msg}")
                return RedirectResponse(
                    url=f"{settings.FRONTEND_URL}/settings/connected-accounts?error=true&message={error_msg}&platform={platform}",
                    status_code=302
                )
            
            # Decode and validate state
            try:
                decoded_state = base64.b64decode(state.encode()).decode()
                state_data = json.loads(decoded_state)
            except Exception as e:
                logger.error(f"Invalid state parameter: {str(e)}")
                return RedirectResponse(
                    url=f"{settings.FRONTEND_URL}/settings/connected-accounts?error=true&message=Invalid+state+parameter&platform={platform}",
                    status_code=302
                )
            
            user_id = state_data.get("user_id")
            platform_id = state_data.get("platform_id")
            
            # Get user and platform
            user = db.query(User).filter(User.id == user_id).first()
            platform_obj = db.query(Platform).filter(Platform.id == platform_id).first()
            
            if not user or not platform_obj:
                return RedirectResponse(
                    url=f"{settings.FRONTEND_URL}/settings/connected-accounts?error=true&message=Invalid+user+or+platform&platform={platform}",
                    status_code=302
                )
            
            # Handle platform-specific OAuth
            connection = None
            if platform.lower() == "instagram":
                connection = await AgentSocialConnectionController._handle_instagram_oauth(
                    code, user, platform_obj, db
                )
            elif platform.lower() == "facebook":
                connection = await AgentSocialConnectionController._handle_facebook_oauth(
                    code, user, platform_obj, db
                )
            elif platform.lower() == "whatsapp":
                connection = await AgentSocialConnectionController._handle_whatsapp_oauth(
                    code, user, platform_obj, db
                )
            else:
                return RedirectResponse(
                    url=f"{settings.FRONTEND_URL}/settings/connected-accounts?error=true&message=Unsupported+platform&platform={platform}",
                    status_code=302
                )
            
            # Success redirect
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/settings/connected-accounts?success=true&platform={platform}&connection_id={connection.id}&username={connection.platform_username}",
                status_code=302
            )
            
        except Exception as e:
            logger.error(f"OAuth callback error for {platform}: {str(e)}")
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/settings/connected-accounts?error=true&message=Connection+failed&platform={platform}",
                status_code=302
            )

    @staticmethod
    async def get_oauth_status(
        platform: str,
        state: str,
        current_user: User,
        db: Session
    ) -> OAuthStatusResponse:
        """Check OAuth connection status"""
        
        try:
            # Decode state to get connection info
            decoded_state = base64.b64decode(state.encode()).decode()
            state_data = json.loads(decoded_state)
            
            user_id = state_data.get("user_id")
            platform_id = state_data.get("platform_id")
            
            if str(user_id) != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="State does not match current user"
                )
            
            # Check if connection was created
            connection = db.query(AgentSocialConnection).filter(
                AgentSocialConnection.user_id == current_user.id,
                AgentSocialConnection.platform_id == platform_id,
                AgentSocialConnection.is_active == True,
                AgentSocialConnection.deleted_at.is_(None)
            ).order_by(AgentSocialConnection.created_at.desc()).first()
            
            if connection:
                return OAuthStatusResponse(
                    status="completed",
                    connection_id=str(connection.id),
                    platform=platform,
                    created_at=connection.created_at
                )
            else:
                # Check if state is expired (older than 10 minutes)
                timestamp = datetime.fromisoformat(state_data.get("timestamp", ""))
                if datetime.utcnow() - timestamp > timedelta(minutes=10):
                    return OAuthStatusResponse(
                        status="expired",
                        connection_id=None,
                        platform=platform,
                        error_message="OAuth session expired"
                    )
                else:
                    return OAuthStatusResponse(
                        status="pending",
                        connection_id=None,
                        platform=platform
                    )
                    
        except Exception as e:
            logger.error(f"Error checking OAuth status: {str(e)}")
            return OAuthStatusResponse(
                status="failed",
                connection_id=None,
                platform=platform,
                error_message=str(e)
            )

    # =============================================================================
    # PLATFORM-SPECIFIC OAUTH HANDLERS
    # =============================================================================

    @staticmethod
    async def _handle_instagram_oauth(
        oauth_code: str,
        user: User,
        platform: Platform,
        db: Session
    ) -> AgentSocialConnection:
        """Handle Instagram OAuth token exchange and create connection"""
        
        try:
            # Step 1: Exchange code for short-lived token
            token_url = "https://api.instagram.com/oauth/access_token"
            
            token_data = {
                "client_id": settings.INSTAGRAM_APP_ID,
                "client_secret": settings.INSTAGRAM_APP_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": f"{settings.BASE_URL}/api/v0/agent-social-connections/oauth-callback/instagram",
                "code": oauth_code
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=token_data)
                response.raise_for_status()
                token_response = response.json()
            
            short_lived_token = token_response["access_token"]
            instagram_user_id = token_response["user_id"]
            
            # Step 2: Exchange for long-lived token
            long_lived_url = f"https://graph.instagram.com/access_token"
            long_lived_params = {
                "grant_type": "ig_exchange_token",
                "client_secret": settings.INSTAGRAM_APP_SECRET,
                "access_token": short_lived_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(long_lived_url, params=long_lived_params)
                response.raise_for_status()
                long_lived_response = response.json()
            
            access_token = long_lived_response["access_token"]
            expires_in = long_lived_response.get("expires_in", 5184000)  # ~60 days
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Step 3: Get user profile info
            profile_url = f"https://graph.instagram.com/me"
            profile_params = {
                "fields": "id,username,media_count,account_type",
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(profile_url, params=profile_params)
                response.raise_for_status()
                profile_data = response.json()
            
            # Step 4: Determine if it's a business account
            instagram_business_account_id = None
            account_type = profile_data.get("account_type", "PERSONAL")
            
            if account_type in ["BUSINESS", "CREATOR"]:
                instagram_business_account_id = profile_data["id"]
            
            # Step 5: Create connection record
            connection_data = AgentSocialConnectionCreate(
                user_id=str(user.id),
                platform_id=str(platform.id),
                platform_user_id=profile_data["id"],
                platform_username=profile_data["username"],
                display_name=profile_data.get("username"),
                access_token=access_token,  # Will be encrypted by service
                expires_at=expires_at,
                scope="user_profile,user_media,instagram_basic",
                instagram_business_account_id=instagram_business_account_id,
                automation_capabilities={
                    "can_send_messages": account_type in ["BUSINESS", "CREATOR"],
                    "can_post_media": True,
                    "can_get_insights": account_type in ["BUSINESS", "CREATOR"],
                    "account_type": account_type,
                    "media_count": profile_data.get("media_count", 0)
                }
            )
            
            # Create connection using existing service
            return await AgentSocialConnectionService.create_connection(connection_data, db)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during Instagram OAuth: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Instagram OAuth failed: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Error handling Instagram OAuth: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to connect Instagram account"
            )

    @staticmethod
    async def _handle_facebook_oauth(
        oauth_code: str,
        user: User,
        platform: Platform,
        db: Session
    ) -> AgentSocialConnection:
        """Handle Facebook OAuth token exchange and create connection"""
        
        try:
            # Exchange code for access token
            token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
            
            token_params = {
                "client_id": settings.FACEBOOK_APP_ID,
                "client_secret": settings.FACEBOOK_APP_SECRET,
                "redirect_uri": f"{settings.BASE_URL}/api/v0/agent-social-connections/oauth-callback/facebook",
                "code": oauth_code
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(token_url, params=token_params)
                response.raise_for_status()
                token_response = response.json()
            
            access_token = token_response["access_token"]
            
            # Get user profile
            profile_url = f"https://graph.facebook.com/v19.0/me"
            profile_params = {
                "fields": "id,name,email",
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(profile_url, params=profile_params)
                response.raise_for_status()
                profile_data = response.json()
            
            # Get user's Facebook pages
            pages_url = f"https://graph.facebook.com/v19.0/me/accounts"
            pages_params = {
                "fields": "id,name,access_token,instagram_business_account{id,username}",
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(pages_url, params=pages_params)
                response.raise_for_status()
                pages_data = response.json()
            
            # Use the first page (in production, you might want to let user choose)
            if not pages_data.get("data"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No Facebook pages found. You need a Facebook page to use messaging features."
                )
            
            page = pages_data["data"][0]
            page_access_token = page["access_token"]
            
            # Get Instagram business account if connected
            instagram_business_account = page.get("instagram_business_account")
            instagram_business_account_id = None
            
            if instagram_business_account:
                instagram_business_account_id = instagram_business_account["id"]
            
            # Create connection record
            connection_data = AgentSocialConnectionCreate(
                user_id=str(user.id),
                platform_id=str(platform.id),
                platform_user_id=profile_data["id"],
                platform_username=profile_data.get("name"),
                display_name=profile_data.get("name"),
                access_token=access_token,
                scope="pages_manage_posts,pages_messaging,instagram_basic,instagram_manage_messages,pages_read_engagement",
                facebook_page_id=page["id"],
                facebook_page_name=page["name"],
                facebook_page_access_token=page_access_token,
                instagram_business_account_id=instagram_business_account_id,
                automation_capabilities={
                    "can_send_messages": True,
                    "can_post_media": True,
                    "can_manage_page": True,
                    "has_instagram_business": instagram_business_account is not None,
                    "instagram_username": instagram_business_account.get("username") if instagram_business_account else None
                }
            )
            
            return await AgentSocialConnectionService.create_connection(connection_data, db)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during Facebook OAuth: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Facebook OAuth failed: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Error handling Facebook OAuth: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to connect Facebook account"
            )

    @staticmethod
    async def _handle_whatsapp_oauth(
        oauth_code: str,
        user: User,
        platform: Platform,
        db: Session
    ) -> AgentSocialConnection:
        """Handle WhatsApp OAuth token exchange and create connection"""
        
        # WhatsApp uses Facebook OAuth, so implementation is similar to Facebook
        # but focuses on WhatsApp Business API access
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="WhatsApp connection will be implemented in next version"
        )

    # =============================================================================
    # INSTAGRAM MESSAGING METHODS
    # =============================================================================

    @staticmethod
    async def get_instagram_conversations(
        connection_id: uuid.UUID,
        limit: int,
        current_user: User,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get Instagram conversations for a connected account"""
        
        # Get and validate connection
        connection = await AgentSocialConnectionService.get_connection(connection_id, db)
        
        # Check ownership
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own connections"
            )
        
        # Use Instagram service
        instagram_service = InstagramIntegrationService()
        return await instagram_service.get_instagram_conversations(connection, limit, db)

    @staticmethod
    async def get_conversation_messages(
        connection_id: uuid.UUID,
        conversation_id: str,
        limit: int,
        current_user: User,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get messages from an Instagram conversation"""
        
        # Get and validate connection
        connection = await AgentSocialConnectionService.get_connection(connection_id, db)
        
        # Check ownership
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own connections"
            )
        
        # Use Instagram service
        instagram_service = InstagramIntegrationService()
        return await instagram_service.get_conversation_messages(connection, conversation_id, limit, db)

    @staticmethod
    async def send_instagram_message(
        connection_id: uuid.UUID,
        message_data: Dict[str, Any],
        current_user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Send Instagram direct message"""
        
        # Get and validate connection
        connection = await AgentSocialConnectionService.get_connection(connection_id, db)
        
        # Check ownership
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only send messages from your own connections"
            )
        
        # Validate required fields
        if "recipient_id" not in message_data or "message_text" not in message_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="recipient_id and message_text are required"
            )
        
        # Use Instagram service
        instagram_service = InstagramIntegrationService()
        return await instagram_service.send_instagram_message(
            connection,
            message_data["recipient_id"],
            message_data["message_text"],
            db
        )

    @staticmethod
    async def setup_instagram_webhooks(
        connection_id: uuid.UUID,
        webhook_data: Dict[str, Any],
        current_user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Setup Instagram webhooks for real-time updates"""
        
        # Get and validate connection
        connection = await AgentSocialConnectionService.get_connection(connection_id, db)
        
        # Check ownership
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only setup webhooks for your own connections"
            )
        
        # Validate required fields
        if "webhook_url" not in webhook_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="webhook_url is required"
            )
        
        # Use Instagram service
        instagram_service = InstagramIntegrationService()
        return await instagram_service.setup_instagram_webhooks(
            connection,
            webhook_data["webhook_url"],
            db
        )

    # =============================================================================
    # EXISTING CRUD METHODS (Keep all existing methods)
    # =============================================================================

    @staticmethod
    async def create_connection(
        connection_data: AgentSocialConnectionCreate,
        current_user: User,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Create a new social media connection"""
        
        # Ensure user can only create connections for themselves unless admin
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and str(connection_data.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create connections for yourself"
            )

        return await AgentSocialConnectionService.create_connection(connection_data, db)

    @staticmethod
    async def get_connection(
        connection_id: uuid.UUID,
        current_user: User,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Get a specific social connection by ID"""
        
        connection = await AgentSocialConnectionService.get_connection(connection_id, db)
        
        # Check permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own connections"
            )

        return connection

    # =============================================================================
    # EXISTING CRUD METHODS (Continue with all existing methods)
    # =============================================================================

    @staticmethod
    async def get_connections_paginated(
        page: int,
        page_size: int,
        user_id: Optional[uuid.UUID],
        platform_id: Optional[uuid.UUID],
        active_only: bool,
        search: Optional[str],
        current_user: User,
        db: Session
    ) -> AgentSocialConnectionsPaginatedResponse:
        """Get paginated list of social connections"""
        
        # Check permission for accessing other users' connections
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if user_id and not is_admin and str(user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own connections"
            )

        return await AgentSocialConnectionService.get_connections_paginated(
            page, page_size, user_id, platform_id, active_only, search, db
        )

    @staticmethod
    async def update_connection(
        connection_id: uuid.UUID,
        update_data: AgentSocialConnectionUpdate,
        current_user: User,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Update a social connection"""
        
        # Get existing connection to check permissions
        existing_connection = await AgentSocialConnectionService.get_connection(connection_id, db)
        
        # Check permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and existing_connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own connections"
            )

        return await AgentSocialConnectionService.update_connection(connection_id, update_data, db)

    @staticmethod
    async def delete_connection(
        connection_id: uuid.UUID,
        current_user: User,
        db: Session
    ) -> Dict[str, str]:
        """Delete a social connection"""
        
        # Get existing connection to check permissions
        existing_connection = await AgentSocialConnectionService.get_connection(connection_id, db)
        
        # Check permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and existing_connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own connections"
            )

        return await AgentSocialConnectionService.delete_connection(connection_id, db)

    @staticmethod
    async def get_user_connections(
        user_id: Optional[uuid.UUID],
        platform_id: Optional[uuid.UUID],
        active_only: bool,
        current_user: User,
        db: Session
    ) -> List[AgentSocialConnectionDetailResponse]:
        """Get all social connections for a specific user"""
        
        # If no user_id provided, use current user
        target_user_id = user_id or current_user.id
        
        # Check permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and str(target_user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own connections"
            )

        return await AgentSocialConnectionService.get_user_connections(
            target_user_id, platform_id, active_only, db
        )

    @staticmethod
    async def get_platform_connections_status(
        user_id: Optional[uuid.UUID],
        current_user: User,
        db: Session
    ) -> UserPlatformConnectionsStatus:
        """Get platform connections status for a user"""
        
        # If no user_id provided, use current user
        target_user_id = user_id or current_user.id
        
        # Check permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and str(target_user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own connection status"
            )

        return await AgentSocialConnectionService.get_platform_connections_status(
            target_user_id, db
        )

    # =============================================================================
    # LEGACY CONNECTION METHODS (Keep for compatibility)
    # =============================================================================

    @staticmethod
    async def connect_platform_account(
        platform_request: PlatformConnectionRequest,
        current_user: User,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Connect a new platform account using OAuth or API credentials (Legacy method)"""
        
        try:
            # This method handles manual OAuth code input
            # Platform-specific logic would go here
            platform_id = platform_request.platform_id
            
            # Get platform info
            platform = db.query(Platform).filter(Platform.id == platform_id).first()
            if not platform:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Platform not found"
                )
            
            platform_name = platform.name.lower()
            
            if platform_name == "instagram":
                return await AgentSocialConnectionController._connect_instagram_account(
                    platform_request, current_user, db
                )
            elif platform_name == "facebook":
                return await AgentSocialConnectionController._connect_facebook_account(
                    platform_request, current_user, db
                )
            elif platform_name == "whatsapp":
                return await AgentSocialConnectionController._connect_whatsapp_account(
                    platform_request, current_user, db
                )
            elif platform_name == "tiktok":
                return await AgentSocialConnectionController._connect_tiktok_account(
                    platform_request, current_user, db
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Platform {platform.name} not supported"
                )

        except Exception as e:
            logger.error(f"Error connecting platform account: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to connect platform account"
            )

    @staticmethod
    async def _connect_instagram_account(
        platform_request: PlatformConnectionRequest,
        current_user: User,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Connect Instagram business account (Legacy method)"""
        
        # This is a legacy method for manual OAuth code input
        # Recommend using the new OAuth flow instead
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Please use /initiate-connection endpoint for Instagram connections"
        )

    @staticmethod
    async def _connect_facebook_account(
        platform_request: PlatformConnectionRequest,
        current_user: User,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Connect Facebook page account (Legacy method)"""
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Please use /initiate-connection endpoint for Facebook connections"
        )

    @staticmethod
    async def _connect_whatsapp_account(
        platform_request: PlatformConnectionRequest,
        current_user: User,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Connect WhatsApp Business account (Legacy method)"""
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Please use /initiate-connection endpoint for WhatsApp connections"
        )

    @staticmethod
    async def _connect_tiktok_account(
        platform_request: PlatformConnectionRequest,
        current_user: User,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Connect TikTok account (Legacy method)"""
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="TikTok connection will be implemented in next version"
        )

    @staticmethod
    async def disconnect_platform_account(
        connection_id: uuid.UUID,
        current_user: User,
        db: Session
    ) -> Dict[str, str]:
        """Disconnect and cleanup a platform account"""
        
        # Get connection to check permissions
        connection = await AgentSocialConnectionService.get_connection(connection_id, db)
        
        # Check permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only disconnect your own connections"
            )

        # Use service to handle disconnection
        return await AgentSocialConnectionService.disconnect_connection(connection_id, db)

    # =============================================================================
    # TOKEN MANAGEMENT METHODS
    # =============================================================================

    @staticmethod
    async def validate_token(
        validation_request: TokenValidationRequest,
        current_user: User,
        db: Session
    ) -> TokenValidationResponse:
        """Validate OAuth token for a connection"""
        
        connection_id = uuid.UUID(validation_request.connection_id)
        connection = await AgentSocialConnectionService.get_connection(connection_id, db)
        
        # Check permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only validate your own connection tokens"
            )

        return await AgentSocialConnectionService.validate_connection_token(connection_id, db)

    @staticmethod
    async def refresh_connection_token(
        connection_id: uuid.UUID,
        current_user: User,
        db: Session
    ) -> TokenValidationResponse:
        """Refresh OAuth token for a connection"""
        
        connection = await AgentSocialConnectionService.get_connection(connection_id, db)
        
        # Check permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only refresh your own connection tokens"
            )

        return await AgentSocialConnectionService.refresh_connection_token(connection_id, db)

    # =============================================================================
    # AUTOMATION METHODS
    # =============================================================================

    @staticmethod
    async def toggle_automation(
        automation_request: AutomationToggleRequest,
        current_user: User,
        db: Session
    ) -> AutomationStatusResponse:
        """Enable or disable automation for a social connection"""
        
        connection_id = uuid.UUID(automation_request.connection_id)
        connection = await AgentSocialConnectionService.get_connection(connection_id, db)
        
        # Check permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only manage automation for your own connections"
            )

        return await AgentSocialConnectionService.toggle_automation(automation_request, db)

    @staticmethod
    async def get_automation_status(
        connection_id: uuid.UUID,
        current_user: User,
        db: Session
    ) -> AutomationStatusResponse:
        """Get automation status for a connection"""
        
        connection = await AgentSocialConnectionService.get_connection(connection_id, db)
        
        # Check permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view automation status for your own connections"
            )

        return await AgentSocialConnectionService.get_automation_status(connection_id, db)

    # =============================================================================
    # BULK OPERATIONS METHODS
    # =============================================================================

    @staticmethod
    async def bulk_update_connections(
        bulk_update: BulkConnectionUpdate,
        current_user: User,
        db: Session
    ) -> BulkOperationResponse:
        """Bulk update multiple connections"""
        
        success_count = 0
        failed_count = 0
        errors = []

        for connection_id_str in bulk_update.connection_ids:
            try:
                connection_id = uuid.UUID(connection_id_str)
                
                # Check permission for each connection
                connection = await AgentSocialConnectionService.get_connection(connection_id, db)
                is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
                
                if not is_admin and connection.user_id != str(current_user.id):
                    failed_count += 1
                    errors.append({
                        "connection_id": connection_id_str,
                        "error": "Permission denied"
                    })
                    continue

                # Update connection
                await AgentSocialConnectionService.update_connection(
                    connection_id, bulk_update.update_data, db
                )
                success_count += 1

            except Exception as e:
                failed_count += 1
                errors.append({
                    "connection_id": connection_id_str,
                    "error": str(e)
                })

        return BulkOperationResponse(
            success_count=success_count,
            failed_count=failed_count,
            errors=errors
        )

    # =============================================================================
    # PLATFORM-SPECIFIC METHODS
    # =============================================================================

    @staticmethod
    async def get_instagram_business_accounts(
        current_user: User,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get available Instagram business accounts for the current user"""
        
        # Get user's Facebook connections that might have Instagram business accounts
        facebook_connections = await AgentSocialConnectionService.get_user_connections(
            current_user.id, None, True, db
        )
        
        business_accounts = []
        for connection in facebook_connections:
            if connection.platform.name.lower() == "facebook" and connection.instagram_business_account_id:
                business_accounts.append({
                    "instagram_business_account_id": connection.instagram_business_account_id,
                    "facebook_page_id": connection.facebook_page_id,
                    "facebook_page_name": connection.facebook_page_name,
                    "connection_id": connection.id
                })
        
        return business_accounts

    @staticmethod
    async def connect_instagram_business_account(
        instagram_data: Dict[str, Any],
        current_user: User,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Connect a specific Instagram business account"""
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Instagram business account connection not yet implemented"
        )

    @staticmethod
    async def get_whatsapp_business_profiles(
        current_user: User,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get available WhatsApp business profiles for the current user"""
        
        # Implementation would integrate with WhatsApp Business API
        return []

    @staticmethod
    async def connect_whatsapp_business_profile(
        whatsapp_data: Dict[str, Any],
        current_user: User,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Connect a WhatsApp business profile"""
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="WhatsApp business profile connection not yet implemented"
        )

    # =============================================================================
    # ANALYTICS AND REPORTING METHODS
    # =============================================================================

    @staticmethod
    async def get_platform_usage_analytics(
        user_id: Optional[uuid.UUID],
        days: int,
        current_user: User,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get platform usage analytics"""
        
        # Check permission for accessing other users' analytics
        target_user_id = user_id or current_user.id
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        
        if not is_admin and str(target_user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own analytics"
            )

        return await AgentSocialConnectionService.get_platform_usage_analytics(
            target_user_id, days, db
        )

    @staticmethod
    async def get_system_health_report(
        db: Session
    ) -> SystemHealthReport:
        """Get system health report for all social connections"""
        
        return await AgentSocialConnectionService.get_system_health_report(db)