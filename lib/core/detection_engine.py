"""
Detection Engine
================
Motor de detección de objetivos con múltiples estrategias.
"""

import math
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from lib.utils.logger import logger

@dataclass
class DetectionConfig:
    """Configuración del motor de detección"""
    fov: int = 350
    confidence: float = 0.45
    iou: float = 0.45
    aim_height_divisor: int = 5
    target_priority: str = 'closest'  # 'closest', 'head_closest', 'largest'
    sticky_target: bool = True
    stickiness_pixels: int = 60
    persistence_frames: int = 10

@dataclass
class Target:
    """Representa un objetivo detectado"""
    box: Tuple[int, int, int, int]  # x1, y1, x2, y2
    head_x: int
    head_y: int
    crosshair_distance: float
    confidence: float
    center_x: int
    center_y: int
    width: int
    height: int
    id: Optional[int] = None

class DetectionEngine:
    """Motor de detección y seguimiento de objetivos"""
    
    def __init__(self, config: DetectionConfig):
        self.config = config
        self.current_target: Optional[Target] = None
        self.target_lock_frames = 0
        self.last_detection_time = 0
        self.detection_count = 0
        self.next_target_id = 0
    
    def process_detections(
        self, 
        boxes: List,
        box_constant: int,
        screen_x: int,
        screen_y: int
    ) -> List[Target]:
        """
        Procesa detecciones brutas del modelo YOLO.
        Retorna lista de objetivos con información calculada.
        """
        if len(boxes) == 0:
            return []
        
        targets = []
        center_x = box_constant / 2
        center_y = box_constant / 2
        
        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            
            # Calcular dimensiones
            width = x2 - x1
            height = y2 - y1
            
            # Calcular centro
            center_box_x = (x1 + x2) / 2
            center_box_y = (y1 + y2) / 2
            
            # Calcular posición de la cabeza
            head_x = int(center_box_x)
            head_y = int(center_box_y - height / self.config.aim_height_divisor)
            
            # Distancia al crosshair
            crosshair_dist = math.hypot(
                center_box_x - center_x,
                center_box_y - center_y
            )
            
            target = Target(
                box=(x1, y1, x2, y2),
                head_x=head_x,
                head_y=head_y,
                crosshair_distance=crosshair_dist,
                confidence=0.0,  # Se obtendría del modelo si está disponible
                center_x=int(center_box_x),
                center_y=int(center_box_y),
                width=width,
                height=height,
                id=self.next_target_id
            )
            
            self.next_target_id += 1
            targets.append(target)
        
        self.detection_count += 1
        self.last_detection_time = time.time()
        
        return targets
    
    def select_best_target(self, targets: List[Target]) -> Optional[Target]:
        """
        Selecciona el mejor objetivo según la estrategia configurada.
        Implementa target stickiness para reducir cambios erráticos.
        """
        if not targets:
            # Si no hay objetivos, resetear target actual
            if self.current_target is not None:
                self.target_lock_frames = 0
                self.current_target = None
            return None
        
        # Si hay un target actual y sticky está activado
        if self.config.sticky_target and self.current_target is not None:
            # Buscar si el target actual sigue presente
            sticky_target = self._find_sticky_target(targets)
            
            if sticky_target is not None:
                self.target_lock_frames += 1
                self.current_target = sticky_target
                return sticky_target
            else:
                # El target se perdió
                self.target_lock_frames -= 1
                
                # Solo cambiar de target si se pierde por varios frames
                if self.target_lock_frames > -self.config.persistence_frames:
                    # Mantener el último target conocido por un momento
                    return self.current_target
                else:
                    # Finalmente liberar el target
                    self.current_target = None
                    self.target_lock_frames = 0
        
        # Seleccionar nuevo target según prioridad
        best_target = self._select_by_priority(targets)
        
        if best_target is not None:
            self.current_target = best_target
            self.target_lock_frames = 1
        
        return best_target
    
    def _find_sticky_target(self, targets: List[Target]) -> Optional[Target]:
        """
        Busca el target actual en la nueva lista de detecciones.
        Usa proximidad para identificar el mismo target.
        """
        if self.current_target is None:
            return None
        
        min_distance = float('inf')
        closest_target = None
        
        for target in targets:
            # Distancia entre centros
            dist = math.hypot(
                target.center_x - self.current_target.center_x,
                target.center_y - self.current_target.center_y
            )
            
            if dist < min_distance and dist < self.config.stickiness_pixels:
                min_distance = dist
                closest_target = target
        
        return closest_target
    
    def _select_by_priority(self, targets: List[Target]) -> Optional[Target]:
        """Selecciona target según estrategia de prioridad"""
        
        if self.config.target_priority == 'closest':
            # Más cercano al crosshair
            return min(targets, key=lambda t: t.crosshair_distance)
        
        elif self.config.target_priority == 'head_closest':
            # Cabeza más cercana al crosshair
            return min(targets, key=lambda t: math.hypot(
                t.head_x - (targets[0].box[0] + targets[0].box[2]) / 4,  # Aproximación
                t.head_y - (targets[0].box[1] + targets[0].box[3]) / 4
            ))
        
        elif self.config.target_priority == 'largest':
            # Target más grande (más cercano en distancia real)
            return max(targets, key=lambda t: t.width * t.height)
        
        else:
            # Default: closest
            return min(targets, key=lambda t: t.crosshair_distance)
    
    def is_locked_on_target(
        self, 
        absolute_x: int, 
        absolute_y: int, 
        screen_x: int, 
        screen_y: int,
        threshold: int = 15
    ) -> bool:
        """Verifica si el crosshair está sobre el objetivo"""
        return (
            screen_x - threshold <= absolute_x <= screen_x + threshold and
            screen_y - threshold <= absolute_y <= screen_y + threshold
        )
    
    def reset(self):
        """Resetea el estado del motor"""
        self.current_target = None
        self.target_lock_frames = 0
        self.detection_count = 0
    
    def get_stats(self) -> dict:
        """Obtiene estadísticas de detección"""
        return {
            "detections": self.detection_count,
            "has_target": self.current_target is not None,
            "lock_frames": self.target_lock_frames,
            "last_detection": self.last_detection_time
        }