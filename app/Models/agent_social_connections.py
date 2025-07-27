# app/Models/agent_social_connections.py

import uuid
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.Models.base import Base

class AgentSocialConnection(Base):
    __tablename__ = 'agent_social_connections'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    platform_id = Column(UUID(as_uuid=True), ForeignKey('platforms.id', ondelete='CASCADE'), nullable=False)
    outreach_agent_id = Column(UUID(as_uuid=True), ForeignKey('outreach_agents.id', ondelete='CASCADE'), nullable=True)  # MISSING FOREIGN KEY
    platform_user_id = Column(String(255), nullable=False)
    platform_username = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    profile_image_url = Column(String(500), nullable=True)
    access_token = Column(Text, nullable=True)  # Encrypted OAuth access token
    refresh_token = Column(Text, nullable=True)  # Encrypted OAuth refresh token
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_oauth_check_at = Column(DateTime(timezone=True), nullable=True)
    scope = Column(Text, nullable=True)  # OAuth permissions granted
    instagram_business_account_id = Column(String(255), nullable=True)
    facebook_page_id = Column(String(255), nullable=True)
    facebook_page_access_token = Column(Text, nullable=True)  # Encrypted Facebook page token
    facebook_page_name = Column(String(255), nullable=True)
    automation_capabilities = Column(JSONB, nullable=True)
    playwright_session_data = Column(JSONB, nullable=True)  # Browser session data for automation
    last_automation_use_at = Column(DateTime(timezone=True), nullable=True)
    automation_error_count = Column(Integer, nullable=False, default=0)
    last_error_message = Column(Text, nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Additional data for platform-specific additional data
    additional_data = Column(JSONB, nullable=True)
    status_id = Column(UUID(as_uuid=True), ForeignKey('statuses.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships - Fixed: added back_populates for platform and missing outreach_records
    user = relationship("User", back_populates="agent_social_connections")
    platform = relationship("Platform", back_populates="agent_social_connections")
    agent = relationship("OutreachAgent", back_populates="social_connections")
    status = relationship("Status", back_populates="agent_social_connections")
    
    # MISSING RELATIONSHIP - This was causing the error
    outreach_records = relationship("InfluencerOutreach", back_populates="agent_social_connection")

    # Indexes for performance
    __table_args__ = (
        Index('ix_agent_social_user_platform', 'user_id', 'platform_id'),
        Index('ix_agent_social_outreach_agent', 'outreach_agent_id'),  # NEW INDEX
        Index('ix_agent_social_username', 'platform_username'),
        Index('ix_agent_social_active_status', 'is_active', 'status_id'),
        Index('ix_agent_social_oauth_expires', 'expires_at'),
        Index('ix_agent_social_last_use', 'last_automation_use_at'),
    )