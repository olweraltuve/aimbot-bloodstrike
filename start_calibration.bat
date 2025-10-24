@echo off
echo ===============================================
echo Lunar AI Aimbot - Calibration Wizard
echo ===============================================
echo.

echo Checking for CUDA virtual environment...
if not exist "venv_cuda\Scripts\activate.bat" (
    echo CUDA virtual environment not found!
    echo Please run setup_cuda.bat first.
    echo.
    pause
    exit /b 1
)

echo Activating CUDA virtual environment...
call venv_cuda\Scripts\activate.bat

echo.
echo Starting calibration wizard...
python lunar.py --calibrate

pause