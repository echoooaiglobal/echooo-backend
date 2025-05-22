# app/Models/message_templates.py
import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.Models.base import Base

class MessageTemplate(Base):
    __tablename__ = 'message_templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=False)  # Template name
    content = Column(Text, nullable=False)  # Template content with placeholders
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False)  # Added field
    is_global = Column(Boolean, default=False)  # Whether this template is available to all campaigns
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="message_templates")
    campaign = relationship("Campaign", back_populates="message_templates")  # Added relationship
    creator = relationship("User", foreign_keys=[created_by])