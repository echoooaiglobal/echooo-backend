# app/Models/system_settings.py

import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.Models.base import Base

class Settings(Base):
    __tablename__ = 'settings'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    setting_key = Column(String(50), nullable=False, index=True)
    setting_value = Column(String(255), nullable=False)
    setting_type = Column(Enum('integer', 'boolean', 'string', 'time', name='setting_type_enum'), nullable=False)
    applies_to_table = Column(String(50), nullable=True, index=True)
    applies_to_field = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    platform_id = Column(UUID(as_uuid=True), ForeignKey('platforms.id', ondelete='SET NULL'), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_by_type = Column(Enum('system', 'user', name='created_by_type_enum'), nullable=False, default='system')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    platform = relationship("Platform", back_populates="settings")
    creator = relationship("User", foreign_keys=[created_by])

    # Indexes for performance
    __table_args__ = (
        Index('ix_settings_key_table', 'setting_key', 'applies_to_table'),
        Index('ix_settings_platform', 'platform_id'),
        Index('ix_settings_key_platform_table', 'setting_key', 'platform_id', 'applies_to_table'),
    )

    def __repr__(self):
        return f"<Settings(key='{self.setting_key}', value='{self.setting_value}', type='{self.setting_type}')>"

    @property
    def typed_value(self):
        """Return the setting value converted to its appropriate type"""
        if self.setting_type == 'integer':
            try:
                return int(self.setting_value)
            except ValueError:
                return 0
        elif self.setting_type == 'boolean':
            return str(self.setting_value).lower() in ['true', '1', 'yes', 'on']
        else:
            return self.setting_value

    @property
    def context_key(self):
        """Return a unique context key for this setting"""
        parts = [self.setting_key]
        if self.platform_id:
            parts.append(f"platform_{self.platform_id}")
        if self.applies_to_table:
            parts.append(f"table_{self.applies_to_table}")
        return "_".join(parts)

    def to_dict(self):
        """Convert the setting to a dictionary"""
        return {
            "id": str(self.id),
            "setting_key": self.setting_key,
            "setting_value": self.setting_value,
            "setting_type": self.setting_type,
            "typed_value": self.typed_value,
            "applies_to_table": self.applies_to_table,
            "applies_to_field": self.applies_to_field,
            "description": self.description,
            "platform_id": str(self.platform_id) if self.platform_id else None,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_by_type": self.created_by_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }