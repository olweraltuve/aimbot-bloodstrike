# 🌍 Configuración de YOLO-World v2 para Detección de Humanoides

## 📋 Descripción

Este proyecto utiliza **YOLOv8-World v2**, un modelo de detección de objetos zero-shot que puede detectar cualquier clase de objetos usando prompts de texto, sin necesidad de entrenamiento adicional.

## 🎯 Ventajas de YOLO-World v2

- ✅ **Zero-Shot Detection**: Detecta objetos mediante descripciones de texto
- ✅ **Sin Entrenamiento Necesario**: Funciona inmediatamente con cualquier clase
- ✅ **Detección de Humanoides Mejorada**: Múltiples prompts para mayor precisión
- ✅ **Flexible**: Puedes cambiar las clases sin reentrenar el modelo

## 📥 Cómo Obtener el Modelo

### Opción 1: Descarga Automática (Recomendado)

El modelo se descargará automáticamente la primera vez que ejecutes el program_t:

```batch
start.bat
```

Ultralytics descargará `yoloe-11l-seg.pt` automáticamente a la carpeta `lib/`.

### Opción 2: Descarga Manual

Si la descarga automática falla, puedes descargarlo manualmente:

1. **Descargar desde Ultralytics:**
```bash
cd lib
python -c "from ultralytics import YOLO; YOLO('yoloe-11l-seg.pt')"
```

2. **O desde el repositorio oficial:**
   - Visita: https://github.com/ultralytics/ultralytics/releases
   - Descarga: `yoloe-11l-seg.pt`
   - Coloca el archivo en la carpeta `lib/`

### Opción 3: Descarga Directa

```bash
# Windows PowerShell
Invoke-WebRequest -Uri "https://github.com/ultralytics/assets/releases/download/v8.3.0/yoloe-11l-seg.pt" -OutFile "lib/yoloe-11l-seg.pt"
```

## 🎮 Configuración de Detección de Humanoides

El modelo está configurado para detectar humanoides usando múltiples prompts de texto:

```python
self.model.set_classes(["person", "human", "player", "character"])
```

Esto permite detectar:
- 👤 **person**: Personas en general
- 🧍 **human**: Seres humanos
- 🎮 **player**: Jugadores en videojuegos
- 🦸 **character**: Personajes y avatares

## ⚙️ Personalización de Clases

Puedes modificar las clases detectadas editando los archivos:

### `lib/core/program_t_engine.py` (Línea ~146)
```python
# Cambiar estas clases según tus necesidades
self.model.set_classes(["person", "soldier", "enemy", "target"])
```

## 🎯 Ejemplos de Clases Útiles

### Para Juegos de Disparos
```python
self.model.set_classes(["soldier", "enemy", "player", "person"])
```

### Para Juegos de Survival
```python
self.model.set_classes(["person", "zombie", "player", "survivor"])
```

### Para Juegos Realistas
```python
self.model.set_classes(["person", "human", "soldier", "character"])
```

## 📊 Rendimiento

- **Modelo**: YOLOv8m-World v2 (Medium)
- **Tamaño**: ~52 MB
- **Velocidad**: ~30-60 FPS (con GPU)
- **Precisión**: Alta para detección de humanoides
- **VRAM**: ~2-3 GB (con CUDA)

## 🔧 Solución de Problemas

### Error: "Model not found"
```bash
# Forzar descarga del modelo
cd lib
python -c "from ultralytics import YOLO; YOLO('yoloe-11l-seg.pt')"
```

### Error: "set_classes not found"
```bash
# Actualizar ultralytics a la última versión
pip install --upgrade ultralytics
```

### Detección Lenta
- Asegúrate de tener CUDA instalado para aceleración GPU
- Ejecuta `setup_cuda.bat` para configurar PyTorch con CUDA
- Verifica que `torch.cuda.is_available()` devuelva `True`

### Detecciones Inexactas
- Ajusta el parámetro `confidence` en `lib/config/game_profiles.json`
- Prueba diferentes combinaciones de clases
- Reduce el FOV para mejorar la precisión

## 📝 Notas Importantes

1. **Primera Ejecución**: La descarga del modelo puede tomar 1-2 minutos
2. **Internet Requerido**: Solo para la primera descarga
3. **Sin Texto en Detecciones**: Se eliminaron las etiquetas "LOCKED" y "TARGETING" para una interfaz más limpia
4. **Indicadores Visuales**: Las cajas de colores y el punto de mira indican el estado del objetivo

## 🔗 Referencias

- [Ultralytics YOLO-World](https://docs.ultralytics.com/models/yolo-world/)
- [Paper YOLO-World](https://arxiv.org/abs/2401.17270)
- [GitHub Ultralytics](https://github.com/ultralytics/ultralytics)

## ✅ Verificación de Instalación

Ejecuta este comando para verificar que todo está correcto:

```python
python -c "from ultralytics import YOLO; m = YOLO('lib/yoloe-11l-seg.pt'); m.set_classes(['person']); print('✓ YOLO-World v2 configurado correctamente')"
```

Si ves el mensaje de éxito, ¡estás listo para usar el program_t con detección de humanoides!

