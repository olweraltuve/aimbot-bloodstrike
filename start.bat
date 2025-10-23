@echo off
echo ===============================================
echo Lunar AI Aimbot - CUDA Enabled
echo ===============================================
echo.

echo Checking for CUDA virtual environment...
if not exist "venv_cuda\Scripts\activate.bat" (
    echo CUDA virtual environment not found!
    echo Please run setup_cuda.bat first to set up the CUDA environment.
    echo.
    pause
    exit /b 1
)

echo Activating CUDA virtual environment...
call venv_cuda\Scripts\activate.bat

echo Running Lunar AI Aimbot with CUDA acceleration...
python lunar.py
pause
