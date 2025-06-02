# app/Models/support_models.py
import uuid
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.Models.base import Base

class Platform(Base):
    __tablename__ = 'platforms'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, nullable=False)  # Increased size for longer platform names
    logo_url = Column(String(500), nullable=True)  # URL for platform logo
    category = Column(String(50), nullable=True)  # Platform category (e.g., "Social Media", "Video Platform")
    status = Column(String(20), nullable=False, default='active')  # Platform status (active, inactive, deprecated)
    url = Column(String(200), nullable=True)  # Platform website URL
    provider = Column(String(100), nullable=True)  # Platform provider/company name
    work_platform_id = Column(String(100), nullable=True)  # External provider identifier
    products = Column(JSONB, nullable=True)  # JSON field for platform products/features
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    social_accounts = relationship("SocialAccount", back_populates="platform")
    # Add this relationship to match the one in Agent model
    agents = relationship("Agent", back_populates="platform")

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Self-referential relationship for hierarchical categories
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    
    # Relationships
    social_accounts = relationship("SocialAccount", back_populates="category")