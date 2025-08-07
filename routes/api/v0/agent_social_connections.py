# routes/api/v0/agent_social_connections.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from app.Http.Controllers.AgentSocialConnectionController import AgentSocialConnectionController
from app.Models.auth_models import User
from app.Schemas.agent_social_connection import (
    AgentSocialConnectionCreate, AgentSocialConnectionUpdate,
    AgentSocialConnectionDetailResponse,
    AgentSocialConnectionsPaginatedResponse, UserPlatformConnectionsStatus,
    TokenValidationRequest, TokenValidationResponse,
    AutomationToggleRequest, AutomationStatusResponse,
    SystemHealthReport,
    BulkConnectionUpdate, BulkOperationResponse,
    PlatformConnectionRequest, PlatformConnectionInitiateRequest,
    OAuthInitiateResponse
)
from app.Utils.Helpers import (
    get_current_active_user, has_role
)
from config.database import get_db

router = APIRouter(prefix="/agent-social-connections", tags=["Agent Social Connections"])

# =============================================================================
# OAUTH CONNECTION FLOW
# =============================================================================

@router.post("/initiate-connection", response_model=OAuthInitiateResponse)
async def initiate_platform_connection(
    platform_request: PlatformConnectionInitiateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Step 1: Initiate platform connection (starts OAuth flow)
    
    Returns OAuth authorization URL for user to visit.
    Call this from your frontend when user clicks "Connect Instagram" button.
    """
    return await AgentSocialConnectionController.initiate_platform_connection(
        platform_request, current_user, db
    )

@router.get("/oauth-callback/{platform}")
async def handle_oauth_callback(
    platform: str,
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="OAuth state parameter"),
    error: Optional[str] = Query(None, description="OAuth error if any"),
    error_description: Optional[str] = Query(None, description="OAuth error description"),
    db: Session = Depends(get_db)
):
    """
    Step 2: Handle OAuth callback and create connection
    
    This endpoint is called by Instagram/Facebook after user authorization.
    Automatically redirects user back to your frontend with success/error status.
    """
    return await AgentSocialConnectionController.handle_oauth_callback(
        platform, code, state, error, error_description, db
    )

@router.get("/oauth-status/{platform}")
async def get_oauth_status(
    platform: str,
    state: str = Query(..., description="OAuth state to check status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check OAuth connection status (for polling from frontend)
    
    Use this to check if OAuth flow completed successfully.
    """
    return await AgentSocialConnectionController.get_oauth_status(
        platform, state, current_user, db
    )

# =============================================================================
# CORE CRUD OPERATIONS
# =============================================================================

@router.post("/", response_model=AgentSocialConnectionDetailResponse)
async def create_social_connection(
    connection_data: AgentSocialConnectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new social media connection for an agent.
    
    This endpoint allows users to connect their social media accounts
    (Instagram, Facebook, WhatsApp, TikTok) for automation purposes.
    """
    return await AgentSocialConnectionController.create_connection(
        connection_data, current_user, db
    )

@router.get("/{connection_id}", response_model=AgentSocialConnectionDetailResponse)
async def get_social_connection(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific social connection by ID.
    
    Returns detailed information about a social media connection
    including platform details, authentication status, and automation capabilities.
    """
    return await AgentSocialConnectionController.get_connection(
        connection_id, current_user, db
    )

@router.put("/{connection_id}", response_model=AgentSocialConnectionDetailResponse)
async def update_social_connection(
    connection_id: uuid.UUID,
    update_data: AgentSocialConnectionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a social media connection.
    
    Allows updating connection settings, automation capabilities,
    and other connection-specific configurations.
    """
    return await AgentSocialConnectionController.update_connection(
        connection_id, update_data, current_user, db
    )

@router.delete("/{connection_id}")
async def delete_social_connection(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete (soft delete) a social media connection.
    
    This will deactivate the connection and remove it from active use
    while preserving historical data.
    """
    return await AgentSocialConnectionController.delete_connection(
        connection_id, current_user, db
    )

# =============================================================================
# LISTING AND FILTERING
# =============================================================================

@router.get("/", response_model=AgentSocialConnectionsPaginatedResponse)
async def get_social_connections(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by user ID (admin only)"),
    platform_id: Optional[uuid.UUID] = Query(None, description="Filter by platform ID"),
    active_only: bool = Query(True, description="Show only active connections"),
    search: Optional[str] = Query(None, description="Search by username or display name"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of social media connections.
    
    Supports filtering by platform, user (admin only), active status,
    and searching by username or display name.
    """
    return await AgentSocialConnectionController.get_connections_paginated(
        page, page_size, user_id, platform_id, active_only, search, current_user, db
    )

@router.get("/user/connections", response_model=List[AgentSocialConnectionDetailResponse])
async def get_user_social_connections(
    user_id: Optional[uuid.UUID] = None,
    platform_id: Optional[uuid.UUID] = Query(None, description="Filter by platform ID"),
    active_only: bool = Query(True, description="Show only active connections"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all social connections for a specific user.
    If no user_id provided, returns current user's connections.
    Admin users can access other users' connections.
    """
    return await AgentSocialConnectionController.get_user_connections(
        current_user.id, platform_id, active_only, current_user, db
    )

@router.get("/user/{user_id}/platforms/status", response_model=UserPlatformConnectionsStatus)
async def get_user_platform_status(
    user_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get connection status across all platforms for a user.
    
    Returns summary of connected platforms, connection counts,
    and last connection dates for each platform.
    """
    return await AgentSocialConnectionController.get_platform_connections_status(
        user_id, current_user, db
    )

# =============================================================================
# PLATFORM CONNECTION MANAGEMENT (Legacy - keep for manual OAuth)
# =============================================================================

@router.post("/connect", response_model=AgentSocialConnectionDetailResponse)
async def connect_platform_account_manual(
    platform_request: PlatformConnectionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Connect platform account with pre-obtained OAuth code (Legacy method)
    
    Use /initiate-connection instead for better UX.
    This endpoint is kept for manual OAuth code input if needed.
    """
    if not platform_request.oauth_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="oauth_code is required for platform connection"
        )
    
    return await AgentSocialConnectionController.connect_platform_account(
        platform_request, current_user, db
    )

@router.post("/{connection_id}/disconnect")
async def disconnect_platform_account(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect and cleanup a platform account.
    
    This will revoke tokens, cleanup webhooks, and remove the connection
    while preserving historical data.
    """
    return await AgentSocialConnectionController.disconnect_platform_account(
        connection_id, current_user, db
    )

# =============================================================================
# INSTAGRAM MESSAGING ENDPOINTS
# =============================================================================

@router.get("/{connection_id}/instagram/conversations", response_model=List[Dict[str, Any]])
async def get_instagram_conversations(
    connection_id: uuid.UUID,
    limit: int = Query(25, ge=1, le=100, description="Number of conversations to fetch"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get Instagram conversations for a connected account
    
    Returns list of Instagram DM conversations with participants and metadata.
    """
    return await AgentSocialConnectionController.get_instagram_conversations(
        connection_id, limit, current_user, db
    )

@router.get("/{connection_id}/instagram/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    connection_id: uuid.UUID,
    conversation_id: str,
    limit: int = Query(25, ge=1, le=100, description="Number of messages to fetch"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get messages from an Instagram conversation
    
    Returns messages from a specific Instagram DM conversation.
    """
    return await AgentSocialConnectionController.get_conversation_messages(
        connection_id, conversation_id, limit, current_user, db
    )

@router.post("/{connection_id}/instagram/send-message")
async def send_instagram_message(
    connection_id: uuid.UUID,
    message_data: Dict[str, Any] = Body(..., example={
        "recipient_id": "instagram_user_id",
        "message_text": "Hello! Thanks for your message.",
        "message_type": "text"
    }),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Send Instagram direct message
    
    Send a DM to an Instagram user through connected business account.
    """
    return await AgentSocialConnectionController.send_instagram_message(
        connection_id, message_data, current_user, db
    )

@router.post("/{connection_id}/instagram/setup-webhooks")
async def setup_instagram_webhooks(
    connection_id: uuid.UUID,
    webhook_data: Dict[str, Any] = Body(..., example={
        "webhook_url": "https://yourdomain.com/api/v0/webhooks/instagram",
        "verify_token": "your_verify_token"
    }),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Setup Instagram webhooks for real-time message updates
    
    Configure webhooks to receive real-time Instagram messaging events.
    """
    return await AgentSocialConnectionController.setup_instagram_webhooks(
        connection_id, webhook_data, current_user, db
    )

# =============================================================================
# TOKEN AND AUTHENTICATION MANAGEMENT
# =============================================================================

@router.post("/validate-token", response_model=TokenValidationResponse)
async def validate_connection_token(
    validation_request: TokenValidationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Validate OAuth token for a connection.
    
    Checks if the access token is still valid and returns
    expiration information and renewal recommendations.
    """
    return await AgentSocialConnectionController.validate_token(
        validation_request, current_user, db
    )

@router.post("/{connection_id}/refresh-token", response_model=TokenValidationResponse)
async def refresh_connection_token(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Refresh OAuth token for a connection.
    
    Attempts to refresh the access token using the refresh token
    and updates the connection with the new token information.
    """
    return await AgentSocialConnectionController.refresh_connection_token(
        connection_id, current_user, db
    )

# =============================================================================
# AUTOMATION CONTROL
# =============================================================================

@router.post("/automation/toggle", response_model=AutomationStatusResponse)
async def toggle_connection_automation(
    automation_request: AutomationToggleRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Enable or disable automation for a social connection.
    
    This controls whether the connection can be used for automated
    messaging, posting, and other automation features.
    """
    return await AgentSocialConnectionController.toggle_automation(
        automation_request, current_user, db
    )

@router.get("/{connection_id}/automation/status", response_model=AutomationStatusResponse)
async def get_automation_status(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get automation status for a connection.
    
    Returns current automation settings, capabilities,
    error count, and last usage information.
    """
    return await AgentSocialConnectionController.get_automation_status(
        connection_id, current_user, db
    )

# =============================================================================
# BULK OPERATIONS
# =============================================================================

@router.post("/bulk-update", response_model=BulkOperationResponse)
async def bulk_update_connections(
    bulk_update: BulkConnectionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Bulk update multiple social connections.
    
    Allows updating multiple connections with the same data.
    Useful for batch operations like enabling/disabling automation
    or updating settings across multiple accounts.
    """
    return await AgentSocialConnectionController.bulk_update_connections(
        bulk_update, current_user, db
    )

@router.post("/bulk-validate-tokens", response_model=List[TokenValidationResponse])
async def bulk_validate_tokens(
    connection_ids: List[str] = Body(..., description="List of connection IDs to validate"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Validate tokens for multiple connections at once.
    
    Useful for checking the health of multiple connections
    and identifying which ones need token refresh.
    """
    results = []
    for connection_id_str in connection_ids:
        try:
            connection_id = uuid.UUID(connection_id_str)
            validation_request = TokenValidationRequest(connection_id=connection_id_str)
            result = await AgentSocialConnectionController.validate_token(
                validation_request, current_user, db
            )
            results.append(result)
        except Exception as e:
            # Add error result for failed validations
            results.append(TokenValidationResponse(
                connection_id=connection_id_str,
                is_valid=False,
                expires_at=None,
                expires_in_hours=None,
                needs_renewal=True,
                last_check=datetime.utcnow()
            ))
    
    return results

# =============================================================================
# PLATFORM-SPECIFIC ENDPOINTS
# =============================================================================

@router.get("/instagram/business-accounts", response_model=List[Dict[str, Any]])
async def get_instagram_business_accounts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get available Instagram business accounts for the current user.
    
    Returns business accounts that can be connected through
    the user's Facebook account connections.
    """
    return await AgentSocialConnectionController.get_instagram_business_accounts(
        current_user, db
    )

@router.post("/instagram/connect-business-account", response_model=AgentSocialConnectionDetailResponse)
async def connect_instagram_business_account(
    instagram_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Connect a specific Instagram business account.
    
    Requires prior Facebook connection to access Instagram business accounts.
    """
    return await AgentSocialConnectionController.connect_instagram_business_account(
        instagram_data, current_user, db
    )

@router.get("/whatsapp/business-profiles", response_model=List[Dict[str, Any]])
async def get_whatsapp_business_profiles(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get available WhatsApp business profiles for the current user.
    """
    return await AgentSocialConnectionController.get_whatsapp_business_profiles(
        current_user, db
    )

@router.post("/whatsapp/connect-business-profile", response_model=AgentSocialConnectionDetailResponse)
async def connect_whatsapp_business_profile(
    whatsapp_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Connect a WhatsApp business profile.
    """
    return await AgentSocialConnectionController.connect_whatsapp_business_profile(
        whatsapp_data, current_user, db
    )

# =============================================================================
# ANALYTICS AND REPORTING
# =============================================================================

@router.get("/analytics/platform-usage", response_model=List[Dict[str, Any]])
async def get_platform_usage_analytics(
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by user ID (admin only)"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get platform usage analytics.
    
    Returns usage statistics for connected platforms including
    message counts, automation activity, and error rates.
    """
    return await AgentSocialConnectionController.get_platform_usage_analytics(
        user_id, days, current_user, db
    )

@router.get("/health", response_model=SystemHealthReport)
async def get_system_health_report(
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """
    Get system health report for all social connections.
    
    Returns overview of connection health, platform statistics,
    and system-wide metrics.
    """
    return await AgentSocialConnectionController.get_system_health_report(db)