"""
Capture Manager
==============
Gestiona diferentes métodos de captura de pantalla con auto-detección.
"""

import numpy as np
import time
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from lib.utils.logger import logger

class CaptureMethod(ABC):
    """Clase base para métodos de captura"""
    
    @abstractmethod
    def capture(self, region: dict) -> Optional[np.ndarray]:
        """Captura una región de la pantalla"""
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """Inicializa el método de captura"""
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

class MSSCapture(CaptureMethod):
    """Captura usando MSS (rápido, solo ventana sin bordes)"""
    
    def __init__(self):
        self.sct = None
        self._name = "MSS"
    
    @property
    def name(self) -> str:
        return self._name
    
    def initialize(self) -> bool:
        try:
            import mss
            self.sct = mss.mss()
            logger.info("MSS capture initialized", "CAPTURE")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MSS: {e}", "CAPTURE")
            return False
    
    def capture(self, region: dict) -> Optional[np.ndarray]:
        try:
            if self.sct is None:
                return None
            
            screenshot = self.sct.grab(region)
            frame = np.array(screenshot, dtype=np.uint8)
            return frame
        except Exception as e:
            logger.debug(f"MSS capture failed: {e}", "CAPTURE")
            return None
    
    def cleanup(self):
        if self.sct:
            try:
                self.sct.close()
                logger.info("MSS capture cleaned up", "CAPTURE")
            except:
                pass

class BitBltCapture(CaptureMethod):
    """Captura usando BitBlt (funciona con pantalla completa)"""
    
    def __init__(self):
        self.desktop_dc = None
        self.mem_dc = None
        self._name = "BitBlt"
    
    @property
    def name(self) -> str:
        return self._name
    
    def initialize(self) -> bool:
        try:
            import win32gui
            import win32ui
            
            hwnd = win32gui.GetDesktopWindow()
            self.desktop_dc = win32gui.GetWindowDC(hwnd)
            self.mem_dc = win32ui.CreateDCFromHandle(self.desktop_dc)
            
            logger.info("BitBlt capture initialized", "CAPTURE")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize BitBlt: {e}", "CAPTURE")
            return False
    
    def capture(self, region: dict) -> Optional[np.ndarray]:
        try:
            import win32ui
            import win32con
            import win32gui
            
            left, top = region['left'], region['top']
            width, height = region['width'], region['height']
            
            save_dc = self.mem_dc.CreateCompatibleDC()
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(self.mem_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            
            save_dc.BitBlt((0, 0), (width, height), self.mem_dc, (left, top), win32con.SRCCOPY)
            
            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)
            frame = np.frombuffer(bmpstr, dtype=np.uint8).reshape((height, width, 4))
            
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            
            return frame
        except Exception as e:
            logger.debug(f"BitBlt capture failed: {e}", "CAPTURE")
            return None
    
    def cleanup(self):
        try:
            import win32gui
            
            if self.mem_dc:
                self.mem_dc.DeleteDC()
            if self.desktop_dc:
                win32gui.ReleaseDC(win32gui.GetDesktopWindow(), self.desktop_dc)
            
            logger.info("BitBlt capture cleaned up", "CAPTURE")
        except:
            pass

class CaptureManager:
    """Gestor de captura con auto-selección de método"""
    
    def __init__(self, preferred_method: str = 'auto'):
        self.current_method: Optional[CaptureMethod] = None
        self.preferred_method = preferred_method.lower()
        self.failed_captures = 0
        self.success_captures = 0
        self.auto_switch_threshold = 30
        
        self.initialize_capture()
    
    def initialize_capture(self):
        """Inicializa el método de captura preferido"""
        if self.preferred_method == 'bitblt':
            self._try_bitblt()
        elif self.preferred_method == 'mss':
            self._try_mss()
        elif self.preferred_method == 'auto':
            # Intentar BitBlt primero (mejor para pantalla completa)
            if not self._try_bitblt():
                self._try_mss()
        
        if self.current_method is None:
            logger.critical("No capture method could be initialized!", "CAPTURE")
    
    def _try_bitblt(self) -> bool:
        """Intenta inicializar BitBlt"""
        method = BitBltCapture()
        if method.initialize():
            self.current_method = method
            return True
        return False
    
    def _try_mss(self) -> bool:
        """Intenta inicializar MSS"""
        method = MSSCapture()
        if method.initialize():
            self.current_method = method
            return True
        return False
    
    def capture(self, region: dict) -> Optional[np.ndarray]:
        """Captura una región de la pantalla"""
        if self.current_method is None:
            return None
        
        frame = self.current_method.capture(region)
        
        if frame is not None and frame.size > 0:
            self.success_captures += 1
            self.failed_captures = 0
            return frame
        else:
            self.failed_captures += 1
            
            # Auto-switch si hay muchos fallos
            if self.failed_captures >= self.auto_switch_threshold:
                logger.warning(
                    f"{self.current_method.name} failed {self.failed_captures} times, "
                    "trying alternative method...", 
                    "CAPTURE"
                )
                self._switch_method()
                self.failed_captures = 0
            
            return None
    
    def _switch_method(self):
        """Cambia al método alternativo"""
        if isinstance(self.current_method, BitBltCapture):
            logger.info("Switching from BitBlt to MSS", "CAPTURE")
            self.cleanup()
            self._try_mss()
        elif isinstance(self.current_method, MSSCapture):
            logger.info("Switching from MSS to BitBlt", "CAPTURE")
            self.cleanup()
            self._try_bitblt()
    
    def get_method_name(self) -> str:
        """Obtiene el nombre del método actual"""
        return self.current_method.name if self.current_method else "None"
    
    def cleanup(self):
        """Limpia recursos"""
        if self.current_method:
            self.current_method.cleanup()
            self.current_method = None