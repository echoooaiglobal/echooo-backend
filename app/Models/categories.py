# app/Models/categories.py
import uuid
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, Text, UniqueConstraint, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.Models.base import Base

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    
    # ADD SOFT DELETE FIELDS:
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Self-referential relationship for hierarchical categories
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    deleter = relationship("User", foreign_keys=[deleted_by])  # ADD THIS
    
    # Relationships
    social_accounts = relationship("SocialAccount", back_populates="category")

    # ADD indexes:
    __table_args__ = (
        Index('ix_categories_parent_id', 'parent_id'),
        Index('ix_categories_created_at', 'created_at'),
        # ADD soft delete indexes:
        Index('ix_categories_is_deleted', 'is_deleted'),
        Index('ix_categories_deleted_at', 'deleted_at'),
        Index('ix_categories_parent_deleted', 'parent_id', 'is_deleted'),
    )
    
    # ADD __repr__:
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', parent_id={self.parent_id}, is_deleted={self.is_deleted})>"