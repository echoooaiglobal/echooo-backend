# app/Models/company_models.py
import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text, func, UniqueConstraint
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
    
    # Relationships
    users = relationship("CompanyUser", back_populates="company", cascade="all, delete-orphan")
    contacts = relationship("CompanyContact", back_populates="company", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    campaigns = relationship("Campaign", back_populates="company", cascade="all, delete-orphan")
    message_templates = relationship("MessageTemplate", back_populates="company")

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
    
    __table_args__ = (
        UniqueConstraint('company_id', 'user_id', name='uq_company_user'),
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