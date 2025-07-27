# app/Models/platforms.py
import uuid
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, Text, UniqueConstraint, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.Models.base import Base

class Platform(Base):
    __tablename__ = 'platforms'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, nullable=False)
    logo_url = Column(String(500), nullable=True)
    category = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False, default='active')
    url = Column(String(200), nullable=True)
    provider = Column(String(100), nullable=True)
    work_platform_id = Column(String(100), nullable=True)
    products = Column(JSONB, nullable=True)
    
    # ADD SOFT DELETE FIELDS:
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    social_accounts = relationship("SocialAccount", back_populates="platform")
    agent_social_connections = relationship("AgentSocialConnection", back_populates="platform")
    automation_sessions = relationship("AutomationSession", back_populates="platform")
    settings = relationship("Settings", back_populates="platform")
    deleter = relationship("User", foreign_keys=[deleted_by])  # ADD THIS

    # UPDATE indexes:
    __table_args__ = (
        # Existing indexes...
        Index('ix_platforms_name', 'name'),
        Index('ix_platforms_category', 'category'),
        Index('ix_platforms_status', 'status'),
        Index('ix_platforms_provider', 'provider'),
        Index('ix_platforms_work_platform_id', 'work_platform_id'),
        Index('ix_platforms_category_status', 'category', 'status'),
        
        # ADD soft delete indexes:
        Index('ix_platforms_is_deleted', 'is_deleted'),
        Index('ix_platforms_status_deleted', 'status', 'is_deleted'),
    )
    
    # ADD __repr__:
    def __repr__(self):
        return f"<Platform(id={self.id}, name='{self.name}', status='{self.status}', is_deleted={self.is_deleted})>"