"""
Aimbot Configuration
====================

This file allows you to easily configure mouse movement and screen capture methods
without editing the main aimbot.py file.

Usage:
    Just change the values below and restart the aimbot.
"""

# ============================================================================
# MOUSE MOVEMENT CONFIGURATION
# ============================================================================

# Available mouse methods:
# 'ddxoft' - Uses DDXoft driver (kernel-level, bypasses most anti-cheat) ⬅️ RECOMENDADO Y MÁS SEGURO
# 'win32'  - Uses Windows SendInput (DETECTABLE by anti-cheat, no funciona en pantalla completa)

MOUSE_METHOD = 'ddxoft'  # Usar 'ddxoft' por defecto. Si falla, el programa cambiará a 'win32' automáticamente.

# Mouse movement settings
MOUSE_DELAY = 0.0009  # Delay between mouse movements (seconds)

# Sensitivity scaling (for fine-tuning mouse movement speed)
# Higher values = faster/more aggressive movement
# Lower values = slower/smoother movement
# Set to None to use values from config.json
TARGETING_SCALE_OVERRIDE = None  # Example: 50.0 for slower, 200.0 for faster

# ============================================================================
# ADVANCED MOVEMENT CONTROL (Solución al overshooting)
# ============================================================================

# Zona muerta - radio en píxeles donde NO se mueve el mouse
# Aumentar si hay "jitter" (temblor) cerca del objetivo
DEADZONE_RADIUS = 5  # Recomendado: 5-15 (reducido para mejor precisión)

# Velocidad máxima por frame (límite de píxeles por movimiento)
# Reducir si el mouse se mueve demasiado rápido y se pasa del objetivo
MAX_MOVE_PER_FRAME = 12  # Recomendado: 10-25 (reducido para evitar overshooting)

# Factor de suavizado (0.0 = no mover, 1.0 = sin suavizado)
# Reducir para movimientos más suaves pero más lentos
SMOOTHING_FACTOR = 0.25  # Recomendado: 0.15-0.35

# Distancia para activar suavizado extra (píxeles)
# Cuando estás más cerca que esto, el movimiento se vuelve MÁS suave
APPROACH_THRESHOLD = 80  # Recomendado: 60-100

# ============================================================================
# SCREEN CAPTURE CONFIGURATION
# ============================================================================

# Available capture methods:
# 'mss'    - Rápido, pero NO FUNCIONA con juegos en pantalla completa (solo ventana sin bordes)
# 'bitblt' - Más lento, pero FUNCIONA CON JUEGOS EN PANTALLA COMPLETA
# 'auto'   - Intenta 'bitblt' primero, y si falla, usa 'mss'.

CAPTURE_METHOD = 'bitblt'  # ⬅️ RECOMENDADO para juegos en pantalla completa

# ============================================================================
# DEBUG SETTINGS
# ============================================================================

DEBUG_MOUSE_MOVEMENT = True  # Show debug messages for mouse movement
DEBUG_SCREEN_CAPTURE = True  # Show debug messages for screen capture
DEBUG_FREQUENCY = 30  # Show debug message every N frames (lower = more messages)

# ============================================================================
# ADVANCED SETTINGS (Don't change unless you know what you're doing)
# ============================================================================

# SendInput flags (only for 'win32' method)
# 0x0001 = MOUSEEVENTF_MOVE (relative movement)
# 0x8000 = MOUSEEVENTF_MOVE_NOCOALESCE (don't merge movements)
SENDINPUT_FLAGS = 0x0001