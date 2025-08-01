# app/Services/AgentSocialConnectionService.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, Integer, and_, or_
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timedelta

from app.Models.agent_social_connections import AgentSocialConnection
from app.Models.platforms import Platform
from app.Models.auth_models import User
from app.Models.outreach_agents import OutreachAgent
from app.Models.statuses import Status
from app.Schemas.agent_social_connection import (
    AgentSocialConnectionCreate, AgentSocialConnectionUpdate,
    AgentSocialConnectionDetailResponse, AgentSocialConnectionsPaginatedResponse,
    UserPlatformConnectionsStatus, TokenValidationResponse,
    AutomationToggleRequest, AutomationStatusResponse,
    SystemHealthReport, UserBrief, PlatformBrief, AgentBrief, StatusBrief
)
from app.Utils.encryption import encrypt_token, decrypt_token
from app.Utils.Logger import logger

class AgentSocialConnectionService:
    """Service for managing agent social connections"""

    @staticmethod
    async def create_connection(
        connection_data: AgentSocialConnectionCreate,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Create a new social media connection"""
        
        try:
            # Validate user exists
            user = db.query(User).filter(User.id == connection_data.user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Validate platform exists
            platform = db.query(Platform).filter(Platform.id == connection_data.platform_id).first()
            if not platform:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Platform not found"
                )
            
            # Check for existing connection
            existing_connection = db.query(AgentSocialConnection).filter(
                and_(
                    AgentSocialConnection.user_id == connection_data.user_id,
                    AgentSocialConnection.platform_id == connection_data.platform_id,
                    AgentSocialConnection.platform_user_id == connection_data.platform_user_id,
                    AgentSocialConnection.deleted_at.is_(None)
                )
            ).first()
            
            if existing_connection:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Connection already exists for this platform and user"
                )

            # Encrypt sensitive tokens
            encrypted_access_token = None
            encrypted_refresh_token = None
            encrypted_page_token = None
            
            if connection_data.access_token:
                encrypted_access_token = encrypt_token(connection_data.access_token)
            if connection_data.refresh_token:
                encrypted_refresh_token = encrypt_token(connection_data.refresh_token)
            if connection_data.facebook_page_access_token:
                encrypted_page_token = encrypt_token(connection_data.facebook_page_access_token)

            # Create connection
            new_connection = AgentSocialConnection(
                user_id=connection_data.user_id,
                platform_id=connection_data.platform_id,
                platform_user_id=connection_data.platform_user_id,
                platform_username=connection_data.platform_username,
                display_name=connection_data.display_name,
                profile_image_url=connection_data.profile_image_url,
                access_token=encrypted_access_token,
                refresh_token=encrypted_refresh_token,
                expires_at=connection_data.expires_at,
                scope=connection_data.scope,
                instagram_business_account_id=connection_data.instagram_business_account_id,
                facebook_page_id=connection_data.facebook_page_id,
                facebook_page_access_token=encrypted_page_token,
                facebook_page_name=connection_data.facebook_page_name,
                automation_capabilities=connection_data.automation_capabilities or {},
                additional_data=connection_data.additional_data or {},
                is_active=True
            )

            db.add(new_connection)
            db.commit()
            db.refresh(new_connection)

            logger.info(f"Created social connection {new_connection.id} for user {connection_data.user_id} on platform {platform.name}")

            return await AgentSocialConnectionService._get_connection_with_relations(new_connection.id, db)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating social connection: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create social connection"
            )

    @staticmethod
    async def get_connection(
        connection_id: uuid.UUID,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Get a social connection by ID"""
        
        connection = await AgentSocialConnectionService._get_connection_with_relations(connection_id, db)
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social connection not found"
            )
        
        return connection

    @staticmethod
    async def update_connection(
        connection_id: uuid.UUID,
        update_data: AgentSocialConnectionUpdate,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Update a social connection"""
        
        try:
            connection = db.query(AgentSocialConnection).filter(
                AgentSocialConnection.id == connection_id,
                AgentSocialConnection.deleted_at.is_(None)
            ).first()
            
            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Social connection not found"
                )
            
            # Update fields if provided
            update_fields = update_data.model_dump(exclude_unset=True)
            
            for field, value in update_fields.items():
                if field in ["access_token", "refresh_token", "facebook_page_access_token"]:
                    # Encrypt sensitive tokens
                    if value:
                        setattr(connection, field, encrypt_token(value))
                    else:
                        setattr(connection, field, None)
                else:
                    setattr(connection, field, value)
            
            connection.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(connection)
            
            logger.info(f"Updated social connection {connection_id}")
            
            return await AgentSocialConnectionService._get_connection_with_relations(connection_id, db)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating social connection: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update social connection"
            )

    @staticmethod
    async def delete_connection(
        connection_id: uuid.UUID,
        db: Session
    ) -> Dict[str, str]:
        """Soft delete a social connection"""
        
        try:
            connection = db.query(AgentSocialConnection).filter(
                AgentSocialConnection.id == connection_id,
                AgentSocialConnection.deleted_at.is_(None)
            ).first()
            
            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Social connection not found"
                )
            
            # Soft delete
            connection.deleted_at = datetime.utcnow()
            connection.is_active = False
            
            db.commit()
            
            logger.info(f"Deleted social connection {connection_id}")
            
            return {"message": "Social connection deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting social connection: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete social connection"
            )

    @staticmethod
    async def disconnect_connection(
        connection_id: uuid.UUID,
        db: Session
    ) -> Dict[str, str]:
        """Disconnect and cleanup a social connection"""
        
        try:
            connection = db.query(AgentSocialConnection).filter(
                AgentSocialConnection.id == connection_id,
                AgentSocialConnection.deleted_at.is_(None)
            ).first()
            
            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Social connection not found"
                )
            
            # TODO: Add platform-specific cleanup logic here
            # - Revoke OAuth tokens
            # - Cleanup webhooks
            # - Cancel subscriptions
            
            # For now, just deactivate the connection
            connection.is_active = False
            connection.access_token = None
            connection.refresh_token = None
            connection.facebook_page_access_token = None
            
            # Add disconnection metadata
            if not connection.additional_data:
                connection.additional_data = {}
            
            connection.additional_data["disconnected_at"] = datetime.utcnow().isoformat()
            connection.additional_data["disconnection_reason"] = "user_requested"
            
            db.commit()
            
            logger.info(f"Disconnected social connection {connection_id}")
            
            return {"message": "Platform account disconnected successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error disconnecting platform account: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to disconnect platform account"
            )

    @staticmethod
    async def get_connections_paginated(
        page: int,
        page_size: int,
        user_id: Optional[uuid.UUID],
        platform_id: Optional[uuid.UUID],
        active_only: bool,
        search: Optional[str],
        db: Session
    ) -> AgentSocialConnectionsPaginatedResponse:
        """Get paginated list of social connections"""
        
        try:
            # Build query
            query = db.query(AgentSocialConnection).options(
                joinedload(AgentSocialConnection.user),
                joinedload(AgentSocialConnection.platform),
                joinedload(AgentSocialConnection.agent),
                joinedload(AgentSocialConnection.status)
            ).filter(AgentSocialConnection.deleted_at.is_(None))
            
            # Apply filters
            if user_id:
                query = query.filter(AgentSocialConnection.user_id == user_id)
            
            if platform_id:
                query = query.filter(AgentSocialConnection.platform_id == platform_id)
            
            if active_only:
                query = query.filter(AgentSocialConnection.is_active == True)
            
            if search:
                search_filter = or_(
                    AgentSocialConnection.platform_username.ilike(f"%{search}%"),
                    AgentSocialConnection.display_name.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * page_size
            connections = query.offset(offset).limit(page_size).all()
            
            # Format response
            items = [
                AgentSocialConnectionService._format_connection_response(conn)
                for conn in connections
            ]
            
            pages = (total + page_size - 1) // page_size
            
            return AgentSocialConnectionsPaginatedResponse(
                items=items,
                total=total,
                page=page,
                size=page_size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Error getting paginated connections: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve connections"
            )

    @staticmethod
    async def get_user_connections(
        user_id: uuid.UUID,
        platform_id: Optional[uuid.UUID],
        active_only: bool,
        db: Session
    ) -> List[AgentSocialConnectionDetailResponse]:
        """Get all connections for a specific user"""
        
        try:
            query = db.query(AgentSocialConnection).options(
                joinedload(AgentSocialConnection.user),
                joinedload(AgentSocialConnection.platform),
                joinedload(AgentSocialConnection.agent),
                joinedload(AgentSocialConnection.status)
            ).filter(
                AgentSocialConnection.user_id == user_id,
                AgentSocialConnection.deleted_at.is_(None)
            )
            
            if platform_id:
                query = query.filter(AgentSocialConnection.platform_id == platform_id)
            
            if active_only:
                query = query.filter(AgentSocialConnection.is_active == True)
            
            connections = query.all()
            
            return [
                AgentSocialConnectionService._format_connection_response(conn)
                for conn in connections
            ]
            
        except Exception as e:
            logger.error(f"Error getting user connections: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user connections"
            )

    @staticmethod
    async def get_platform_connections_status(
        user_id: uuid.UUID,
        db: Session
    ) -> UserPlatformConnectionsStatus:
        """Get platform connection status for a user"""
        
        try:
            # Get user's connections grouped by platform
            connections = db.query(AgentSocialConnection).options(
                joinedload(AgentSocialConnection.platform)
            ).filter(
                AgentSocialConnection.user_id == user_id,
                AgentSocialConnection.deleted_at.is_(None)
            ).all()
            
            # Group by platform
            platform_stats = {}
            total_connections = len(connections)
            active_connections = 0
            last_connection_date = None
            
            for conn in connections:
                platform_name = conn.platform.name
                
                if platform_name not in platform_stats:
                    platform_stats[platform_name] = {
                        "platform_id": str(conn.platform_id),
                        "platform_name": platform_name,
                        "total_connections": 0,
                        "active_connections": 0,
                        "last_connection_date": None
                    }
                
                platform_stats[platform_name]["total_connections"] += 1
                
                if conn.is_active:
                    platform_stats[platform_name]["active_connections"] += 1
                    active_connections += 1
                
                # Track latest connection date
                conn_date = conn.created_at
                if not platform_stats[platform_name]["last_connection_date"] or conn_date > platform_stats[platform_name]["last_connection_date"]:
                    platform_stats[platform_name]["last_connection_date"] = conn_date
                
                if not last_connection_date or conn_date > last_connection_date:
                    last_connection_date = conn_date
            
            platforms = list(platform_stats.values())
            
            return UserPlatformConnectionsStatus(
                user_id=str(user_id),
                total_connections=total_connections,
                active_connections=active_connections,
                platforms=platforms,
                last_connection_date=last_connection_date
            )
            
        except Exception as e:
            logger.error(f"Error getting platform connection status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve platform connection status"
            )

    # =============================================================================
    # TOKEN MANAGEMENT METHODS
    # =============================================================================

    @staticmethod
    async def validate_connection_token(
        connection_id: uuid.UUID,
        db: Session
    ) -> TokenValidationResponse:
        """Validate OAuth token for a connection"""
        
        try:
            connection = db.query(AgentSocialConnection).filter(
                AgentSocialConnection.id == connection_id,
                AgentSocialConnection.deleted_at.is_(None)
            ).first()
            
            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Connection not found"
                )
            
            # Update last check time
            connection.last_oauth_check_at = datetime.utcnow()
            
            # Check token expiration
            is_valid = True
            needs_renewal = False
            expires_in_hours = None
            
            if connection.expires_at:
                now = datetime.utcnow()
                expires_in_hours = int((connection.expires_at - now).total_seconds() / 3600)
                
                if connection.expires_at <= now:
                    is_valid = False
                elif expires_in_hours < 24:  # Needs renewal if expires in less than 24 hours
                    needs_renewal = True
            
            # TODO: Add platform-specific token validation here
            # For now, just check expiration
            
            db.commit()
            
            return TokenValidationResponse(
                connection_id=str(connection_id),
                is_valid=is_valid,
                expires_at=connection.expires_at,
                expires_in_hours=expires_in_hours,
                needs_renewal=needs_renewal,
                last_check=connection.last_oauth_check_at
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating connection token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to validate connection token"
            )

    @staticmethod
    async def refresh_connection_token(
        connection_id: uuid.UUID,
        db: Session
    ) -> TokenValidationResponse:
        """Refresh OAuth token for a connection"""
        
        try:
            connection = db.query(AgentSocialConnection).filter(
                AgentSocialConnection.id == connection_id,
                AgentSocialConnection.deleted_at.is_(None)
            ).first()
            
            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Connection not found"
                )
            
            # TODO: Add platform-specific token refresh logic here
            # For now, return current status
            
            logger.info(f"Token refresh attempted for connection {connection_id}")
            
            return TokenValidationResponse(
                connection_id=str(connection_id),
                is_valid=True,
                expires_at=connection.expires_at,
                expires_in_hours=None,
                needs_renewal=False,
                last_check=datetime.utcnow()
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error refreshing connection token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to refresh connection token"
            )

    # =============================================================================
    # AUTOMATION METHODS
    # =============================================================================

    @staticmethod
    async def toggle_automation(
        automation_request: AutomationToggleRequest,
        db: Session
    ) -> AutomationStatusResponse:
        """Enable or disable automation for a connection"""
        
        try:
            connection_id = uuid.UUID(automation_request.connection_id)
            connection = db.query(AgentSocialConnection).filter(
                AgentSocialConnection.id == connection_id,
                AgentSocialConnection.deleted_at.is_(None)
            ).first()
            
            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Connection not found"
                )
            
            # Update automation capabilities
            if not connection.automation_capabilities:
                connection.automation_capabilities = {}
            
            connection.automation_capabilities["automation_enabled"] = automation_request.enable_automation
            
            if automation_request.automation_features:
                connection.automation_capabilities["enabled_features"] = automation_request.automation_features
            
            connection.automation_capabilities["last_updated"] = datetime.utcnow().isoformat()
            
            db.commit()
            
            logger.info(f"Automation {'enabled' if automation_request.enable_automation else 'disabled'} for connection {connection_id}")
            
            return AutomationStatusResponse(
                connection_id=str(connection_id),
                is_automation_enabled=automation_request.enable_automation,
                automation_capabilities=connection.automation_capabilities,
                last_automation_use=connection.last_automation_use_at,
                automation_error_count=connection.automation_error_count or 0,
                last_error=connection.last_error_message
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error toggling automation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to toggle automation"
            )

    @staticmethod
    async def get_automation_status(
        connection_id: uuid.UUID,
        db: Session
    ) -> AutomationStatusResponse:
        """Get automation status for a connection"""
        
        try:
            connection = db.query(AgentSocialConnection).filter(
                AgentSocialConnection.id == connection_id,
                AgentSocialConnection.deleted_at.is_(None)
            ).first()
            
            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Connection not found"
                )
            
            automation_capabilities = connection.automation_capabilities or {}
            is_enabled = automation_capabilities.get("automation_enabled", False)
            
            return AutomationStatusResponse(
                connection_id=str(connection_id),
                is_automation_enabled=is_enabled,
                automation_capabilities=automation_capabilities,
                last_automation_use=connection.last_automation_use_at,
                automation_error_count=connection.automation_error_count or 0,
                last_error=connection.last_error_message
            )
            
        except Exception as e:
            logger.error(f"Error getting automation status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get automation status"
            )

    # =============================================================================
    # ANALYTICS AND REPORTING METHODS
    # =============================================================================

    @staticmethod
    async def get_platform_usage_analytics(
        user_id: uuid.UUID,
        days: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get platform usage analytics"""
        
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get connections for the user
            connections = db.query(AgentSocialConnection).options(
                joinedload(AgentSocialConnection.platform)
            ).filter(
                AgentSocialConnection.user_id == user_id,
                AgentSocialConnection.deleted_at.is_(None),
                AgentSocialConnection.created_at >= start_date
            ).all()
            
            # Group analytics by platform
            platform_analytics = {}
            
            for conn in connections:
                platform_name = conn.platform.name
                
                if platform_name not in platform_analytics:
                    platform_analytics[platform_name] = {
                        "platform_name": platform_name,
                        "total_connections": 0,
                        "active_connections": 0,
                        "total_automation_uses": 0,
                        "total_errors": 0,
                        "last_activity": None
                    }
                
                platform_analytics[platform_name]["total_connections"] += 1
                
                if conn.is_active:
                    platform_analytics[platform_name]["active_connections"] += 1
                
                if conn.automation_error_count:
                    platform_analytics[platform_name]["total_errors"] += conn.automation_error_count
                
                # Track last activity
                last_activity = conn.last_automation_use_at or conn.created_at
                if not platform_analytics[platform_name]["last_activity"] or last_activity > platform_analytics[platform_name]["last_activity"]:
                    platform_analytics[platform_name]["last_activity"] = last_activity
            
            return list(platform_analytics.values())
            
        except Exception as e:
            logger.error(f"Error getting platform usage analytics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get platform usage analytics"
            )

    @staticmethod
    async def get_system_health_report(db: Session) -> SystemHealthReport:
        """Get system health report for all connections"""
        
        try:
            # Get total connections
            total_connections = db.query(AgentSocialConnection).filter(
                AgentSocialConnection.deleted_at.is_(None)
            ).count()
            
            # Get healthy connections (active with no recent errors)
            healthy_connections = db.query(AgentSocialConnection).filter(
                AgentSocialConnection.deleted_at.is_(None),
                AgentSocialConnection.is_active == True,
                or_(
                    AgentSocialConnection.automation_error_count == 0,
                    AgentSocialConnection.automation_error_count.is_(None)
                )
            ).count()
            
            unhealthy_connections = total_connections - healthy_connections
            
            # Get platform statistics
            platform_stats = db.query(
                Platform.name,
                func.count(AgentSocialConnection.id).label('connection_count'),
                func.sum(func.cast(AgentSocialConnection.is_active, Integer)).label('active_count')
            ).join(
                AgentSocialConnection, Platform.id == AgentSocialConnection.platform_id
            ).filter(
                AgentSocialConnection.deleted_at.is_(None)
            ).group_by(Platform.name).all()
            
            platforms_status = [
                {
                    "platform_name": stat.name,
                    "total_connections": stat.connection_count,
                    "active_connections": stat.active_count or 0
                }
                for stat in platform_stats
            ]
            
            return SystemHealthReport(
                total_connections=total_connections,
                healthy_connections=healthy_connections,
                unhealthy_connections=unhealthy_connections,
                platforms_status=platforms_status,
                last_check=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error getting system health report: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get system health report"
            )

    # =============================================================================
    # HELPER METHODS
    # =============================================================================

    @staticmethod
    async def _get_connection_with_relations(connection_id: uuid.UUID, db: Session):
        """Helper method to get connection with all relations"""
        connection = db.query(AgentSocialConnection).options(
            joinedload(AgentSocialConnection.user),
            joinedload(AgentSocialConnection.platform),
            joinedload(AgentSocialConnection.agent),
            joinedload(AgentSocialConnection.status)
        ).filter(
            AgentSocialConnection.id == connection_id,
            AgentSocialConnection.deleted_at.is_(None)
        ).first()

        if not connection:
            return None

        return AgentSocialConnectionService._format_connection_response(connection)

    @staticmethod
    def _format_connection_response(connection: AgentSocialConnection) -> AgentSocialConnectionDetailResponse:
        """Helper method to format connection response with relations"""
        
        # Format user brief
        user_brief = None
        if connection.user:
            user_brief = UserBrief(
                id=str(connection.user.id),
                email=connection.user.email,
                full_name=connection.user.full_name or f"{connection.user.first_name or ''} {connection.user.last_name or ''}".strip()
            )

        # Format platform brief
        platform_brief = None
        if connection.platform:
            platform_brief = PlatformBrief(
                id=str(connection.platform.id),
                name=connection.platform.name,
                logo_url=connection.platform.logo_url,
                category=connection.platform.category
            )

        # Format agent brief
        agent_brief = None
        if connection.agent:
            agent_brief = AgentBrief(
                id=str(connection.agent.id),
                assigned_user_id=str(connection.agent.assigned_user_id),
                is_automation_enabled=connection.agent.is_automation_enabled
            )

        # Format status brief
        status_brief = None
        if connection.status:
            status_brief = StatusBrief(
                id=str(connection.status.id),
                name=connection.status.name,
                description=connection.status.description
            )

        return AgentSocialConnectionDetailResponse(
            id=str(connection.id),
            user_id=str(connection.user_id),
            platform_id=str(connection.platform_id),
            platform_user_id=connection.platform_user_id,
            platform_username=connection.platform_username,
            display_name=connection.display_name,
            profile_image_url=connection.profile_image_url,
            expires_at=connection.expires_at,
            last_oauth_check_at=connection.last_oauth_check_at,
            scope=connection.scope,
            instagram_business_account_id=connection.instagram_business_account_id,
            facebook_page_id=connection.facebook_page_id,
            facebook_page_name=connection.facebook_page_name,
            automation_capabilities=connection.automation_capabilities,
            last_automation_use_at=connection.last_automation_use_at,
            automation_error_count=connection.automation_error_count or 0,
            last_error_message=connection.last_error_message,
            last_error_at=connection.last_error_at,
            is_active=connection.is_active,
            additional_data=connection.additional_data,
            status_id=str(connection.status_id) if connection.status_id else None,
            created_at=connection.created_at,
            updated_at=connection.updated_at,
            user=user_brief,
            platform=platform_brief,
            agent=agent_brief,
            status=status_brief
        )