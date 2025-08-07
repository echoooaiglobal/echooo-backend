# routes/api/v0/system_settings.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.Http.Controllers.SystemSettingsController import SystemSettingsController
from app.Models.auth_models import User
from app.Schemas.system_settings import (
    SettingsCreate, SettingsUpdate, SettingsResponse, 
    SettingsBulkUpdate
)
from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission
)
from config.database import get_db

router = APIRouter(prefix="/system-settings", tags=["System Settings"])

@router.get("/", response_model=List[SettingsResponse])
async def get_all_settings(
    platform_id: Optional[uuid.UUID] = Query(None, description="Filter by platform ID"),
    setting_key: Optional[str] = Query(None, description="Filter by setting key"),
    applies_to_table: Optional[str] = Query(None, description="Filter by table name"),
    setting_type: Optional[str] = Query(None, description="Filter by setting type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all settings with optional filtering"""
    return await SystemSettingsController.get_all_settings(
        db, platform_id, setting_key, applies_to_table, setting_type, skip, limit
    )

@router.get("/{setting_id}", response_model=SettingsResponse)
async def get_setting(
    setting_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific setting by ID"""
    return await SystemSettingsController.get_setting(setting_id, db)

@router.get("/key/{setting_key}", response_model=SettingsResponse)
async def get_setting_by_key(
    setting_key: str,
    platform_id: Optional[uuid.UUID] = Query(None, description="Platform ID for context"),
    applies_to_table: Optional[str] = Query(None, description="Table context"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a setting by key with optional context filters"""
    return await SystemSettingsController.get_setting_by_key(
        setting_key, db, platform_id, applies_to_table
    )

@router.get("/platform/{platform_id}", response_model=List[SettingsResponse])
async def get_platform_settings(
    platform_id: uuid.UUID,
    applies_to_table: Optional[str] = Query(None, description="Filter by table name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all settings for a specific platform"""
    return await SystemSettingsController.get_platform_settings(platform_id, db, applies_to_table)

@router.get("/table/{table_name}", response_model=List[SettingsResponse])
async def get_table_settings(
    table_name: str,
    platform_id: Optional[uuid.UUID] = Query(None, description="Filter by platform ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all settings that apply to a specific table"""
    return await SystemSettingsController.get_table_settings(table_name, db, platform_id)

@router.post("/", response_model=SettingsResponse)
async def create_setting(
    setting_data: SettingsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(["settings:create"]))
):
    """Create a new setting"""
    return await SystemSettingsController.create_setting(setting_data, current_user.id, db)

@router.put("/{setting_id}", response_model=SettingsResponse)
async def update_setting(
    setting_id: uuid.UUID,
    setting_data: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(["settings:update"]))
):
    """Update a specific setting"""
    return await SystemSettingsController.update_setting(setting_id, setting_data, current_user.id, db)

@router.delete("/{setting_id}")
async def delete_setting(
    setting_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(["settings:delete"]))
):
    """Delete a specific setting"""
    return await SystemSettingsController.delete_setting(setting_id, db)

@router.post("/bulk-update", response_model=List[SettingsResponse])
async def bulk_update_settings(
    bulk_data: SettingsBulkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(["settings:bulk_update"]))
):
    """Bulk update multiple settings"""
    return await SystemSettingsController.bulk_update_settings(bulk_data, current_user.id, db)

@router.get("/search/keys", response_model=List[str])
async def search_setting_keys(
    query: str = Query(..., min_length=1, description="Search query for setting keys"),
    platform_id: Optional[uuid.UUID] = Query(None, description="Filter by platform ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Search for setting keys that match a query"""
    return await SystemSettingsController.search_setting_keys(query, db, platform_id, limit)

@router.get("/validate/key/{setting_key}")
async def validate_setting_key(
    setting_key: str,
    platform_id: Optional[uuid.UUID] = Query(None, description="Platform ID for context"),
    applies_to_table: Optional[str] = Query(None, description="Table context"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Validate if a setting key is unique within the given context"""
    return await SystemSettingsController.validate_setting_key(
        setting_key, db, platform_id, applies_to_table
    )

@router.post("/reset/defaults")
async def reset_to_defaults(
    platform_id: Optional[uuid.UUID] = Query(None, description="Platform ID to reset"),
    table_name: Optional[str] = Query(None, description="Specific table to reset"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role(["system_admin", "platform_admin"]))
):
    """Reset settings to default values"""
    return await SystemSettingsController.reset_to_defaults(platform_id, table_name, current_user.id, db)

@router.get("/export/json")
async def export_settings_json(
    platform_id: Optional[uuid.UUID] = Query(None, description="Filter by platform ID"),
    applies_to_table: Optional[str] = Query(None, description="Filter by table name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(["settings:export"]))
):
    """Export settings as JSON"""
    return await SystemSettingsController.export_settings(db, platform_id, applies_to_table, format="json")

@router.post("/import/json")
async def import_settings_json(
    settings_data: dict,
    overwrite_existing: bool = Query(False, description="Whether to overwrite existing settings"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(["settings:import"]))
):
    """Import settings from JSON"""
    return await SystemSettingsController.import_settings(
        settings_data, current_user.id, db, overwrite_existing
    )