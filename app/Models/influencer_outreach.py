# app/Models/influencer_outreach.py

import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.Models.base import Base

class InfluencerOutreach(Base):
    __tablename__ = 'influencer_outreach'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys matching the screenshot
    assigned_influencer_id = Column(UUID(as_uuid=True), ForeignKey('assigned_influencers.id', ondelete='CASCADE'), nullable=False)
    agent_assignment_id = Column(UUID(as_uuid=True), ForeignKey('agent_assignments.id', ondelete='SET NULL'), nullable=True)
    outreach_agent_id = Column(UUID(as_uuid=True), ForeignKey('outreach_agents.id', ondelete='SET NULL'), nullable=False)
    agent_social_connection_id = Column(UUID(as_uuid=True), ForeignKey('agent_social_connections.id', ondelete='SET NULL'), nullable=True)
    communication_channel_id = Column(UUID(as_uuid=True), ForeignKey('communication_channels.id', ondelete='SET NULL'), nullable=True)
    message_status_id = Column(UUID(as_uuid=True), ForeignKey('statuses.id', ondelete='SET NULL'), nullable=True)
    
    # Message details
    message_sent_at = Column(DateTime(timezone=True), nullable=True)
    error_code = Column(String(20), nullable=True)  # VARCHAR(20)
    error_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    assigned_influencer = relationship("AssignedInfluencer", back_populates="outreach_records")
    agent_assignment = relationship("AgentAssignment", back_populates="outreach_records")
    outreach_agent = relationship("OutreachAgent", back_populates="outreach_records")
    agent_social_connection = relationship("AgentSocialConnection", back_populates="outreach_records")
    communication_channel = relationship("CommunicationChannel", back_populates="outreach_records")
    message_status = relationship("Status", foreign_keys=[message_status_id], overlaps="outreach_message_statuses")

    # Indexes for performance
    __table_args__ = (
        Index('ix_influencer_outreach_assigned_influencer', 'assigned_influencer_id'),
        Index('ix_influencer_outreach_agent_assignment', 'agent_assignment_id'),
        Index('ix_influencer_outreach_outreach_agent', 'outreach_agent_id'),
        Index('ix_influencer_outreach_social_connection', 'agent_social_connection_id'),
        Index('ix_influencer_outreach_communication_channel', 'communication_channel_id'),
        Index('ix_influencer_outreach_message_status', 'message_status_id'),
        Index('ix_influencer_outreach_sent_at', 'message_sent_at'),
        Index('ix_influencer_outreach_created_at', 'created_at'),
    )