# app/Models/auth_models.py
import uuid
import enum
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.Models.base import Base

# Role-User Association Table
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
)

class UserType(enum.Enum):
    PLATFORM = "platform"
    INFLUENCER = "influencer"
    COMPANY = "b2c"
    AGENCY = "b2b"
    AGENCY_CLIENT = "b2b_client"

class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Made nullable for OAuth users
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    profile_image_url = Column(String(255), nullable=True)
    status = Column(String(20), default=UserStatus.PENDING.value, index=True)  # Added index
    user_type = Column(String(20), nullable=True, index=True)  # Added index
    email_verified = Column(Boolean, default=False, index=True)  # Added index
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # Added index
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Added index
    
    # Soft delete fields - IMPORTANT for GDPR compliance and data retention
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    deletion_reason = Column(String(255), nullable=True)  # Optional: track why user was deleted
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", foreign_keys="RefreshToken.user_id", cascade="all, delete-orphan")

    # Relationships to other domains - using back_populates to establish bidirectional relationships
    influencer = relationship("Influencer", back_populates="user", uselist=False)
    company_associations = relationship("CompanyUser", back_populates="user", cascade="all, delete-orphan")

    # OAuth accounts for login/signup via social media
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    
    # Agent social connections for platform agents to manage Instagram business accounts
    agent_social_connections = relationship("AgentSocialConnection", back_populates="user", cascade="all, delete-orphan")
    
    # Self-referential relationship for who deleted this user
    deleter = relationship("User", remote_side=[id], foreign_keys=[deleted_by])

    # Relationships for tokens/actions this user revoked (optional, for audit purposes)
    revoked_refresh_tokens = relationship("RefreshToken", foreign_keys="RefreshToken.revoked_by", overlaps="revoker")
    deleted_users = relationship("User", foreign_keys=[deleted_by], overlaps="deleter")
    # Additional indexes including soft delete optimizations
    __table_args__ = (
        Index('idx_users_status_type', 'status', 'user_type'),
        Index('idx_users_created_at_status', 'created_at', 'status'),
        Index('idx_users_is_deleted', 'is_deleted'),
        Index('idx_users_email_deleted', 'email', 'is_deleted'),
        Index('idx_users_status_deleted', 'status', 'is_deleted'),
        Index('idx_users_type_deleted', 'user_type', 'is_deleted'),

        Index('idx_users_phone_number', 'phone_number'),  # For phone lookup
        Index('idx_users_last_login', 'last_login_at'),  # For activity tracking
        Index('idx_users_deleted_at', 'deleted_at'),  # For soft delete queries
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', user_type='{self.user_type}', status='{self.status}')>"

class Role(Base):
    __tablename__ = 'roles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)  # Added index
    description = Column(String(255), nullable=True)
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"
class Permission(Base):
    __tablename__ = 'permissions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)  # Added index
    description = Column(String(255), nullable=True)
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission")

    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}')>"

class RolePermission(Base):
    __tablename__ = 'role_permissions'
    
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
    
    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="role_permissions")

class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)  # Added index
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)  # Added index
    is_revoked = Column(Boolean, default=False, index=True)  # Added index
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)  # Track when revoked
    revoked_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)  # Who revoked it
    
    # Relationships - FIXED: Specify foreign_keys explicitly to avoid ambiguity
    user = relationship("User", back_populates="refresh_tokens", foreign_keys=[user_id])
    revoker = relationship("User", foreign_keys=[revoked_by], overlaps="revoked_refresh_tokens")  # Who revoked the token
    
    # Additional indexes
    __table_args__ = (
        Index('idx_refresh_tokens_user_active', 'user_id', 'is_revoked'),
        Index('idx_refresh_tokens_expires_revoked', 'expires_at', 'is_revoked'),
        Index('idx_refresh_tokens_user_expires', 'user_id', 'expires_at'),
    )

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at}, is_revoked={self.is_revoked})>"
    
    @classmethod
    def create_token(cls, user_id, expires_in_days=7):
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        return cls(token=token, user_id=user_id, expires_at=expires_at)
    
class EmailVerificationToken(Base):
    __tablename__ = 'email_verification_tokens'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)  # Added index
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)  # Added index
    is_used = Column(Boolean, default=False, index=True)  # Added index
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="email_verification_tokens")
    
    # Additional indexes
    __table_args__ = (
        Index('idx_email_tokens_user_used', 'user_id', 'is_used'),
        Index('idx_email_tokens_expires_used', 'expires_at', 'is_used'),
    )
    
    @classmethod
    def create_token(cls, user_id: uuid.UUID, expires_in_hours: int = 24):
        """Create a new email verification token"""
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        return cls(token=token, user_id=user_id, expires_at=expires_at)
    
    def is_valid(self) -> bool:
        """Check if token is still valid"""
        return not self.is_used and self.expires_at > datetime.utcnow()