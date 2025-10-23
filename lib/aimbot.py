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
import win32api  # For GetCursorPos verification
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

aim_height = 10 # The lower the number, the higher the aim_height. For example: 2 would be the head and 100 would be the feet.

fov = 350

confidence = 0.45 # How confident the AI needs to be for it to lock on to the player. Default is 45%

use_trigger_bot = True # Will shoot if crosshair is locked on the player

# Anti-cheat avoidance settings
human_like_delay = True  # Add random delays to mimic human behavior
min_shot_delay = 0.08    # Minimum delay between shots (seconds)
max_shot_delay = 0.15    # Maximum delay between shots (seconds)

# Try to load config from mouse_config.py (now handles both mouse and capture), fallback to defaults
try:
    from lib.config.mouse_config import (
        MOUSE_METHOD, 
        MOUSE_DELAY as CONFIG_MOUSE_DELAY,
        CAPTURE_METHOD as CONFIG_CAPTURE_METHOD
    )
    mouse_method = MOUSE_METHOD
    config_mouse_delay = CONFIG_MOUSE_DELAY
    capture_method = CONFIG_CAPTURE_METHOD
except ImportError:
    mouse_methods = ['win32', 'ddxoft']
    mouse_method = mouse_methods[1]  # 1 is ddxoft (less detectable). 0 is win32.
    config_mouse_delay = 0.0009
    capture_method = 'bitblt'  # Default to bitblt for fullscreen compatibility

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
    
    # SOLUCIÓN: Parámetros de control de movimiento robusto
    DEADZONE_RADIUS = 8  # Píxeles - no mover si estamos dentro de este radio
    MAX_MOVE_PER_FRAME = 15  # Píxeles - límite máximo de movimiento por frame
    SMOOTHING_FACTOR = 0.25  # 0.0-1.0 - factor de suavizado (menor = más suave)
    APPROACH_THRESHOLD = 80  # Píxeles - distancia para activar suavizado extra
    MIN_MOVE_THRESHOLD = 0.3  # Píxeles - no mover si el cálculo da menos que esto

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
        self.debug_counter = 0  # Counter for debug messages
        
        # Movement tracking for debugging
        self.last_move_command = None
        self.movement_verification_enabled = True

        print("[INFO] Loading the neural network model")
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

    def update_status_aimbot():
        if Aimbot.aimbot_status == colored("ENABLED", 'green'):
            Aimbot.aimbot_status = colored("DISABLED", 'red')
        else:
            Aimbot.aimbot_status = colored("ENABLED", 'green')
        sys.stdout.write("\033[K")
        print(f"[!] AIMBOT ESTÁ [{Aimbot.aimbot_status}]", end = "\r")
    
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

    def move_crosshair(self, x, y):
        """
        SOLUCIÓN ROBUSTA AL OVERSHOOTING
        =================================
        Sistema de control proporcional con:
        1. Zona muerta (deadzone) para evitar micro-movimientos
        2. Límite de velocidad máxima por frame
        3. Suavizado adaptativo basado en distancia
        4. Filtro de movimientos mínimos
        5. Tracking de posición real del cursor
        """
        
        # SOLUCIÓN CRÍTICA: Obtener posición REAL del cursor
        # El cursor NO siempre está en el centro después del primer movimiento
        try:
            current_x, current_y = win32api.GetCursorPos()
            if self.debug_counter % 60 == 0:
                print(colored(f"[DEBUG] CURSOR: Current position=({current_x},{current_y})", "cyan"))
        except Exception as e:
            # Si falla GetCursorPos, asumir centro (fallback)
            current_x, current_y = screen_x, screen_y
            if self.debug_counter % 120 == 0:
                print(colored(f"[WARNING] Could not get cursor position: {e}. Using screen center.", "yellow"))
        
        # Calcular diferencia desde la posición ACTUAL del cursor al objetivo
        # NO desde el centro de la pantalla
        diff_x = x - current_x
        diff_y = y - current_y
        
        # Calcular distancia euclidiana al objetivo
        distance = math.sqrt(diff_x**2 + diff_y**2)
        
        # SOLUCIÓN 1: Zona muerta - si estamos MUY cerca, no mover
        # Esto evita el "jitter" (temblor) cuando ya estamos en el objetivo
        if distance < Aimbot.DEADZONE_RADIUS:
            if self.debug_counter % 60 == 0:
                print(colored(f"[DEBUG] MOVEMENT: Inside deadzone ({distance:.1f}px < {Aimbot.DEADZONE_RADIUS}px) - SKIP", "yellow"))
            return
        
        # SOLUCIÓN 2: Suavizado adaptativo
        # Mientras más cerca estamos, más lento nos movemos
        smoothing = Aimbot.SMOOTHING_FACTOR
        
        if distance < Aimbot.APPROACH_THRESHOLD:
            # Aplicar suavizado extra cuando estamos cerca
            # A 10px: smoothing = 0.25 * (10/80) = 0.031 (MUY suave)
            # A 40px: smoothing = 0.25 * (40/80) = 0.125 (suave)
            # A 80px: smoothing = 0.25 * (80/80) = 0.25 (normal)
            smoothing *= (distance / Aimbot.APPROACH_THRESHOLD)
            if self.debug_counter % 30 == 0:
                print(colored(f"[DEBUG] MOVEMENT: Close approach mode. Distance={distance:.1f}px, Smoothing={smoothing:.3f}", "cyan"))

        # Determinar qué escala de sensibilidad usar (apuntando o desde la cadera)
        divisor = self.sens_config['targeting_scale'] if Aimbot.is_targeted() else self.sens_config['xy_scale']
        
        if divisor == 0:
            print(colored("[ERROR] MOVEMENT: Divisor is 0! Check config.json", "red"))
            return
        
        # Calcular movimiento base con sensibilidad y suavizado
        move_x = (diff_x / divisor) * smoothing
        move_y = (diff_y / divisor) * smoothing
        
        # SOLUCIÓN 3: Límite de velocidad máxima
        # Nunca mover más de MAX_MOVE_PER_FRAME píxeles en un solo frame
        move_magnitude = math.sqrt(move_x**2 + move_y**2)
        
        if move_magnitude > Aimbot.MAX_MOVE_PER_FRAME:
            # Escalar el movimiento para que no exceda el límite
            scale_factor = Aimbot.MAX_MOVE_PER_FRAME / move_magnitude
            move_x *= scale_factor
            move_y *= scale_factor
            if self.debug_counter % 30 == 0:
                print(colored(f"[DEBUG] MOVEMENT: Capped at max speed. Original={move_magnitude:.1f}px, Capped={Aimbot.MAX_MOVE_PER_FRAME}px", "yellow"))
        
        # SOLUCIÓN 4: Filtro de movimientos insignificantes
        # Si el movimiento calculado es menor al umbral, ignorarlo
        if abs(move_x) < Aimbot.MIN_MOVE_THRESHOLD and abs(move_y) < Aimbot.MIN_MOVE_THRESHOLD:
            if self.debug_counter % 60 == 0:
                print(colored(f"[DEBUG] MOVEMENT: Movement too small ({move_x:.2f}, {move_y:.2f}) - SKIP", "yellow"))
            return
        
        # Ejecutar el movimiento
        if self.mouse_method.lower() == 'ddxoft':
            Aimbot.mouse_dll.DD_movR(int(move_x), int(move_y))
        elif self.mouse_method.lower() == 'win32':
            Aimbot.ii_.mi = MouseInput(int(move_x), int(move_y), 0, 0x0001, 0, ctypes.pointer(Aimbot.extra))
            command = Input(ctypes.c_ulong(0), Aimbot.ii_)
            ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))
        
        # Debug mejorado con más información
        if self.debug_counter % 10 == 0:
            target_abs = f"Target=({x},{y})"
            cursor_pos = f"Cursor=({current_x},{current_y})"
            movement = f"Move=({int(move_x)},{int(move_y)})"
            print(colored(f"[DEBUG] MOVEMENT: Dist={distance:.1f}px, {target_abs}, {cursor_pos}, {movement}, Smooth={smoothing:.3f}", "green"))
        
        Aimbot.sleep(self.mouse_delay)


    def start(self):
        print("[INFO] Iniciando captura de pantalla")
        Aimbot.update_status_aimbot()
        half_screen_width = ctypes.windll.user32.GetSystemMetrics(0)/2
        half_screen_height = ctypes.windll.user32.GetSystemMetrics(1)/2
        detection_box = {'left': int(half_screen_width - self.box_constant//2), #x1 coord (for top-left corner of the box)
                          'top': int(half_screen_height - self.box_constant//2), #y1 coord (for top-left corner of the box)
                          'width': int(self.box_constant),  #width of the box
                          'height': int(self.box_constant)} #height of the box

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
                least_crosshair_dist = closest_detection = player_in_frame = False
                for box in result.boxes.xyxy: #iterate over each player detected
                    x1, y1, x2, y2 = map(int, box)
                    x1y1 = (x1, y1)
                    x2y2 = (x2, y2)
                    height = y2 - y1
                    relative_head_X, relative_head_Y = int((x1 + x2)/2), int((y1 + y2)/2 - height/aim_height) # offset to roughly approximate the head using a ratio of the height
                    own_player = x1 < 15 or (x1 < self.box_constant/5 and y2 > self.box_constant/1.2) # helps ensure that your own player is not regarded as a valid detection

                    crosshair_dist = math.dist((relative_head_X, relative_head_Y), (self.box_constant/2, self.box_constant/2))

                    if not least_crosshair_dist: least_crosshair_dist = crosshair_dist

                    if crosshair_dist <= least_crosshair_dist and not own_player:
                        least_crosshair_dist = crosshair_dist
                        closest_detection = {"x1y1": x1y1, "x2y2": x2y2, "relative_head_X": relative_head_X, "relative_head_Y": relative_head_Y}

                    if own_player:
                        own_player = False
                        if not player_in_frame:
                            player_in_frame = True

                if closest_detection: #if valid detection exists
                    cv2.circle(frame, (closest_detection["relative_head_X"], closest_detection["relative_head_Y"]), 5, (115, 244, 113), -1) #draw circle on the head
                    cv2.line(frame, (closest_detection["relative_head_X"], closest_detection["relative_head_Y"]), (self.box_constant//2, self.box_constant//2), (244, 242, 113), 2)

                    absolute_head_X, absolute_head_Y = closest_detection["relative_head_X"] + detection_box['left'], closest_detection["relative_head_Y"] + detection_box['top']
                    x1, y1 = closest_detection["x1y1"]

                    rel_x, rel_y = closest_detection['relative_head_X'], closest_detection['relative_head_Y']
                    dist = least_crosshair_dist
                    abs_coords_str = f"Abs Coords=({absolute_head_X},{absolute_head_Y})"
                    rel_coords_str = f"Rel Coords=({rel_x},{rel_y})"
                    
                    # Debug con información adicional del cursor
                    if self.debug_counter % 10 == 0:
                        try:
                            cur_x, cur_y = win32api.GetCursorPos()
                            cursor_info = f"Cursor=({cur_x},{cur_y})"
                            print(colored(f"[DEBUG] TARGET: Dist={dist:.1f}. {rel_coords_str}. {abs_coords_str}. {cursor_info}", "green"))
                        except:
                            print(colored(f"[DEBUG] TARGET: Dist={dist:.1f}. {rel_coords_str}. {abs_coords_str}", "green"))

                    if Aimbot.is_target_locked(absolute_head_X, absolute_head_Y):
                        current_time = time.perf_counter()
                        
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
                        self.move_crosshair(absolute_head_X, absolute_head_Y)
                elif self.debug_counter % 30 == 0 and len(result.boxes) > 0:
                    # This case happens if detections are found but filtered out (e.g., as own player)
                    print(colored(f"[DEBUG] TARGET: Detections found, but none were valid targets after filtering.", "yellow"))

            fps = int(1/(time.perf_counter() - start_time)) if (time.perf_counter() - start_time) > 0 else 0
            cv2.putText(frame, f"FPS: {fps}", (5, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (113, 116, 244), 2)
            
            try:
                cv2.imshow("Screen Capture", frame)
                if cv2.waitKey(1) & 0xFF == ord('0'):
                    break
            except Exception as e:
                print(f"[WARNING] Error de display OpenCV: {e}")
            
            # Increment debug counter at the end of each frame cycle
            self.debug_counter = (self.debug_counter + 1) % 6000

            elapsed_time = time.perf_counter() - start_time
            if elapsed_time < 0.016:
                time.sleep(0.016 - elapsed_time)

    def clean_up():
        print("\n[INFO] F2 PRESIONADO. CERRANDO...")
        try:
            if 'lunar' in globals():
                lunar.running = False
            Aimbot.screen.close()
            if Aimbot.mem_dc is not None:
                Aimbot.mem_dc.DeleteDC()
            if Aimbot.desktop_dc is not None:
                win32gui.ReleaseDC(win32gui.GetDesktopWindow(), Aimbot.desktop_dc)
            cv2.destroyAllWindows()
        except Exception as e:
            print(f"[WARNING] Error en la limpieza: {e}")
        finally:
            os._exit(0)

if __name__ == "__main__": print("Estás en el directorio incorrecto y ejecutando el archivo equivocado; debes ejecutar lunar.py")