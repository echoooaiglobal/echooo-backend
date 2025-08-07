# app/Models/agent_assignments.py

import uuid
from sqlalchemy import Column, ForeignKey, DateTime, func, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.Models.base import Base

class AgentAssignment(Base):
    __tablename__ = 'agent_assignments'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    outreach_agent_id = Column(UUID(as_uuid=True), ForeignKey('outreach_agents.id', ondelete='CASCADE'), nullable=False)
    campaign_list_id = Column(UUID(as_uuid=True), ForeignKey('campaign_lists.id', ondelete='CASCADE'), nullable=False)
    status_id = Column(UUID(as_uuid=True), ForeignKey('statuses.id', ondelete='SET NULL'), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    # Soft delete fields
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    agent = relationship("OutreachAgent", back_populates="agent_assignments")
    campaign_list = relationship("CampaignList", back_populates="agent_assignments")
    status = relationship("Status", back_populates="agent_assignments")
    assigned_influencers = relationship("AssignedInfluencer", back_populates="agent_assignment", cascade="all, delete-orphan")
    outreach_records = relationship("InfluencerOutreach", back_populates="agent_assignment")
    assignment_histories = relationship("InfluencerAssignmentHistory", back_populates="agent_assignment")
    deleter = relationship("User", foreign_keys=[deleted_by])

    # Indexes for performance
    __table_args__ = (
        Index('ix_agent_assignments_agent_list', 'outreach_agent_id', 'campaign_list_id'),
        Index('ix_agent_assignments_status', 'status_id'),
        Index('ix_agent_assignments_is_deleted', 'is_deleted'),
        Index('ix_agent_assignments_assigned_at', 'assigned_at'),
    )