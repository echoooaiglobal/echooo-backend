# app/Models/message_templates.py - Updated version
import uuid
import enum
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text, func, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.Models.base import Base

class TemplateType(enum.Enum):
    INITIAL = "initial"
    FOLLOWUP = "followup"
 
class MessageTemplate(Base):
    __tablename__ = 'message_templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    subject = Column(String(100), nullable=True)  # Made nullable for follow-ups
    content = Column(Text, nullable=False)  # Template content with placeholders
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)  # KEEP: For direct company queries
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False)
    
    # Fields for follow-ups
    template_type = Column(String(20), nullable=False, default='initial')  # 'initial' or 'followup'
    parent_template_id = Column(UUID(as_uuid=True), ForeignKey('message_templates.id', ondelete='CASCADE'), nullable=True)  # For follow-ups
    followup_sequence = Column(Integer, nullable=True)  # 1, 2, 3... for follow-up order
    followup_delay_hours = Column(Integer, nullable=True)  # CHANGED: Hours instead of days for better precision
    
    is_global = Column(Boolean, default=False)  # Whether this template is available to all campaigns
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    company = relationship("Company", back_populates="message_templates")
    campaign = relationship("Campaign", back_populates="message_templates")
    creator = relationship("User", foreign_keys=[created_by])
    campaign_lists = relationship("CampaignList", back_populates="message_template")
    deleter = relationship("User", foreign_keys=[deleted_by])
    
    # Relationships for follow-ups
    parent_template = relationship("MessageTemplate", remote_side=[id], back_populates="followup_templates")
    followup_templates = relationship("MessageTemplate", back_populates="parent_template", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('ix_message_templates_company_id', 'company_id'),
        Index('ix_message_templates_campaign_id', 'campaign_id'),
        Index('ix_message_templates_created_by', 'created_by'),
        Index('ix_message_templates_is_global', 'is_global'),
        Index('ix_message_templates_subject', 'subject'),
        Index('ix_message_templates_company_global', 'company_id', 'is_global'),
        Index('ix_message_templates_campaign_global', 'campaign_id', 'is_global'),
        Index('ix_message_templates_created_at', 'created_at'),
        Index('ix_message_templates_is_deleted', 'is_deleted'),
        Index('ix_message_templates_deleted_at', 'deleted_at'),
        Index('ix_message_templates_company_deleted', 'company_id', 'is_deleted'),
        Index('ix_message_templates_campaign_deleted', 'campaign_id', 'is_deleted'),
        
        # Indexes for follow-ups
        Index('ix_message_templates_type', 'template_type'),
        Index('ix_message_templates_parent', 'parent_template_id'),
        Index('ix_message_templates_sequence', 'followup_sequence'),
        Index('ix_message_templates_parent_sequence', 'parent_template_id', 'followup_sequence'),
        Index('ix_message_templates_delay_hours', 'followup_delay_hours'),  # For scheduling queries
    )

    def __repr__(self):
        return f"<MessageTemplate(id={self.id}, subject='{self.subject}', type='{self.template_type}', campaign_id={self.campaign_id}, is_deleted={self.is_deleted})>"