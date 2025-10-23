@echo off
echo ===============================================
echo AI Aimbot RTX 5060 CUDA Compatibility Update
echo ===============================================
echo.

echo This script will update your CUDA installation to support RTX 5060 (sm_120)
echo.

echo Checking current PyTorch installation...
venv_cuda\Scripts\python -c "import torch; print('Current PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); print('Compute capability:', torch.cuda.get_device_capability(0) if torch.cuda.is_available() else 'N/A')"

echo.
echo Updating PyTorch to nightly build for RTX 5060 compatibility...
call venv_cuda\Scripts\activate
pip uninstall torch torchvision torchaudio -y
pip install --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu124

echo.
echo Verifying RTX 5060 compatibility...
venv_cuda\Scripts\python -c "import torch; print('=== CUDA Compatibility Check ==='); print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); print('CUDA version:', torch.version.cuda if torch.cuda.is_available() else 'N/A'); print('GPU count:', torch.cuda.device_count()); print('GPU name:', torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else 'N/A'); print('Compute capability:', torch.cuda.get_device_capability(0) if torch.cuda.device_count() > 0 else 'N/A'); print('RTX 5060 (sm_120) support:', 'YES' if torch.cuda.is_available() and torch.cuda.get_device_capability(0) >= (12, 0) else 'NO')"

echo.
echo ===============================================
echo Update Complete!
echo ===============================================
echo.
echo If CUDA functionality test passed, your RTX 5060 should now work with the aimbot.
echo If it failed, the aimbot will automatically fall back to CPU mode.
echo.
echo Run: python lunar.py
pause