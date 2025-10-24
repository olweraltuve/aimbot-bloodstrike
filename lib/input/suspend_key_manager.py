"""
Suspend Key Manager
==================
Gestiona una tecla de suspensión temporal del aimbot.
Mientras se mantiene presionada, el aimbot no moverá el mouse.
"""

import json
import threading
from pathlib import Path
from typing import Optional
from pynput import keyboard
from lib.utils.logger import logger
from lib.config.config_manager import config

class SuspendKeyManager:
    """Gestor de tecla de suspensión del aimbot"""
    
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
        self.suspended = False
        self.suspend_key = None
        self.listener = None
        self.lock = threading.Lock()
        
        # Cargar o solicitar tecla de suspensión
        self._load_or_request_suspend_key()
    
    def _load_or_request_suspend_key(self):
        """Carga la tecla desde config o la solicita al usuario"""
        # Intentar cargar desde configuración
        saved_key = config.get_user_setting('suspend_key', None)
        
        if saved_key:
            self.suspend_key = self._parse_key_string(saved_key)
            logger.info(f"Suspend key loaded: {saved_key}", "SUSPEND")
        else:
            # Solicitar al usuario
            self._request_suspend_key()
    
    def _request_suspend_key(self):
        """Solicita al usuario que ingrese una tecla de suspensión"""
        from termcolor import colored
        
        print("\n" + "="*60)
        print(colored("SUSPEND KEY CONFIGURATION", "cyan", attrs=['bold']))
        print("="*60)
        print(colored("\nThis key will TEMPORARILY SUSPEND the aimbot while held.", "yellow"))
        print(colored("When you release it, the aimbot will continue working.", "yellow"))
        print(colored("\nRecommended keys: Shift, Ctrl, Alt, CapsLock", "cyan"))
        print(colored("\nPress the key you want to use as suspend key...", "green"))
        
        selected_key = None
        
        def on_press(key):
            nonlocal selected_key
            selected_key = key
            return False  # Stop listener
        
        # Escuchar la siguiente tecla presionada
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
        
        if selected_key:
            # Guardar la tecla
            key_string = self._key_to_string(selected_key)
            self.suspend_key = selected_key
            config.set_user_setting('suspend_key', key_string)
            
            print(colored(f"\n✅ Suspend key set to: {key_string}", "green"))
            print(colored(f"Hold '{key_string}' to temporarily suspend aimbot movements.", "yellow"))
            print("="*60 + "\n")
            
            logger.info(f"Suspend key configured: {key_string}", "SUSPEND")
        else:
            logger.warning("No suspend key configured", "SUSPEND")
    
    def _key_to_string(self, key) -> str:
        """Convierte un objeto Key a string"""
        try:
            # Teclas especiales
            if hasattr(key, 'name'):
                return key.name
            # Teclas alfanuméricas
            elif hasattr(key, 'char'):
                return key.char
            else:
                return str(key)
        except:
            return str(key)
    
    def _parse_key_string(self, key_string: str):
        """Convierte un string a objeto Key"""
        try:
            # Intentar como tecla especial
            if hasattr(keyboard.Key, key_string):
                return getattr(keyboard.Key, key_string)
            # Intentar como carácter
            elif len(key_string) == 1:
                return keyboard.KeyCode.from_char(key_string)
            else:
                # Fallback
                return keyboard.KeyCode.from_char(key_string[0])
        except Exception as e:
            logger.error(f"Failed to parse key string '{key_string}': {e}", "SUSPEND")
            return None
    
    def start_monitoring(self):
        """Inicia el monitoreo de la tecla de suspensión"""
        if self.suspend_key is None:
            logger.warning("No suspend key configured, monitoring disabled", "SUSPEND")
            return False
        
        if self.listener is not None:
            logger.warning("Suspend key monitoring already active", "SUSPEND")
            return True
        
        # Crear listener
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
        
        key_name = self._key_to_string(self.suspend_key)
        logger.info(f"Suspend key monitoring started: {key_name}", "SUSPEND")
        logger.info(f"Hold '{key_name}' to temporarily suspend aimbot", "SUSPEND")
        
        return True
    
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        if self.listener:
            self.listener.stop()
            self.listener = None
            logger.info("Suspend key monitoring stopped", "SUSPEND")
    
    def _on_press(self, key):
        """Callback cuando se presiona una tecla"""
        if key == self.suspend_key:
            with self.lock:
                if not self.suspended:
                    self.suspended = True
                    key_name = self._key_to_string(key)
                    logger.info(f"Aimbot SUSPENDED (holding '{key_name}')", "SUSPEND")
    
    def _on_release(self, key):
        """Callback cuando se suelta una tecla"""
        if key == self.suspend_key:
            with self.lock:
                if self.suspended:
                    self.suspended = False
                    key_name = self._key_to_string(key)
                    logger.info(f"Aimbot RESUMED (released '{key_name}')", "SUSPEND")
    
    def is_suspended(self) -> bool:
        """Verifica si el aimbot está suspendido"""
        with self.lock:
            return self.suspended
    
    def reconfigure(self):
        """Reconfigura la tecla de suspensión"""
        self.stop_monitoring()
        self.suspend_key = None
        self._request_suspend_key()
        self.start_monitoring()

# Instancia global
suspend_manager = SuspendKeyManager()