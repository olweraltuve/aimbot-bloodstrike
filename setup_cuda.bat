@echo off
echo ===============================================
echo AI Aimbot CUDA Setup Script
echo ===============================================
echo.

echo Checking for existing Python 3.13 installation...
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo Python found!
    goto :create_venv
) else (
    echo Python not found.
    echo.
    echo Python 3.13 is required but not found in system PATH.
    echo.
    echo Options:
    echo 1. Run install_python313.bat to install Python 3.13 automatically
    echo 2. Install Python 3.13 manually from python.org
    echo 3. Ensure Python is added to PATH during installation
    echo.
    echo After installing Python 3.13, run this script again.
    pause
    exit /b 1
)

:create_venv
echo.
echo Creating CUDA-enabled virtual environment...
python -m venv venv_cuda
if %errorlevel% neq 0 (
    echo Failed to create virtual environment
    pause
    exit /b 1
)

echo.
echo Activating virtual environment...
call venv_cuda\Scripts\activate

echo.
echo Installing CUDA-enabled PyTorch and dependencies for RTX 5060 (sm_120)...
echo Using PyTorch nightly build for RTX 5060 (sm_120) compatibility...
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu124
if %errorlevel% neq 0 (
    echo Failed to install PyTorch with CUDA
    pause
    exit /b 1
)

echo.
echo Installing other requirements...
pip install -r requirements_cuda.txt
if %errorlevel% neq 0 (
    echo Failed to install requirements
    pause
    exit /b 1
)

echo.
echo Verifying CUDA installation and RTX 5060 compatibility...
python -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); print('CUDA version:', torch.version.cuda if torch.cuda.is_available() else 'N/A'); print('GPU count:', torch.cuda.device_count()); print('GPU name:', torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else 'N/A'); print('Compute capability:', torch.cuda.get_device_capability(0) if torch.cuda.device_count() > 0 else 'N/A'); print('RTX 5060 (sm_120) support:', 'YES' if torch.cuda.is_available() and torch.cuda.get_device_capability(0) >= (12, 0) else 'NO')"

echo.
echo ===============================================
echo CUDA Setup Complete!
echo ===============================================
echo.
echo To use the CUDA-enabled environment:
echo   venv_cuda\Scripts\activate
echo   python lunar.py
echo.
echo Your aimbot should now run with CUDA acceleration!
pause