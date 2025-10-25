"""
Lunar AI Program_t - Main Entry Point
===================================
Neural Network-based program_t with multi-game support.

Usage:
    python lunar.py              - Run with default settings
    python lunar.py --calibrate  - Run calibration wizard
    python lunar.py --profile fortnite - Use specific game profile
    python lunar.py --debug      - Enable debug mode
"""

import os
import sys
import argparse
from pathlib import Path
from pynput import keyboard
from termcolor import colored

# ==================== INICIO DE LA SOLUCIÓN - CORRECCIÓN DPI ====================
# Esto DEBE ejecutarse ANTES de cualquier otra cosa, especialmente antes de importar
# módulos locales que usen 'ctypes' (como admin_check). De esta forma, garantizamos
# que el proceso se marque como DPI-Aware desde el principio.
import platform
if platform.system() == "Windows":
    try:
        import ctypes
        # Usamos la API de shcore.dll, que es la forma moderna y recomendada.
        # El valor '2' corresponde a PER_MONITOR_AWARE_V2.
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (ImportError, AttributeError):
        # Si falla (ej. Windows 7), usamos el método más antiguo.
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception as e:
            # If everything fails, warn the user via logger.
            from lib.utils.logger import logger
            logger.warning(f"Could not set DPI awareness. Resolution might be incorrect on scaled displays: {e}", "MAIN")
# ===================== FIN DE LA SOLUCIÓN - CORRECCIÓN DPI =====================


# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

# Import utilities
from lib.utils.logger import logger
from lib.utils.calibration import run_calibration
from lib.config.config_manager import config

# Import admin check
try:
    from admin_check import check_and_request_admin
except ImportError:
    logger.warning("Admin check module not found. Running without admin check.", "MAIN")
    def check_and_request_admin():
        return False

# Global reference to program_t engine
program_t_engine = None

def on_key_release(key):
    """Maneja eventos de teclado"""
    global program_t_engine
    
    try:
        if key == keyboard.Key.f1:
            if program_t_engine:
                program_t_engine.toggle_program_t()
        elif key == keyboard.Key.f2:
            if program_t_engine:
                program_t_engine.stop()
        elif key == keyboard.Key.f3:
            if program_t_engine:
                program_t_engine.perf_monitor.print_stats()
        elif key == keyboard.Key.f4:
            # NUEVO: Iniciar calibración adaptativa con targets reales
            if program_t_engine:
                program_t_engine.start_adaptive_learning()
        elif key == keyboard.Key.f5:
            if program_t_engine:
                program_t_engine.save_learning_profile()
    except Exception as e:
        logger.error(f"Error in key handler: {e}", "MAIN")

def print_banner():
    """Imprime el banner de inicio"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    banner = r'''
  _    _   _ _   _    _    ____     _     ___ _____ _____ 
 | |  | | | | \ | |  / \  |  _ \   | |   |_ _|_   _| ____|
 | |  | | | |  \| | / _ \ | |_) |  | |    | |  | | |  _|  
 | |__| |_| | |\  |/ ___ \|  _ <   | |___ | |  | | | |___ 
 |_____\___/|_| \_/_/   \_\_| \_\  |_____|___| |_| |_____|
                                                           
        🧠 AI-Powered Neural Network Program_t 🎯
        Version 2.0 - Multi-Game Support Edition
'''
    print(colored(banner, "green", attrs=['bold']))
    print(colored("="*60, "cyan"))
    print(colored("  LUNAR LITE - Free Edition", "yellow"))
    print(colored("  For full version, visit: https://gannonr.com/lunar", "yellow"))
    print(colored("  Discord: discord.gg/aiprogram_t", "yellow"))
    print(colored("="*60 + "\n", "cyan"))
    
    from lib.input.suspend_key_manager import suspend_manager

    if suspend_manager.suspend_key:
        key_name = suspend_manager._key_to_string(suspend_manager.suspend_key)
        print(colored(f"  Hold '{key_name}' to temporarily suspend program_t", "cyan"))

def check_requirements():
    """Verifica que todos los archivos necesarios existan"""
    required_files = [
        "lib/yoloe-11l-seg.pt",
        "lib/config/game_profiles.json"
    ]
    
    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)
    
    if missing:
        logger.error("Missing required files:", "MAIN")
        for f in missing:
            logger.error(f"  - {f}", "MAIN")
        logger.error("Please ensure all files are present.", "MAIN")
        return False
    
    return True

def setup_environment():
    """Configura el entorno de ejecución"""
    # Ocultar mensajes de pygame
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
    
    # Crear directorios necesarios
    directories = [
        "lib/config",
        "logs",
        "lib/data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def parse_arguments():
    """Parsea argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Lunar AI Program_t - Neural Network-based aim assistance',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--calibrate', 
        action='store_true',
        help='Run calibration wizard for game-specific settings'
    )
    
    parser.add_argument(
        '--profile',
        type=str,
        default=None,
        help='Specify game profile to use (e.g., fortnite, valorant)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with verbose logging'
    )
    
    parser.add_argument(
        '--no-admin',
        action='store_true',
        help='Skip admin privilege check (not recommended)'
    )
    
    parser.add_argument(
        '--list-profiles',
        action='store_true',
        help='List all available game profiles'
    )
    
    return parser.parse_args()

def list_available_profiles():
    """Lista todos los perfiles disponibles"""
    profiles = config.list_profiles()
    
    print(colored("\n📋 Available Game Profiles:", "cyan", attrs=['bold']))
    print(colored("="*60, "cyan"))
    
    for profile_name in profiles:
        profile = config.get_profile(profile_name)
        name = profile.get('name', profile_name)
        desc = profile.get('description', 'No description')
        
        print(colored(f"\n🎮 {name}", "yellow", attrs=['bold']))
        print(colored(f"   ID: {profile_name}", "white"))
        print(colored(f"   Description: {desc}", "white"))
        
        # Mostrar configuración clave
        det = profile.get('detection', {})
        mov = profile.get('movement', {})
        
        print(colored(f"   FOV: {det.get('fov', 'N/A')}", "white"))
        print(colored(f"   Smoothing: {mov.get('smoothing', 'N/A')}", "white"))
    
    print(colored("\n" + "="*60 + "\n", "cyan"))

def main():
    """Función principal"""
    
    global program_t_engine
    
    # Parsear argumentos
    args = parse_arguments()
    
    # Configurar entorno
    setup_environment()
    
    # Mostrar banner
    print_banner()
    
    # Listar perfiles si se solicita
    if args.list_profiles:
        list_available_profiles()
        return
    
    # Verificar requisitos
    if not check_requirements():
        logger.critical("Requirement check failed. Exiting.", "MAIN")
        input("Press ENTER to exit...")
        return
    
    # Calibración
    if args.calibrate:
        run_calibration()
        
        response = input(colored("\nDo you want to start the program_t now? (y/n): ", "cyan"))
        if response.lower() not in ['y', 'yes']:
            logger.info("Exiting after calibration.", "MAIN")
            return
    
    # Verificar privilegios de administrador
    if not args.no_admin:
        check_and_request_admin()
    
    # Información de inicio
    logger.info("Starting Lunar AI Program_t...", "MAIN")
    
    # Cargar perfil
    profile_name = args.profile or config.get_user_setting('active_profile', 'default')
    logger.info(f"Using profile: {profile_name}", "MAIN")
    
    # Inicializar program_t engine
    try:
        from lib.core.program_t_engine import ProgramTEngine
        
        program_t_engine = ProgramTEngine(profile_name=profile_name)
        
        # Configurar listener de teclado
        listener = keyboard.Listener(on_release=on_key_release)
        listener.start()
        
        logger.info("Keyboard listener started", "MAIN")
        logger.info("Press F1 to toggle program_t", "MAIN")
        logger.info("Press F2 to exit", "MAIN")
        logger.info("Press F3 to show performance stats", "MAIN")
        logger.info("Press F4 to start ADAPTIVE LEARNING (learns from real targets)", "MAIN")
        logger.info("Press F5 to save learned profile", "MAIN")
        
        # Ejecutar bucle principal
        program_t_engine.run()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user (Ctrl+C)", "MAIN")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", "MAIN")
        import traceback
        logger.critical(traceback.format_exc(), "MAIN")
    finally:
        # Cleanup
        if program_t_engine:
            program_t_engine.cleanup()
        
        logger.info("Program_t stopped. Goodbye!", "MAIN")
        input("\nPress ENTER to exit...")

if __name__ == "__main__":
    main()
