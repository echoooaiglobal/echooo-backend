# app/Models/statuses.py

import uuid
from sqlalchemy import Column, String, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.Models.base import Base

class Status(Base):
    __tablename__ = 'statuses'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    model = Column(String(50), nullable=False)  # Where it's used (e.g. "campaign_influencer", "outreach", "agent")
    name = Column(String(50), nullable=False)   # e.g. "discovered", "assigned_to_ai", "responded", "active", "inactive"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships - Corrected model names and relationships
    campaign_influencers = relationship("CampaignInfluencer", back_populates="status")
    outreach_message_statuses = relationship("InfluencerOutreach", foreign_keys="InfluencerOutreach.message_status_id")
    outreach_agents = relationship("OutreachAgent", back_populates="status")
    agent_assignments = relationship("AgentAssignment", back_populates="status")
    agent_social_connections = relationship("AgentSocialConnection", back_populates="status")
    automation_sessions = relationship("AutomationSession", back_populates="status")
    assigned_influencers = relationship("AssignedInfluencer", back_populates="status")

    # Indexes for performance
    __table_args__ = (
        Index('ix_statuses_model_name', 'model', 'name'),  # Existing
        Index('ix_statuses_model', 'model'),  # Add this for model filtering
        Index('ix_statuses_name', 'name'),  # Add this for name search
    )