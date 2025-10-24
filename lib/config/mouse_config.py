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
# MOUSE SMOOTHING & SPEED
# ============================================================================
# SOLUCIÓN: Este es el factor de suavizado que controla qué fracción del error
# se corrige en cada frame.
#
# Valores recomendados:
#   0.15-0.25 : Muy suave, para snipers o precisión extrema
#   0.25-0.35 : Equilibrado, recomendado para la mayoría de situaciones
#   0.35-0.50 : Rápido, para tracking agresivo
#   0.50+     : Muy rápido, puede causar overshoot
MOUSE_SMOOTHING = 0.30  # Valor por defecto balanceado

# ============================================================================
# TARGETING DEAD ZONE (NUEVO)
# ============================================================================
# SOLUCIÓN: Dead-zone aplicada al error AL CENTRO, no al cursor.
# Si el objetivo está a menos de X píxeles del centro, no mover.
# Esto previene vibración cuando ya estamos casi apuntando correctamente.
#
# Valores recomendados: 3-5 píxeles
TARGETING_DEADZONE_PIXELS = 4  # Aumentado de 2 a 4 para reducir vibración

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