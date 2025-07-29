# app/Models/campaign_influencers.py

import uuid
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DateTime, Numeric, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.Models.base import Base

class CampaignInfluencer(Base): 
    __tablename__ = 'campaign_influencers'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    campaign_list_id = Column(UUID(as_uuid=True), ForeignKey('campaign_lists.id', ondelete='CASCADE'), nullable=False)
    social_account_id = Column(UUID(as_uuid=True), ForeignKey('social_accounts.id', ondelete='CASCADE'), nullable=False)
    status_id = Column(UUID(as_uuid=True), ForeignKey('statuses.id', ondelete='SET NULL'), nullable=False)
    is_assigned_to_agent = Column(Boolean, nullable=False, default=False)
    total_contact_attempts = Column(Integer, nullable=False, default=0)
    collaboration_price = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), nullable=True, default='USD')  # NEW: ISO currency code
    # is_ready_for_onboarding = Column(Boolean, nullable=False, default=False)
    onboarded_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    campaign_list = relationship("CampaignList", back_populates="campaign_influencers")
    social_account = relationship("SocialAccount", back_populates="campaign_influencers")
    status = relationship("Status", back_populates="campaign_influencers")
    assigned_influencers = relationship("AssignedInfluencer", back_populates="campaign_influencer", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('ix_campaign_influencers_list_status', 'campaign_list_id', 'status_id'),
        Index('ix_campaign_influencers_social_account', 'social_account_id'),
        Index('ix_campaign_influencers_onboarding', 'is_ready_for_onboarding', 'onboarded_at'),
        Index('ix_campaign_influencers_contact_attempts', 'total_contact_attempts'),
        Index('ix_campaign_influencers_price_range', 'collaboration_price'),
        Index('ix_campaign_influencers_created_desc', 'created_at'),
        Index('ix_campaign_influencers_search_composite', 'campaign_list_id', 'status_id', 'is_ready_for_onboarding'),
        
        # NEW: Currency-related indexes
        Index('ix_campaign_influencers_price_currency', 'collaboration_price', 'currency'),
        Index('ix_campaign_influencers_currency', 'currency'),
    )

    def __repr__(self):
        return f"<CampaignInfluencer(id={self.id}, price={self.collaboration_price} {self.currency})>"