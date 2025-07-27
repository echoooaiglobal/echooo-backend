# app/Models/influencers.py
import uuid
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, Text, UniqueConstraint, func, Index
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
    social_accounts = relationship("SocialAccount", back_populates="influencer", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_influencers_user_id', 'user_id'),  # Foreign key index
        Index('ix_influencers_created_at', 'created_at'),  # For sorting
    )

    def __repr__(self):
        return f"<Influencer(id={self.id}, user_id={self.user_id})>"