@echo off
setlocal enabledelayedexpansion

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges
) else (
    echo Requesting administrator privileges automatically...
    echo.
    echo If you reject the UAC prompt, the application will not run.
    echo.
    :: Re-launch as admin automatically (no y/n prompt)
    PowerShell -Command "$process = Start-Process cmd -ArgumentList '/c %~dpnx0' -Verb RunAs -PassThru; if (!$process) { Write-Error 'Administrator privileges required' }"
    if %errorLevel% neq 0 (
        echo.
        echo ERROR: Administrator privileges are required to run this application.
        echo Please accept the UAC prompt to continue.
        echo.
        pause
        exit /b 1
    )
    exit /b
)

echo ===============================================
echo Lunar AI Aimbot - Administrator Mode with CUDA
echo ===============================================
echo.

:: Check for Python installation
echo Checking for Python 3.13 installation...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python 3.13 not found in system PATH.
    echo.
    echo Installing Python 3.13 for Windows...
    echo.
    call install_python313.bat
    if %errorlevel% neq 0 (
        echo Python installation failed. Please install Python 3.13 manually.
        pause
        exit /b 1
    )
) else (
    echo Python found in system.
)

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

echo Running Lunar AI Aimbot with administrator privileges and CUDA acceleration...
echo.
echo Benefits of running as administrator:
echo - Enhanced mouse input simulation
echo - Improved screen capture in fullscreen applications
echo - Better system resource management
echo - Reduced input latency
echo - Compatibility with more game protection systems
echo - CUDA acceleration for AI processing
echo.
python lunar.py
pause