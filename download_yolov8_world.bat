@echo off
echo ====================================
echo  Descargando YOLOv8-World v2 Model
echo ====================================
echo.

REM Activar entorno virtual
if exist "venv_cuda\Scripts\activate.bat" (
    call venv_cuda\Scripts\activate.bat
    echo [OK] Entorno virtual activado
) else (
    echo [INFO] No se encontro entorno virtual, usando Python del sistema
)

echo.
echo Descargando modelo yoloe-11l-seg.pt...
echo Este proceso puede tomar 1-2 minutos dependiendo de tu conexion.
echo.

REM Crear directorio lib si no existe
if not exist "lib" mkdir lib

REM Descargar modelo usando Python
python -c "from ultralytics import YOLO; import os; os.chdir('lib'); model = YOLO('yoloe-11l-seg.pt'); print('[SUCCESS] Modelo descargado exitosamente a lib/yoloe-11l-seg.pt')"

if %errorlevel% equ 0 (
    echo.
    echo ====================================
    echo  DESCARGA COMPLETADA CON EXITO
    echo ====================================
    echo.
    echo El modelo esta listo en: lib\yoloe-11l-seg.pt
    echo Puedes ejecutar el program_t con: start.bat
) else (
    echo.
    echo ====================================
    echo  ERROR EN LA DESCARGA
    echo ====================================
    echo.
    echo Intenta descargar manualmente desde:
    echo https://github.com/ultralytics/assets/releases/download/v8.3.0/yoloe-11l-seg.pt
    echo.
    echo Y coloca el archivo en la carpeta: lib\
)

echo.
pause

