# app/Models/influencer_list_members.py -> app/Models/campaign_list_members.py
import uuid
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DateTime, Numeric, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.Models.base import Base

class CampaignListMember(Base):
    __tablename__ = 'campaign_list_members'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    list_id = Column(UUID(as_uuid=True), ForeignKey('campaign_lists.id', ondelete='CASCADE'), nullable=False)
    # Removed influencer_id field
    social_account_id = Column(UUID(as_uuid=True), ForeignKey('social_accounts.id', ondelete='CASCADE'), nullable=False)
    status_id = Column(UUID(as_uuid=True), ForeignKey('statuses.id', ondelete='SET NULL'), nullable=False)
    platform_id = Column(UUID(as_uuid=True), ForeignKey('platforms.id', ondelete='SET NULL'), nullable=False)
    contact_attempts = Column(Integer, nullable=False, default=0)
    last_contacted_at = Column(DateTime, nullable=True)
    next_contact_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    collaboration_price = Column(Numeric(10, 2), nullable=True)
    onboarded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    list = relationship("CampaignList", back_populates="members")
    social_account = relationship("SocialAccount", back_populates="list_memberships")
    status = relationship("Status", back_populates="list_members")
    platform = relationship("Platform")
    outreach_records = relationship("InfluencerOutreach", back_populates="list_member")