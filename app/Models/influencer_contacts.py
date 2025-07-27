# app/Models/influencer_contacts.py
import uuid
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, Text, UniqueConstraint, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.Models.base import Base

class InfluencerContact(Base):
    __tablename__ = 'influencer_contacts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    social_account_id = Column(UUID(as_uuid=True), ForeignKey('social_accounts.id', ondelete='CASCADE'), nullable=False)
    platform_specific = Column(Boolean, default=False, nullable=False)
    platform_id = Column(UUID(as_uuid=True), ForeignKey('platforms.id', ondelete='SET NULL'), nullable=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id', ondelete='SET NULL'), nullable=True)
    name = Column(String(100), nullable=True)
    contact_type = Column(String(30), nullable=False)
    contact_value = Column(String(150), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    
    # ADD SOFT DELETE FIELDS HERE (before timestamps):
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    social_account = relationship("SocialAccount", back_populates="contacts")
    platform = relationship("Platform")
    role = relationship("Role")
    deleter = relationship("User", foreign_keys=[deleted_by])  # ADD THIS

    # UPDATE indexes:
    __table_args__ = (
        # Existing indexes...
        Index('ix_influencer_contacts_social_account', 'social_account_id'),
        Index('ix_influencer_contacts_platform', 'platform_id'),
        Index('ix_influencer_contacts_contact_type', 'contact_type'),
        Index('ix_influencer_contacts_is_primary', 'is_primary'),
        Index('ix_influencer_contacts_social_type', 'social_account_id', 'contact_type'),
        Index('ix_influencer_contacts_platform_type', 'platform_id', 'contact_type'),
        Index('ix_influencer_contacts_created_at', 'created_at'),
        
        # ADD soft delete indexes:
        Index('ix_influencer_contacts_is_deleted', 'is_deleted'),
        Index('ix_influencer_contacts_deleted_at', 'deleted_at'),
        Index('ix_influencer_contacts_social_deleted', 'social_account_id', 'is_deleted'),
    )
    
    # ADD __repr__:
    def __repr__(self):
        return f"<InfluencerContact(id={self.id}, contact_type='{self.contact_type}', contact_value='{self.contact_value}', social_account_id={self.social_account_id}, is_deleted={self.is_deleted})>"