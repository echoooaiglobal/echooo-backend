# app/Models/communication_channels.py

import uuid
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.Models.base import Base

class CommunicationChannel(Base):
    __tablename__ = 'communication_channels'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=False, index=True)  # Full name (e.g. "Instagram Direct Message")
    code = Column(String(20), nullable=False, index=True)   # Short code (e.g. "ig_dm")
    platform_id = Column(UUID(as_uuid=True), ForeignKey('platforms.id', ondelete='CASCADE'), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    order = Column(Integer, nullable=True, default=0)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    platform = relationship("Platform")
    outreach_records = relationship("InfluencerOutreach", back_populates="communication_channel")

    # Indexes for performance
    __table_args__ = (
        Index('ix_comm_channels_platform_active', 'platform_id', 'is_active'),
        Index('ix_comm_channels_code', 'code'),
    )