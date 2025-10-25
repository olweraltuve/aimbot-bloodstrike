# 🧠 YOLO-World v2 AI Assistance Program - Lunar LITE v2.0

**Lunar LITE v2.0** is a completely rewritten and improved version of the original [Lunar](https://github.com/zeyad-mansour/lunar) program.

## 🌍 **NEW: YOLO-World v2 - Humanoid Detection**

This version uses **YOLOv8-World v2**, a revolutionary zero-shot detection model:

- 🎯 **Improved Humanoid Detection**: Uses text prompts ("person", "human", "player", "character")
- ⚡ **Zero-Shot Detection**: No additional training required
- 🎨 **Clean Interface**: No text overlays on detections, only visual indicators
- 🔧 **Customizable**: Easily change detected classes

> 📖 See complete guide: [docs/YOLO_WORLD_SETUP.md](docs/YOLO_WORLD_SETUP.md)

---

## ✨ What's New in v2.0

### 🎮 **Multi-Game Support**
- Optimized profiles for multiple games (Fortnite, Valorant, Apex Legends)
- Automatic calibration system
- Game-specific configuration with custom parameters

### 🔧 **Modular Architecture**
- Separate and improved detection engine
- Advanced humanization movement engine
- Capture system with auto-detection of optimal method
- Mouse management with automatic fallback

### 📊 **Performance Monitoring**
- Real-time FPS metrics
- Detailed logging with levels
- CPU/memory usage statistics
- Category-separated logs

### 🎯 **Precision Improvements**
- Target stickiness (reduces erratic changes)
- Configurable deadzone
- Movement humanization (Bézier curves, noise, overshoot)
- Dynamic acceleration/deceleration

### 🛡️ **Detection Mitigation Improvements**
- DDXoft support (kernel-level, low detection signature)
- Humanized movements with randomness
- Trigger system with variable delays
- Fullscreen-compatible capture system

---

## 🚀 Installation

### Prerequisites
- Windows 10/11
- Python 3.12 or 3.13
- NVIDIA GPU with CUDA (recommended for better performance)
- 4GB+ RAM

### Automatic Installation

1. **Clone the repository:**
```bash
git clone https://github.com/tu-usuario/AI-Program_t.git
cd AI-Program_t
```

2. **Run setup:**
```batch
setup_cuda.bat
```

3. **Download YOLO-World v2 model:**
```batch
download_yolov8_world.bat
```
> The model will automatically download on first startup if not done manually.

4. **Start the program:**
```batch
start.bat
```

### Manual Installation

1. **Install Python 3.13:**
```batch
install_python313.bat
```

2. **Create virtual environment:**
```batch
python -m venv venv_cuda
venv_cuda\Scripts\activate
```

3. **Install dependencies:**
```batch
pip install -r requirements_cuda.txt
```

---

## ⚙️ Configuration

### 🎮 Quick Calibration (Recommended)

```batch
start_calibration.bat
```

The wizard will guide you through:
1. Selecting your game
2. Calibrating sensitivity (if needed)
3. Choosing capture method
4. Configuring mouse method

### 📝 Available Game Profiles

| Game | ID | Features |
|-------|-----|----------------|
| **Fortnite** | `fortnite` | Large FOV, fast movement |
| **Valorant** | `valorant` | Extreme precision, headshot focus |
| **Apex Legends** | `apex_legends` | Very fast movement, tracking |
| **Custom** | `custom` | Customizable for other games |

### 🎯 Use a Specific Profile

```batch
python lunar.py --profile valorant
```

### 📋 List Available Profiles

```batch
python lunar.py --list-profiles
```

---

## 🎮 Usage

### Keyboard Controls

| Key | Action |
|-------|--------|
| **F1** | Enable/Disable assistance |
| **F2** | Exit program |
| **F3** | Show performance statistics |

### Command Line Options

```batch
# Normal mode
python lunar.py

# With calibration
python lunar.py --calibrate

# Specific profile
python lunar.py --profile fortnite

# Debug mode
python lunar.py --debug

# No admin check
python lunar.py --no-admin

# List profiles
python lunar.py --list-profiles
```

---

## 🔧 Troubleshooting

### ❌ The program only works when you Alt+Tab (doesn't work in the game)

**Cause:** Screen capture issue with fullscreen games.

**Solution:**
1. **Change the game to BORDERLESS WINDOW MODE** (more reliable)
2. Or run calibration and select `BitBlt` method
3. Or edit `lib/config/user_config.json`:
```json
{
  "capture_method": "bitblt"
}
```

### ❌ The program detects but doesn't move the mouse

**Cause:** Mouse method not compatible or no admin permissions.

**Solution:**
1. **Run as ADMINISTRATOR:** `start_admin.bat`
2. Or run calibration and test both methods
3. Verify that `lib/mouse/dd40605x64.dll` exists
4. If DDXoft fails, the system will automatically switch to Win32

### ❌ Error "CUDA IS UNAVAILABLE"

**Solution:**
```batch
# For RTX 5060 (sm_120):
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# For other GPUs:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

### ❌ Mouse moves too fast/slow

**Solution:**
Edit `lib/config/game_profiles.json` and adjust:
```json
{
  "movement": {
    "smoothing": 0.7,  // Lower = slower (0.3-1.0)
    "max_move_speed": 100  // Maximum speed
  }
}
```

### ❌ Detection is inaccurate

**Solution:**
Adjust in `lib/config/game_profiles.json`:
```json
{
  "detection": {
    "confidence": 0.50,  // Higher = more strict (0.4-0.7)
    "fov": 300  // Lower = smaller area
  }
}
```

---

## 📁 Project Structure

```
AI-Program_t/
├── lib/
│   ├── core/              # Main engines
│   │   ├── program_t_engine.py
│   │   ├── detection_engine.py
│   │   └── movement_engine.py
│   ├── capture/           # Screen capture
│   │   ├── capture_manager.py
│   │   ├── bitblt_capture.py
│   │   └── mss_capture.py
│   ├── input/             # Mouse input
│   │   ├── mouse_manager.py
│   │   ├── ddxoft_mouse.py
│   │   └── win32_mouse.py
│   ├── config/            # Configuration
│   │   ├── config_manager.py
│   │   ├── game_profiles.json
│   │   └── user_config.json
│   ├── utils/             # Utilities
│   │   ├── logger.py
│   │   ├── calibration.py
│   │   └── performance_monitor.py
│   └── yoloe-11l-seg.pt # YOLO-World v2 model
├── docs/
│   └── YOLO_WORLD_SETUP.md # Model guide
├── logs/                  # Log files
├── lunar.py               # Main entry point
├── download_yolov8_world.bat # Model download
└── start.bat              # Startup script
```

---

## 🎯 Advanced Features

### Movement Humanization

The movement engine includes:
- **Bézier Curves**: Natural curved trajectories
- **Gaussian Noise**: Simulated human imperfection
- **Random Overshoot**: Slightly overshooting the target
- **Acceleration/Deceleration**: Variable speed based on distance

### Target Stickiness

Reduces erratic changes between targets:
- Maintains current target if still visible
- Configurable distance tolerance
- Persistence across multiple frames

### Auto-Fallback

The system automatically detects and switches:
- If BitBlt fails → switches to MSS
- If DDXoft fails → switches to Win32
- Console notifications for each change

---

## 📊 Performance Monitoring

### View Live Statistics

Press **F3** during execution to see:
- Current, average, min, max FPS
- Frame time
- CPU and memory usage
- Total detections
- Total frames processed

### Detailed Logs

Logs are saved in `logs/` with:
- Timestamp for each event
- Category (ENGINE, CAPTURE, MOUSE, etc.)
- Level (DEBUG, INFO, WARNING, ERROR)
- Session-rotated files

---

## 🔒 Security and Responsibility

⚠️ **DISCLAIMER:**

This project is intended for **educational purposes** and for testing in **private, controlled environments only**.

- ✅ **USE** to learn about AI, computer vision, and object detection.
- ✅ **USE** to test and develop your own detection mitigation systems.
- ❌ **DO NOT** use this software in public online multiplayer games.
- ❌ **DO NOT** use this software to gain an unfair advantage over other players.

Misuse of this software can lead to:
- Permanent account suspensions from online services.
- Damage to online gaming communities.
- Other potential consequences.

**The user assumes all responsibility for their actions. Use this code responsibly.**

---

## 💬 Support and Community

### Discord
👉 [Join our Discord Community](https://discord.gg/aiprogram_t)

### Premium Version (Lunar V2)

The full version includes:
- ✅ 25+ customizable settings
- ✅ Integrated graphical interface
- ✅ Support for YOLOv8, v10, v12 and TensorRT
- ✅ Xbox controller support
- ✅ Logitech GHUB input
- ✅ AMD and NVIDIA compatible

[Download Lunar V2](https://gannonr.com/lunar)

---

## 📝 License

This project is under MIT license. See `LICENSE` for details.

---

## 🙏 Credits

- Original project: [Lunar by zeyad-mansour](https://github.com/zeyad-mansour/lunar)
- YOLO model: [Ultralytics](https://github.com/ultralytics/ultralytics)
- Discord community

---

## 📈 Changelog

### v2.0.0 (2024)
- ✨ Completely rewritten architecture
- ✨ Multi-game support with profiles
- ✨ Automatic calibration system
- ✨ Advanced humanization engine
- ✨ Improved logging and monitoring
- ✨ Auto-fallback for capture and mouse
- ✨ Target stickiness and deadzone
- ✨ Real-time performance monitor

### v1.0.0
- 🎯 Original version with YOLOv8/v12
- 🎯 Basic Fortnite support
- 🎯 MSS capture and Win32 mouse

---

**Enjoy the project and use it responsibly! 🎮🤖**
