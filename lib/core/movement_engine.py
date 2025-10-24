"""
Movement Engine
===============
Motor de movimiento humanizado con múltiples estrategias.
"""

import math
import random
import time
from typing import Tuple, List, Optional
from dataclasses import dataclass
import numpy as np
from lib.utils.logger import logger

@dataclass
class MovementConfig:
    """Configuración del motor de movimiento"""
    smoothing: float = 0.7
    deadzone_pixels: int = 2
    max_move_speed: float = 100.0
    acceleration_factor: float = 0.8
    mouse_delay: float = 0.0009
    humanization_enabled: bool = True
    noise_amplitude: float = 0.1
    overshoot_probability: float = 0.15
    overshoot_max_pixels: int = 3

class MovementEngine:
    """Motor de movimiento con humanización"""
    
    def __init__(self, config: MovementConfig):
        self.config = config
        self.movement_path: List[Tuple[float, float]] = []
        self.current_velocity = np.array([0.0, 0.0])
        self.last_move_time = 0
        self.total_distance_moved = 0
    
    def calculate_movement(
        self, 
        current_x: int, 
        current_y: int, 
        target_x: int, 
        target_y: int
    ) -> Optional[Tuple[float, float]]:
        """
        Calcula el siguiente movimiento hacia el objetivo.
        Retorna (dx, dy) o None si está en deadzone.
        """
        # Calcular distancia al objetivo
        dist_x = target_x - current_x
        dist_y = target_y - current_y
        distance = math.hypot(dist_x, dist_y)
        
        # Check deadzone
        if distance < self.config.deadzone_pixels:
            self.movement_path.clear()
            self.current_velocity = np.array([0.0, 0.0])
            return None
        
        # Calcular movimiento base con suavizado
        move_ratio = min(self.config.smoothing, 1.0)
        base_move_x = dist_x * move_ratio
        base_move_y = dist_y * move_ratio
        
        # Limitar velocidad máxima
        move_magnitude = math.hypot(base_move_x, base_move_y)
        if move_magnitude > self.config.max_move_speed:
            scale = self.config.max_move_speed / move_magnitude
            base_move_x *= scale
            base_move_y *= scale
        
        # Aplicar humanización
        if self.config.humanization_enabled:
            base_move_x, base_move_y = self._apply_humanization(
                base_move_x, base_move_y, distance
            )
        
        return (base_move_x, base_move_y)
    
    def _apply_humanization(
        self, 
        move_x: float, 
        move_y: float, 
        distance: float
    ) -> Tuple[float, float]:
        """Aplica humanización al movimiento"""
        
        # 1. Ruido perlin/aleatorio para simular imperfección humana
        if self.config.noise_amplitude > 0:
            noise_x = random.gauss(0, self.config.noise_amplitude)
            noise_y = random.gauss(0, self.config.noise_amplitude)
            move_x += noise_x
            move_y += noise_y
        
        # 2. Aceleración/desaceleración según distancia
        if distance > 50:
            # Aceleración cuando está lejos
            accel = 1.0 + (self.config.acceleration_factor * 0.2)
            move_x *= accel
            move_y *= accel
        elif distance < 20:
            # Desaceleración cuando está cerca
            decel = 0.7 + (distance / 20) * 0.3
            move_x *= decel
            move_y *= decel
        
        # 3. Overshoot ocasional (pasarse ligeramente)
        if random.random() < self.config.overshoot_probability:
            overshoot = random.randint(1, self.config.overshoot_max_pixels)
            direction = math.atan2(move_y, move_x)
            move_x += math.cos(direction) * overshoot
            move_y += math.sin(direction) * overshoot
        
        return (move_x, move_y)
    
    def calculate_bezier_path(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        steps: int = 20
    ) -> List[Tuple[float, float]]:
        """
        Calcula una trayectoria de Bézier cuadrática.
        Útil para movimientos largos y curvos.
        """
        # Punto de control intermedio con offset aleatorio
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        
        # Offset perpendicular para crear curva
        dx = end_x - start_x
        dy = end_y - start_y
        distance = math.hypot(dx, dy)
        
        if distance < 10:
            return [(end_x - start_x, end_y - start_y)]
        
        # Offset aleatorio (10-30% de la distancia)
        offset_magnitude = random.uniform(0.1, 0.3) * distance
        offset_angle = math.atan2(dy, dx) + math.pi / 2
        
        control_x = mid_x + math.cos(offset_angle) * offset_magnitude
        control_y = mid_y + math.sin(offset_angle) * offset_magnitude
        
        # Generar puntos de la curva
        path = []
        prev_x, prev_y = start_x, start_y
        
        for i in range(1, steps + 1):
            t = i / steps
            
            # Fórmula de Bézier cuadrática
            x = (1-t)**2 * start_x + 2*(1-t)*t * control_x + t**2 * end_x
            y = (1-t)**2 * start_y + 2*(1-t)*t * control_y + t**2 * end_y
            
            # Calcular movimiento relativo
            dx = x - prev_x
            dy = y - prev_y
            
            path.append((dx, dy))
            prev_x, prev_y = x, y
        
        return path
    
    def reset(self):
        """Resetea el estado del motor"""
        self.movement_path.clear()
        self.current_velocity = np.array([0.0, 0.0])
        self.total_distance_moved = 0
    
    def get_stats(self) -> dict:
        """Obtiene estadísticas de movimiento"""
        return {
            "total_distance": self.total_distance_moved,
            "path_length": len(self.movement_path),
            "current_velocity": self.current_velocity.tolist()
        }