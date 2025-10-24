# 🧠 YoloV12 AI Aimbot - Lunar LITE v2.0

**Lunar LITE v2.0** es una versión completamente reescrita y mejorada del aimbot original [Lunar](https://github.com/zeyad-mansour/lunar).

## ✨ Novedades en v2.0

### 🎮 **Soporte Multi-Juego**
- Perfiles optimizados para múltiples juegos (Fortnite, Valorant, Apex Legends)
- Sistema de calibración automática
- Configuración por juego con parámetros específicos

### 🔧 **Arquitectura Modular**
- Motor de detección separado y mejorado
- Motor de movimiento con humanización avanzada
- Sistema de captura con auto-detección de método óptimo
- Gestión de mouse con fallback automático

### 📊 **Monitoreo de Rendimiento**
- Métricas de FPS en tiempo real
- Logging detallado con niveles
- Estadísticas de uso de CPU/memoria
- Logs separados por categoría

### 🎯 **Mejoras en Precisión**
- Target stickiness (reduce cambios erráticos)
- Deadzone configurable
- Humanización de movimientos (curvas Bézier, ruido, overshoot)
- Aceleración/desaceleración dinámica

### 🛡️ **Mejoras Anti-Detección**
- Soporte DDXoft (kernel-level, baja detección)
- Movimientos humanizados con aleatoriedad
- Trigger bot con delays variables
- Sistema de captura compatible con pantalla completa

---

## 🚀 Instalación

### Requisitos Previos
- Windows 10/11
- Python 3.12 o 3.13
- NVIDIA GPU con CUDA (recomendado para mejor rendimiento)
- 4GB+ RAM

### Instalación Automática

1. **Clonar el repositorio:**
```bash
git clone https://github.com/tu-usuario/AI-Aimbot.git
cd AI-Aimbot
```

2. **Ejecutar setup:**
```batch
setup_cuda.bat
```

3. **Iniciar el aimbot:**
```batch
start.bat
```

### Instalación Manual

1. **Instalar Python 3.13:**
```batch
install_python313.bat
```

2. **Crear entorno virtual:**
```batch
python -m venv venv_cuda
venv_cuda\Scripts\activate
```

3. **Instalar dependencias:**
```batch
pip install -r requirements_cuda.txt
```

---

## ⚙️ Configuración

### 🎮 Calibración Rápida (Recomendado)

```batch
start_calibration.bat
```

El asistente te guiará para:
1. Seleccionar tu juego
2. Calibrar sensibilidad (si es necesario)
3. Elegir método de captura
4. Configurar método de mouse

### 📝 Perfiles de Juego Disponibles

| Juego | ID | Características |
|-------|-----|----------------|
| **Fortnite** | `fortnite` | FOV grande, movimiento rápido |
| **Valorant** | `valorant` | Precisión extrema, headshot focus |
| **Apex Legends** | `apex_legends` | Movimiento muy rápido, tracking |
| **Custom** | `custom` | Personalizable para otros juegos |

### 🎯 Usar un Perfil Específico

```batch
python lunar.py --profile valorant
```

### 📋 Listar Perfiles Disponibles

```batch
python lunar.py --list-profiles
```

---

## 🎮 Uso

### Controles de Teclado

| Tecla | Acción |
|-------|--------|
| **F1** | Activar/Desactivar aimbot |
| **F2** | Salir del programa |
| **F3** | Mostrar estadísticas de rendimiento |

### Opciones de Línea de Comandos

```batch
# Modo normal
python lunar.py

# Con calibración
python lunar.py --calibrate

# Perfil específico
python lunar.py --profile fortnite

# Modo debug
python lunar.py --debug

# Sin verificación de admin
python lunar.py --no-admin

# Listar perfiles
python lunar.py --list-profiles
```

---

## 🔧 Solución de Problemas

### ❌ El aimbot solo funciona cuando haces Alt+Tab (no funciona en el juego)

**Causa:** Problema de captura de pantalla con juegos en pantalla completa.

**Solución:**
1. **Cambiar el juego a MODO VENTANA SIN BORDES** (más confiable)
2. O ejecutar calibración y seleccionar método `BitBlt`
3. O editar `lib/config/user_config.json`:
```json
{
  "capture_method": "bitblt"
}
```

### ❌ El aimbot detecta pero no mueve el mouse

**Causa:** Método de mouse no compatible o sin permisos de admin.

**Solución:**
1. **Ejecutar como ADMINISTRADOR:** `start_admin.bat`
2. O ejecutar calibración y probar ambos métodos
3. Verificar que `lib/mouse/dd40605x64.dll` existe
4. Si DDXoft falla, el sistema cambiará a Win32 automáticamente

### ❌ Error "CUDA IS UNAVAILABLE"

**Solución:**
```batch
# Para RTX 5060 (sm_120):
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Para otras GPUs:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

### ❌ El mouse se mueve muy rápido/lento

**Solución:**
Editar `lib/config/game_profiles.json` y ajustar:
```json
{
  "movement": {
    "smoothing": 0.7,  // Más bajo = más lento (0.3-1.0)
    "max_move_speed": 100  // Velocidad máxima
  }
}
```

### ❌ La detección es imprecisa

**Solución:**
Ajustar en `lib/config/game_profiles.json`:
```json
{
  "detection": {
    "confidence": 0.50,  // Más alto = más estricto (0.4-0.7)
    "fov": 300  // Más bajo = área más pequeña
  }
}
```

---

## 📁 Estructura del Proyecto

```
AI-Aimbot/
├── lib/
│   ├── core/              # Motores principales
│   │   ├── aimbot_engine.py
│   │   ├── detection_engine.py
│   │   └── movement_engine.py
│   ├── capture/           # Captura de pantalla
│   │   ├── capture_manager.py
│   │   ├── bitblt_capture.py
│   │   └── mss_capture.py
│   ├── input/             # Entrada de mouse
│   │   ├── mouse_manager.py
│   │   ├── ddxoft_mouse.py
│   │   └── win32_mouse.py
│   ├── config/            # Configuración
│   │   ├── config_manager.py
│   │   ├── game_profiles.json
│   │   └── user_config.json
│   ├── utils/             # Utilidades
│   │   ├── logger.py
│   │   ├── calibration.py
│   │   └── performance_monitor.py
│   └── best.pt            # Modelo YOLO
├── logs/                  # Archivos de log
├── lunar.py               # Punto de entrada principal
└── start.bat              # Script de inicio
```

---

## 🎯 Características Avanzadas

### Humanización de Movimientos

El motor de movimiento incluye:
- **Curvas Bézier**: Trayectorias curvas naturales
- **Ruido Gaussiano**: Imperfección humana simulada
- **Overshoot Aleatorio**: Pasarse ligeramente del objetivo
- **Aceleración/Desaceleración**: Velocidad variable según distancia

### Target Stickiness

Reduce cambios erráticos entre objetivos:
- Mantiene el target actual si sigue visible
- Tolerancia de distancia configurable
- Persistencia por varios frames

### Auto-Fallback

El sistema detecta y cambia automáticamente:
- Si BitBlt falla → cambia a MSS
- Si DDXoft falla → cambia a Win32
- Notificaciones en consola de cada cambio

---

## 📊 Monitoreo de Rendimiento

### Ver Estadísticas en Vivo

Presiona **F3** durante la ejecución para ver:
- FPS actual, promedio, mín, máx
- Tiempo de frame
- Uso de CPU y memoria
- Total de detecciones
- Total de frames procesados

### Logs Detallados

Los logs se guardan en `logs/` con:
- Timestamp de cada evento
- Categoría (ENGINE, CAPTURE, MOUSE, etc.)
- Nivel (DEBUG, INFO, WARNING, ERROR)
- Archivos rotados por sesión

---

## 🔒 Seguridad y Responsabilidad

⚠️ **DISCLAIMER:**

Este proyecto es para **propósitos educativos** y pruebas en **entornos propios**.

- ❌ **NO** usar en juegos online
- ❌ **NO** usar para hacer trampas
- ✅ **SÍ** usar para aprender IA y detección de objetos
- ✅ **SÍ** usar para probar sistemas anti-cheat propios

El uso indebido puede resultar en:
- Baneos permanentes
- Consecuencias legales
- Daño a la comunidad de jugadores

**Usa este código de forma responsable.**

---

## 💬 Soporte y Comunidad

### Discord
👉 [discord.gg/aiaimbot](https://discord.gg/aiaimbot)

### Versión Premium (Lunar V2)

La versión completa incluye:
- ✅ 25+ configuraciones personalizables
- ✅ Interfaz gráfica integrada
- ✅ Soporte YOLOv8, v10, v12 y TensorRT
- ✅ Soporte para control Xbox
- ✅ Input Logitech GHUB
- ✅ Compatible AMD y NVIDIA

[Descargar Lunar V2](https://gannonr.com/lunar)

---

## 📝 Licencia

Este proyecto está bajo licencia MIT. Ver `LICENSE` para más detalles.

---

## 🙏 Créditos

- Proyecto original: [Lunar by zeyad-mansour](https://github.com/zeyad-mansour/lunar)
- Modelo YOLO: [Ultralytics](https://github.com/ultralytics/ultralytics)
- Comunidad de Discord

---

## 📈 Changelog

### v2.0.0 (2024)
- ✨ Arquitectura completamente reescrita
- ✨ Soporte multi-juego con perfiles
- ✨ Sistema de calibración automática
- ✨ Motor de humanización avanzado
- ✨ Logging y monitoreo mejorados
- ✨ Auto-fallback para captura y mouse
- ✨ Target stickiness y deadzone
- ✨ Performance monitor en tiempo real

### v1.0.0
- 🎯 Versión original con YOLOv8/v12
- 🎯 Soporte básico para Fortnite
- 🎯 Captura MSS y mouse Win32

---

**¡Disfruta del proyecto y úsalo de forma responsable! 🎮🤖**
