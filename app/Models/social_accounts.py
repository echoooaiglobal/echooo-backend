# app/Models/social_accounts.py
import uuid
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, Text, UniqueConstraint, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.Models.base import Base

class SocialAccount(Base):
    __tablename__ = 'social_accounts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    influencer_id = Column(UUID(as_uuid=True), ForeignKey('influencers.id', ondelete='CASCADE'), nullable=True)
    platform_id = Column(UUID(as_uuid=True), ForeignKey('platforms.id', ondelete='CASCADE'), nullable=False)
    platform_account_id = Column(String(255), nullable=False)
    account_handle = Column(String(100), nullable=False)
    full_name = Column(String(150), nullable=False)
    profile_pic_url = Column(String(255), nullable=True)
    profile_pic_url_hd = Column(String(255), nullable=True)
    account_url = Column(String(200), nullable=True)
    is_private = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_business = Column(Boolean, default=False)
    media_count = Column(Integer, nullable=True)
    followers_count = Column(Integer, nullable=True)
    following_count = Column(Integer, nullable=True)
    subscribers_count = Column(Integer, nullable=True)
    likes_count = Column(Integer, nullable=True)
    biography = Column(Text, nullable=True)
    has_highlight_reels = Column(Boolean, default=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    has_clips = Column(Boolean, default=False)
    additional_metrics = Column(JSONB, nullable=True)
    # Claimed account fields
    claimed_at = Column(DateTime, nullable=True)
    claimed_status = Column(String(50), nullable=True)  # e.g., "pending", "verified", "rejected"
    verification_method = Column(String(100), nullable=True)  # e.g., "email", "dm", "phone"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    # Soft delete fields
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    influencer = relationship("Influencer", back_populates="social_accounts", foreign_keys=[influencer_id])
    platform = relationship("Platform", back_populates="social_accounts")
    category = relationship("Category", back_populates="social_accounts")
    campaign_influencers = relationship("CampaignInfluencer", back_populates="social_account", cascade="all, delete-orphan")
    contacts = relationship("InfluencerContact", back_populates="social_account")
    profile_analytics = relationship("ProfileAnalytics", back_populates="social_account")
    deleter = relationship("User", foreign_keys=[deleted_by])

    # Indexes for performance
    __table_args__ = (
        UniqueConstraint('influencer_id', 'platform_id', name='uix_influencer_platform'),
        # Core indexes:
        Index('ix_social_accounts_influencer_id', 'influencer_id'),
        Index('ix_social_accounts_platform_id', 'platform_id'),
        Index('ix_social_accounts_platform_account_id', 'platform_account_id'),
        Index('ix_social_accounts_account_handle', 'account_handle'),
        Index('ix_social_accounts_is_verified', 'is_verified'),
        Index('ix_social_accounts_is_business', 'is_business'),
        Index('ix_social_accounts_is_private', 'is_private'),
        Index('ix_social_accounts_category_id', 'category_id'),
        Index('ix_social_accounts_claimed_status', 'claimed_status'),
        Index('ix_social_accounts_followers_count', 'followers_count'),
        Index('ix_social_accounts_created_at', 'created_at'),
        # Soft delete indexes:
        Index('ix_social_accounts_is_deleted', 'is_deleted'),
        Index('ix_social_accounts_deleted_at', 'deleted_at'),
        Index('ix_social_accounts_platform_deleted', 'platform_id', 'is_deleted'),
        # Composite indexes for common queries:
        Index('ix_social_accounts_platform_verified', 'platform_id', 'is_verified'),
        Index('ix_social_accounts_platform_business', 'platform_id', 'is_business'),
        Index('ix_social_accounts_platform_followers', 'platform_id', 'followers_count'),
    )

    def __repr__(self):
        return f"<SocialAccount(id={self.id}, handle='{self.account_handle}', platform_id={self.platform_id}, followers={self.followers_count}, is_deleted={self.is_deleted})>"
