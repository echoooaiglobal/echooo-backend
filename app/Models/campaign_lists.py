# app/Models/campaign_lists.py

import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, func, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.Models.base import Base
    
class CampaignList(Base):
    __tablename__ = 'campaign_lists'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    message_template_id = Column(UUID(as_uuid=True), ForeignKey('message_templates.id', ondelete='SET NULL'), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=False)
    notes = Column(Text, nullable=True)
    
    # Soft delete fields
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    campaign = relationship("Campaign", back_populates="campaign_lists")
    creator = relationship("User", foreign_keys=[created_by])
    campaign_influencers = relationship("CampaignInfluencer", back_populates="campaign_list", cascade="all, delete-orphan")
    agent_assignments = relationship("AgentAssignment", back_populates="campaign_list", cascade="all, delete-orphan")
    message_template = relationship("MessageTemplate", back_populates="campaign_lists")
    deleter = relationship("User", foreign_keys=[deleted_by])

    # Performance indexes
    __table_args__ = (
        # Campaign-based queries (most common)
        Index('ix_campaign_lists_campaign_id', 'campaign_id'),
        
        # Search functionality
        Index('ix_campaign_lists_name_search', 'name'),
        
        # User-based queries
        Index('ix_campaign_lists_created_by', 'created_by'),
        
        # Timestamp-based sorting
        Index('ix_campaign_lists_created_desc', 'created_at'),
        
        # Composite index for campaign + name search
        Index('ix_campaign_lists_campaign_name', 'campaign_id', 'name'),
        
        # Message template relationship
        Index('ix_campaign_lists_template', 'message_template_id'),

        Index('ix_campaign_lists_is_deleted', 'is_deleted'),
    )

    def __repr__(self):
        return f"<CampaignList(id={self.id}, name='{self.name}', campaign_id={self.campaign_id}, is_deleted={self.is_deleted})>"

