"""
Advanced Logging System
=======================
Sistema de logs robusto con niveles, colores y rotación de archivos.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from termcolor import colored
import json

class ColoredFormatter(logging.Formatter):
    """Formatter personalizado con colores para consola"""
    
    COLORS = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'magenta'
    }
    
    def format(self, record):
        levelname = record.levelname
        message = super().format(record)
        
        if levelname in self.COLORS:
            levelname_colored = colored(f"[{levelname}]", self.COLORS[levelname])
            message = message.replace(f"[{levelname}]", levelname_colored)
        
        return message

class Program_tLogger:
    """Logger centralizado para todo el program_t"""
    
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
        self.setup_logger()
    
    def setup_logger(self):
        """Configura el sistema de logging"""
        # Crear directorio de logs
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configurar logger principal
        self.logger = logging.getLogger("Program_tLogger")
        self.logger.setLevel(logging.DEBUG)
        
        # Handler para consola con colores
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '[%(levelname)s] %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Handler para archivo con todos los detalles
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(
            log_dir / f"program_t_{timestamp}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Agregar handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def debug(self, message, category="GENERAL"):
        """Log de depuración"""
        self.logger.debug(f"[{category}] {message}")
    
    def info(self, message, category="GENERAL"):
        """Log informativo"""
        self.logger.info(f"[{category}] {message}")
    
    def warning(self, message, category="GENERAL"):
        """Log de advertencia"""
        self.logger.warning(f"[{category}] {message}")
    
    def error(self, message, category="GENERAL"):
        """Log de error"""
        self.logger.error(f"[{category}] {message}")
    
    def critical(self, message, category="GENERAL"):
        """Log crítico"""
        self.logger.critical(f"[{category}] {message}")
    
    def performance(self, data):
        """Log de métricas de rendimiento"""
        perf_log = Path("logs") / "performance.jsonl"
        with open(perf_log, 'a', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                **data
            }, f)
            f.write('\n')

# Instancia global
logger = Program_tLogger()