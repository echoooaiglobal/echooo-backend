# app/Models/influencer_models.py
import uuid
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.Models.base import Base

class Influencer(Base):
    __tablename__ = 'influencers'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="influencer")
    social_accounts = relationship("InfluencerSocialAccount", back_populates="influencer", cascade="all, delete-orphan")
    contacts = relationship("InfluencerContact", back_populates="influencer", cascade="all, delete-orphan")

class InfluencerSocialAccount(Base):
    __tablename__ = 'influencer_social_accounts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    influencer_id = Column(UUID(as_uuid=True), ForeignKey('influencers.id', ondelete='CASCADE'), nullable=False)
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    influencer = relationship("Influencer", back_populates="social_accounts")
    platform = relationship("Platform", back_populates="social_accounts")
    category = relationship("Category", back_populates="social_accounts")
    
    # Unique constraint to prevent duplicate platform accounts per influencer
    __table_args__ = (
        UniqueConstraint('influencer_id', 'platform_id', name='uix_influencer_platform'),
    )

class InfluencerContact(Base):
    __tablename__ = 'influencer_contacts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    influencer_id = Column(UUID(as_uuid=True), ForeignKey('influencers.id', ondelete='CASCADE'), nullable=False)
    platform_specific = Column(Boolean, default=False, nullable=False)
    platform_id = Column(UUID(as_uuid=True), ForeignKey('platforms.id', ondelete='SET NULL'), nullable=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id', ondelete='SET NULL'), nullable=True)
    name = Column(String(100), nullable=True)
    contact_type = Column(String(30), nullable=False)
    contact_value = Column(String(150), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    influencer = relationship("Influencer", back_populates="contacts")
    platform = relationship("Platform")
    role = relationship("Role")