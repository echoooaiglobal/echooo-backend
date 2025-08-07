# app/Models/company_models.py
import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, func, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.Models.base import Base

class Company(Base):
    __tablename__ = 'companies'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(150), nullable=False)
    domain = Column(String(100), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    deletion_reason = Column(String(255), nullable=True)
    
    # Relationships
    users = relationship("CompanyUser", back_populates="company", cascade="all, delete-orphan")
    contacts = relationship("CompanyContact", back_populates="company", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    campaigns = relationship("Campaign", back_populates="company", cascade="all, delete-orphan")
    message_templates = relationship("MessageTemplate", back_populates="company")
    deleter = relationship("User", foreign_keys=[deleted_by])
    outreach_agents = relationship("OutreachAgent", back_populates="company")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_companies_name', 'name'),  # For company search/lookup
        Index('ix_companies_domain', 'domain'),  # For domain-based queries
        Index('ix_companies_created_by', 'created_by'),  # For creator filtering
        Index('ix_companies_created_at', 'created_at'),  # For sorting by creation date
        Index('ix_companies_is_deleted', 'is_deleted'),
        Index('ix_companies_deleted_at', 'deleted_at'),
        Index('ix_companies_created_deleted', 'created_by', 'is_deleted'),
    )

    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}', is_deleted={self.is_deleted})>"
    
class CompanyUser(Base):
    __tablename__ = 'company_users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id', ondelete='RESTRICT'), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="users")
    user = relationship("User", back_populates="company_associations")
    role = relationship("Role")
    
    # Indexes for performance
    __table_args__ = (
        UniqueConstraint('company_id', 'user_id', name='uq_company_user'),  # Existing
        Index('ix_company_users_company_id', 'company_id'),  # For company-based queries
        Index('ix_company_users_user_id', 'user_id'),  # For user-based queries
        Index('ix_company_users_role_id', 'role_id'),  # For role filtering
        Index('ix_company_users_is_primary', 'is_primary'),  # For primary user queries
        Index('ix_company_users_company_role', 'company_id', 'role_id'),  # Composite for filtering
    )

class CompanyContact(Base):
    __tablename__ = 'company_contacts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    company_user_id = Column(UUID(as_uuid=True), ForeignKey('company_users.id', ondelete='SET NULL'), nullable=True)
    role = Column(String(50), nullable=True)
    name = Column(String(100), nullable=True)
    contact_type = Column(String(30), nullable=False)
    contact_value = Column(String(150), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="contacts")
    company_user = relationship("CompanyUser", backref="contacts")

    # Indexes for performance
    __table_args__ = (
        Index('ix_company_contacts_company_id', 'company_id'),
        Index('ix_company_contacts_type_value', 'contact_type', 'contact_value'),
        Index('ix_company_contacts_is_primary', 'is_primary'),
        Index('ix_company_contacts_company_type', 'company_id', 'contact_type'),
    )


# class B2BClient(Base):
#     __tablename__ = 'b2b_clients'
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
#     company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
#     user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
#     role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id', ondelete='RESTRICT'), nullable=False)
#     is_primary = Column(Boolean, default=False, nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
#     # Relationships
#     company = relationship("Company", back_populates="users")
#     user = relationship("User", back_populates="company_associations")
#     role = relationship("Role")
    
#     # Indexes for performance
#     __table_args__ = (
#         UniqueConstraint('company_id', 'user_id', name='uq_company_user'),  # Existing
#         Index('ix_company_users_company_id', 'company_id'),  # For company-based queries
#         Index('ix_company_users_user_id', 'user_id'),  # For user-based queries
#         Index('ix_company_users_role_id', 'role_id'),  # For role filtering
#         Index('ix_company_users_is_primary', 'is_primary'),  # For primary user queries
#         Index('ix_company_users_company_role', 'company_id', 'role_id'),  # Composite for filtering
#     )