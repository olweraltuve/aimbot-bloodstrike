"""
Configuration Manager
====================
Gestiona perfiles de juego, configuración dinámica y hot-reload.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from lib.utils.logger import logger

class ConfigManager:
    """Gestor centralizado de configuración"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.config_dir = Path("lib/config")
        self.profiles_path = self.config_dir / "game_profiles.json"
        self.user_config_path = self.config_dir / "user_config.json"
        
        self.profiles = {}
        self.current_profile = "default"
        self.user_settings = {}
        
        self.load_profiles()
        self.load_user_config()
    
    def load_profiles(self):
        """Carga perfiles de juego desde JSON"""
        try:
            if self.profiles_path.exists():
                with open(self.profiles_path, 'r', encoding='utf-8') as f:
                    self.profiles = json.load(f)
                logger.info(f"Loaded {len(self.profiles)} game profiles", "CONFIG")
            else:
                logger.warning("No game profiles found, using defaults", "CONFIG")
                self.create_default_profiles()
        except Exception as e:
            logger.error(f"Failed to load profiles: {e}", "CONFIG")
            self.create_default_profiles()
    
    def load_user_config(self):
        """Carga configuración del usuario"""
        try:
            if self.user_config_path.exists():
                with open(self.user_config_path, 'r', encoding='utf-8') as f:
                    self.user_settings = json.load(f)
                self.current_profile = self.user_settings.get('active_profile', 'default')
                logger.info(f"Loaded user config. Active profile: {self.current_profile}", "CONFIG")
            else:
                self.create_default_user_config()
        except Exception as e:
            logger.error(f"Failed to load user config: {e}", "CONFIG")
            self.create_default_user_config()
    
    def create_default_profiles(self):
        """Crea perfiles por defecto"""
        self.profiles = {
            "default": {
                "name": "Default",
                "detection": {"fov": 350, "confidence": 0.45},
                "movement": {"smoothing": 0.7, "deadzone_pixels": 2},
                "targeting": {"lock_threshold_pixels": 15},
                "trigger_bot": {"enabled": False}
            }
        }
        self.save_profiles()
    
    def create_default_user_config(self):
        """Crea configuración de usuario por defecto"""
        self.user_settings = {
            "active_profile": "default",
            "mouse_method": "ddxoft",
            "capture_method": "bitblt",
            "show_debug_window": True,
            "enable_performance_logging": False
        }
        self.save_user_config()
    
    def save_profiles(self):
        """Guarda perfiles en archivo"""
        try:
            with open(self.profiles_path, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, indent=2, ensure_ascii=False)
            logger.info("Profiles saved successfully", "CONFIG")
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}", "CONFIG")
    
    def save_user_config(self):
        """Guarda configuración de usuario"""
        try:
            with open(self.user_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.user_settings, f, indent=2, ensure_ascii=False)
            logger.info("User config saved successfully", "CONFIG")
        except Exception as e:
            logger.error(f"Failed to save user config: {e}", "CONFIG")
    
    def get_profile(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene configuración de un perfil"""
        profile_name = profile_name or self.current_profile
        
        if profile_name not in self.profiles:
            logger.warning(f"Profile '{profile_name}' not found, using default", "CONFIG")
            profile_name = "default"
        
        return self.profiles.get(profile_name, {})
    
    def set_active_profile(self, profile_name: str):
        """Cambia el perfil activo"""
        if profile_name in self.profiles:
            self.current_profile = profile_name
            self.user_settings['active_profile'] = profile_name
            self.save_user_config()
            logger.info(f"Active profile changed to: {profile_name}", "CONFIG")
            return True
        else:
            logger.error(f"Profile '{profile_name}' does not exist", "CONFIG")
            return False
    
    def get_value(self, *keys, default=None):
        """
        Obtiene un valor anidado de la configuración actual.
        Ejemplo: get_value('detection', 'fov') -> 350
        """
        profile = self.get_profile()
        value = profile
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set_value(self, *keys, value):
        """
        Establece un valor anidado en la configuración actual.
        Ejemplo: set_value('detection', 'fov', value=400)
        """
        if len(keys) < 1:
            return False
        
        profile = self.get_profile()
        target = profile
        
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        target[keys[-1]] = value
        self.save_profiles()
        logger.info(f"Config updated: {'.'.join(keys)} = {value}", "CONFIG")
        return True
    
    def list_profiles(self) -> list:
        """Lista todos los perfiles disponibles"""
        return list(self.profiles.keys())
    
    def get_user_setting(self, key: str, default=None):
        """Obtiene una configuración de usuario"""
        return self.user_settings.get(key, default)
    
    def set_user_setting(self, key: str, value):
        """Establece una configuración de usuario"""
        self.user_settings[key] = value
        self.save_user_config()

# Instancia global
config = ConfigManager()