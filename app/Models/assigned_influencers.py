# app/Models/assigned_influencers.py

import uuid
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, Enum, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.Models.base import Base

class AssignedInfluencer(Base):
    __tablename__ = 'assigned_influencers'
     
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    campaign_influencer_id = Column(UUID(as_uuid=True), ForeignKey('campaign_influencers.id', ondelete='CASCADE'), nullable=False)
    agent_assignment_id = Column(UUID(as_uuid=True), ForeignKey('agent_assignments.id', ondelete='CASCADE'), nullable=False)
    type = Column(Enum('active', 'archived', 'completed', name='assignment_type_enum'), nullable=False, default='active')
    
    status_id = Column(UUID(as_uuid=True), ForeignKey('statuses.id', ondelete='SET NULL'), nullable=False)
    attempts_made = Column(Integer, nullable=False, default=0)
    last_contacted_at = Column(DateTime(timezone=True), nullable=True)
    next_contact_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    archived_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    campaign_influencer = relationship("CampaignInfluencer", back_populates="assigned_influencers")
    agent_assignment = relationship("AgentAssignment", back_populates="assigned_influencers")
    status = relationship("Status", back_populates="assigned_influencers")
    outreach_records = relationship("InfluencerOutreach", back_populates="assigned_influencer", cascade="all, delete-orphan")
    

    # Indexes for performance
    __table_args__ = (
        Index('ix_assigned_influencers_influencer_assignment', 'campaign_influencer_id', 'agent_assignment_id'),
        Index('ix_assigned_influencers_type_status', 'type', 'status_id'),
        Index('ix_assigned_influencers_contact_times', 'last_contacted_at', 'next_contact_at'),
        Index('ix_assigned_influencers_assigned_at', 'assigned_at'),
        Index('ix_assigned_influencers_attempts', 'attempts_made'),
    )