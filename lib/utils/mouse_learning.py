"""
Active Mouse Learning System
=====================
Sistema de calibración ACTIVA que:
- Genera objetivos de prueba en pantalla
- Prueba acercarse desde 8 direcciones (N, NE, E, SE, S, SO, O, NO)
- Mide precisión y detecta problemas (overshoot, vibración)
- Ajusta automáticamente los parámetros
- Vuelve al origen entre pruebas

NUEVO: Sistema de Aprendizaje Adaptativo que:
- Usa TARGETS REALES detectados por YOLO
- Se acerca con pasos pequeños
- Aumenta velocidad si funciona
- Se aleja y vuelve a enfocar (3 ciclos)
- Guarda parámetros aprendidos
"""

import json
import math
import time
import random
import cv2
import numpy as np
import win32api
import win32con
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import deque
from lib.utils.logger import logger

@dataclass
class CalibrationTest:
    """Una prueba de calibración"""
    direction: str  # 'N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'
    angle_degrees: float
    start_x: int
    start_y: int
    target_x: int
    target_y: int
    distance: int
    success: bool = False
    overshoot: bool = False
    vibration: bool = False
    actual_final_x: int = 0
    actual_final_y: int = 0
    final_error_px: float = 0.0
    attempts: int = 0
    corrections_applied: List[str] = None
    
    def __post_init__(self):
        if self.corrections_applied is None:
            self.corrections_applied = []

@dataclass
class MovementSample:
    """Muestra de un intento de movimiento"""
    timestamp: float
    # Input que enviamos
    input_dx: float
    input_dy: float
    # Posición del cursor antes
    cursor_before_x: int
    cursor_before_y: int
    # Posición del cursor después
    cursor_after_x: int
    cursor_after_y: int
    # Posición del objetivo
    target_x: int
    target_y: int
    # Resultado calculado
    actual_dx: int
    actual_dy: int
    # Éxito del movimiento
    success: bool

@dataclass
class LearningProfile:
    """Perfil aprendido de movimiento del mouse"""
    # Inversión de ejes
    x_inverted: bool = False
    y_inverted: bool = False
    
    # Escalado (multiplicadores)
    x_scale: float = 1.0
    y_scale: float = 1.0
    
    # Smoothing ajustado
    smoothing: float = 0.5
    
    # Deadzone ajustado
    deadzone: int = 5
    
    # Confianza en las detecciones (0-1)
    confidence: float = 0.0
    
    # Número de muestras usadas
    sample_count: int = 0
    
    # Timestamp de última actualización
    last_updated: float = 0.0
    
    # Tests realizados
    tests_completed: int = 0
    
    # Notas/problemas detectados
    notes: List[str] = None
    
    def __post_init__(self):
        if self.notes is None:
            self.notes = []

@dataclass
class AdaptiveLearningCycle:
    """Un ciclo de aprendizaje adaptativo"""
    cycle_number: int
    target_x: int
    target_y: int
    start_distance: float
    approach_steps: int = 0
    final_error: float = 0.0
    initial_smoothing: float = 0.0
    final_smoothing: float = 0.0
    success: bool = False
    retreat_distance: int = 0

class AdaptiveLearningSystem:
    """
    Sistema de aprendizaje adaptativo con TARGETS REALES.
    
    Flujo:
    1. Detecta un target real del juego
    2. Se acerca con pasos MUY pequeños (smoothing bajo)
    3. Mide qué tan bien funciona
    4. Aumenta velocidad gradualmente si funciona
    5. Cuando llega, se aleja un poco
    6. Vuelve a enfocar
    7. Repite hasta 3 ciclos
    8. Guarda parámetros
    """
    
    def __init__(self, movement_engine=None, detection_engine=None, mouse_manager=None):
        self.movement_engine = movement_engine
        self.detection_engine = detection_engine
        self.mouse_manager = mouse_manager
        
        # Estado
        self.active = False
        self.current_cycle = 0
        self.max_cycles = 3
        self.cycles_history: List[AdaptiveLearningCycle] = []
        
        # Target actual
        self.target_x: Optional[int] = None
        self.target_y: Optional[int] = None
        self.target_locked = False
        
        # Parámetros de aprendizaje
        self.initial_smoothing = 0.15  # MUY lento al inicio
        self.max_smoothing = 0.6  # Máximo cuando funciona bien
        self.current_smoothing = self.initial_smoothing
        self.smoothing_increment = 0.05  # Incremento gradual
        
        # Thresholds
        self.approach_threshold = 15  # píxeles para considerar "llegada"
        self.retreat_distance_min = 50  # píxeles mínimo de alejamiento
        self.retreat_distance_max = 100  # píxeles máximo de alejamiento
        
        # Estadísticas
        self.approach_steps = 0
        self.successful_approaches = 0
        
        logger.info("Adaptive Learning System initialized", "ADAPTIVE")
    
    def start(self):
        """Inicia el sistema de aprendizaje adaptativo"""
        if self.movement_engine is None or self.detection_engine is None:
            logger.error("Movement or detection engine not set", "ADAPTIVE")
            return False
        
        self.active = True
        self.current_cycle = 0
        self.cycles_history.clear()
        self.target_locked = False
        self.current_smoothing = self.initial_smoothing
        self.approach_steps = 0
        
        logger.info("=" * 60, "ADAPTIVE")
        logger.info("🎯 ADAPTIVE LEARNING STARTED", "ADAPTIVE")
        logger.info("=" * 60, "ADAPTIVE")
        logger.info("The system will learn from REAL TARGETS detected in-game", "ADAPTIVE")
        logger.info(f"Will perform {self.max_cycles} approach cycles", "ADAPTIVE")
        logger.info("Aimbot is now DISABLED - learning mode active", "ADAPTIVE")
        logger.info("=" * 60, "ADAPTIVE")
        
        return True
    
    def stop(self):
        """Detiene el sistema"""
        self.active = False
        self._finalize_learning()
        logger.info("Adaptive learning stopped", "ADAPTIVE")
    
    def process_target(self, target_x: int, target_y: int, screen_x: int, screen_y: int) -> bool:
        """
        Procesa un target detectado en el ciclo de aprendizaje.
        
        Args:
            target_x: Coordenada X absoluta del target
            target_y: Coordenada Y absoluta del target
            screen_x: Centro X de pantalla
            screen_y: Centro Y de pantalla
        
        Returns:
            True si el ciclo continúa, False si terminó
        """
        if not self.active:
            return False
        
        # Si no tenemos target, establecer uno nuevo
        if self.target_x is None:
            self.target_x = target_x
            self.target_y = target_y
            self.target_locked = False
            
            initial_distance = math.hypot(target_x - screen_x, target_y - screen_y)
            
            self.current_cycle_data = AdaptiveLearningCycle(
                cycle_number=self.current_cycle + 1,
                target_x=target_x,
                target_y=target_y,
                start_distance=initial_distance,
                initial_smoothing=self.current_smoothing,
                retreat_distance=random.randint(self.retreat_distance_min, self.retreat_distance_max)
            )
            
            logger.info(
                f"🎯 Cycle {self.current_cycle + 1}/{self.max_cycles}: "
                f"Target locked at ({target_x}, {target_y}), "
                f"distance: {initial_distance:.1f}px, "
                f"smoothing: {self.current_smoothing:.3f}",
                "ADAPTIVE"
            )
        
        # Calcular distancia actual
        current_distance = math.hypot(target_x - screen_x, target_y - screen_y)
        
        # ¿Llegamos al target?
        if current_distance < self.approach_threshold:
            if not self.target_locked:
                self.target_locked = True
                self.current_cycle_data.final_error = current_distance
                self.current_cycle_data.approach_steps = self.approach_steps
                self.current_cycle_data.success = True
                self.successful_approaches += 1
                
                logger.info(
                    f"✅ Target reached in {self.approach_steps} steps! "
                    f"Error: {current_distance:.1f}px, "
                    f"Final smoothing: {self.current_smoothing:.3f}",
                    "ADAPTIVE"
                )
                
                # Aumentar smoothing para el siguiente ciclo (si funciona bien)
                if current_distance < 10:
                    self.current_smoothing = min(
                        self.current_smoothing + self.smoothing_increment,
                        self.max_smoothing
                    )
                    logger.info(
                        f"📈 Increasing smoothing to {self.current_smoothing:.3f} (good precision)",
                        "ADAPTIVE"
                    )
                
                # Esperar un momento
                time.sleep(0.5)
                
                # Alejarse del target
                self._retreat_from_target(screen_x, screen_y)
                
                # Esperar otro momento
                time.sleep(0.5)
                
                # Guardar ciclo y preparar siguiente
                self.current_cycle_data.final_smoothing = self.current_smoothing
                self.cycles_history.append(self.current_cycle_data)
                
                self.current_cycle += 1
                self.target_x = None
                self.target_y = None
                self.target_locked = False
                self.approach_steps = 0
                
                # ¿Terminamos todos los ciclos?
                if self.current_cycle >= self.max_cycles:
                    self.stop()
                    return False
        else:
            # Acercarse al target con el smoothing actual
            self.approach_steps += 1
            
            # Aplicar movimiento con el smoothing aprendido
            dx = (target_x - screen_x) * self.current_smoothing
            dy = (target_y - screen_y) * self.current_smoothing
            
            # Limitar velocidad máxima para control
            max_step = 30
            magnitude = math.hypot(dx, dy)
            if magnitude > max_step:
                scale = max_step / magnitude
                dx *= scale
                dy *= scale
            
            # Mover
            if self.mouse_manager:
                self.mouse_manager.move(dx, dy, delay=0.01)
            
            # Log progreso cada 10 pasos
            if self.approach_steps % 10 == 0:
                logger.info(
                    f"📍 Step {self.approach_steps}: distance={current_distance:.1f}px, "
                    f"smoothing={self.current_smoothing:.3f}",
                    "ADAPTIVE"
                )
        
        return True
    
    def _retreat_from_target(self, screen_x: int, screen_y: int):
        """Se aleja del target"""
        if self.target_x is None:
            return
        
        retreat_distance = self.current_cycle_data.retreat_distance
        
        logger.info(f"🔄 Retreating {retreat_distance}px from target...", "ADAPTIVE")
        
        # Calcular dirección opuesta
        dx = screen_x - self.target_x
        dy = screen_y - self.target_y
        distance = math.hypot(dx, dy)
        
        if distance < 1:
            return
        
        # Normalizar y escalar
        dx = (dx / distance) * retreat_distance
        dy = (dy / distance) * retreat_distance
        
        # Mover en pasos
        steps = 10
        for i in range(steps):
            step_dx = dx / steps
            step_dy = dy / steps
            
            if self.mouse_manager:
                self.mouse_manager.move(step_dx, step_dy, delay=0.01)
            
            time.sleep(0.02)
        
        logger.info("✅ Retreat complete, ready for next cycle", "ADAPTIVE")
    
    def _finalize_learning(self):
        """Finaliza el aprendizaje y calcula resultados"""
        if not self.cycles_history:
            logger.warning("No cycles completed, cannot finalize", "ADAPTIVE")
            return
        
        logger.info("=" * 60, "ADAPTIVE")
        logger.info("🎉 ADAPTIVE LEARNING COMPLETE", "ADAPTIVE")
        logger.info("=" * 60, "ADAPTIVE")
        
        # Calcular estadísticas
        total_steps = sum(c.approach_steps for c in self.cycles_history)
        avg_steps = total_steps / len(self.cycles_history)
        avg_error = sum(c.final_error for c in self.cycles_history) / len(self.cycles_history)
        success_rate = self.successful_approaches / len(self.cycles_history)
        
        logger.info(f"Cycles completed: {len(self.cycles_history)}/{self.max_cycles}", "ADAPTIVE")
        logger.info(f"Success rate: {success_rate:.1%}", "ADAPTIVE")
        logger.info(f"Average steps to target: {avg_steps:.1f}", "ADAPTIVE")
        logger.info(f"Average final error: {avg_error:.1f}px", "ADAPTIVE")
        logger.info(f"Final smoothing: {self.current_smoothing:.3f}", "ADAPTIVE")
        
        # Determinar parámetros óptimos
        optimal_smoothing = self.current_smoothing
        
        logger.info("=" * 60, "ADAPTIVE")
        logger.info(f"📊 LEARNED PARAMETERS:", "ADAPTIVE")
        logger.info(f"   Optimal smoothing: {optimal_smoothing:.3f}", "ADAPTIVE")
        logger.info(f"   Initial smoothing: {self.initial_smoothing:.3f}", "ADAPTIVE")
        if self.initial_smoothing > 0:
            logger.info(f"   Improvement: {((optimal_smoothing / self.initial_smoothing) - 1) * 100:.1f}%", "ADAPTIVE")
        logger.info("=" * 60, "ADAPTIVE")
        
        # Aplicar parámetros al movement engine
        if self.movement_engine:
            self.movement_engine.config.smoothing = optimal_smoothing
            logger.info(f"✅ Applied learned smoothing to movement engine", "ADAPTIVE")
        
        logger.info("Press F5 to SAVE this profile", "ADAPTIVE")
        logger.info("Aimbot is now RE-ENABLED", "ADAPTIVE")
        logger.info("=" * 60, "ADAPTIVE")

    def get_learned_profile(self) -> LearningProfile:
        """Obtiene el perfil aprendido"""
        profile = LearningProfile(
            smoothing=self.current_smoothing,
            confidence=self.successful_approaches / max(len(self.cycles_history), 1),
            sample_count=len(self.cycles_history),
            tests_completed=len(self.cycles_history),
            last_updated=time.time()
        )
        
        if self.successful_approaches == len(self.cycles_history) and self.cycles_history:
            profile.notes.append("All cycles successful - high confidence")
        elif self.cycles_history and self.successful_approaches < len(self.cycles_history) * 0.5:
            profile.notes.append("Low success rate - may need manual adjustment")
        
        return profile


class ActiveMouseLearningSystem:
    """Sistema de aprendizaje ACTIVO con calibración direccional (LEGACY)"""
    
    # Direcciones de prueba
    DIRECTIONS = {
        'N':  0,     # Norte (arriba)
        'NE': 45,    # Noreste
        'E':  90,    # Este (derecha)
        'SE': 135,   # Sureste
        'S':  180,   # Sur (abajo)
        'SW': 225,   # Suroeste
        'W':  270,   # Oeste (izquierda)
        'NW': 315    # Noroeste
    }
    
    def __init__(self, mouse_manager=None, screen_center=None):
        self.profile = LearningProfile()
        self.calibration_active = False
        self.mouse_manager = mouse_manager
        self.screen_center = screen_center or (960, 540)
        
        # Tests
        self.current_test: Optional[CalibrationTest] = None
        self.test_history: List[CalibrationTest] = []
        
        # Estado de calibración
        self.calibration_step = 0
        self.max_attempts_per_test = 3
        self.test_distance = 200  # píxeles desde el centro
        
        # Visualización
        self.calibration_window = None
        
        self.profiles_dir = Path("lib/data/learning_profiles")
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Umbrales de error
        self.error_threshold = 15  # píxeles de error aceptable
        self.overshoot_threshold = 30  # si supera por más de esto, es overshoot
        self.vibration_threshold = 5  # oscilaciones menores a esto
        
        logger.info("Active Mouse Learning System initialized", "LEARNING")
    
    def start_calibration(self):
        """Inicia el proceso de calibración activa"""
        if self.mouse_manager is None:
            logger.error("Mouse manager not set. Cannot calibrate.", "LEARNING")
            return False
        
        self.calibration_active = True
        self.calibration_step = 0
        self.test_history.clear()
        
        logger.info("=" * 60, "LEARNING")
        logger.info("🎯 ACTIVE CALIBRATION STARTED", "LEARNING")
        logger.info("=" * 60, "LEARNING")
        logger.info("The system will now perform directional tests", "LEARNING")
        logger.info("Please don't move your mouse during calibration", "LEARNING")
        logger.info("This will take about 30-60 seconds", "LEARNING")
        logger.info("=" * 60, "LEARNING")
        
        # Crear ventana de visualización
        self._init_calibration_window()
        
        return True
    
    def stop_calibration(self):
        """Detiene la calibración"""
        self.calibration_active = False
        if self.calibration_window is not None:
            cv2.destroyWindow("Calibration")
            self.calibration_window = None
        logger.info("Calibration stopped", "LEARNING")
    
    def _init_calibration_window(self):
        """Inicializa ventana de visualización"""
        self.calibration_window = np.zeros((600, 800, 3), dtype=np.uint8)
    
    def run_calibration_step(self) -> bool:
        """
        Ejecuta un paso de calibración.
        
        Returns:
            True si debe continuar, False si terminó
        """
        if not self.calibration_active:
            return False
        
        # Si no hay test actual, crear uno nuevo
        if self.current_test is None:
            if self.calibration_step >= len(self.DIRECTIONS):
                # Terminamos todos los tests
                self._finalize_calibration()
                return False
            
            # Crear nuevo test
            direction_name = list(self.DIRECTIONS.keys())[self.calibration_step]
            self.current_test = self._create_test(direction_name)
            logger.info(f"Testing direction: {direction_name} ({self.current_test.angle_degrees}°)", "LEARNING")
        
        # Ejecutar el test
        success = self._execute_test(self.current_test)
        
        if success or self.current_test.attempts >= self.max_attempts_per_test:
            # Test completado (exitoso o máx intentos)
            self.test_history.append(self.current_test)
            self.current_test = None
            self.calibration_step += 1
            
            # Esperar un poco entre tests
            time.sleep(0.5)
        else:
            # Reintentar
            self.current_test.attempts += 1
            logger.warning(f"Test failed, retrying ({self.current_test.attempts}/{self.max_attempts_per_test})", "LEARNING")
            time.sleep(0.3)
        
        return True
    
    def _create_test(self, direction: str) -> CalibrationTest:
        """Crea un test para una dirección"""
        angle = self.DIRECTIONS[direction]
        angle_rad = math.radians(angle)
        
        # Calcular posición del objetivo
        center_x, center_y = self.screen_center
        target_x = int(center_x + self.test_distance * math.cos(angle_rad))
        target_y = int(center_y - self.test_distance * math.sin(angle_rad))  # Y invertido
        
        return CalibrationTest(
            direction=direction,
            angle_degrees=angle,
            start_x=center_x,
            start_y=center_y,
            target_x=target_x,
            target_y=target_y,
            distance=self.test_distance
        )
    
    def _execute_test(self, test: CalibrationTest) -> bool:
        """
        Ejecuta un test de calibración.
        
        Returns:
            True si fue exitoso, False si falló
        """
        # 1. Mover cursor al punto de inicio (centro)
        self._move_cursor_to(test.start_x, test.start_y)
        time.sleep(0.1)
        
        # 2. Calcular movimiento necesario
        dx = test.target_x - test.start_x
        dy = test.target_y - test.start_y
        
        # 3. Aplicar correcciones actuales del perfil
        corrected_dx, corrected_dy = self._apply_current_corrections(dx, dy)
        
        # 4. Mover con smoothing simulado
        steps = 10  # Dividir en 10 pasos
        for i in range(steps):
            step_dx = corrected_dx / steps
            step_dy = corrected_dy / steps
            
            self.mouse_manager.move(step_dx, step_dy, delay=0.01)
            time.sleep(0.02)
        
        # 5. Esperar que el movimiento se complete
        time.sleep(0.2)
        
        # 6. Medir posición final
        try:
            final_x, final_y = win32api.GetCursorPos()
        except:
            logger.error("Failed to get cursor position", "LEARNING")
            return False
        
        test.actual_final_x = final_x
        test.actual_final_y = final_y
        
        # 7. Calcular error
        error_x = final_x - test.target_x
        error_y = final_y - test.target_y
        error_distance = math.hypot(error_x, error_y)
        test.final_error_px = error_distance
        
        # 8. Analizar resultado
        if error_distance <= self.error_threshold:
            # Éxito!
            test.success = True
            logger.info(f"✅ {test.direction}: SUCCESS (error: {error_distance:.1f}px)", "LEARNING")
            
            # Actualizar visualización
            self._draw_calibration_result(test, success=True)
            return True
        else:
            # Fallo - detectar tipo de problema
            test.success = False
            
            # ¿Overshoot?
            if error_distance > self.overshoot_threshold:
                test.overshoot = True
                logger.warning(f"❌ {test.direction}: OVERSHOOT (error: {error_distance:.1f}px)", "LEARNING")
                self._adjust_for_overshoot(test, error_x, error_y)
            
            # ¿Dirección incorrecta?
            elif self._is_wrong_direction(dx, dy, final_x - test.start_x, final_y - test.start_y):
                logger.warning(f"❌ {test.direction}: WRONG DIRECTION", "LEARNING")
                self._adjust_for_wrong_direction(test, dx, dy, final_x - test.start_x, final_y - test.start_y)
            
            else:
                logger.warning(f"❌ {test.direction}: MISSED (error: {error_distance:.1f}px)", "LEARNING")
                self._adjust_for_miss(test, error_x, error_y)
            
            # Actualizar visualización
            self._draw_calibration_result(test, success=False)
            return False
    
    def _move_cursor_to(self, x: int, y: int):
        """Mueve el cursor a una posición absoluta (usando Win32)"""
        try:
            # Usar SetCursorPos para movimiento absoluto
            win32api.SetCursorPos((x, y))
        except Exception as e:
            logger.error(f"Failed to move cursor to ({x}, {y}): {e}", "LEARNING")
    
    def _apply_current_corrections(self, dx: float, dy: float) -> Tuple[float, float]:
        """Aplica las correcciones actuales del perfil"""
        corrected_dx = dx * self.profile.x_scale
        corrected_dy = dy * self.profile.y_scale
        
        if self.profile.x_inverted:
            corrected_dx = -corrected_dx
        
        if self.profile.y_inverted:
            corrected_dy = -corrected_dy
        
        return corrected_dx, corrected_dy
    
    def _is_wrong_direction(self, expected_dx: float, expected_dy: float, 
                           actual_dx: float, actual_dy: float) -> bool:
        """Detecta si el movimiento fue en dirección opuesta"""
        if abs(expected_dx) > 10:
            if (expected_dx > 0 and actual_dx < -10) or (expected_dx < 0 and actual_dx > 10):
                return True
        
        if abs(expected_dy) > 10:
            if (expected_dy > 0 and actual_dy < -10) or (expected_dy < 0 and actual_dy > 10):
                return True
        
        return False
    
    def _adjust_for_overshoot(self, test: CalibrationTest, error_x: float, error_y: float):
        """Ajusta parámetros cuando hay overshoot"""
        # Reducir smoothing
        old_smoothing = self.profile.smoothing
        self.profile.smoothing *= 0.7
        logger.info(f"Reducing smoothing: {old_smoothing:.3f} → {self.profile.smoothing:.3f}", "LEARNING")
        test.corrections_applied.append(f"smoothing:{self.profile.smoothing:.3f}")
        
        # Reducir scale si el error es muy grande
        if abs(error_x) > 50:
            self.profile.x_scale *= 0.9
            logger.info(f"Reducing X scale: {self.profile.x_scale:.3f}", "LEARNING")
            test.corrections_applied.append(f"x_scale:{self.profile.x_scale:.3f}")
        
        if abs(error_y) > 50:
            self.profile.y_scale *= 0.9
            logger.info(f"Reducing Y scale: {self.profile.y_scale:.3f}", "LEARNING")
            test.corrections_applied.append(f"y_scale:{self.profile.y_scale:.3f}")
    
    def _adjust_for_wrong_direction(self, test: CalibrationTest, 
                                   expected_dx: float, expected_dy: float,
                                   actual_dx: float, actual_dy: float):
        """Ajusta parámetros cuando la dirección es incorrecta"""
        # Detectar inversión de ejes
        if abs(expected_dx) > 10:
            if (expected_dx > 0 and actual_dx < 0) or (expected_dx < 0 and actual_dx > 0):
                self.profile.x_inverted = not self.profile.x_inverted
                logger.info(f"Inverting X axis: {self.profile.x_inverted}", "LEARNING")
                test.corrections_applied.append(f"x_inverted:{self.profile.x_inverted}")
        
        if abs(expected_dy) > 10:
            if (expected_dy > 0 and actual_dy < 0) or (expected_dy < 0 and actual_dy > 0):
                self.profile.y_inverted = not self.profile.y_inverted
                logger.info(f"Inverting Y axis: {self.profile.y_inverted}", "LEARNING")
                test.corrections_applied.append(f"y_inverted:{self.profile.y_inverted}")
    
    def _adjust_for_miss(self, test: CalibrationTest, error_x: float, error_y: float):
        """Ajusta parámetros cuando no llegó al objetivo"""
        # Si el error es consistente, ajustar scale
        if abs(error_x) > 20 and (test.actual_final_x - test.start_x) != 0:
            adjustment = (test.target_x - test.start_x) / (test.actual_final_x - test.start_x)
            self.profile.x_scale *= adjustment
            logger.info(f"Adjusting X scale: {self.profile.x_scale:.3f}", "LEARNING")
            test.corrections_applied.append(f"x_scale:{self.profile.x_scale:.3f}")
        
        if abs(error_y) > 20 and (test.actual_final_y - test.start_y) != 0:
            adjustment = (test.target_y - test.start_y) / (test.actual_final_y - test.start_y)
            self.profile.y_scale *= adjustment
            logger.info(f"Adjusting Y scale: {self.profile.y_scale:.3f}", "LEARNING")
            test.corrections_applied.append(f"y_scale:{self.profile.y_scale:.3f}")
    
    def _draw_calibration_result(self, test: CalibrationTest, success: bool):
        """Dibuja el resultado del test en la ventana de calibración"""
        if self.calibration_window is None:
            return
        
        # Limpiar
        self.calibration_window.fill(0)
        
        # Dibujar centro
        center = (400, 300)
        cv2.circle(self.calibration_window, center, 5, (255, 255, 255), -1)
        
        # Dibujar todos los tests previos
        for prev_test in self.test_history[-7:]:  # Últimos 7
            self._draw_test_on_window(prev_test, center, (100, 100, 100))
        
        # Dibujar test actual
        color = (0, 255, 0) if success else (0, 0, 255)
        self._draw_test_on_window(test, center, color)
        
        # Info de texto
        cv2.putText(self.calibration_window, f"Direction: {test.direction}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(self.calibration_window, f"Error: {test.final_error_px:.1f}px", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(self.calibration_window, f"Attempt: {test.attempts + 1}/{self.max_attempts_per_test}", 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        status = "SUCCESS" if success else "FAILED"
        cv2.putText(self.calibration_window, status, 
                   (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Progreso
        progress = f"Progress: {self.calibration_step}/{len(self.DIRECTIONS)}"
        cv2.putText(self.calibration_window, progress, 
                   (10, 580), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        cv2.imshow("Calibration", self.calibration_window)
        cv2.waitKey(1)
    
    def _draw_test_on_window(self, test: CalibrationTest, center: Tuple[int, int], color: Tuple[int, int, int]):
        """Dibuja un test en la ventana"""
        # Escalar para que quepa en la ventana
        scale = 150.0 / self.test_distance
        
        # Target
        target_x = int(center[0] + (test.target_x - test.start_x) * scale)
        target_y = int(center[1] + (test.target_y - test.start_y) * scale)
        cv2.circle(self.calibration_window, (target_x, target_y), 8, color, 2)
        
        # Actual
        actual_x = int(center[0] + (test.actual_final_x - test.start_x) * scale)
        actual_y = int(center[1] + (test.actual_final_y - test.start_y) * scale)
        cv2.circle(self.calibration_window, (actual_x, actual_y), 5, color, -1)
        
        # Línea de error
        cv2.line(self.calibration_window, (target_x, target_y), (actual_x, actual_y), color, 1)
    
    def _finalize_calibration(self):
        """Finaliza la calibración y calcula resultados finales"""
        logger.info("=" * 60, "LEARNING")
        logger.info("🎉 CALIBRATION COMPLETE", "LEARNING")
        logger.info("=" * 60, "LEARNING")
        
        # Calcular estadísticas
        successful_tests = sum(1 for t in self.test_history if t.success)
        total_tests = len(self.test_history)
        
        self.profile.confidence = successful_tests / total_tests if total_tests > 0 else 0.0
        self.profile.tests_completed = total_tests
        self.profile.sample_count = total_tests
        self.profile.last_updated = time.time()
        
        # Log resultados
        logger.info(f"Success rate: {successful_tests}/{total_tests} ({self.profile.confidence:.1%})", "LEARNING")
        logger.info(f"X-axis: {'INVERTED' if self.profile.x_inverted else 'NORMAL'} (scale: {self.profile.x_scale:.3f})", "LEARNING")
        logger.info(f"Y-axis: {'INVERTED' if self.profile.y_inverted else 'NORMAL'} (scale: {self.profile.y_scale:.3f})", "LEARNING")
        logger.info(f"Smoothing: {self.profile.smoothing:.3f}", "LEARNING")
        logger.info(f"Deadzone: {self.profile.deadzone}px", "LEARNING")
        
        # Análisis de problemas
        overshoot_count = sum(1 for t in self.test_history if t.overshoot)
        if overshoot_count > total_tests * 0.3:
            self.profile.notes.append("Frequent overshoot detected - reduced smoothing")
        
        if self.profile.confidence < 0.5:
            self.profile.notes.append("Low confidence - manual adjustment may be needed")
        
        if self.profile.notes:
            logger.warning("Notes:", "LEARNING")
            for note in self.profile.notes:
                logger.warning(f"  - {note}", "LEARNING")
        
        logger.info("=" * 60, "LEARNING")
        logger.info("Press F5 to SAVE this profile", "LEARNING")
        logger.info("=" * 60, "LEARNING")
        
        self.stop_calibration()
    
    def save_profile(self, name: str):
        """Guarda el perfil aprendido"""
        profile_path = self.profiles_dir / f"{name}.json"
        
        profile_dict = asdict(self.profile)
        
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile_dict, f, indent=2)
        
        logger.info(f"Learning profile saved: {profile_path}", "LEARNING")
    
    def load_profile(self, name: str) -> bool:
        """Carga un perfil guardado"""
        profile_path = self.profiles_dir / f"{name}.json"
        
        if not profile_path.exists():
            return False
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_dict = json.load(f)
            
            self.profile = LearningProfile(**profile_dict)
            logger.info(f"Learning profile loaded: {profile_path}", "LEARNING")
            return True
        except Exception as e:
            logger.error(f"Failed to load profile: {e}", "LEARNING")
            return False
    
    def apply_correction(self, dx: float, dy: float) -> Tuple[float, float]:
        """Aplica las correcciones aprendidas"""
        corrected_dx = dx * self.profile.x_scale
        corrected_dy = dy * self.profile.y_scale
        
        if self.profile.x_inverted:
            corrected_dx = -corrected_dx
        
        if self.profile.y_inverted:
            corrected_dy = -corrected_dy
        
        return corrected_dx, corrected_dy