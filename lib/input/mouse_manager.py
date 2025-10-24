"""
Mouse Manager
=============
Gestiona diferentes métodos de entrada de mouse con detección automática.
"""

import ctypes
import time
import os
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from lib.utils.logger import logger

PUL = ctypes.POINTER(ctypes.c_ulong)

class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL)
    ]

class Input_I(ctypes.Union):
    _fields_ = [("mi", MouseInput)]

class Input(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("ii", Input_I)
    ]

class MouseMethod(ABC):
    """Clase base para métodos de mouse"""
    
    @abstractmethod
    def move(self, dx: int, dy: int) -> bool:
        """Mueve el mouse de forma relativa"""
        pass
    
    @abstractmethod
    def click(self, button: str = 'left') -> bool:
        """Hace clic con el mouse"""
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """Inicializa el método"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Limpia recursos"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre del método"""
        pass
    
    @property
    @abstractmethod
    def detection_level(self) -> str:
        """Nivel de detección (LOW, MEDIUM, HIGH)"""
        pass

class DDXoftMouse(MouseMethod):
    """Método DDXoft (kernel-level, baja detección)"""
    
    def __init__(self):
        self.dll = None
        self._name = "DDXoft"
        self._detection_level = "LOW"
        self.initialized = False
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def detection_level(self) -> str:
        return self._detection_level
    
    def initialize(self) -> bool:
        """Inicializa el driver DDXoft"""
        try:
            # Construir ruta robusta a la DLL
            script_dir = os.path.dirname(os.path.abspath(__file__))
            dll_path = os.path.join(script_dir, "..", "mouse", "dd40605x64.dll")
            dll_path = os.path.normpath(dll_path)
            
            if not os.path.exists(dll_path):
                logger.error(f"DDXoft DLL not found at: {dll_path}", "MOUSE")
                return False
            
            # Cargar DLL
            self.dll = ctypes.WinDLL(dll_path)
            time.sleep(0.1)
            
            # Configurar tipos de argumentos
            self.dll.DD_btn.argtypes = [ctypes.c_int]
            self.dll.DD_btn.restype = ctypes.c_int
            
            self.dll.DD_movR.argtypes = [ctypes.c_int, ctypes.c_int]
            self.dll.DD_movR.restype = ctypes.c_int
            
            self.dll.DD_key.argtypes = [ctypes.c_int, ctypes.c_int]
            self.dll.DD_key.restype = ctypes.c_int
            
            # Inicializar driver
            init_code = self.dll.DD_btn(0)
            
            if init_code != 1:
                logger.error(
                    f"DDXoft driver initialization failed (code: {init_code}). "
                    "MAKE SURE TO RUN AS ADMINISTRATOR!", 
                    "MOUSE"
                )
                return False
            
            # Test de movimiento
            test_result = self.dll.DD_movR(0, 0)
            if test_result != 1:
                logger.warning(f"DDXoft test movement returned: {test_result}", "MOUSE")
            
            self.initialized = True
            logger.info("DDXoft driver initialized successfully (LOW detection risk)", "MOUSE")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize DDXoft: {e}", "MOUSE")
            logger.warning("Possible causes: Antivirus blocking, missing admin rights", "MOUSE")
            return False
    
    def move(self, dx: int, dy: int) -> bool:
        """Mueve el mouse de forma relativa"""
        if not self.initialized or self.dll is None:
            return False
        
        try:
            # DDXoft requiere valores enteros
            dx_int = int(round(dx))
            dy_int = int(round(dy))
            
            if dx_int == 0 and dy_int == 0:
                return True
            
            result = self.dll.DD_movR(dx_int, dy_int)
            return result == 1
            
        except Exception as e:
            logger.debug(f"DDXoft move failed: {e}", "MOUSE")
            return False
    
    def click(self, button: str = 'left') -> bool:
        """Hace clic con el mouse"""
        if not self.initialized or self.dll is None:
            return False
        
        try:
            if button == 'left':
                self.dll.DD_btn(1)  # Mouse down
                time.sleep(0.001)
                self.dll.DD_btn(2)  # Mouse up
            elif button == 'right':
                self.dll.DD_btn(4)  # Right down
                time.sleep(0.001)
                self.dll.DD_btn(8)  # Right up
            return True
        except Exception as e:
            logger.debug(f"DDXoft click failed: {e}", "MOUSE")
            return False
    
    def cleanup(self):
        """Limpia recursos"""
        self.dll = None
        self.initialized = False
        logger.info("DDXoft driver cleaned up", "MOUSE")

class Win32Mouse(MouseMethod):
    """Método Win32 SendInput (alta detección, no funciona en pantalla completa)"""
    
    def __init__(self):
        self.extra = ctypes.c_ulong(0)
        self.ii_ = Input_I()
        self._name = "Win32"
        self._detection_level = "HIGH"
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def detection_level(self) -> str:
        return self._detection_level
    
    def initialize(self) -> bool:
        """Inicializa el método Win32"""
        logger.warning(
            "Win32 method is HIGHLY DETECTABLE and may not work in fullscreen games!", 
            "MOUSE"
        )
        logger.info("Win32 mouse initialized", "MOUSE")
        return True
    
    def move(self, dx: int, dy: int) -> bool:
        """Mueve el mouse usando SendInput"""
        try:
            dx_int = int(dx)
            dy_int = int(dy)
            
            if dx_int == 0 and dy_int == 0:
                return True
            
            self.ii_.mi = MouseInput(
                dx_int, dy_int, 0, 0x0001, 0, 
                ctypes.pointer(self.extra)
            )
            command = Input(ctypes.c_ulong(0), self.ii_)
            result = ctypes.windll.user32.SendInput(
                1, ctypes.pointer(command), ctypes.sizeof(command)
            )
            return result == 1
            
        except Exception as e:
            logger.debug(f"Win32 move failed: {e}", "MOUSE")
            return False
    
    def click(self, button: str = 'left') -> bool:
        """Hace clic usando mouse_event"""
        try:
            if button == 'left':
                ctypes.windll.user32.mouse_event(0x0002)  # Left down
                time.sleep(0.0001)
                ctypes.windll.user32.mouse_event(0x0004)  # Left up
            elif button == 'right':
                ctypes.windll.user32.mouse_event(0x0008)  # Right down
                time.sleep(0.0001)
                ctypes.windll.user32.mouse_event(0x0010)  # Right up
            return True
        except Exception as e:
            logger.debug(f"Win32 click failed: {e}", "MOUSE")
            return False
    
    def cleanup(self):
        """Limpia recursos"""
        logger.info("Win32 mouse cleaned up", "MOUSE")

class MouseManager:
    """Gestor de mouse con auto-selección de método"""
    
    def __init__(self, preferred_method: str = 'auto'):
        self.current_method: Optional[MouseMethod] = None
        self.preferred_method = preferred_method.lower()
        self.move_failures = 0
        self.move_successes = 0
        self.auto_switch_threshold = 50
        
        self.initialize_mouse()
    
    def initialize_mouse(self):
        """Inicializa el método de mouse preferido"""
        if self.preferred_method == 'ddxoft':
            self._try_ddxoft()
        elif self.preferred_method == 'win32':
            self._try_win32()
        elif self.preferred_method == 'auto':
            # Intentar DDXoft primero (menos detectable)
            if not self._try_ddxoft():
                logger.warning("DDXoft failed, falling back to Win32", "MOUSE")
                self._try_win32()
        
        if self.current_method is None:
            logger.critical("No mouse method could be initialized!", "MOUSE")
    
    def _try_ddxoft(self) -> bool:
        """Intenta inicializar DDXoft"""
        method = DDXoftMouse()
        if method.initialize():
            self.current_method = method
            return True
        return False
    
    def _try_win32(self) -> bool:
        """Intenta inicializar Win32"""
        method = Win32Mouse()
        if method.initialize():
            self.current_method = method
            return True
        return False
    
    def move(self, dx: float, dy: float, delay: float = 0.0009) -> bool:
        """Mueve el mouse con delay opcional"""
        if self.current_method is None:
            return False
        
        success = self.current_method.move(dx, dy)
        
        if success:
            self.move_successes += 1
            self.move_failures = 0
        else:
            self.move_failures += 1
            
            # Auto-switch si hay muchos fallos
            if self.move_failures >= self.auto_switch_threshold:
                logger.warning(
                    f"{self.current_method.name} failed {self.move_failures} times, "
                    "trying alternative method...", 
                    "MOUSE"
                )
                self._switch_method()
                self.move_failures = 0
        
        if delay > 0:
            time.sleep(delay)
        
        return success
    
    def click(self, button: str = 'left') -> bool:
        """Hace clic"""
        if self.current_method is None:
            return False
        return self.current_method.click(button)
    
    def _switch_method(self):
        """Cambia al método alternativo"""
        if isinstance(self.current_method, DDXoftMouse):
            logger.info("Switching from DDXoft to Win32", "MOUSE")
            self.cleanup()
            self._try_win32()
        elif isinstance(self.current_method, Win32Mouse):
            logger.info("Switching from Win32 to DDXoft", "MOUSE")
            self.cleanup()
            self._try_ddxoft()
    
    def get_method_name(self) -> str:
        """Obtiene el nombre del método actual"""
        return self.current_method.name if self.current_method else "None"
    
    def get_detection_level(self) -> str:
        """Obtiene el nivel de detección"""
        return self.current_method.detection_level if self.current_method else "UNKNOWN"
    
    def cleanup(self):
        """Limpia recursos"""
        if self.current_method:
            self.current_method.cleanup()
            self.current_method = None