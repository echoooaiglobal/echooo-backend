# app/Models/oauth_accounts.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, func, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.Models.base import Base

class OAuthAccount(Base):
    """
    Table for general OAuth authentication (login/signup via social media)
    This is separate from SocialAccount which is used for influencers
    """
    __tablename__ = 'oauth_accounts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    provider = Column(String(50), nullable=False)  # 'google', 'facebook', 'instagram', etc.
    provider_id = Column(String(255), nullable=False)  # Provider's user ID
    email = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=True)
    profile_image_url = Column(String(500), nullable=True)
    access_token = Column(Text, nullable=True)  # Encrypted token
    refresh_token = Column(Text, nullable=True)  # Encrypted refresh token
    expires_at = Column(DateTime(timezone=True), nullable=True)
    scope = Column(Text, nullable=True)  # Permissions granted
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="oauth_accounts")
    
    # Indexes for performance
    __table_args__ = (
        UniqueConstraint('user_id', 'provider', name='uix_user_oauth_provider'),  # Existing
        Index('ix_oauth_accounts_user_id', 'user_id'),  # User lookup
        Index('ix_oauth_accounts_provider', 'provider'),  # Provider filtering
        Index('ix_oauth_accounts_provider_id', 'provider_id'),  # Provider ID lookup
        Index('ix_oauth_accounts_email', 'email'),  # Email lookup
        Index('ix_oauth_accounts_is_active', 'is_active'),  # Active accounts
        Index('ix_oauth_accounts_expires_at', 'expires_at'),  # Token expiration queries
        Index('ix_oauth_accounts_user_active', 'user_id', 'is_active'),  # Composite
    )