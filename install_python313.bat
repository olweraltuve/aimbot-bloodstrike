@echo off
echo ===============================================
echo Python 3.13 Installation Script
echo ===============================================
echo.
echo This will install Python 3.13 for Windows.
echo.

echo Downloading Python 3.13 installer...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe' -OutFile 'python313-installer.exe'"

if exist python313-installer.exe (
    echo.
    echo Running Python 3.13 installer...
    echo IMPORTANT: During installation, make sure to:
    echo   - Check "Add python.exe to PATH"
    echo   - Click "Customize installation"
    echo   - In Advanced Options, check "Install for all users"
    echo   - Change installation path to: C:\Python313\
    echo   - DO NOT check "Associate files with Python"
    echo.
    echo The installer will now open. Please follow the instructions above.
    echo.
    pause
    start /wait python313-installer.exe
) else (
    echo Failed to download Python 3.13 installer
    echo Please download manually from:
    echo https://www.python.org/downloads/release/python-3130/
    pause
    exit /b 1
)

echo.
echo Cleaning up installer...
del python313-installer.exe

echo.
echo Verifying Python 3.13 installation...
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo Python 3.13 successfully installed!
    echo.
    echo Now run setup_cuda.bat to set up the CUDA environment.
) else (
    echo Python 3.13 installation may have failed.
    echo Please check if Python 3.13 is available in your system.
)

echo.
pause