# app/Http/Controllers/SystemSettingsController.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from app.Models.system_settings import Settings
from app.Schemas.system_settings import (
    SettingsCreate, SettingsUpdate, SettingsResponse, 
    SettingsBulkUpdate
)
from app.Utils.Logger import logger

class SystemSettingsController:
    
    @staticmethod
    async def get_all_settings(
        db: Session,
        platform_id: Optional[uuid.UUID] = None,
        setting_key: Optional[str] = None,
        applies_to_table: Optional[str] = None,
        setting_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SettingsResponse]:
        """Get all settings with optional filtering"""
        try:
            query = db.query(Settings)
            
            # Apply filters
            if platform_id:
                query = query.filter(Settings.platform_id == platform_id)
            if setting_key:
                query = query.filter(Settings.setting_key.ilike(f"%{setting_key}%"))
            if applies_to_table:
                query = query.filter(Settings.applies_to_table == applies_to_table)
            if setting_type:
                query = query.filter(Settings.setting_type == setting_type)
            
            # Apply pagination and ordering
            settings = query.order_by(Settings.setting_key).offset(skip).limit(limit).all()
            
            return [SettingsResponse.from_orm(setting) for setting in settings]
            
        except Exception as e:
            logger.error(f"Error fetching settings: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching settings"
            )
    
    @staticmethod
    async def get_setting(setting_id: uuid.UUID, db: Session) -> SettingsResponse:
        """Get a specific setting by ID"""
        try:
            setting = db.query(Settings).filter(Settings.id == setting_id).first()
            
            if not setting:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Setting not found"
                )
            
            return SettingsResponse.from_orm(setting)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching setting {setting_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching setting"
            )
    
    @staticmethod
    async def get_setting_by_key(
        setting_key: str,
        db: Session,
        platform_id: Optional[uuid.UUID] = None,
        applies_to_table: Optional[str] = None
    ) -> SettingsResponse:
        """Get a setting by key with optional context filters"""
        try:
            query = db.query(Settings).filter(Settings.setting_key == setting_key)
            
            # Apply context filters
            if platform_id:
                query = query.filter(Settings.platform_id == platform_id)
            if applies_to_table:
                query = query.filter(Settings.applies_to_table == applies_to_table)
            
            # Order by specificity (platform-specific first, then general)
            query = query.order_by(
                Settings.platform_id.desc().nullslast(),
                Settings.applies_to_table.desc().nullslast()
            )
            
            setting = query.first()
            
            if not setting:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Setting with key '{setting_key}' not found"
                )
            
            return SettingsResponse.from_orm(setting)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching setting by key {setting_key}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching setting"
            )
    
    @staticmethod
    async def get_platform_settings(
        platform_id: uuid.UUID,
        db: Session,
        applies_to_table: Optional[str] = None
    ) -> List[SettingsResponse]:
        """Get all settings for a specific platform"""
        try:
            query = db.query(Settings).filter(
                or_(
                    Settings.platform_id == platform_id,
                    Settings.platform_id.is_(None)  # Include global settings
                )
            )
            
            if applies_to_table:
                query = query.filter(Settings.applies_to_table == applies_to_table)
            
            settings = query.order_by(
                Settings.platform_id.desc().nullslast(),
                Settings.setting_key
            ).all()
            
            return [SettingsResponse.from_orm(setting) for setting in settings]
            
        except Exception as e:
            logger.error(f"Error fetching platform settings: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching platform settings"
            )
    
    @staticmethod
    async def get_table_settings(
        table_name: str,
        db: Session,
        platform_id: Optional[uuid.UUID] = None
    ) -> List[SettingsResponse]:
        """Get all settings that apply to a specific table"""
        try:
            query = db.query(Settings).filter(
                or_(
                    Settings.applies_to_table == table_name,
                    Settings.applies_to_table.is_(None)  # Include global settings
                )
            )
            
            if platform_id:
                query = query.filter(
                    or_(
                        Settings.platform_id == platform_id,
                        Settings.platform_id.is_(None)
                    )
                )
            
            settings = query.order_by(
                Settings.applies_to_table.desc().nullslast(),
                Settings.platform_id.desc().nullslast(),
                Settings.setting_key
            ).all()
            
            return [SettingsResponse.from_orm(setting) for setting in settings]
            
        except Exception as e:
            logger.error(f"Error fetching table settings: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching table settings"
            )
    
    @staticmethod
    async def create_setting(
        setting_data: SettingsCreate,
        created_by: uuid.UUID,
        db: Session
    ) -> SettingsResponse:
        """Create a new setting"""
        try:
            # Check for duplicate key in same context
            existing = db.query(Settings).filter(
                and_(
                    Settings.setting_key == setting_data.setting_key,
                    Settings.platform_id == setting_data.platform_id,
                    Settings.applies_to_table == setting_data.applies_to_table
                )
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Setting with this key already exists in the same context"
                )
            
            # Validate setting value based on type
            SystemSettingsController._validate_setting_value(
                setting_data.setting_value, 
                setting_data.setting_type
            )
            
            # Create new setting
            new_setting = Settings(
                setting_key=setting_data.setting_key,
                setting_value=setting_data.setting_value,
                setting_type=setting_data.setting_type,
                applies_to_table=setting_data.applies_to_table,
                applies_to_field=setting_data.applies_to_field,
                description=setting_data.description,
                platform_id=setting_data.platform_id,
                created_by=created_by,
                created_by_type='user'
            )
            
            db.add(new_setting)
            db.commit()
            db.refresh(new_setting)
            
            logger.info(f"Setting created: {setting_data.setting_key}")
            return SettingsResponse.from_orm(new_setting)
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating setting: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating setting"
            )
    
    @staticmethod
    async def update_setting(
        setting_id: uuid.UUID,
        setting_data: SettingsUpdate,
        updated_by: uuid.UUID,
        db: Session
    ) -> SettingsResponse:
        """Update a specific setting"""
        try:
            setting = db.query(Settings).filter(Settings.id == setting_id).first()
            
            if not setting:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Setting not found"
                )
            
            # Update fields if provided
            update_data = setting_data.dict(exclude_unset=True)
            
            # Validate setting value if being updated
            if 'setting_value' in update_data:
                setting_type = update_data.get('setting_type', setting.setting_type)
                SystemSettingsController._validate_setting_value(
                    update_data['setting_value'], 
                    setting_type
                )
            
            # Check for duplicate key if key is being changed
            if 'setting_key' in update_data and update_data['setting_key'] != setting.setting_key:
                existing = db.query(Settings).filter(
                    and_(
                        Settings.setting_key == update_data['setting_key'],
                        Settings.platform_id == setting.platform_id,
                        Settings.applies_to_table == setting.applies_to_table,
                        Settings.id != setting_id
                    )
                ).first()
                
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Setting with this key already exists in the same context"
                    )
            
            # Update the setting
            for field, value in update_data.items():
                setattr(setting, field, value)
            
            setting.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(setting)
            
            logger.info(f"Setting updated: {setting.setting_key}")
            return SettingsResponse.from_orm(setting)
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating setting {setting_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating setting"
            )
    
    @staticmethod
    async def delete_setting(setting_id: uuid.UUID, db: Session) -> Dict[str, str]:
        """Delete a specific setting"""
        try:
            setting = db.query(Settings).filter(Settings.id == setting_id).first()
            
            if not setting:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Setting not found"
                )
            
            setting_key = setting.setting_key
            db.delete(setting)
            db.commit()
            
            logger.info(f"Setting deleted: {setting_key}")
            return {"message": f"Setting '{setting_key}' deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting setting {setting_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting setting"
            )
    
    @staticmethod
    async def bulk_update_settings(
        bulk_data: SettingsBulkUpdate,
        updated_by: uuid.UUID,
        db: Session
    ) -> List[SettingsResponse]:
        """Bulk update multiple settings"""
        try:
            updated_settings = []
            
            for setting_update in bulk_data.settings:
                if setting_update.id:
                    # Update existing setting
                    setting = db.query(Settings).filter(Settings.id == setting_update.id).first()
                    if setting:
                        # Validate setting value
                        if setting_update.setting_value is not None:
                            setting_type = setting_update.setting_type or setting.setting_type
                            SystemSettingsController._validate_setting_value(
                                setting_update.setting_value, 
                                setting_type
                            )
                        
                        # Update fields
                        update_data = setting_update.dict(exclude_unset=True, exclude={'id'})
                        for field, value in update_data.items():
                            if value is not None:
                                setattr(setting, field, value)
                        
                        setting.updated_at = datetime.utcnow()
                        updated_settings.append(setting)
                
                else:
                    # Create new setting
                    SystemSettingsController._validate_setting_value(
                        setting_update.setting_value, 
                        setting_update.setting_type
                    )
                    
                    new_setting = Settings(
                        setting_key=setting_update.setting_key,
                        setting_value=setting_update.setting_value,
                        setting_type=setting_update.setting_type,
                        applies_to_table=setting_update.applies_to_table,
                        applies_to_field=setting_update.applies_to_field,
                        description=setting_update.description,
                        platform_id=setting_update.platform_id,
                        created_by=updated_by,
                        created_by_type='user'
                    )
                    
                    db.add(new_setting)
                    updated_settings.append(new_setting)
            
            db.commit()
            
            # Refresh all settings
            for setting in updated_settings:
                db.refresh(setting)
            
            logger.info(f"Bulk updated {len(updated_settings)} settings")
            return [SettingsResponse.from_orm(setting) for setting in updated_settings]
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in bulk update: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error in bulk update operation"
            )
    
    @staticmethod
    async def search_setting_keys(
        query: str,
        db: Session,
        platform_id: Optional[uuid.UUID] = None,
        limit: int = 50
    ) -> List[str]:
        """Search for setting keys that match a query"""
        try:
            query_filter = db.query(Settings.setting_key).filter(
                Settings.setting_key.ilike(f"%{query}%")
            )
            
            if platform_id:
                query_filter = query_filter.filter(
                    or_(
                        Settings.platform_id == platform_id,
                        Settings.platform_id.is_(None)
                    )
                )
            
            keys = query_filter.distinct().limit(limit).all()
            return [key[0] for key in keys]
            
        except Exception as e:
            logger.error(f"Error searching setting keys: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error searching setting keys"
            )
    
    @staticmethod
    async def validate_setting_key(
        setting_key: str,
        db: Session,
        platform_id: Optional[uuid.UUID] = None,
        applies_to_table: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate if a setting key is unique within the given context"""
        try:
            existing = db.query(Settings).filter(
                and_(
                    Settings.setting_key == setting_key,
                    Settings.platform_id == platform_id,
                    Settings.applies_to_table == applies_to_table
                )
            ).first()
            
            return {
                "is_unique": existing is None,
                "existing_setting_id": str(existing.id) if existing else None,
                "message": "Setting key is unique" if existing is None else "Setting key already exists in this context"
            }
            
        except Exception as e:
            logger.error(f"Error validating setting key: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error validating setting key"
            )
    
    @staticmethod
    async def reset_to_defaults(
        platform_id: Optional[uuid.UUID],
        table_name: Optional[str],
        db: Session
    ) -> Dict[str, Any]:
        """Reset settings to default values"""
        try:
            # This would typically load default settings from a configuration file
            # For now, we'll just delete non-system settings
            query = db.query(Settings).filter(Settings.created_by_type == 'user')
            
            if platform_id:
                query = query.filter(Settings.platform_id == platform_id)
            if table_name:
                query = query.filter(Settings.applies_to_table == table_name)
            
            deleted_count = query.count()
            query.delete(synchronize_session=False)
            db.commit()
            
            logger.info(f"Reset {deleted_count} settings to defaults")
            return {
                "message": f"Reset {deleted_count} settings to defaults",
                "deleted_count": deleted_count
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error resetting settings: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error resetting settings"
            )
    
    @staticmethod
    async def export_settings(
        db: Session,
        platform_id: Optional[uuid.UUID] = None,
        applies_to_table: Optional[str] = None,
        export_format: str = "json"
    ) -> Dict[str, Any]:
        """Export settings as JSON"""
        # TODO: Implement support for other export formats besides JSON
        _ = export_format  # Currently only JSON is supported
        try:
            query = db.query(Settings)
            
            if platform_id:
                query = query.filter(Settings.platform_id == platform_id)
            if applies_to_table:
                query = query.filter(Settings.applies_to_table == applies_to_table)
            
            settings = query.all()
            
            export_data = {
                "exported_at": datetime.utcnow().isoformat(),
                "platform_id": str(platform_id) if platform_id else None,
                "applies_to_table": applies_to_table,
                "settings": [
                    {
                        "setting_key": setting.setting_key,
                        "setting_value": setting.setting_value,
                        "setting_type": setting.setting_type,
                        "applies_to_table": setting.applies_to_table,
                        "applies_to_field": setting.applies_to_field,
                        "description": setting.description,
                        "platform_id": str(setting.platform_id) if setting.platform_id else None
                    }
                    for setting in settings
                ]
            }
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting settings: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error exporting settings"
            )
    
    @staticmethod
    async def import_settings(
        settings_data: Dict[str, Any],
        imported_by: uuid.UUID,
        db: Session,
        overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """Import settings from JSON"""
        try:
            imported_count = 0
            skipped_count = 0
            error_count = 0
            
            for setting_data in settings_data.get("settings", []):
                try:
                    # Check if setting already exists
                    platform_id = uuid.UUID(setting_data["platform_id"]) if setting_data.get("platform_id") else None
                    
                    existing = db.query(Settings).filter(
                        and_(
                            Settings.setting_key == setting_data["setting_key"],
                            Settings.platform_id == platform_id,
                            Settings.applies_to_table == setting_data.get("applies_to_table")
                        )
                    ).first()
                    
                    if existing and not overwrite_existing:
                        skipped_count += 1
                        continue
                    
                    # Validate setting value
                    SystemSettingsController._validate_setting_value(
                        setting_data["setting_value"], 
                        setting_data["setting_type"]
                    )
                    
                    if existing and overwrite_existing:
                        # Update existing setting
                        existing.setting_value = setting_data["setting_value"]
                        existing.setting_type = setting_data["setting_type"]
                        existing.applies_to_field = setting_data.get("applies_to_field")
                        existing.description = setting_data.get("description")
                        existing.updated_at = datetime.utcnow()
                    else:
                        # Create new setting
                        new_setting = Settings(
                            setting_key=setting_data["setting_key"],
                            setting_value=setting_data["setting_value"],
                            setting_type=setting_data["setting_type"],
                            applies_to_table=setting_data.get("applies_to_table"),
                            applies_to_field=setting_data.get("applies_to_field"),
                            description=setting_data.get("description"),
                            platform_id=platform_id,
                            created_by=imported_by,
                            created_by_type='user'
                        )
                        db.add(new_setting)
                    
                    imported_count += 1
                    
                except Exception as setting_error:
                    logger.error(f"Error importing setting {setting_data.get('setting_key')}: {str(setting_error)}")
                    error_count += 1
                    continue
            
            db.commit()
            
            logger.info(f"Import completed: {imported_count} imported, {skipped_count} skipped, {error_count} errors")
            return {
                "message": "Settings import completed",
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "error_count": error_count
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error importing settings: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error importing settings"
            )
    
    @staticmethod
    def _validate_setting_value(value: str, setting_type: str) -> None:
        """Validate setting value based on its type"""
        try:
            if setting_type == 'integer':
                int(value)
            elif setting_type == 'boolean':
                if value.lower() not in ['true', 'false', '1', '0', 'yes', 'no']:
                    raise ValueError("Invalid boolean value")
            elif setting_type == 'time':
                # Basic time format validation (HH:MM or HH:MM:SS)
                import re
                if not re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', value):
                    raise ValueError("Invalid time format")
            # 'string' type doesn't need validation
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid value for {setting_type}: {str(e)}"
            )