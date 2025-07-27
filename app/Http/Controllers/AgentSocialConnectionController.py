# app/Http/Controllers/AgentSocialConnectionController.py
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid

from app.Models.auth_models import User
from app.Services.AgentSocialConnectionService import AgentSocialConnectionService
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
from app.Utils.Logger import logger

class AgentSocialConnectionController:
    """Controller for agent social connections endpoints"""

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
        
        # Check permission - users can only access their own connections unless admin
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own connections"
            )

        return connection

    @staticmethod
    async def get_user_connections(
        user_id: Optional[uuid.UUID],
        platform_id: Optional[uuid.UUID],
        active_only: bool,
        current_user: User,
        db: Session
    ) -> List[AgentSocialConnectionDetailResponse]:
        """Get connections for a user"""
        
        # Determine target user
        target_user_id = user_id if user_id else current_user.id
        
        # Check permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and target_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own connections"
            )

        return await AgentSocialConnectionService.get_user_connections(
            target_user_id, platform_id, active_only, db
        )

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
        """Get paginated social connections"""
        
        # If not admin, restrict to current user's connections
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin:
            user_id = current_user.id

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
    async def get_platform_connections_status(
        user_id: Optional[uuid.UUID],
        current_user: User,
        db: Session
    ) -> UserPlatformConnectionsStatus:
        """Get platform connection status for a user"""
        
        # Determine target user
        target_user_id = user_id if user_id else current_user.id
        
        # Check permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and target_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own connection status"
            )

        return await AgentSocialConnectionService.get_platform_connections_status(target_user_id, db)

    @staticmethod
    async def validate_token(
        validation_request: TokenValidationRequest,
        current_user: User,
        db: Session
    ) -> TokenValidationResponse:
        """Validate OAuth token for a connection"""
        
        # Get connection to check permissions
        connection = await AgentSocialConnectionService.get_connection(
            uuid.UUID(validation_request.connection_id), db
        )
        
        # Check permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only validate your own connection tokens"
            )

        return await AgentSocialConnectionService.validate_token(
            uuid.UUID(validation_request.connection_id), db
        )

    @staticmethod
    async def toggle_automation(
        automation_request: AutomationToggleRequest,
        current_user: User,
        db: Session
    ) -> AutomationStatusResponse:
        """Toggle automation for a connection"""
        
        # Get connection to check permissions
        connection = await AgentSocialConnectionService.get_connection(
            uuid.UUID(automation_request.connection_id), db
        )
        
        # Check permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only modify your own connection automation"
            )

        return await AgentSocialConnectionService.toggle_automation(
            uuid.UUID(automation_request.connection_id), 
            automation_request.enabled, 
            db
        )

    @staticmethod
    async def check_connection_health(
        connection_id: uuid.UUID,
        current_user: User,
        db: Session
    ) -> ConnectionHealthCheck:
        """Check health of a connection"""
        
        # Get connection to check permissions
        connection = await AgentSocialConnectionService.get_connection(connection_id, db)
        
        # Check permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only check your own connection health"
            )

        return await AgentSocialConnectionService.check_connection_health(connection_id, db)

    @staticmethod
    async def get_system_health_report(
        current_user: User,
        db: Session
    ) -> SystemHealthReport:
        """Get system-wide health report (admin only)"""
        
        # Check admin permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can access system health reports"
            )

        return await AgentSocialConnectionService.get_system_health_report(db)

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

    @staticmethod
    async def connect_platform_account(
        platform_request: PlatformConnectionRequest,
        current_user: User,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Connect a new platform account using OAuth or API credentials"""
        
        try:
            # This method would integrate with your OAuth service
            # and platform-specific APIs to establish connections
            
            # For Instagram, this would:
            # 1. Exchange OAuth code for access token
            # 2. Get user profile information
            # 3. Get business account information
            # 4. Create the connection record
            
            # Platform-specific logic would go here
            if platform_request.platform_id == "instagram":
                return await AgentSocialConnectionController._connect_instagram_account(
                    platform_request, current_user, db
                )
            elif platform_request.platform_id == "facebook":
                return await AgentSocialConnectionController._connect_facebook_account(
                    platform_request, current_user, db
                )
            elif platform_request.platform_id == "whatsapp":
                return await AgentSocialConnectionController._connect_whatsapp_account(
                    platform_request, current_user, db
                )
            elif platform_request.platform_id == "tiktok":
                return await AgentSocialConnectionController._connect_tiktok_account(
                    platform_request, current_user, db
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Platform {platform_request.platform_id} not supported"
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
        """Connect Instagram business account"""
        # Implementation would integrate with Instagram Basic Display API
        # and Instagram Graph API for business accounts
        
        # This is a placeholder - you'll need to implement the actual
        # Instagram API integration based on your OAuth setup
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Instagram connection implementation needed"
        )

    @staticmethod
    async def _connect_facebook_account(
        platform_request: PlatformConnectionRequest,
        current_user: User,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Connect Facebook page account"""
        # Implementation would integrate with Facebook Graph API
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Facebook connection implementation needed"
        )

    @staticmethod
    async def _connect_whatsapp_account(
        platform_request: PlatformConnectionRequest,
        current_user: User,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Connect WhatsApp Business account"""
        # Implementation would integrate with WhatsApp Business API
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="WhatsApp connection implementation needed"
        )

    @staticmethod
    async def _connect_tiktok_account(
        platform_request: PlatformConnectionRequest,
        current_user: User,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Connect TikTok account"""
        # Implementation would integrate with TikTok for Developers API
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="TikTok connection implementation needed"
        )

    @staticmethod
    async def disconnect_platform_account(
        connection_id: uuid.UUID,
        current_user: User,
        db: Session
    ) -> Dict[str, str]:
        """Disconnect and cleanup a platform account"""
        
        # Get connection to check permissions and get platform info
        connection = await AgentSocialConnectionService.get_connection(connection_id, db)
        
        # Check permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only disconnect your own accounts"
            )

        # Platform-specific cleanup could go here
        # (e.g., revoking tokens, cleaning up webhooks)
        
        # Delete the connection
        result = await AgentSocialConnectionService.delete_connection(connection_id, db)
        
        logger.info(f"Disconnected {connection.platform.name if connection.platform else 'unknown'} account for user {current_user.id}")
        
        return result

    @staticmethod
    async def refresh_connection_token(
        connection_id: uuid.UUID,
        current_user: User,
        db: Session
    ) -> TokenValidationResponse:
        """Refresh OAuth token for a connection"""
        
        # Get connection to check permissions
        connection = await AgentSocialConnectionService.get_connection(connection_id, db)
        
        # Check permission
        is_admin = any(role.name in ["platform_admin", "admin"] for role in current_user.roles)
        if not is_admin and connection.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only refresh your own connection tokens"
            )

        # This would integrate with your OAuth service to refresh tokens
        # Platform-specific token refresh logic would go here
        
        # For now, just validate the current token
        return await AgentSocialConnectionService.validate_token(connection_id, db)