@echo off
echo ===============================================
echo AI Aimbot - Reinstall Stable PyTorch
echo ===============================================
echo.

echo This script will reinstall the stable PyTorch version
echo and ensure the aimbot works reliably in CPU mode.
echo.

echo Removing current PyTorch installation...
call venv_cuda\Scripts\activate
pip uninstall torch torchvision torchaudio -y

echo.
echo Installing stable PyTorch with CUDA 12.4 support...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

echo.
echo Installing other dependencies...
pip install -r requirements_cuda.txt

echo.
echo Verifying installation...
venv_cuda\Scripts\python -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); print('GPU name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'); print('Compute capability:', torch.cuda.get_device_capability(0) if torch.cuda.is_available() else 'N/A')"

echo.
echo ===============================================
echo IMPORTANT INFORMATION FOR RTX 5060 USERS
echo ===============================================
echo.
echo Your RTX 5060 GPU (sm_120) is not yet supported by stable PyTorch.
echo.
echo The aimbot will run in CPU mode which is slower but functional.
echo.
echo For future CUDA support:
echo - PyTorch nightly builds may eventually support RTX 5060
echo - Check https://pytorch.org/get-started/locally/ for updates
echo - The aimbot will automatically detect when CUDA becomes available
echo.
echo ===============================================
echo Reinstallation Complete!
echo ===============================================
echo.
echo Run: python lunar.py
echo The aimbot will automatically use CPU mode for now.
pause