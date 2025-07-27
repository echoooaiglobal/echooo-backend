# app/Models/automation_sessions.py

import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.Models.base import Base

class AutomationSession(Base):
    __tablename__ = 'automation_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    outreach_agent_id = Column(UUID(as_uuid=True), ForeignKey('outreach_agents.id', ondelete='CASCADE'), nullable=False)
    platform_id = Column(UUID(as_uuid=True), ForeignKey('platforms.id', ondelete='CASCADE'), nullable=False)
    agent_social_connection_id = Column(UUID(as_uuid=True), ForeignKey('agent_social_connections.id', ondelete='CASCADE'), nullable=False)
    session_type = Column(Enum('playwright', 'automation', 'bulk_messaging', 'manual_session', name='session_type_enum'), nullable=False)
    status_id = Column(UUID(as_uuid=True), ForeignKey('statuses.id', ondelete='SET NULL'), nullable=False)  # Changed from session_status ENUM to status_id FK
    
    target_influencers_count = Column(Integer, nullable=False, default=0)
    processed_influencers_count = Column(Integer, nullable=False, default=0)
    successful_messages_count = Column(Integer, nullable=False, default=0)
    failed_messages_count = Column(Integer, nullable=False, default=0)
    current_influencer_id = Column(UUID(as_uuid=True), ForeignKey('campaign_influencers.id', ondelete='SET NULL'), nullable=True)
    browser_process_id = Column(String(100), nullable=True)  # Playwright process ID
    browser_session_data = Column(JSONB, nullable=True)  # Current browser state, cookies, etc.
    automation_settings = Column(JSONB, nullable=True)  # Session-specific settings (delays, limits, etc.)
    error_message = Column(String, nullable=True)
    error_count = Column(Integer, nullable=False, default=0)
    max_errors_allowed = Column(Integer, nullable=False, default=5)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    paused_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    timeout_at = Column(DateTime(timezone=True), nullable=True)
    session_duration_minutes = Column(Integer, nullable=True)  # How long session ran (calculated)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships - Updated to include status relationship and correct platform relationship
    agent = relationship("OutreachAgent", back_populates="automation_sessions")
    platform = relationship("Platform", back_populates="automation_sessions")  # Fixed: added back_populates
    social_connection = relationship("AgentSocialConnection")
    current_influencer = relationship("CampaignInfluencer", foreign_keys=[current_influencer_id])
    status = relationship("Status", back_populates="automation_sessions")  # Added back: now has status_id foreign key

    # Indexes for performance - Updated to use status_id instead of session_status
    __table_args__ = (
        Index('ix_automation_sessions_agent_status', 'outreach_agent_id', 'status_id'),  # Changed from session_status to status_id
        Index('ix_automation_sessions_platform', 'platform_id'),
        Index('ix_automation_sessions_started_at', 'started_at'),
        Index('ix_automation_sessions_activity', 'last_activity_at'),
        Index('ix_automation_sessions_browser_pid', 'browser_process_id'),
    )