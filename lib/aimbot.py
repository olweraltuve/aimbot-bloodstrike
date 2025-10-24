import ctypes
import cv2
import json
import math
import mss
import os
import random
import sys
import time
import torch
import numpy as np
import win32api
import win32con
import win32gui
import win32ui
import threading
from termcolor import colored
from ultralytics import YOLO

# If you're a skid and you know it clap your hands 👏👏

# Auto Screen Resolution
screensize = {'X': ctypes.windll.user32.GetSystemMetrics(0), 'Y': ctypes.windll.user32.GetSystemMetrics(1)}

# If you use stretched res, hardcode the X and Y. For example: screen_res_x = 1234
screen_res_x = screensize['X']
screen_res_y = screensize['Y']

# Divide screen_res by 2
# No need to change this
screen_x = int(screen_res_x / 2)
screen_y = int(screen_res_y / 2)

aim_height = 5 # The lower the number, the higher the aim_height. For example: 2 would be the head and 100 would be the feet.

fov = 350

confidence = 0.45 # How confident the AI needs to be for it to lock on to the player. Default is 45%

use_trigger_bot = True # Will shoot if crosshair is locked on the player

# Anti-cheat avoidance settings
human_like_delay = True  # Add random delays to mimic human behavior
min_shot_delay = 0.08    # Minimum delay between shots (seconds)
max_shot_delay = 0.15    # Maximum delay between shots (seconds)

# Try to load config from mouse_config.py (now handles both mouse and capture), fallback to defaults
try:
    from lib.config.mouse_config import MOUSE_METHOD
    from lib.config.mouse_config import MOUSE_DELAY as CONFIG_MOUSE_DELAY
    from lib.config.mouse_config import CAPTURE_METHOD as CONFIG_CAPTURE_METHOD
    from lib.config.mouse_config import MOUSE_SMOOTHING
    from lib.config.mouse_config import TARGETING_DEADZONE_PIXELS
    mouse_method = MOUSE_METHOD
    config_mouse_delay = CONFIG_MOUSE_DELAY
    capture_method = CONFIG_CAPTURE_METHOD
except ImportError:
    mouse_methods = ['win32', 'ddxoft']
    mouse_method = mouse_methods[1]  # 1 is ddxoft (less detectable). 0 is win32.
    config_mouse_delay = 0.0009
    capture_method = 'bitblt'  # Default to bitblt for fullscreen compatibility
    MOUSE_SMOOTHING = 0.2 # Default smoothing factor if not in config
    TARGETING_DEADZONE_PIXELS = 3 # Default deadzone if not in config
    TARGET_STICKINESS_PIXELS = 60
    LOCK_PERSISTENCE_FRAMES = 10

PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class Aimbot:
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    screen = mss.mss()
    pixel_increment = 1 #controls how many pixels the mouse moves for each relative movement
    with open("lib/config/config.json", encoding='utf-8') as f:
        sens_config = json.load(f)
    aimbot_status = colored("ENABLED", 'green')
    mouse_dll = None
    
    # BitBlt capture resources (initialized later if needed)
    desktop_dc = None
    mem_dc = None
    bitmap = None

    def __init__(self, box_constant = fov, collect_data = False, mouse_delay = None):
        #controls the initial centered box width and height of the "Lunar Vision" window
        self.box_constant = box_constant #controls the size of the detection box (equaling the width and height)
        
        # Thread safety lock for screen operations
        self.screen_lock = threading.Lock()
        self.running = True
        self.last_shot_time = 0
        self.shot_cooldown = 0.1  # Minimum 100ms between shots to prevent freezing
        self.consecutive_shots = 0
        self.max_consecutive_shots = 3  # Limit burst firing to prevent detection

        print("[INFO] Loading the neural network model")
            
        self.debug_counter = 0
        self.movement_path = []
        self.model = YOLO('lib/best.pt')
        
        # Check CUDA availability and compatibility
        self.device = 'cpu'  # Default to CPU
        self.cuda_compatible = False
        
        if torch.cuda.is_available():
            try:
                # Get GPU info first
                gpu_name = torch.cuda.get_device_name(0)
                compute_capability = torch.cuda.get_device_capability(0)
                compute_capability_str = f"sm_{compute_capability[0]}{compute_capability[1]}"
                
                print(colored(f"[INFO] Detected GPU: {gpu_name}", "yellow"))
                print(colored(f"[INFO] Compute capability: {compute_capability_str}", "yellow"))
                
                # Check for RTX 5060 (sm_120) compatibility
                if compute_capability >= (12, 0):
                    print(colored("[!] RTX 5060 DETECTED - CUDA compatibility check...", "yellow"))
                    try:
                        # Test CUDA functionality
                        device = torch.device('cuda')
                        test_tensor = torch.tensor([1.0]).to(device)
                        result = test_tensor * 2
                        self.device = 'cuda'
                        self.cuda_compatible = True
                        print(colored("CUDA ACCELERATION [ENABLED]", "green"))
                        print(colored(f"[SUCCESS] RTX 5060 is working with CUDA!", "green"))
                    except Exception as e:
                        print(colored(f"[!] CUDA TEST FAILED: {e}", "red"))
                        print(colored("[!] RTX 5060 requires PyTorch nightly build for full support", "yellow"))
                        print(colored("[!] Falling back to CPU mode for now", "yellow"))
                        self.device = 'cpu'
                        self.cuda_compatible = False
                else:
                    # For other GPUs
                    try:
                        device = torch.device('cuda')
                        test_tensor = torch.tensor([1.0]).to(device)
                        self.device = 'cuda'
                        self.cuda_compatible = True
                        print(colored("CUDA ACCELERATION [ENABLED]", "green"))
                    except Exception as e:
                        print(colored(f"[!] CUDA INITIALIZATION FAILED: {e}", "red"))
                        print(colored("[!] Falling back to CPU mode", "red"))
                        self.device = 'cpu'
            except Exception as e:
                print(colored(f"[!] CUDA DETECTION FAILED: {e}", "red"))
                print(colored("[!] Falling back to CPU mode", "red"))
                self.device = 'cpu'
        else:
            print(colored("[!] CUDA ACCELERATION IS UNAVAILABLE", "red"))
            print(colored("[!] Running in CPU mode - performance may be limited", "yellow"))
        
        if self.device == 'cpu':
            print(colored("[INFO] Running in CPU mode - consider upgrading PyTorch for RTX 5060 support", "yellow"))

        self.conf = confidence # base confidence threshold (or base detection (0-1)
        self.iou = 0.45 # NMS IoU (0-1)
        self.collect_data = collect_data
        self.mouse_delay = mouse_delay if mouse_delay is not None else config_mouse_delay
        self.mouse_method = mouse_method
        self.capture_method = capture_method
        self.failed_captures = 0  # Track failed captures to auto-switch methods

        # ==================== INICIO DE LA SOLUCIÓN ====================
        # Mouse method initialization with robust error handling
        if self.mouse_method.lower() == 'ddxoft':
            try:
                # SOLUCIÓN 1: Ruta robusta a la DLL.
                # Esto construye la ruta a la DLL basándose en la ubicación de este script,
                # no desde donde se ejecuta el comando. Evita errores de "archivo no encontrado".
                script_dir = os.path.dirname(os.path.abspath(__file__))
                dll_path = os.path.join(script_dir, "mouse", "dd40605x64.dll")

                # SOLUCIÓN 2: Verificación explícita de la existencia del archivo.
                if not os.path.exists(dll_path):
                    print(colored(f"[ERROR] La DLL de ddxoft no se encuentra en la ruta esperada: {dll_path}", "red"))
                    print(colored("[INFO] Cambiando al método de mouse 'win32'. Este puede no funcionar en pantalla completa.", "yellow"))
                    self.mouse_method = 'win32'
                else:
                    Aimbot.mouse_dll = ctypes.WinDLL(dll_path)
                    time.sleep(1)

                    Aimbot.mouse_dll.DD_btn.argtypes = [ctypes.c_int]
                    Aimbot.mouse_dll.DD_btn.restype = ctypes.c_int

                    # SOLUCIÓN ROBUSTA: Definir explícitamente los tipos de argumentos para DD_movR.
                    # Sin esto, ctypes puede pasar incorrectamente los enteros (especialmente los negativos) a la DLL.
                    Aimbot.mouse_dll.DD_movR.argtypes = [ctypes.c_int, ctypes.c_int]
                    Aimbot.mouse_dll.DD_movR.restype = ctypes.c_int
                    
                    # NUEVO: Verificar función de obtener estado del driver
                    Aimbot.mouse_dll.DD_key.argtypes = [ctypes.c_int, ctypes.c_int]
                    Aimbot.mouse_dll.DD_key.restype = ctypes.c_int
                    
                    # SOLUCIÓN 3: Inicialización del driver y mensaje de error mejorado.
                    init_code = Aimbot.mouse_dll.DD_btn(0)
                    if init_code != 1:
                        print(colored(f'ERROR: Fallo al inicializar el driver ddxoft (Código: {init_code}).', "red"))
                        print(colored('SOLUCIÓN: ¡ASEGÚRATE DE EJECUTAR EL SCRIPT COMO ADMINISTRADOR!', "cyan"))
                        print(colored("Cambiando al método 'win32'. Este puede no funcionar en pantalla completa.", "yellow"))
                        self.mouse_method = 'win32'
                    else:
                        print(colored('Driver ddxoft cargado e inicializado con éxito.', 'green'))
                        
                        # NUEVO: Test de movimiento inicial
                        test_result = Aimbot.mouse_dll.DD_movR(1, 1)
                        print(colored(f'[DEBUG] Test de movimiento DDXoft: código retorno = {test_result}', 'cyan'))
            except Exception as e:
                print(colored(f"[ERROR] No se pudo cargar la DLL de ddxoft: {e}", "red"))
                print(colored("SOLUCIÓN: Asegúrate que tu antivirus no la esté bloqueando y ejecuta como administrador.", "cyan"))
                print(colored("Cambiando al método 'win32'.", "yellow"))
                self.mouse_method = 'win32'
        # ===================== FIN DE LA SOLUCIÓN =====================
        
        if self.mouse_method.lower() == 'win32':
            print(colored(f'[INFO] Usando el método Win32 (SendInput) para el movimiento del mouse.', 'yellow'))
            print(colored(f'[AVISO] Este método es más detectable y puede no funcionar en juegos a pantalla completa.', 'red'))
        
        # Initialize BitBlt if needed
        if self.capture_method.lower() in ['bitblt', 'auto']:
            self.init_bitblt()
            print(colored(f'[INFO] Using capture method: {self.capture_method.upper()} (works with fullscreen games).', 'green'))
        else:
            print(colored(f'[INFO] Using capture method: {self.capture_method.upper()} (faster, but may not work with fullscreen games).', 'yellow'))
        
        print(colored(f'[INFO] Using mouse method: {self.mouse_method.upper()}', 'cyan'))
        
        print("\n[INFO] PRESIONA 'F1' PARA ACTIVAR/DESACTIVAR AIMBOT\n[INFO] PRESIONA 'F2' PARA SALIR")

    # Ahora se pasa la instancia para poder limpiar la ruta de movimiento fantasma
    def update_status_aimbot():
        if Aimbot.aimbot_status == colored("ENABLED", 'green'):
            Aimbot.aimbot_status = colored("DISABLED", 'red')
            # SOLUCIÓN MOVIMIENTO FANTASMA: Si hay una instancia activa, limpiar su ruta de movimiento.
            if 'lunar' in sys.modules['__main__'].__dict__:
                sys.modules['__main__'].__dict__['lunar'].movement_path.clear()
        else:
            Aimbot.aimbot_status = colored("ENABLED", 'green')
        # La impresión del estado se gestiona ahora de forma limpia dentro del bucle principal
    
    def init_bitblt(self):
        """Initialize BitBlt screen capture (works with fullscreen games)"""
        try:
            # Get desktop window
            hwnd = win32gui.GetDesktopWindow()
            
            # Get device contexts
            Aimbot.desktop_dc = win32gui.GetWindowDC(hwnd)
            Aimbot.mem_dc = win32ui.CreateDCFromHandle(Aimbot.desktop_dc)
            
            print("[INFO] Captura de pantalla BitBlt inicializada con éxito.")
        except Exception as e:
            print(f"[WARNING] Fallo al inicializar BitBlt: {e}")
            print("[INFO] Cambiando al método de captura MSS.")
            self.capture_method = 'mss'
    
    def capture_screen_bitblt(self, region):
        """Capture screen using BitBlt (compatible with fullscreen games)"""
        try:
            left, top, width, height = region['left'], region['top'], region['width'], region['height']
            
            # Create compatible DC and bitmap
            save_dc = Aimbot.mem_dc.CreateCompatibleDC()
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(Aimbot.mem_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            
            # Copy screen to bitmap using BitBlt
            save_dc.BitBlt((0, 0), (width, height), Aimbot.mem_dc, (left, top), win32con.SRCCOPY)
            
            # Convert to numpy array
            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)
            img = np.frombuffer(bmpstr, dtype=np.uint8).reshape((height, width, 4))
            
            # Clean up
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            
            return img
        except Exception as e:
            if self.debug_counter % 30 == 0:
                print(f"[ERROR] Captura con BitBlt falló: {e}")
            return None

    def left_click(self):
        try:
            if self.mouse_method.lower() == 'ddxoft':
                Aimbot.mouse_dll.DD_btn(1)
                time.sleep(0.001)
                Aimbot.mouse_dll.DD_btn(2)
            elif self.mouse_method.lower() == 'win32':
                ctypes.windll.user32.mouse_event(0x0002) #left mouse down
                time.sleep(0.0001)
                ctypes.windll.user32.mouse_event(0x0004) #left mouse up
        except Exception as e:
            print(f"[WARNING] Click izquierdo falló: {e}")

    def sleep(duration, get_now = time.perf_counter):
        """Sleep with high precision"""
        if duration == 0:
            return
        
        # Para delays muy cortos, usar busy-wait para precisión
        if duration > 0.005:
            # Para delays largos, usar time.sleep normal
            time.sleep(duration)
        else:
            now = get_now()
            end = now + duration
            while now < end:
                now = get_now()

    def is_aimbot_enabled():
        return Aimbot.aimbot_status == colored("ENABLED", 'green')

    def is_shooting():
        return win32api.GetKeyState(0x01) in (-127, -128)
    
    def is_targeted():
        return win32api.GetKeyState(0x02) in (-127, -128)

    def is_target_locked(x, y):
        #plus/minus 15 pixel threshold for better target acquisition
        threshold = 15
        return screen_x - threshold <= x <= screen_x + threshold and screen_y - threshold <= y <= screen_y + threshold
    
    def get_cursor_position(self):
        """Get current cursor position for verification"""
        try:
            x, y = win32api.GetCursorPos()
            return (x, y)
        except:
            return None
    
    def verify_mouse_movement(self, expected_dx, expected_dy, cursor_before, cursor_after):
        """Verify if mouse actually moved"""
        if cursor_before is None or cursor_after is None:
            return False, "No se pudo obtener posición del cursor"
        
        actual_dx = cursor_after[0] - cursor_before[0]
        actual_dy = cursor_after[1] - cursor_before[1]
        
        # Tolerancia de ±2 píxeles
        tolerance = 2
        dx_ok = abs(actual_dx - expected_dx) <= tolerance
        dy_ok = abs(actual_dy - expected_dy) <= tolerance
        
        if dx_ok and dy_ok:
            return True, f"OK: esperado({expected_dx},{expected_dy}) vs real({actual_dx},{actual_dy})"
        else:
            return False, f"FALLO: esperado({expected_dx},{expected_dy}) vs real({actual_dx},{actual_dy})"

    def plan_smooth_movement(self, target_x, target_y):
        """
        SOLUCIÓN CORREGIDA: Ahora calcula el movimiento respecto al CENTRO DE PANTALLA,
        no respecto al cursor. Esto es crítico para juegos con pointer-lock.
        
        Args:
            target_x: Coordenada X absoluta del objetivo en pantalla
            target_y: Coordenada Y absoluta del objetivo en pantalla
        """
        # SOLUCIÓN CLAVE: Calcular error respecto al CENTRO de la pantalla
        # NO respecto al cursor (GetCursorPos)
        error_x = target_x - screen_x
        error_y = target_y - screen_y
        dist = math.hypot(error_x, error_y)
        
        # Telemetría para debugging
        if self.debug_counter % 10 == 0:
            print(colored(
                f"[TELEMETRY] ErrCentro=({error_x:.1f},{error_y:.1f}), "
                f"DistCentro={dist:.1f}px",
                "cyan"
            ))

        # SOLUCIÓN 1: Dead-zone aplicada al error AL CENTRO (no al cursor)
        if dist < TARGETING_DEADZONE_PIXELS:
            self.movement_path = []
            if self.debug_counter % 30 == 0:
                print(colored(
                    f"[DEBUG] Dentro de dead-zone ({TARGETING_DEADZONE_PIXELS}px). "
                    f"No se requiere movimiento.",
                    "green"
                ))
            return
        
        # SOLUCIÓN 2: Calcular delta basado en el error al centro
        # Aplicar suavizado para movimiento natural
        delta_x = error_x * MOUSE_SMOOTHING
        delta_y = error_y * MOUSE_SMOOTHING
        
        # Acumular en float para precisión, redondear solo al aplicar
        self.movement_path = [(delta_x, delta_y)]
        
        # Telemetría del delta calculado
        if self.debug_counter % 10 == 0:
            print(colored(
                f"[TELEMETRY] DeltaCalculado=({delta_x:.2f},{delta_y:.2f}), "
                f"Smoothing={MOUSE_SMOOTHING}",
                "yellow"
            ))

    def move_crosshair(self, x, y):
        """
        Executes the next step in a pre-planned movement path.
        SOLUCIÓN: Redondea solo en el momento de inyectar para máxima precisión.
        """
        if not self.movement_path:
            return

        # Pop the next movement step from the path
        move_x, move_y = self.movement_path.pop(0)

        # SOLUCIÓN: Redondear solo aquí, justo antes de inyectar
        rounded_x = round(move_x)
        rounded_y = round(move_y)
        
        # Si el movimiento redondeado es 0, no hacer nada
        if rounded_x == 0 and rounded_y == 0:
            if self.debug_counter % 30 == 0:
                print(colored(
                    f"[DEBUG] Delta muy pequeño post-redondeo: "
                    f"original=({move_x:.2f},{move_y:.2f}) -> (0,0). Skipped.",
                    "yellow"
                ))
            return

        # Ejecutar el movimiento
        if self.mouse_method.lower() == 'ddxoft':
            result = Aimbot.mouse_dll.DD_movR(rounded_x, rounded_y)
            if self.debug_counter % 30 == 0:
                print(colored(
                    f"[DEBUG] DDXoft.DD_movR({rounded_x},{rounded_y}) -> ret={result}",
                    "cyan"
                ))
        elif self.mouse_method.lower() == 'win32':
            Aimbot.ii_.mi = MouseInput(
                rounded_x, rounded_y, 0, 0x0001, 0,
                ctypes.pointer(Aimbot.extra)
            )
            command = Input(ctypes.c_ulong(0), Aimbot.ii_)
            result = ctypes.windll.user32.SendInput(
                1, ctypes.pointer(command), ctypes.sizeof(command)
            )
            if self.debug_counter % 30 == 0:
                print(colored(
                    f"[DEBUG] Win32.SendInput({rounded_x},{rounded_y}) -> ret={result}",
                    "cyan"
                ))
        
        # Telemetría de movimiento aplicado
        if self.debug_counter % 10 == 0:
            print(colored(
                f"[TELEMETRY] DeltaEnviado=({rounded_x},{rounded_y}), "
                f"PathStepsLeft={len(self.movement_path)}",
                "green"
            ))
        
        Aimbot.sleep(self.mouse_delay)
    
    def stop(self):
        """Señaliza al bucle principal que debe detenerse."""
        print("\n[INFO] F2 PRESIONADO. CERRANDO DE FORMA SEGURA...")
        self.running = False
    
    def start(self):
        """
        Inicia el bucle principal del aimbot.
        SOLUCIÓN DE CIERRE: Ahora está envuelto en un try/finally para garantizar
        que la limpieza se ejecute en el hilo principal, evitando errores.
        """
        print(f"[INFO] Iniciando captura de pantalla. Estado inicial: {Aimbot.aimbot_status}")

        half_screen_width = ctypes.windll.user32.GetSystemMetrics(0)/2
        half_screen_height = ctypes.windll.user32.GetSystemMetrics(1)/2
        detection_box = {'left': int(half_screen_width - self.box_constant//2), #x1 coord (for top-left corner of the box)
                          'top': int(half_screen_height - self.box_constant//2), #y1 coord (for top-left corner of the box)
                          'width': int(self.box_constant),  #width of the box
                          'height': int(self.box_constant)} #height of the box

        try:
            while self.running:
                start_time = time.perf_counter()
                frame = None
                try:
                    with self.screen_lock:
                        if self.capture_method.lower() == 'bitblt':
                            frame = self.capture_screen_bitblt(detection_box)
                        elif self.capture_method.lower() == 'mss':
                            initial_frame = Aimbot.screen.grab(detection_box)
                            frame = np.array(initial_frame, dtype=np.uint8)
                        elif self.capture_method.lower() == 'auto':
                            frame = self.capture_screen_bitblt(detection_box)
                            if frame is None or frame.size == 0:
                                initial_frame = Aimbot.screen.grab(detection_box)
                                frame = np.array(initial_frame, dtype=np.uint8)
                    
                    if self.debug_counter % 30 == 0: # Print debug info every 30 frames
                        if frame is not None and frame.size > 0:
                            # Check if frame is mostly black, which indicates a capture issue
                            is_black = "Yes" if np.mean(frame) < 10 else "No"
                            print(colored(f"[DEBUG] CAPTURE: Method='{self.capture_method}', Shape={frame.shape}, All Black?={is_black}", "cyan"))
                        else:
                            print(colored(f"[DEBUG] CAPTURE: Frame capture FAILED via '{self.capture_method}'.", "red"))
                    
                    if frame is None or frame.size == 0:
                        self.failed_captures += 1
                        if self.failed_captures % 30 == 0:
                            print(f"[WARNING] La captura de pantalla devolvió un frame vacío ({self.failed_captures} fallos)")
                            print("[INFO] Asegúrate que el juego está en modo VENTANA SIN BORDES o prueba otro método de captura.")
                        continue
                    else:
                        if self.failed_captures > 0:
                            self.failed_captures = 0
                    
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                except Exception as e:
                    self.failed_captures += 1
                    if self.failed_captures % 30 == 0:
                        print(f"[ERROR] La captura de pantalla falló: {e}")
                        print(f"[INFO] Fallos de captura: {self.failed_captures}")
                    time.sleep(0.1)
                    continue
                
                try:
                    use_half = (self.device == 'cuda' and self.cuda_compatible)
                    boxes = self.model.predict(source=frame, verbose=False, conf=self.conf, iou=self.iou,
                                             half=use_half, device=self.device)
                    result = boxes[0]
                    
                    if self.debug_counter % 30 == 0:
                        box_count = len(result.boxes)
                        color = "green" if box_count > 0 else "yellow"
                        # SOLUCIÓN: Mostrar el estado del aimbot de forma estática junto con los logs de depuración
                        print(f"[INFO] AIMBOT STATUS: {Aimbot.aimbot_status}")
                        print(colored(f"[DEBUG] PREDICT: Found {box_count} potential targets.", color))
                except Exception as e:
                    print(f"[WARNING] La predicción de YOLO falló: {e}")
                    if self.device == 'cuda':
                        print("[INFO] La predicción con CUDA falló, cambiando a CPU.")
                        try:
                            boxes = self.model.predict(source=frame, verbose=False, conf=self.conf, iou=self.iou,
                                                     half=False, device='cpu')
                            result = boxes[0]
                            self.device = 'cpu'
                            self.cuda_compatible = False
                            print(colored("[INFO] Se ha cambiado a modo CPU con éxito.", "yellow"))
                        except Exception as e2:
                            print(f"[ERROR] La predicción con CPU también falló: {e2}")
                            continue
                    else:
                        continue
                if len(result.boxes.xyxy) != 0: #player detected
                    # This entire block now only runs if a target is found in the current frame.
                    detections = [{
                        "box": tuple(map(int, box)),
                        "relative_head_X": int((box[0] + box[2]) / 2),
                        "relative_head_Y": int((box[1] + box[3]) / 2 - (box[3] - box[1]) / aim_height),
                        "crosshair_dist": math.dist(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), (self.box_constant / 2, self.box_constant / 2))
                    } for box in result.boxes.xyxy]

                    best_target = self.get_best_target(detections)

                    if best_target:
                        # All logic for drawing, planning, and moving is now safely inside this block.
                        x1, y1, x2, y2 = best_target["box"]
                        head_x, head_y = best_target["relative_head_X"], best_target["relative_head_Y"]
                        
                        # 🔍 DIBUJA LA CAJA DE DETECCIÓN COMPLETA
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Verde
                        
                        # 🎯 DIBUJA EL PUNTO DE MIRA CALCULADO
                        cv2.circle(frame, (head_x, head_y), 5, (115, 244, 113), -1)
                        
                        # 📏 DIBUJA LA LÍNEA DESDE EL CENTRO
                        cv2.line(frame, (head_x, head_y), (self.box_constant//2, self.box_constant//2), (244, 242, 113), 2)
                        
                        # ➕ DIBUJA UNA CRUZ EN EL CENTRO DE LA PANTALLA
                        center = self.box_constant // 2
                        cv2.line(frame, (center - 10, center), (center + 10, center), (0, 0, 255), 2)  # Rojo horizontal
                        cv2.line(frame, (center, center - 10), (center, center + 10), (0, 0, 255), 2)  # Rojo vertical

                        absolute_head_X = head_x + detection_box['left']
                        absolute_head_Y = head_y + detection_box['top']
                        
                        abs_coords_str = f"Abs Coords=({absolute_head_X},{absolute_head_Y})"
                        rel_coords_str = f"Rel Coords=({head_x},{head_y})"
                        
                        # SOLUCIÓN: Calcular distancia AL CENTRO, no al cursor
                        dist_to_center = math.hypot(
                            absolute_head_X - screen_x,
                            absolute_head_Y - screen_y
                        )
                        
                        if self.debug_counter % 10 == 0:
                            # Mostrar la distancia AL CENTRO (métrica correcta)
                            print(colored(
                                f"[DEBUG] TARGET: DistToCENTER={dist_to_center:.1f}px, "
                                f"{rel_coords_str}, {abs_coords_str}",
                                "green"
                            ))
                        
                        is_locked_on_target = Aimbot.is_target_locked(absolute_head_X, absolute_head_Y)

                        if Aimbot.is_aimbot_enabled() and not is_locked_on_target:
                            # SOLUCIÓN: Planificar movimiento con coordenadas absolutas
                            self.plan_smooth_movement(absolute_head_X, absolute_head_Y)

                        if is_locked_on_target:
                            # Limpiar path cuando está locked
                            self.movement_path.clear()
                            current_time = time.perf_counter()
                            
                            if self.debug_counter % 30 == 0:
                                print(colored("[DEBUG] TARGET LOCKED! No movement needed.", "green"))
                            
                            if use_trigger_bot and not Aimbot.is_shooting() and (current_time - self.last_shot_time) > self.shot_cooldown:
                                if self.consecutive_shots < self.max_consecutive_shots:
                                    self.left_click()
                                    self.last_shot_time = current_time
                                    self.consecutive_shots += 1
                                    
                                    if human_like_delay:
                                        self.shot_cooldown = random.uniform(min_shot_delay, max_shot_delay)
                                    else:
                                        self.shot_cooldown = 0.1
                                else:
                                    self.consecutive_shots = 0
                                    self.shot_cooldown = random.uniform(0.2, 0.4)

                            cv2.putText(frame, "LOCKED", (x1 + 40, y1), cv2.FONT_HERSHEY_DUPLEX, 0.5, (115, 244, 113), 2)
                        else:
                            cv2.putText(frame, "TARGETING", (x1 + 40, y1), cv2.FONT_HERSHEY_DUPLEX, 0.5, (115, 113, 244), 2)

                        if Aimbot.is_aimbot_enabled():
                            # NOTA: move_crosshair ya no necesita las coordenadas del objetivo
                            # porque plan_smooth_movement ya calculó el path necesario.
                            # Solo ejecutamos el siguiente paso del path.
                            # Las coordenadas que pasamos aquí son ignoradas por move_crosshair,
                            # pero las mantenemos por compatibilidad de firma.
                            self.move_crosshair(absolute_head_X, absolute_head_Y)
                else:
                    # This is the crucial new part: If no targets are detected, clear any old movement plan.
                    if self.movement_path:
                        self.movement_path.clear()

                fps = int(1/(time.perf_counter() - start_time)) if (time.perf_counter() - start_time) > 0 else 0
                cv2.putText(frame, f"FPS: {fps}", (5, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (113, 116, 244), 2)
                
                try:
                    cv2.imshow("Screen Capture", frame) # Título de ventana estático
                    if cv2.waitKey(1) & 0xFF == ord('0'):
                        break
                except Exception as e:
                    print(f"[WARNING] Error de display OpenCV: {e}")
                
                # Increment debug counter at the end of each frame cycle
                self.debug_counter = (self.debug_counter + 1) % 6000

                elapsed_time = time.perf_counter() - start_time
                if elapsed_time < 0.016:
                    time.sleep(0.016 - elapsed_time)
        finally:
            # Esta sección se ejecuta siempre al salir del bucle, ya sea de forma normal o por error
            self.clean_up()

    def get_best_target(self, detections):
        """
        Finds the single best target based on proximity to the crosshair.
        This version has NO target locking or memory.
        """
        if not detections:
            return None

        # Always choose the target closest to the crosshair.
        detections.sort(key=lambda d: d["crosshair_dist"])
        closest_target = detections[0]
        if self.debug_counter % 30 == 0: print(colored(f"[DEBUG] TARGET: Found closest target. Dist={closest_target['crosshair_dist']:.1f}px", "yellow"))
        return closest_target


    def clean_up(self):
        """Libera todos los recursos de forma segura. Se llama desde el hilo principal."""
        print("[INFO] Realizando limpieza de recursos...")
        try:
            Aimbot.screen.close()
            if Aimbot.mem_dc is not None:
                Aimbot.mem_dc.DeleteDC()
            if Aimbot.desktop_dc is not None:
                win32gui.ReleaseDC(win32gui.GetDesktopWindow(), Aimbot.desktop_dc)
            cv2.destroyAllWindows()
            print("[INFO] Limpieza completada.")
        except Exception as e:
            print(f"[WARNING] Error durante la limpieza: {e}")
        finally:
            os._exit(0) # Salida final y definitiva del programa

    # La función estática original clean_up() se elimina porque ahora es un método de instancia
    # y se llama desde el flujo principal del programa para evitar problemas de concurrencia.
    @staticmethod
    def clean_up_static_removed():
        # Esta función ya no se usa.
        pass

if __name__ == "__main__": print("Estás en el directorio incorrecto y ejecutando el archivo equivocado; debes ejecutar lunar.py")