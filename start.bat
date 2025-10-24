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

echo.
echo ===============================================
echo   LUNAR AI AIMBOT - STARTING
echo ===============================================
echo.
echo Available commands:
echo   python lunar.py              - Run with default settings
echo   python lunar.py --calibrate  - Run setup wizard
echo   python lunar.py --profile fortnite - Use Fortnite profile
echo   python lunar.py --list-profiles - Show all profiles
echo.
echo Starting with default settings...
echo.

python lunar.py
pause
