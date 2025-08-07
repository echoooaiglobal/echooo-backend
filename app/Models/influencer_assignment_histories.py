# app/Models/influencer_assignment_histories.py

import uuid
from sqlalchemy import Column, Text, Integer, ForeignKey, DateTime, Enum, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.Models.base import Base

class InfluencerAssignmentHistory(Base):
    __tablename__ = 'influencer_assignment_histories'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    campaign_influencer_id = Column(UUID(as_uuid=True), ForeignKey('campaign_influencers.id', ondelete='CASCADE'), nullable=False)
    agent_assignment_id = Column(UUID(as_uuid=True), ForeignKey('agent_assignments.id', ondelete='SET NULL'), nullable=False)  # New field added
    from_outreach_agent_id = Column(UUID(as_uuid=True), ForeignKey('outreach_agents.id', ondelete='SET NULL'), nullable=True)
    to_outreach_agent_id = Column(UUID(as_uuid=True), ForeignKey('outreach_agents.id', ondelete='SET NULL'), nullable=False)
    reassignment_reason_id = Column(UUID(as_uuid=True), ForeignKey('reassignment_reasons.id', ondelete='RESTRICT'), nullable=False)
    attempts_before_reassignment = Column(Integer, nullable=False, default=0)
    reassignment_triggered_by = Column(Enum('system', 'user', 'agent', name='triggered_by_enum'), nullable=False)
    reassigned_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    reassignment_notes = Column(Text, nullable=True)
    
    previous_assignment_data = Column(JSONB, nullable=True)  # Snapshot of the previous assignment data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    campaign_influencer = relationship("CampaignInfluencer")
    agent_assignment = relationship("AgentAssignment", back_populates="assignment_histories")  # New relationship
    reassignment_reason = relationship("ReassignmentReason", back_populates="assignment_histories")
    from_agent = relationship("OutreachAgent", foreign_keys=[from_outreach_agent_id])
    to_agent = relationship("OutreachAgent", foreign_keys=[to_outreach_agent_id])
    reassigned_by_user = relationship("User", foreign_keys=[reassigned_by])

    # Indexes for performance
    __table_args__ = (
        Index('ix_assignment_history_influencer', 'campaign_influencer_id'),
        Index('ix_assignment_history_agent_assignment', 'agent_assignment_id'),  # New index
        Index('ix_assignment_history_agents', 'from_outreach_agent_id', 'to_outreach_agent_id'),
        Index('ix_assignment_history_reason', 'reassignment_reason_id'),
        Index('ix_assignment_history_created', 'created_at'),
        Index('ix_assignment_history_triggered_by', 'reassignment_triggered_by'),
    )