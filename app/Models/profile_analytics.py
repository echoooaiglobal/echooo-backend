# app/Models/profile_analytics.py
import uuid
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.Models.base import Base

class ProfileAnalytics(Base):
    __tablename__ = 'profile_analytics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    social_account_id = Column(UUID(as_uuid=True), ForeignKey('social_accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    analytics = Column(JSONB, nullable=False)  # Store complete analytics object as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    social_account = relationship("SocialAccount", back_populates="profile_analytics")