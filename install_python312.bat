@echo off
echo ===============================================
echo Python 3.12 Installation Script
echo ===============================================
echo.
echo This will install Python 3.12 alongside your existing Python 3.13
echo without overwriting or affecting your current installation.
echo.

echo Downloading Python 3.12 installer...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe' -OutFile 'python312-installer.exe'"

if exist python312-installer.exe (
    echo.
    echo Running Python 3.12 installer...
    echo IMPORTANT: During installation, make sure to:
    echo   - Check "Add python.exe to PATH"
    echo   - Click "Customize installation"
    echo   - In Advanced Options, check "Install for all users"
    echo   - Change installation path to: C:\Python312\
    echo   - DO NOT check "Associate files with Python"
    echo.
    echo The installer will now open. Please follow the instructions above.
    echo.
    pause
    start /wait python312-installer.exe
) else (
    echo Failed to download Python 3.12 installer
    echo Please download manually from:
    echo https://www.python.org/downloads/release/python-3120/
    pause
    exit /b 1
)

echo.
echo Cleaning up installer...
del python312-installer.exe

echo.
echo Verifying Python 3.12 installation...
where python3.12 >nul 2>&1
if %errorlevel% equ 0 (
    echo Python 3.12 successfully installed!
    echo.
    echo Now run setup_cuda.bat to set up the CUDA environment.
) else (
    echo Python 3.12 installation may have failed.
    echo Please check if Python 3.12 is available in your system.
)

echo.
pause