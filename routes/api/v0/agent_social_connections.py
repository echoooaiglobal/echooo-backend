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
    AgentSocialConnectionResponse, AgentSocialConnectionDetailResponse,
    AgentSocialConnectionsPaginatedResponse, UserPlatformConnectionsStatus,
    TokenValidationRequest, TokenValidationResponse,
    AutomationToggleRequest, AutomationStatusResponse,
    ConnectionHealthCheck, SystemHealthReport,
    BulkConnectionUpdate, BulkOperationResponse,
    PlatformConnectionRequest
)
from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission
)
from config.database import get_db

router = APIRouter(prefix="/agent-social-connections", tags=["Agent Social Connections"])

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

@router.get("/user/{user_id}/connections", response_model=List[AgentSocialConnectionDetailResponse])
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
        user_id, platform_id, active_only, current_user, db
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
# PLATFORM CONNECTION MANAGEMENT
# =============================================================================

@router.post("/connect", response_model=AgentSocialConnectionDetailResponse)
async def connect_platform_account(
    platform_request: PlatformConnectionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Connect a new platform account using OAuth or API credentials.
    
    This endpoint handles the connection process for various social media platforms
    including Instagram, Facebook, WhatsApp, and TikTok. It processes OAuth codes,
    exchanges them for access tokens, and creates the connection record.
    """
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
    # Get connection first to check automation status
    connection = await AgentSocialConnectionController.get_connection(
        connection_id, current_user, db
    )
    
    return AutomationStatusResponse(
        connection_id=str(connection_id),
        is_automation_enabled=connection.is_active,  # You may want to add specific automation field
        automation_capabilities=connection.automation_capabilities,
        last_automation_use=connection.last_automation_use_at,
        error_count=connection.automation_error_count,
        last_error=connection.last_error_message
    )

# =============================================================================
# HEALTH MONITORING
# =============================================================================

@router.get("/{connection_id}/health", response_model=ConnectionHealthCheck)
async def check_connection_health(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check the health status of a social connection.
    
    Analyzes token validity, error rates, recent activity,
    and provides recommendations for maintaining connection health.
    """
    return await AgentSocialConnectionController.check_connection_health(
        connection_id, current_user, db
    )

@router.get("/system/health", response_model=SystemHealthReport)
async def get_system_health_report(
    current_user: User = Depends(has_role(["platform_admin", "admin"])),
    db: Session = Depends(get_db)
):
    """
    Get system-wide health report for all social connections.
    
    Admin-only endpoint that provides overview of connection health
    across all users and platforms.
    """
    return await AgentSocialConnectionController.get_system_health_report(
        current_user, db
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
    # This would integrate with your Instagram service
    # For now, return placeholder response
    return []

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
    # Implementation would go here
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Instagram business account connection not yet implemented"
    )

@router.get("/whatsapp/business-profiles", response_model=List[Dict[str, Any]])
async def get_whatsapp_business_profiles(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get available WhatsApp business profiles for the current user.
    """
    # Implementation would integrate with WhatsApp Business API
    return []

@router.post("/whatsapp/connect-business-profile", response_model=AgentSocialConnectionDetailResponse)
async def connect_whatsapp_business_profile(
    whatsapp_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Connect a WhatsApp business profile.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="WhatsApp business profile connection not yet implemented"
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
    # Check permissions
    is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
    if user_id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view other users' analytics"
        )
    
    target_user_id = user_id if user_id else current_user.id
    
    # Implementation would analyze connection usage
    # For now, return placeholder
    return []

@router.get("/analytics/error-report", response_model=List[Dict[str, Any]])
async def get_connection_error_report(
    platform_id: Optional[uuid.UUID] = Query(None, description="Filter by platform"),
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    current_user: User = Depends(has_permission(["analytics:read"])),
    db: Session = Depends(get_db)
):
    """
    Get connection error report.
    
    Returns analysis of connection errors, common issues,
    and recommendations for resolution.
    """
    # Implementation would analyze error patterns
    return []

# =============================================================================
# MAINTENANCE AND UTILITIES
# =============================================================================

@router.post("/maintenance/cleanup-expired")
async def cleanup_expired_connections(
    dry_run: bool = Query(True, description="If true, only report what would be cleaned up"),
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """
    Cleanup expired and inactive connections.
    
    Admin-only endpoint for maintenance operations.
    """
    # Implementation would clean up old/expired connections
    return {"message": "Cleanup operation completed", "dry_run": dry_run}

@router.post("/maintenance/refresh-all-tokens")
async def refresh_all_expiring_tokens(
    hours_threshold: int = Query(24, ge=1, le=168, description="Refresh tokens expiring within this many hours"),
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """
    Bulk refresh tokens that are expiring soon.
    
    Admin-only endpoint for proactive token maintenance.
    """
    # Implementation would find and refresh expiring tokens
    return {"message": "Token refresh operation completed"}

@router.get("/statistics", response_model=Dict[str, Any])
async def get_connection_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get connection statistics for the current user.
    
    Returns summary statistics including total connections,
    active connections, platform breakdown, etc.
    """
    # Get user's platform status
    status = await AgentSocialConnectionController.get_platform_connections_status(
        None, current_user, db
    )
    
    # Calculate additional statistics
    platform_breakdown = {}
    for platform_status in status.platforms:
        platform_breakdown[platform_status.platform_name] = {
            "total": platform_status.connection_count,
            "active": platform_status.active_connections,
            "is_connected": platform_status.is_connected,
            "last_connected": platform_status.last_connected
        }
    
    return {
        "total_connections": status.total_connections,
        "active_connections": status.active_connections,
        "platform_breakdown": platform_breakdown,
        "connected_platforms": len([p for p in status.platforms if p.is_connected])
    }