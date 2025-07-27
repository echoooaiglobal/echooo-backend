# app/Models/outreach_agents.py

import uuid
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.Models.base import Base

class OutreachAgent(Base):
    __tablename__ = 'outreach_agents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    assigned_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=False)
    active_lists_count = Column(Integer, nullable=False, default=0)
    active_influencers_count = Column(Integer, nullable=False, default=0)
    is_automation_enabled = Column(Boolean, nullable=False, default=False)
    automation_settings = Column(JSONB, nullable=True)
    messages_sent_today = Column(Integer, nullable=False, default=0)
    is_available_for_assignment = Column(Boolean, nullable=False, default=True)
    current_automation_session_id = Column(String(100), nullable=True)  # Playwright session identifier
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    is_company_exclusive = Column(Boolean, nullable=False, default=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id', ondelete='SET NULL'), nullable=True)
    status_id = Column(UUID(as_uuid=True), ForeignKey('statuses.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships - Updated with company relationship
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    company = relationship("Company", foreign_keys=[company_id], back_populates="outreach_agents")  # New relationship
    status = relationship("Status", back_populates="outreach_agents")
    social_connections = relationship("AgentSocialConnection", back_populates="agent", cascade="all, delete-orphan")
    agent_assignments = relationship("AgentAssignment", back_populates="agent", cascade="all, delete-orphan")
    automation_sessions = relationship("AutomationSession", back_populates="agent", cascade="all, delete-orphan")
    outreach_records = relationship("InfluencerOutreach", back_populates="outreach_agent")
    

    # Enhanced indexes for performance - Updated with company_id indexes
    __table_args__ = (
        Index('ix_outreach_agents_user_status', 'assigned_user_id', 'status_id'),
        Index('ix_outreach_agents_availability', 'is_available_for_assignment', 'is_automation_enabled'),
        Index('ix_outreach_agents_activity', 'last_activity_at'),
        Index('ix_outreach_agents_capacity', 'active_lists_count', 'active_influencers_count'),
        # New indexes for company-related queries
        Index('ix_outreach_agents_company_exclusive', 'company_id', 'is_company_exclusive'),
        Index('ix_outreach_agents_company_availability', 'company_id', 'is_available_for_assignment', 'is_company_exclusive'),
        Index('ix_outreach_agents_assignment_lookup', 'is_available_for_assignment', 'company_id', 'active_influencers_count'),
        # Partial index for platform agents (company_id IS NULL)
        Index('ix_outreach_agents_platform_agents', 'is_available_for_assignment', 'is_company_exclusive', 
              postgresql_where="company_id IS NULL"),
    )