# app/Models/oauth_models.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, func, ForeignKey, UniqueConstraint
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
    
    # Unique constraint: one OAuth account per provider per user
    __table_args__ = (
        UniqueConstraint('user_id', 'provider', name='uix_user_oauth_provider'),
    )

class AgentSocialConnection(Base):
    """
    Table for platform agents' social media connections (Instagram Business, Facebook Pages, etc.)
    This is specifically for platform agents to manage business accounts
    """
    __tablename__ = 'agent_social_connections'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    platform = Column(String(50), nullable=False)  # 'instagram', 'facebook', etc.
    platform_user_id = Column(String(255), nullable=False)  # Platform's user/account ID
    platform_username = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=True)
    profile_image_url = Column(String(500), nullable=True)
    
    # OAuth tokens for API access
    access_token = Column(Text, nullable=True)  # Encrypted
    refresh_token = Column(Text, nullable=True)  # Encrypted
    expires_at = Column(DateTime(timezone=True), nullable=True)
    scope = Column(Text, nullable=True)
    
    # Instagram Business specific fields
    instagram_business_account_id = Column(String(255), nullable=True)
    facebook_page_id = Column(String(255), nullable=True)
    facebook_page_access_token = Column(Text, nullable=True)  # Encrypted
    facebook_page_name = Column(String(255), nullable=True)
    
    # Additional metadata
    additional_data = Column(Text, nullable=True)  # JSON string for extra data
    
    # Status and type
    is_active = Column(Boolean, default=True)
    connection_type = Column(String(50), default='business_api')  # 'oauth', 'business_api'
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="agent_social_connections")
    
    # Unique constraint: one connection per platform per user per platform_user_id
    __table_args__ = (
        UniqueConstraint('user_id', 'platform', 'platform_user_id', name='uix_agent_platform_connection'),
    )