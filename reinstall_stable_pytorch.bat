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
echo Installing stable PyTorch with CUDA 12.8 support for RTX 5060 (sm_120)...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

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
echo Your RTX 5060 GPU (sm_120) is now fully supported by PyTorch 2.7+!
echo.
echo The aimbot will run with full CUDA acceleration on your RTX 5060.
echo.
echo For optimal performance:
echo - Ensure you have NVIDIA driver R570 or newer
echo - Verify CUDA 12.8 is detected in the verification above
echo - The aimbot will automatically use GPU acceleration
echo.
echo ===============================================
echo Reinstallation Complete!
echo ===============================================
echo.
echo Run: python lunar.py
echo The aimbot will now use GPU acceleration on your RTX 5060!
pause