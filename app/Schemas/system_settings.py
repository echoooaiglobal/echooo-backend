# app/Schemas/system_settings.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import datetime
import uuid

class SettingsBase(BaseModel):
    setting_key: str = Field(..., min_length=1, max_length=50, description="Unique key for the setting")
    setting_value: str = Field(..., min_length=1, max_length=255, description="Value of the setting")
    setting_type: Literal['integer', 'boolean', 'string', 'time'] = Field(..., description="Type of the setting value")
    applies_to_table: Optional[str] = Field(None, max_length=50, description="Table this setting applies to")
    applies_to_field: Optional[str] = Field(None, max_length=50, description="Field this setting applies to")
    description: Optional[str] = Field(None, description="Description of what this setting does")
    platform_id: Optional[uuid.UUID] = Field(None, description="Platform this setting belongs to")

    @validator('setting_key')
    def validate_setting_key(cls, v):
        # Setting key should not contain spaces and should be lowercase with underscores
        if ' ' in v:
            raise ValueError('Setting key cannot contain spaces')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Setting key can only contain alphanumeric characters, underscores, and hyphens')
        return v.lower()

    @validator('setting_value')
    def validate_setting_value_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Setting value cannot be empty')
        return v.strip()

class SettingsCreate(SettingsBase):
    pass

class SettingsUpdate(BaseModel):
    setting_key: Optional[str] = Field(None, min_length=1, max_length=50)
    setting_value: Optional[str] = Field(None, min_length=1, max_length=255)
    setting_type: Optional[Literal['integer', 'boolean', 'string', 'time']] = None
    applies_to_table: Optional[str] = Field(None, max_length=50)
    applies_to_field: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    platform_id: Optional[uuid.UUID] = None

    @validator('setting_key')
    def validate_setting_key(cls, v):
        if v is not None:
            if ' ' in v:
                raise ValueError('Setting key cannot contain spaces')
            if not v.replace('_', '').replace('-', '').isalnum():
                raise ValueError('Setting key can only contain alphanumeric characters, underscores, and hyphens')
            return v.lower()
        return v

    @validator('setting_value')
    def validate_setting_value_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Setting value cannot be empty')
        return v.strip() if v else v

class SettingsResponse(SettingsBase):
    id: uuid.UUID
    created_by: Optional[uuid.UUID]
    created_by_type: Literal['system', 'user']
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SettingsBulkUpdateItem(BaseModel):
    id: Optional[uuid.UUID] = Field(None, description="ID for existing setting to update")
    setting_key: str = Field(..., min_length=1, max_length=50)
    setting_value: Optional[str] = Field(None, min_length=1, max_length=255)
    setting_type: Optional[Literal['integer', 'boolean', 'string', 'time']] = None
    applies_to_table: Optional[str] = Field(None, max_length=50)
    applies_to_field: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    platform_id: Optional[uuid.UUID] = None

    @validator('setting_key')
    def validate_setting_key(cls, v):
        if ' ' in v:
            raise ValueError('Setting key cannot contain spaces')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Setting key can only contain alphanumeric characters, underscores, and hyphens')
        return v.lower()

class SettingsBulkUpdate(BaseModel):
    settings: List[SettingsBulkUpdateItem] = Field(..., min_items=1, max_items=100)

class SettingsFilterResponse(BaseModel):
    total_count: int
    settings: List[SettingsResponse]
    filters_applied: dict

class SettingsImportData(BaseModel):
    settings: List[dict]
    metadata: Optional[dict] = None

class SettingsExportResponse(BaseModel):
    exported_at: datetime
    platform_id: Optional[str]
    applies_to_table: Optional[str]
    settings_count: int
    settings: List[dict]

class SettingsValidationResponse(BaseModel):
    is_unique: bool
    existing_setting_id: Optional[str]
    message: str

class SettingsSearchResponse(BaseModel):
    keys: List[str]
    total_found: int