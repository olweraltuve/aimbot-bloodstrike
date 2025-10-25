"""
Program_t Engine
=============
Motor principal que coordina detección, movimiento y trigger.
"""

import ctypes
import cv2
import math
import time
import torch
from pathlib import Path
import win32api
import numpy as np
from typing import Optional, Tuple
from ultralytics import YOLO

from lib.config.config_manager import config
from lib.capture.capture_manager import CaptureManager
from lib.input.mouse_manager import MouseManager
from lib.core.detection_engine import DetectionEngine, DetectionConfig, Target
from lib.core.movement_engine import MovementEngine, MovementConfig
from lib.utils.logger import logger
from lib.utils.performance_monitor import PerformanceMonitor
from lib.utils.mouse_learning import ActiveMouseLearningSystem, AdaptiveLearningSystem

class ProgramTEngine:
    """Motor principal del program_t"""
    
    def __init__(self, profile_name: Optional[str] = None):
        self.running = True
        self.enabled = True
        
        # Cargar perfil
        if profile_name:
            config.set_active_profile(profile_name)
        
        profile = config.get_profile()
        logger.info(f"Loading profile: {profile.get('name', 'Unknown')}", "ENGINE")
        
        # Inicializar componentes
        self._init_screen_params()
        self._init_capture()
        self._init_mouse()
        self._init_detection(profile)
        self._init_movement(profile)
        self._init_model()
        self._init_trigger_bot(profile)
        
        # Performance monitoring
        self.perf_monitor = PerformanceMonitor()
        self.debug_counter = 0
        
        # Learning system
        self.learning_system = ActiveMouseLearningSystem(
            mouse_manager=self.mouse_manager,
            screen_center=(self.screen_x, self.screen_y)
        )

        # NUEVO: Sistema de aprendizaje adaptativo
        self.adaptive_learning = AdaptiveLearningSystem(
            movement_engine=self.movement_engine,
            detection_engine=self.detection_engine,
            mouse_manager=self.mouse_manager
        )

        # NUEVO: Sistema de suspensión temporal
        from lib.input.suspend_key_manager import suspend_manager
        self.suspend_manager = suspend_manager
        self.suspend_manager.start_monitoring()

        logger.info("Suspend key system initialized", "ENGINE")

        self._load_learning_profile()
        
        logger.info("Program_t engine initialized successfully", "ENGINE")
        logger.info(f"Press F1 to toggle program_t, F2 to exit", "ENGINE")
    
    def _init_screen_params(self):
        """Inicializa parámetros de pantalla"""
        self.screen_res_x = ctypes.windll.user32.GetSystemMetrics(0)
        self.screen_res_y = ctypes.windll.user32.GetSystemMetrics(1)
        self.screen_x = int(self.screen_res_x / 2)
        self.screen_y = int(self.screen_res_y / 2)
        
        logger.info(
            f"Screen resolution: {self.screen_res_x}x{self.screen_res_y}", 
            "ENGINE"
        )
    
    def _init_capture(self):
        """Inicializa sistema de captura"""
        capture_method = config.get_user_setting('capture_method', 'bitblt')
        self.capture_manager = CaptureManager(capture_method)
        logger.info(
            f"Capture method: {self.capture_manager.get_method_name()}", 
            "ENGINE"
        )
    
    def _init_mouse(self):
        """Inicializa sistema de mouse"""
        mouse_method = config.get_user_setting('mouse_method', 'ddxoft')
        self.mouse_manager = MouseManager(mouse_method)
        logger.info(
            f"Mouse method: {self.mouse_manager.get_method_name()} "
            f"(Detection risk: {self.mouse_manager.get_detection_level()})", 
            "ENGINE"
        )
    
    def _init_detection(self, profile: dict):
        """Inicializa motor de detección"""
        det_config = profile.get('detection', {})
        self.detection_config = DetectionConfig(
            fov=det_config.get('fov', 350),
            confidence=det_config.get('confidence', 0.45),
            iou=det_config.get('iou', 0.45),
            aim_height_divisor=det_config.get('aim_height_divisor', 5),
            target_priority=profile.get('targeting', {}).get('target_priority', 'closest'),
            sticky_target=profile.get('targeting', {}).get('sticky_target', True),
            stickiness_pixels=profile.get('targeting', {}).get('stickiness_pixels', 60),
            persistence_frames=profile.get('targeting', {}).get('persistence_frames', 10)
        )
        self.detection_engine = DetectionEngine(self.detection_config)
        self.box_constant = self.detection_config.fov
    
    def _init_movement(self, profile: dict):
        """Inicializa motor de movimiento"""
        mov_config = profile.get('movement', {})
        self.movement_config = MovementConfig(
            smoothing=mov_config.get('smoothing', 0.7),
            deadzone_pixels=mov_config.get('deadzone_pixels', 2),
            max_move_speed=mov_config.get('max_move_speed', 100.0),
            acceleration_factor=mov_config.get('acceleration_factor', 0.8),
            mouse_delay=mov_config.get('mouse_delay', 0.0009),
            humanization_enabled=True
        )
        self.movement_engine = MovementEngine(self.movement_config)
    
    def _init_model(self):
        """Inicializa modelo YOLO"""
        model_path = 'lib/yoloe-11l-seg.pt'
        logger.info("=" * 60, "ENGINE")
        logger.info("LOADING AI MODEL", "ENGINE")
        logger.info("=" * 60, "ENGINE")
        logger.info(f"Model file: {model_path}", "ENGINE")
        logger.info("Model type: YOLOE (YOLO11-based) - Open Vocabulary Detection + Segmentation", "ENGINE")
        
        self.model = YOLO(model_path)
        
        # Poner el modelo en modo evaluación (necesario para get_text_pe)
        self.model.eval()
        
        logger.info(f"Model loaded successfully from: {model_path}", "ENGINE")
        
        # Configurar YOLOE para detectar SOLO humanoides sin texto/nombres encima
        # Prompts específicos que evitan detecciones con UI/texto
        detection_classes = [
            "person",
            "human",
            "human without description low visibility",
            "player model without UI elements or labels"
        ]
        # YOLOE requiere text embeddings como segundo parámetro
        text_embeddings = self.model.get_text_pe(detection_classes)
        self.model.set_classes(detection_classes, text_embeddings)
        
        logger.info("Detection classes configured:", "ENGINE")
        for i, cls in enumerate(detection_classes, 1):
            logger.info(f"  {i}. {cls}", "ENGINE")
        logger.info("=" * 60, "ENGINE")
        
        # Detectar CUDA
        self.device = 'cpu'
        self.cuda_compatible = False
        
        if torch.cuda.is_available():
            try:
                gpu_name = torch.cuda.get_device_name(0)
                compute_cap = torch.cuda.get_device_capability(0)
                
                logger.info(f"GPU detected: {gpu_name}", "ENGINE")
                logger.info(f"Compute capability: sm_{compute_cap[0]}{compute_cap[1]}", "ENGINE")
                
                # Test CUDA
                test_tensor = torch.tensor([1.0]).to('cuda')
                _ = test_tensor * 2
                
                self.device = 'cuda'
                self.cuda_compatible = True
                logger.info("CUDA acceleration ENABLED", "ENGINE")
                
            except Exception as e:
                logger.warning(f"CUDA test failed: {e}", "ENGINE")
                logger.info("Falling back to CPU mode", "ENGINE")
        else:
            logger.warning("CUDA not available, using CPU", "ENGINE")
    
    def _init_trigger_bot(self, profile: dict):
        """Inicializa trigger bot"""
        tb_config = profile.get('trigger_bot', {})
        self.trigger_enabled = tb_config.get('enabled', False)
        self.trigger_human_delay = tb_config.get('human_like_delay', True)
        self.trigger_min_delay = tb_config.get('min_shot_delay', 0.08)
        self.trigger_max_delay = tb_config.get('max_shot_delay', 0.15)
        self.trigger_burst_limit = tb_config.get('burst_limit', 3)
        self.trigger_burst_cooldown = tb_config.get('burst_cooldown', 0.3)
        
        self.last_shot_time = 0
        self.shot_cooldown = 0.1
        self.consecutive_shots = 0
        
        if self.trigger_enabled:
            logger.warning("Trigger bot is ENABLED", "ENGINE")
    
    def _load_learning_profile(self):
        """Carga el perfil de learning, priorizando el adaptativo por defecto."""
        profile_name = config.get_user_setting('active_profile', 'default')

        # Leer la preferencia del usuario desde user_config.json
        use_adaptive = config.get_user_setting('use_adaptive_learning_profile', True)
        
        if use_adaptive:
            # Priorizar perfil adaptativo
            adaptive_profile_name = f"learned_adaptive_{profile_name}"
            if self.learning_system.load_profile(adaptive_profile_name):
                logger.info(f"Loaded adaptive learning profile: {adaptive_profile_name}", "ENGINE")
                self._apply_learning_corrections()
                return  # Perfil adaptativo cargado con éxito
            else:
                logger.info(f"Adaptive profile '{adaptive_profile_name}' not found. Checking for legacy profile.", "ENGINE")

        # Fallback a perfil legacy si el adaptativo no se cargó o está deshabilitado
        legacy_profile_name = f"learned_{profile_name}"
        if self.learning_system.load_profile(legacy_profile_name):
            logger.info(f"Loaded legacy learning profile: {legacy_profile_name}", "ENGINE")
            self._apply_learning_corrections()
        else:
            logger.info(f"No learning profile found for '{profile_name}'. Using default values.", "ENGINE")

    def _apply_learning_corrections(self):
        """Aplica las correcciones del sistema de learning"""
        profile = self.learning_system.profile
        if profile.confidence > 0.5:
            logger.info(
                f"Applying learned corrections: X={profile.x_scale:.2f}{'(inv)' if profile.x_inverted else ''}, "
                f"Y={profile.y_scale:.2f}{'(inv)' if profile.y_inverted else ''}",
                "ENGINE"
            )
    
    def toggle_program_t(self):
        """Activa/desactiva el program_t"""
        self.enabled = not self.enabled
        status = "ENABLED" if self.enabled else "DISABLED"
        logger.info(f"Program_t {status}", "ENGINE")
        
        if not self.enabled:
            self.movement_engine.reset()
            self.detection_engine.reset()

    def start_adaptive_learning(self):
        """Inicia aprendizaje adaptativo con targets reales"""
        if self.adaptive_learning.active:
            logger.warning("Adaptive learning already active", "ENGINE")
            return
        
        # Deshabilitar program_t normal
        was_enabled = self.enabled
        self.enabled = False
        
        if was_enabled:
            logger.info("Program_t DISABLED for adaptive learning", "ENGINE")
        
        # Iniciar sistema adaptativo
        if not self.adaptive_learning.start():
            # Si falla, reactivar program_t si estaba activo
            self.enabled = was_enabled
    
    def start_calibration(self):
        """Inicia calibración activa"""
        if not self.learning_system.calibration_active:
            self.learning_system.start_calibration()
        else:
            logger.warning("Calibration already in progress", "ENGINE")
    
    def save_learning_profile(self):
        """Guarda el perfil aprendido del sistema activo (legacy o adaptativo)"""
        profile_name = config.get_user_setting('active_profile', 'default')
        
        # Si el sistema adaptativo se usó, guardar su perfil
        if self.adaptive_learning.cycles_history:
            learned_profile = self.adaptive_learning.get_learned_profile()
            profile_filename = f"learned_adaptive_{profile_name}.json"
            
            profiles_dir = Path("lib/data/learning_profiles")
            profiles_dir.mkdir(parents=True, exist_ok=True)
            profile_path = profiles_dir / profile_filename
            
            try:
                from dataclasses import asdict
                import json
                
                with open(profile_path, 'w', encoding='utf-8') as f:
                    json.dump(asdict(learned_profile), f, indent=2)
                
                logger.info(f"Adaptive learning profile saved: {profile_path}", "ENGINE")
            except Exception as e:
                logger.error(f"Failed to save adaptive profile: {e}", "ENGINE")
        else:
            # Si no, guardar el del sistema legacy
            learning_profile = f"learned_{profile_name}"
            self.learning_system.save_profile(learning_profile)
    
    def stop(self):
        """Detiene el program_t"""
        logger.info("Shutting down program_t engine...", "ENGINE")
        self.running = False
    
    def run(self):
        """Bucle principal del program_t"""
        # Calcular región de detección
        half_w = self.screen_res_x / 2
        half_h = self.screen_res_y / 2
        detection_box = {
            'left': int(half_w - self.box_constant // 2),
            'top': int(half_h - self.box_constant // 2),
            'width': int(self.box_constant),
            'height': int(self.box_constant)
        }
        
        logger.info("Starting main loop...", "ENGINE")
        
        try:
            while self.running:
                loop_start = time.perf_counter()
                
                # Si está en calibración, ejecutar paso de calibración
                if self.learning_system.calibration_active:
                    if not self.learning_system.run_calibration_step():
                        # Calibración terminada
                        self.learning_system.stop_calibration()
                    continue
                
                # Capturar pantalla
                frame = self._capture_frame(detection_box)
                if frame is None:
                    time.sleep(0.01)
                    continue
                
                # Detectar objetivos
                targets = self._detect_targets(frame)
                
                # Si estamos en modo de aprendizaje adaptativo
                if self.adaptive_learning.active and targets:
                    best_target = self.detection_engine.select_best_target(targets)
                    if best_target:
                        absolute_x = best_target.head_x + detection_box['left']
                        absolute_y = best_target.head_y + detection_box['top']
                        
                        # Procesar en el sistema adaptativo
                        continue_learning = self.adaptive_learning.process_target(
                            absolute_x, absolute_y,
                            self.screen_x, self.screen_y
                        )
                        
                        # Si terminó, reactivar program_t
                        if not continue_learning:
                            self.enabled = True
                            logger.info("Adaptive learning complete - Program_t RE-ENABLED", "ENGINE")
                    
                    # Continuar al siguiente frame sin procesar normalmente
                    self._render_frame(frame, loop_start)
                    self.debug_counter += 1
                    continue

                # Seleccionar mejor objetivo
                best_target = self.detection_engine.select_best_target(targets)
                
                # Procesar objetivo
                if best_target:
                    self._process_target(best_target, detection_box, frame)
                else:
                    self.movement_engine.reset()
                
                # Calcular FPS y mostrar
                self._render_frame(frame, loop_start)
                
                # Performance logging
                if self.debug_counter % 300 == 0:
                    self.perf_monitor.log_frame(
                        fps=1 / (time.perf_counter() - loop_start) if (time.perf_counter() - loop_start) > 0 else 0,
                        targets=len(targets),
                        locked=best_target is not None
                    )
                
                self.debug_counter += 1
                
                # Frame limiting
                elapsed = time.perf_counter() - loop_start
                if elapsed < 0.016:  # ~60 FPS cap
                    time.sleep(0.016 - elapsed)
                    
        except KeyboardInterrupt:
            logger.info("Interrupted by user", "ENGINE")
        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}", "ENGINE")
        finally:
            self.cleanup()
    
    def _capture_frame(self, detection_box: dict) -> Optional[np.ndarray]:
        """Captura un frame de la pantalla"""
        frame = self.capture_manager.capture(detection_box)
        
        if frame is None or frame.size == 0:
            if self.debug_counter % 30 == 0:
                logger.warning("Frame capture returned empty", "CAPTURE")
            return None
        
        # Convertir a BGR para OpenCV
        if frame.shape[2] == 4:  # BGRA
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        
        return frame
    
    def _detect_targets(self, frame: np.ndarray) -> list:
        """Detecta objetivos en el frame"""
        try:
            use_half = (self.device == 'cuda' and self.cuda_compatible)
            results = self.model.predict(
                source=frame,
                verbose=False,
                conf=self.detection_config.confidence,
                iou=self.detection_config.iou,
                half=use_half,
                device=self.device
            )
            
            if len(results) > 0 and len(results[0].boxes.xyxy) > 0:
                # Obtener clases y confidences detectadas
                boxes_data = results[0].boxes
                class_ids = boxes_data.cls.cpu().numpy() if len(boxes_data.cls) > 0 else []
                confidences = boxes_data.conf.cpu().numpy() if len(boxes_data.conf) > 0 else []
                
                targets = self.detection_engine.process_detections(
                    results[0].boxes.xyxy,
                    self.box_constant,
                    self.screen_x,
                    self.screen_y
                )
                
                # Agregar información de clase y confianza a cada target
                valid_targets = []
                rejected_targets = []
                
                for i, target in enumerate(targets):
                    if i < len(class_ids):
                        class_id = int(class_ids[i])
                        class_name = self.model.names.get(class_id, "unknown")
                        target.class_name = class_name
                        target.confidence = float(confidences[i]) if i < len(confidences) else 0.0
                    else:
                        target.class_name = "unknown"
                        target.confidence = 0.0
                    
                    # FILTRO: Confianza mínima del 56%
                    if target.confidence > 0.50:
                        valid_targets.append(target)
                    else:
                        rejected_targets.append(target)
                
                # Log de targets rechazados
                if rejected_targets and self.debug_counter % 30 == 0:
                    for target in rejected_targets:
                        conf_pct = int(target.confidence * 100)
                        logger.warning(
                            f"Detection rejected: {target.class_name} ({conf_pct}%) - "
                            f"Did not reach minimum confidence (56%)",
                            "DETECT"
                        )
                
                # Debug: Mostrar qué clases válidas detectó YOLO-World
                if self.debug_counter % 30 == 0 and len(valid_targets) > 0:
                    classes_detected = [f"{t.class_name} ({t.confidence*100:.0f}%)" for t in valid_targets]
                    logger.info(f"Valid targets: {len(valid_targets)} - {', '.join(classes_detected)}", "DETECT")
                
                return valid_targets
            
            return []
            
        except Exception as e:
            if self.debug_counter % 30 == 0:
                logger.error(f"Detection failed: {e}", "DETECT")
            return []
    
    def _process_target(
        self, 
        target: Target, 
        detection_box: dict, 
        frame: np.ndarray
    ):
        """Procesa un objetivo detectado"""
        # Calcular coordenadas absolutas
        absolute_x = target.head_x + detection_box['left']
        absolute_y = target.head_y + detection_box['top']
        
        # Obtener posición actual del cursor
        try:
            current_x, current_y = win32api.GetCursorPos()
            cursor_before = (current_x, current_y)
        except:
            current_x, current_y = self.screen_x, self.screen_y
            cursor_before = None
        
        # Verificar si está locked
        is_locked = self.detection_engine.is_locked_on_target(
            absolute_x, absolute_y,
            self.screen_x, self.screen_y,
            config.get_value('targeting', 'lock_threshold_pixels', default=15)
        )
        
        # NUEVO: Verificar si está suspendido
        if self.suspend_manager.is_suspended():
            # No mover, pero seguir dibujando y detectando
            self._draw_target(frame, target, is_locked)
            
            # Mostrar indicador de suspensión
            cv2.putText(
                frame, "SUSPENDED",
                (5, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 165, 255), 2
            )
            return  # Salir sin mover
        
        # Dibujar en frame
        self._draw_target(frame, target, is_locked)
        
        # Mover si está habilitado y no locked
        if self.enabled and not is_locked:
            movement = self.movement_engine.calculate_movement(
                current_x, current_y,
                absolute_x, absolute_y
            )
            
            if movement:
                dx, dy = movement
                
                # Aplicar correcciones del learning system
                if self.learning_system.profile.confidence > 0.3:
                    dx, dy = self.learning_system.apply_correction(dx, dy)
                
                # Aplicar smoothing del perfil aprendido
                adjusted_smoothing = self.learning_system.profile.smoothing
                dx *= adjusted_smoothing
                dy *= adjusted_smoothing
                
                # Mover mouse
                self.mouse_manager.move(dx, dy, self.movement_config.mouse_delay)
        
        # Trigger bot
        if is_locked and self.trigger_enabled:
            self._handle_trigger(absolute_x, absolute_y)
    
    def _draw_target(self, frame: np.ndarray, target: Target, is_locked: bool):
        """Dibuja el objetivo en el frame"""
        x1, y1, x2, y2 = target.box
        
        # Color según estado
        color = (115, 244, 113) if is_locked else (115, 113, 244)
        
        # Caja de detección
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Punto de mira (cabeza)
        cv2.circle(frame, (target.head_x, target.head_y), 5, color, -1)
        
        # Línea al centro
        center = self.box_constant // 2
        cv2.line(
            frame, 
            (target.head_x, target.head_y), 
            (center, center), 
            (244, 242, 113), 
            2
        )
        
        # Cruz en el centro
        cv2.line(frame, (center - 10, center), (center + 10, center), (0, 0, 255), 2)
        cv2.line(frame, (center, center - 10), (center, center + 10), (0, 0, 255), 2)
        
        # Texto de estado + clase detectada + porcentaje
        status_text = "LOCKED" if is_locked else "TARGETING"
        confidence_pct = int(target.confidence * 100)
        class_text = f"{status_text}: {target.class_name} ({confidence_pct}%)"
        
        cv2.putText(
            frame, class_text, 
            (x1 + 5, y1 - 5), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.5, color, 2
        )
        
    
    def _handle_trigger(self, x: int, y: int):
        """Maneja el trigger bot"""
        current_time = time.perf_counter()
        
        # No disparar si ya estamos disparando manualmente
        if self._is_shooting():
            return
        
        # Verificar cooldown
        if (current_time - self.last_shot_time) < self.shot_cooldown:
            return
        
        # Verificar límite de ráfaga
        if self.consecutive_shots >= self.trigger_burst_limit:
            self.consecutive_shots = 0
            self.shot_cooldown = self.trigger_burst_cooldown
            return
        
        # Disparar
        self.mouse_manager.click('left')
        self.last_shot_time = current_time
        self.consecutive_shots += 1
        
        # Calcular próximo cooldown
        if self.trigger_human_delay:
            import random
            self.shot_cooldown = random.uniform(
                self.trigger_min_delay,
                self.trigger_max_delay
            )
        else:
            self.shot_cooldown = 0.1
    
    def _is_shooting(self) -> bool:
        """Verifica si el usuario está disparando"""
        return win32api.GetKeyState(0x01) in (-127, -128)
    
    def _render_frame(self, frame: np.ndarray, loop_start: float):
        """Renderiza el frame con información"""
        fps = int(1 / (time.perf_counter() - loop_start)) if (time.perf_counter() - loop_start) > 0 else 0
        
        # FPS counter
        cv2.putText(
            frame, f"FPS: {fps}", 
            (5, 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, (113, 116, 244), 2
        )
        
        # Estado del program_t
        status_text = "ENABLED" if self.enabled else "DISABLED"
        status_color = (0, 255, 0) if self.enabled else (0, 0, 255)
        cv2.putText(
            frame, f"Program_t: {status_text}", 
            (5, 60), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7, status_color, 2
        )
        
        # Mostrar frame
        try:
            cv2.imshow("AI Program_t - Lunar LITE", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.running = False
        except Exception as e:
            if self.debug_counter % 30 == 0:
                logger.warning(f"OpenCV display error: {e}", "RENDER")
    
    def cleanup(self):
        """Limpia recursos"""
        logger.info("Cleaning up resources...", "ENGINE")
        
        try:
            # Detener monitoreo de suspensión
            self.suspend_manager.stop_monitoring()
            
            self.capture_manager.cleanup()
            self.mouse_manager.cleanup()
            cv2.destroyAllWindows()
            logger.info("Cleanup completed successfully", "ENGINE")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", "ENGINE")