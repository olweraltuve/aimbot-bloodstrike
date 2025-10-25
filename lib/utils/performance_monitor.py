"""
Performance Monitor
==================
Monitorea y registra el rendimiento del program_t.
"""

import time
import psutil
import json
from pathlib import Path
from collections import deque
from typing import Dict, Any
from lib.utils.logger import logger

class PerformanceMonitor:
    """Monitor de rendimiento del sistema"""
    
    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self.fps_history = deque(maxlen=history_size)
        self.frame_time_history = deque(maxlen=history_size)
        self.detection_time_history = deque(maxlen=history_size)
        self.movement_time_history = deque(maxlen=history_size)
        
        self.total_frames = 0
        self.total_detections = 0
        self.total_movements = 0
        self.start_time = time.time()
        
        self.process = psutil.Process()
    
    def log_frame(
        self, 
        fps: float, 
        targets: int = 0, 
        locked: bool = False,
        frame_time: float = 0,
        detection_time: float = 0,
        movement_time: float = 0
    ):
        """Registra métricas de un frame"""
        self.total_frames += 1
        
        if fps > 0:
            self.fps_history.append(fps)
        
        if frame_time > 0:
            self.frame_time_history.append(frame_time * 1000)  # ms
        
        if detection_time > 0:
            self.detection_time_history.append(detection_time * 1000)  # ms
        
        if movement_time > 0:
            self.movement_time_history.append(movement_time * 1000)  # ms
        
        if targets > 0:
            self.total_detections += targets
        
        if locked:
            self.total_movements += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas actuales"""
        uptime = time.time() - self.start_time
        
        # CPU y memoria
        cpu_percent = self.process.cpu_percent()
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # FPS
        avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
        min_fps = min(self.fps_history) if self.fps_history else 0
        max_fps = max(self.fps_history) if self.fps_history else 0
        
        # Frame time
        avg_frame_time = sum(self.frame_time_history) / len(self.frame_time_history) if self.frame_time_history else 0
        
        return {
            'uptime_seconds': uptime,
            'total_frames': self.total_frames,
            'total_detections': self.total_detections,
            'total_movements': self.total_movements,
            'cpu_percent': cpu_percent,
            'memory_mb': memory_mb,
            'fps': {
                'current': self.fps_history[-1] if self.fps_history else 0,
                'average': avg_fps,
                'min': min_fps,
                'max': max_fps
            },
            'frame_time_ms': {
                'current': self.frame_time_history[-1] if self.frame_time_history else 0,
                'average': avg_frame_time
            }
        }
    
    def print_stats(self):
        """Imprime estadísticas en consola"""
        stats = self.get_stats()
        
        logger.info("=== Performance Statistics ===", "PERF")
        logger.info(f"Uptime: {stats['uptime_seconds']:.1f}s", "PERF")
        logger.info(f"Total Frames: {stats['total_frames']}", "PERF")
        logger.info(f"Total Detections: {stats['total_detections']}", "PERF")
        logger.info(f"FPS: {stats['fps']['current']:.1f} (avg: {stats['fps']['average']:.1f})", "PERF")
        logger.info(f"CPU: {stats['cpu_percent']:.1f}%", "PERF")
        logger.info(f"Memory: {stats['memory_mb']:.1f} MB", "PERF")
        logger.info("=" * 30, "PERF")
    
    def save_stats(self, filename: str = "performance_stats.json"):
        """Guarda estadísticas en archivo"""
        stats = self.get_stats()
        stats_path = Path("logs") / filename
        
        try:
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
            logger.info(f"Performance stats saved to {stats_path}", "PERF")
        except Exception as e:
            logger.error(f"Failed to save stats: {e}", "PERF")
    
    def reset(self):
        """Resetea las métricas"""
        self.fps_history.clear()
        self.frame_time_history.clear()
        self.detection_time_history.clear()
        self.movement_time_history.clear()
        self.total_frames = 0
        self.total_detections = 0
        self.total_movements = 0
        self.start_time = time.time()
        logger.info("Performance monitor reset", "PERF")