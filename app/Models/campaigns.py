# app/Models/campaigns.py

import uuid
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, Numeric, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.Models.base import Base

class Campaign(Base):
    __tablename__ = 'campaigns'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(150), nullable=False)

    brand_name = Column(String(150), nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    audience_age_group = Column(String(50), nullable=True)
    budget = Column(Numeric(10, 2), nullable=True)
    currency_code = Column(String(3), nullable=True)
    
    # Status field
    status_id = Column(UUID(as_uuid=True), ForeignKey('statuses.id', ondelete='SET NULL'), nullable=True)
    
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=False)
    
    # Field to control default filters application
    default_filters = Column(Boolean, nullable=False, default=True)
    
    # Soft delete fields
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="campaigns")
    creator = relationship("User", foreign_keys=[created_by])
    deleter = relationship("User", foreign_keys=[deleted_by])  # Relationship for who deleted
    category = relationship("Category", foreign_keys=[category_id])
    status = relationship("Status", foreign_keys=[status_id])
    campaign_lists = relationship("CampaignList", back_populates="campaign", cascade="all, delete-orphan")
    message_templates = relationship("MessageTemplate", back_populates="campaign", cascade="all, delete-orphan")

    # Define indexes for better performance
    __table_args__ = (
        # Core query indexes
        Index('ix_campaigns_company_id', 'company_id'),  # CRITICAL - most queries filter by company
        Index('ix_campaigns_created_by', 'created_by'),
        Index('ix_campaigns_status_id', 'status_id'),
        Index('ix_campaigns_category_id', 'category_id'),
        
        # Date range queries
        Index('ix_campaigns_start_date', 'start_date'),
        Index('ix_campaigns_end_date', 'end_date'),
        Index('ix_campaigns_created_at', 'created_at'),
        
        # Soft delete optimization
        Index('ix_campaigns_is_deleted', 'is_deleted'),
        Index('ix_campaigns_deleted_at', 'deleted_at'),
        
        # Budget queries
        Index('ix_campaigns_budget', 'budget'),
        Index('ix_campaigns_currency_code', 'currency_code'),
        
        # Search functionality
        Index('ix_campaigns_name', 'name'),  # For campaign search
        Index('ix_campaigns_brand_name', 'brand_name'),
        
        # Composite indexes for common queries
        Index('ix_campaigns_company_status', 'company_id', 'status_id'),
        Index('ix_campaigns_company_deleted', 'company_id', 'is_deleted'),
        Index('ix_campaigns_company_created', 'company_id', 'created_at'),
        Index('ix_campaigns_status_deleted', 'status_id', 'is_deleted'),
        Index('ix_campaigns_date_range', 'start_date', 'end_date'),
    )

    # ADD __repr__ method:
    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}', company_id={self.company_id}, status_id={self.status_id})>"

    @property
    def all_list_assignments(self):
        """Get all list assignments for this campaign through campaign lists"""
        assignments = []
        for campaign_list in self.campaign_lists:
            assignments.extend(campaign_list.agent_assignments)
        return assignments