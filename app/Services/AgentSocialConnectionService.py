# app/Services/AgentSocialConnectionService.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import func, and_, or_, desc, Integer
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status
import uuid
from datetime import datetime, timedelta
import httpx
import json

from app.Models.agent_social_connections import AgentSocialConnection
from app.Models.outreach_agents import OutreachAgent
from app.Models.auth_models import User
from app.Models.platforms import Platform
from app.Schemas.agent_social_connection import (
    AgentSocialConnectionCreate, AgentSocialConnectionUpdate,
    AgentSocialConnectionResponse, AgentSocialConnectionDetailResponse,
    AgentSocialConnectionsPaginatedResponse, PlatformConnectionStatus,
    UserPlatformConnectionsStatus, TokenValidationResponse,
    AutomationStatusResponse, ConnectionHealthCheck, SystemHealthReport
)
from app.Utils.Logger import logger
from app.Utils.encryption import encrypt_token, decrypt_token
from config.settings import settings

class AgentSocialConnectionService:
    """Service for managing agent social connections across platforms"""

    @staticmethod
    async def create_connection(
        connection_data: AgentSocialConnectionCreate, 
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Create a new social media connection for an agent"""
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

            # Check for existing connection (one per user per platform)
            existing_connection = db.query(AgentSocialConnection).filter(
                and_(
                    AgentSocialConnection.user_id == connection_data.user_id,
                    AgentSocialConnection.platform_id == connection_data.platform_id,
                    AgentSocialConnection.platform_user_id == connection_data.platform_user_id
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

        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error creating connection: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database constraint violation"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating social connection: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create social connection"
            )

    @staticmethod
    async def get_connection(connection_id: uuid.UUID, db: Session) -> AgentSocialConnectionDetailResponse:
        """Get a specific social connection by ID"""
        connection = await AgentSocialConnectionService._get_connection_with_relations(connection_id, db)
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social connection not found"
            )
        return connection

    @staticmethod
    async def get_user_connections(
        user_id: uuid.UUID, 
        platform_id: Optional[uuid.UUID] = None,
        active_only: bool = True,
        db: Session = None
    ) -> List[AgentSocialConnectionDetailResponse]:
        """Get all connections for a specific user"""
        query = db.query(AgentSocialConnection).options(
            joinedload(AgentSocialConnection.user),
            joinedload(AgentSocialConnection.platform),
            joinedload(AgentSocialConnection.agent),
            joinedload(AgentSocialConnection.status)
        ).filter(AgentSocialConnection.user_id == user_id)

        if platform_id:
            query = query.filter(AgentSocialConnection.platform_id == platform_id)
        
        if active_only:
            query = query.filter(AgentSocialConnection.is_active == True)

        query = query.filter(AgentSocialConnection.deleted_at.is_(None))
        connections = query.all()

        return [AgentSocialConnectionService._format_connection_response(conn) for conn in connections]

    @staticmethod
    async def get_connections_paginated(
        page: int = 1,
        page_size: int = 10,
        user_id: Optional[uuid.UUID] = None,
        platform_id: Optional[uuid.UUID] = None,
        active_only: bool = True,
        search: Optional[str] = None,
        db: Session = None
    ) -> AgentSocialConnectionsPaginatedResponse:
        """Get paginated social connections with filters"""
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Build base query
        query = db.query(AgentSocialConnection).options(
            joinedload(AgentSocialConnection.user),
            joinedload(AgentSocialConnection.platform),
            joinedload(AgentSocialConnection.agent),
            joinedload(AgentSocialConnection.status)
        )

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

        # Exclude soft deleted
        query = query.filter(AgentSocialConnection.deleted_at.is_(None))

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        connections = query.order_by(desc(AgentSocialConnection.created_at)).offset(offset).limit(page_size).all()

        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size

        # Format responses
        formatted_connections = [
            AgentSocialConnectionService._format_connection_response(conn) 
            for conn in connections
        ]

        return AgentSocialConnectionsPaginatedResponse(
            connections=formatted_connections,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    @staticmethod
    async def update_connection(
        connection_id: uuid.UUID,
        update_data: AgentSocialConnectionUpdate,
        db: Session
    ) -> AgentSocialConnectionDetailResponse:
        """Update a social connection"""
        try:
            connection = db.query(AgentSocialConnection).filter(
                AgentSocialConnection.id == connection_id
            ).first()

            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Social connection not found"
                )

            # Update fields
            update_dict = update_data.model_dump(exclude_unset=True)
            
            # Handle token encryption
            if 'access_token' in update_dict and update_dict['access_token']:
                update_dict['access_token'] = encrypt_token(update_dict['access_token'])
            
            if 'refresh_token' in update_dict and update_dict['refresh_token']:
                update_dict['refresh_token'] = encrypt_token(update_dict['refresh_token'])
            
            if 'facebook_page_access_token' in update_dict and update_dict['facebook_page_access_token']:
                update_dict['facebook_page_access_token'] = encrypt_token(update_dict['facebook_page_access_token'])

            for field, value in update_dict.items():
                setattr(connection, field, value)

            connection.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(connection)

            logger.info(f"Updated social connection {connection_id}")
            return await AgentSocialConnectionService._get_connection_with_relations(connection_id, db)

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating social connection {connection_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update social connection"
            )

    @staticmethod
    async def delete_connection(connection_id: uuid.UUID, db: Session) -> dict:
        """Soft delete a social connection"""
        try:
            connection = db.query(AgentSocialConnection).filter(
                AgentSocialConnection.id == connection_id
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

        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting social connection {connection_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete social connection"
            )

    @staticmethod
    async def get_platform_connections_status(
        user_id: uuid.UUID, 
        db: Session
    ) -> UserPlatformConnectionsStatus:
        """Get connection status across all platforms for a user"""
        
        # Get all platforms
        platforms = db.query(Platform).all()
        platform_statuses = []
        total_connections = 0
        active_connections = 0

        for platform in platforms:
            # Get connections for this platform
            connections = db.query(AgentSocialConnection).filter(
                and_(
                    AgentSocialConnection.user_id == user_id,
                    AgentSocialConnection.platform_id == platform.id,
                    AgentSocialConnection.deleted_at.is_(None)
                )
            ).all()

            connection_count = len(connections)
            active_count = len([c for c in connections if c.is_active])
            last_connected = None

            if connections:
                last_connected = max(c.created_at for c in connections)

            platform_statuses.append(PlatformConnectionStatus(
                platform_id=str(platform.id),
                platform_name=platform.name,
                is_connected=connection_count > 0,
                connection_count=connection_count,
                active_connections=active_count,
                last_connected=last_connected
            ))

            total_connections += connection_count
            active_connections += active_count

        return UserPlatformConnectionsStatus(
            user_id=str(user_id),
            platforms=platform_statuses,
            total_connections=total_connections,
            active_connections=active_connections
        )

    @staticmethod
    async def validate_token(connection_id: uuid.UUID, db: Session) -> TokenValidationResponse:
        """Validate OAuth token for a connection"""
        connection = db.query(AgentSocialConnection).filter(
            AgentSocialConnection.id == connection_id
        ).first()

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social connection not found"
            )

        is_valid = True
        expires_in_hours = None
        needs_renewal = False

        if connection.expires_at:
            now = datetime.utcnow()
            if connection.expires_at <= now:
                is_valid = False
            else:
                expires_in_hours = (connection.expires_at - now).total_seconds() / 3600
                # Mark for renewal if expires within 24 hours
                needs_renewal = expires_in_hours <= 24

        # Update last check time
        connection.last_oauth_check_at = datetime.utcnow()
        db.commit()

        return TokenValidationResponse(
            connection_id=str(connection_id),
            is_valid=is_valid,
            expires_at=connection.expires_at,
            expires_in_hours=expires_in_hours,
            needs_renewal=needs_renewal,
            last_check=connection.last_oauth_check_at
        )

    @staticmethod
    async def toggle_automation(
        connection_id: uuid.UUID, 
        enabled: bool, 
        db: Session
    ) -> AutomationStatusResponse:
        """Enable/disable automation for a connection"""
        connection = db.query(AgentSocialConnection).filter(
            AgentSocialConnection.id == connection_id
        ).first()

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social connection not found"
            )

        # Get related agent and update automation
        agent = db.query(OutreachAgent).filter(
            OutreachAgent.assigned_user_id == connection.user_id
        ).first()

        if agent:
            agent.is_automation_enabled = enabled

        # Reset error count when enabling automation
        if enabled:
            connection.automation_error_count = 0
            connection.last_error_message = None

        db.commit()

        return AutomationStatusResponse(
            connection_id=str(connection_id),
            is_automation_enabled=enabled,
            automation_capabilities=connection.automation_capabilities,
            last_automation_use=connection.last_automation_use_at,
            error_count=connection.automation_error_count,
            last_error=connection.last_error_message
        )

    @staticmethod
    async def check_connection_health(
        connection_id: uuid.UUID, 
        db: Session
    ) -> ConnectionHealthCheck:
        """Check the health of a social connection"""
        connection = db.query(AgentSocialConnection).options(
            joinedload(AgentSocialConnection.platform)
        ).filter(AgentSocialConnection.id == connection_id).first()

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social connection not found"
            )

        is_healthy = True
        issues = []
        recommendations = []

        # Check token expiration
        if connection.expires_at and connection.expires_at <= datetime.utcnow():
            is_healthy = False
            issues.append("Access token has expired")
            recommendations.append("Refresh or reconnect the account")

        # Check error count
        if connection.automation_error_count > 5:
            is_healthy = False
            issues.append(f"High error count: {connection.automation_error_count}")
            recommendations.append("Review automation settings or reconnect account")

        # Check last activity
        if connection.last_automation_use_at:
            days_since_use = (datetime.utcnow() - connection.last_automation_use_at).days
            if days_since_use > 30:
                issues.append("No recent automation activity")
                recommendations.append("Verify account is still needed")

        return ConnectionHealthCheck(
            connection_id=str(connection_id),
            platform_name=connection.platform.name,
            is_healthy=is_healthy,
            last_successful_operation=connection.last_automation_use_at,
            issues=issues,
            recommendations=recommendations
        )

    @staticmethod
    async def get_system_health_report(db: Session) -> SystemHealthReport:
        """Get overall system health report for all connections"""
        total_connections = db.query(AgentSocialConnection).filter(
            AgentSocialConnection.deleted_at.is_(None)
        ).count()

        # Get healthy connections (active, recent activity, no errors)
        healthy_query = db.query(AgentSocialConnection).filter(
            and_(
                AgentSocialConnection.deleted_at.is_(None),
                AgentSocialConnection.is_active == True,
                AgentSocialConnection.automation_error_count <= 3,
                or_(
                    AgentSocialConnection.expires_at.is_(None),
                    AgentSocialConnection.expires_at > datetime.utcnow()
                )
            )
        )
        healthy_connections = healthy_query.count()
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

    @staticmethod
    async def _get_connection_with_relations(connection_id: uuid.UUID, db: Session):
        """Helper method to get connection with all relations"""
        connection = db.query(AgentSocialConnection).options(
            joinedload(AgentSocialConnection.user),
            joinedload(AgentSocialConnection.platform),
            joinedload(AgentSocialConnection.agent),
            joinedload(AgentSocialConnection.status)
        ).filter(AgentSocialConnection.id == connection_id).first()

        if not connection:
            return None

        return AgentSocialConnectionService._format_connection_response(connection)

    @staticmethod
    def _format_connection_response(connection: AgentSocialConnection) -> AgentSocialConnectionDetailResponse:
        """Helper method to format connection response with relations"""
        from app.Schemas.agent_social_connection import (
            UserBrief, PlatformBrief, AgentBrief, StatusBrief
        )

        # Format user brief
        user_brief = None
        if connection.user:
            user_brief = UserBrief(
                id=str(connection.user.id),
                email=connection.user.email,
                full_name=connection.user.full_name or f"{connection.user.first_name} {connection.user.last_name}"
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
            automation_error_count=connection.automation_error_count,
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