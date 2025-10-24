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
# PRO-PLAYER MOVEMENT & TARGETING
# ============================================================================
# Estos ajustes controlan la "humanización" del movimiento y la lógica de fijación de objetivos.

# (SOLUCIÓN) ANCLAJE DEL VECTOR INICIAL
# Controla la rectitud del INICIO del movimiento. Un valor bajo ("minúsculo")
# asegura que el movimiento COMIENCE en la dirección perfecta, pero permite que la
# curva se forme casi de inmediato de manera sutil.
# 0.0 = La curva puede empezar desviada. 0.2 = Inicio perfecto, curva suave (RECOMENDADO). 1.0 = Línea recta.
INITIAL_STRAIGHTNESS = 0.4  # Rango recomendado: 0.2 - 0.5 (Más alto = más directo)

# Intensidad de la curva. Controla qué tan pronunciado es el arco del movimiento.
HUMANIZATION_INTENSITY = 0.15  # Rango recomendado: 0.1 (casi recto) - 0.4 (curva notable)

# Cantidad del "overshoot" (micro-corrección). Ocurre muy raramente (8% de probabilidad).
# Este valor es un % de la distancia total. 1.0 = se pasa un 1% de la distancia.
OVERSHOOT_AMOUNT = 0.1  # Rango recomendado: 0.1 (deshabilitado) - 2.0

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