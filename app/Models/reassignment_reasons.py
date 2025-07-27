# app/Models/reassignment_reasons.py

import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, func, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.Models.base import Base

class ReassignmentReason(Base):
    __tablename__ = 'reassignment_reasons'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    code = Column(String(50), unique=True, nullable=False)  # e.g. "max_attempts_reached"
    name = Column(String(100), nullable=False)  # e.g. "Maximum Attempts Reached"
    description = Column(Text, nullable=True)  # Detailed explanation
    is_system_triggered = Column(Boolean, nullable=False, default=True)  # Can be triggered by system
    is_user_triggered = Column(Boolean, nullable=False, default=True)  # Can be triggered by user
    is_active = Column(Boolean, nullable=False, default=True)  # Can be used for new assignments
    display_order = Column(Integer, nullable=False, default=0)  # For UI ordering
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    assignment_histories = relationship("InfluencerAssignmentHistory", back_populates="reassignment_reason")

    # Indexes for performance
    __table_args__ = (
        Index('ix_reassignment_reasons_code', 'code'),
        Index('ix_reassignment_reasons_active_system', 'is_active', 'is_system_triggered'),
        Index('ix_reassignment_reasons_active_user', 'is_active', 'is_user_triggered'),
        Index('ix_reassignment_reasons_display_order', 'display_order'),
    )