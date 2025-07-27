# app/Services/SystemSettingsService.py
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import uuid
import json
from datetime import datetime

from app.Models.system_settings import Settings
from app.Utils.dictionaries.settings import DEFAULT_SETTINGS
from app.Utils.Logger import logger

class SystemSettingsService:
    """Service layer for settings business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_setting_value(
        self,
        setting_key: str,
        platform_id: Optional[uuid.UUID] = None,
        applies_to_table: Optional[str] = None,
        default_value: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a setting value with context-aware fallback logic.
        Priority: platform + table specific > platform specific > global table specific > global
        """
        try:
            # Build query with priority order
            query = self.db.query(Settings).filter(Settings.setting_key == setting_key)
            
            # Try most specific first (platform + table)
            if platform_id and applies_to_table:
                setting = query.filter(
                    Settings.platform_id == platform_id,
                    Settings.applies_to_table == applies_to_table
                ).first()
                if setting:
                    return self._convert_value(setting.setting_value, setting.setting_type)
            
            # Try platform specific
            if platform_id:
                setting = query.filter(
                    Settings.platform_id == platform_id,
                    Settings.applies_to_table.is_(None)
                ).first()
                if setting:
                    return self._convert_value(setting.setting_value, setting.setting_type)
            
            # Try table specific (global)
            if applies_to_table:
                setting = query.filter(
                    Settings.platform_id.is_(None),
                    Settings.applies_to_table == applies_to_table
                ).first()
                if setting:
                    return self._convert_value(setting.setting_value, setting.setting_type)
            
            # Try global setting
            setting = query.filter(
                Settings.platform_id.is_(None),
                Settings.applies_to_table.is_(None)
            ).first()
            if setting:
                return self._convert_value(setting.setting_value, setting.setting_type)
            
            # Return default if provided
            return default_value
            
        except Exception as e:
            logger.error(f"Error getting setting value for {setting_key}: {str(e)}")
            return default_value
    
    def get_typed_setting(
        self,
        setting_key: str,
        expected_type: type,
        platform_id: Optional[uuid.UUID] = None,
        applies_to_table: Optional[str] = None,
        default_value: Any = None
    ) -> Any:
        """Get a setting value converted to the expected type"""
        value = self.get_setting_value(setting_key, platform_id, applies_to_table)
        
        if value is None:
            return default_value
        
        try:
            if expected_type == bool:
                return str(value).lower() in ['true', '1', 'yes', 'on']
            elif expected_type == int:
                return int(value)
            elif expected_type == float:
                return float(value)
            else:
                return str(value)
        except (ValueError, TypeError):
            logger.warning(f"Failed to convert setting {setting_key} to {expected_type.__name__}")
            return default_value
    
    def set_setting(
        self,
        setting_key: str,
        setting_value: str,
        setting_type: str,
        created_by: uuid.UUID,
        platform_id: Optional[uuid.UUID] = None,
        applies_to_table: Optional[str] = None,
        applies_to_field: Optional[str] = None,
        description: Optional[str] = None,
        overwrite_existing: bool = True
    ) -> Settings:
        """Set a setting value, creating or updating as needed"""
        try:
            # Check if setting exists
            existing = self.db.query(Settings).filter(
                Settings.setting_key == setting_key,
                Settings.platform_id == platform_id,
                Settings.applies_to_table == applies_to_table
            ).first()
            
            if existing:
                if overwrite_existing:
                    existing.setting_value = setting_value
                    existing.setting_type = setting_type
                    existing.applies_to_field = applies_to_field
                    existing.description = description
                    existing.updated_at = datetime.utcnow()
                    self.db.commit()
                    return existing
                else:
                    return existing
            else:
                # Create new setting
                new_setting = Settings(
                    setting_key=setting_key,
                    setting_value=setting_value,
                    setting_type=setting_type,
                    applies_to_table=applies_to_table,
                    applies_to_field=applies_to_field,
                    description=description,
                    platform_id=platform_id,
                    created_by=created_by,
                    created_by_type='user'
                )
                
                self.db.add(new_setting)
                self.db.commit()
                self.db.refresh(new_setting)
                return new_setting
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error setting value for {setting_key}: {str(e)}")
            raise
    
    def get_settings_group(
        self,
        platform_id: Optional[uuid.UUID] = None,
        applies_to_table: Optional[str] = None,
        setting_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get multiple settings as a dictionary"""
        try:
            query = self.db.query(Settings)
            
            if platform_id:
                query = query.filter(
                    (Settings.platform_id == platform_id) | 
                    (Settings.platform_id.is_(None))
                )
            
            if applies_to_table:
                query = query.filter(
                    (Settings.applies_to_table == applies_to_table) | 
                    (Settings.applies_to_table.is_(None))
                )
            
            if setting_keys:
                query = query.filter(Settings.setting_key.in_(setting_keys))
            
            # Order by specificity (most specific first)
            settings = query.order_by(
                Settings.platform_id.desc().nullslast(),
                Settings.applies_to_table.desc().nullslast()
            ).all()
            
            # Build result dictionary with most specific values
            result = {}
            for setting in settings:
                if setting.setting_key not in result:
                    result[setting.setting_key] = self._convert_value(
                        setting.setting_value, 
                        setting.setting_type
                    )
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting settings group: {str(e)}")
            return {}
    
    def initialize_default_settings(self, force: bool = False) -> int:
        """Initialize default system settings"""
        try:
            initialized_count = 0
            
            for default_setting in DEFAULT_SETTINGS:
                existing = self.db.query(Settings).filter(
                    Settings.setting_key == default_setting["setting_key"],
                    Settings.platform_id.is_(None),
                    Settings.applies_to_table.is_(None)
                ).first()
                
                if not existing or force:
                    if existing and force:
                        # Update existing
                        existing.setting_value = default_setting["setting_value"]
                        existing.setting_type = default_setting["setting_type"]
                        existing.description = default_setting["description"]
                        existing.updated_at = datetime.utcnow()
                    else:
                        # Create new
                        new_setting = Settings(
                            setting_key=default_setting["setting_key"],
                            setting_value=default_setting["setting_value"],
                            setting_type=default_setting["setting_type"],
                            description=default_setting["description"],
                            created_by_type=default_setting["created_by_type"]
                        )
                        self.db.add(new_setting)
                    
                    initialized_count += 1
            
            self.db.commit()
            logger.info(f"Initialized {initialized_count} default settings")
            return initialized_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error initializing default settings: {str(e)}")
            raise
    
    def backup_settings(
        self,
        platform_id: Optional[uuid.UUID] = None,
        applies_to_table: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a backup of settings"""
        try:
            query = self.db.query(Settings)
            
            if platform_id:
                query = query.filter(Settings.platform_id == platform_id)
            if applies_to_table:
                query = query.filter(Settings.applies_to_table == applies_to_table)
            
            settings = query.all()
            
            backup_data = {
                "backup_timestamp": datetime.utcnow().isoformat(),
                "platform_id": str(platform_id) if platform_id else None,
                "applies_to_table": applies_to_table,
                "settings_count": len(settings),
                "settings": [
                    {
                        "id": str(setting.id),
                        "setting_key": setting.setting_key,
                        "setting_value": setting.setting_value,
                        "setting_type": setting.setting_type,
                        "applies_to_table": setting.applies_to_table,
                        "applies_to_field": setting.applies_to_field,
                        "description": setting.description,
                        "platform_id": str(setting.platform_id) if setting.platform_id else None,
                        "created_by": str(setting.created_by) if setting.created_by else None,
                        "created_by_type": setting.created_by_type,
                        "created_at": setting.created_at.isoformat(),
                        "updated_at": setting.updated_at.isoformat()
                    }
                    for setting in settings
                ]
            }
            
            return backup_data
            
        except Exception as e:
            logger.error(f"Error creating settings backup: {str(e)}")
            raise
    
    def restore_settings(
        self,
        backup_data: Dict[str, Any],
        restored_by: uuid.UUID,
        overwrite_existing: bool = False
    ) -> Dict[str, int]:
        """Restore settings from backup"""
        try:
            restored_count = 0
            skipped_count = 0
            error_count = 0
            
            for setting_data in backup_data.get("settings", []):
                try:
                    platform_id = None
                    if setting_data.get("platform_id"):
                        platform_id = uuid.UUID(setting_data["platform_id"])
                    
                    existing = self.db.query(Settings).filter(
                        Settings.setting_key == setting_data["setting_key"],
                        Settings.platform_id == platform_id,
                        Settings.applies_to_table == setting_data.get("applies_to_table")
                    ).first()
                    
                    if existing and not overwrite_existing:
                        skipped_count += 1
                        continue
                    
                    if existing and overwrite_existing:
                        # Update existing
                        existing.setting_value = setting_data["setting_value"]
                        existing.setting_type = setting_data["setting_type"]
                        existing.applies_to_field = setting_data.get("applies_to_field")
                        existing.description = setting_data.get("description")
                        existing.updated_at = datetime.utcnow()
                    else:
                        # Create new
                        new_setting = Settings(
                            setting_key=setting_data["setting_key"],
                            setting_value=setting_data["setting_value"],
                            setting_type=setting_data["setting_type"],
                            applies_to_table=setting_data.get("applies_to_table"),
                            applies_to_field=setting_data.get("applies_to_field"),
                            description=setting_data.get("description"),
                            platform_id=platform_id,
                            created_by=restored_by,
                            created_by_type='user'
                        )
                        self.db.add(new_setting)
                    
                    restored_count += 1
                    
                except Exception as setting_error:
                    logger.error(f"Error restoring setting {setting_data.get('setting_key')}: {str(setting_error)}")
                    error_count += 1
                    continue
            
            self.db.commit()
            
            return {
                "restored_count": restored_count,
                "skipped_count": skipped_count,
                "error_count": error_count
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error restoring settings: {str(e)}")
            raise
    
    def _convert_value(self, value: str, setting_type: str) -> Any:
        """Convert string value to appropriate type"""
        try:
            if setting_type == 'integer':
                return int(value)
            elif setting_type == 'boolean':
                return str(value).lower() in ['true', '1', 'yes', 'on']
            else:
                return value
        except (ValueError, TypeError):
            logger.warning(f"Failed to convert value '{value}' to type '{setting_type}'")
            return value