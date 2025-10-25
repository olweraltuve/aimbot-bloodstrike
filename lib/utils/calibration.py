"""
Calibration Utility
==================
Herramienta de calibración para diferentes juegos.
"""

import json
import time
from pathlib import Path
from termcolor import colored
from lib.utils.logger import logger

class CalibrationWizard:
    """Asistente de calibración para juegos"""
    
    def __init__(self):
        self.config_path = Path("lib/config/user_config.json")
    
    def run(self):
        """Ejecuta el asistente de calibración"""
        print(colored("\n" + "="*60, "cyan"))
        print(colored("  AI PROGRAM_T - CALIBRATION WIZARD", "cyan", attrs=['bold']))
        print(colored("="*60 + "\n", "cyan"))
        
        # Seleccionar juego
        game_profile = self._select_game()
        
        # Calibrar sensibilidad (opcional para algunos juegos)
        if self._ask_yes_no("Do you want to calibrate sensitivity settings?"):
            self._calibrate_sensitivity()
        
        # Configurar método de captura
        capture_method = self._select_capture_method()
        
        # Configurar método de mouse
        mouse_method = self._select_mouse_method()
        
        # Guardar configuración
        self._save_config(game_profile, capture_method, mouse_method)
        
        print(colored("\n✅ Calibration complete!", "green", attrs=['bold']))
        print(colored("You can now run the program_t with your settings.\n", "green"))
    
    def _select_game(self) -> str:
        """Selecciona el perfil del juego"""
        from lib.config.config_manager import config
        
        profiles = config.list_profiles()
        
        print(colored("Available game profiles:", "yellow"))
        for i, profile_name in enumerate(profiles, 1):
            profile = config.get_profile(profile_name)
            desc = profile.get('description', 'No description')
            print(f"  {i}. {colored(profile.get('name', profile_name), 'cyan')} - {desc}")
        
        while True:
            try:
                choice = input(colored("\nSelect profile number: ", "yellow"))
                idx = int(choice) - 1
                if 0 <= idx < len(profiles):
                    selected = profiles[idx]
                    config.set_active_profile(selected)
                    print(colored(f"✓ Selected: {selected}", "green"))
                    return selected
                else:
                    print(colored("Invalid selection. Try again.", "red"))
            except (ValueError, IndexError):
                print(colored("Invalid input. Enter a number.", "red"))
    
    def _calibrate_sensitivity(self):
        """Calibra la sensibilidad del juego"""
        print(colored("\n--- Sensitivity Calibration ---", "yellow"))
        print("This helps the program_t match your in-game mouse settings.")
        print("Make sure both X and Y sensitivity are the SAME in-game.\n")
        
        def get_float(prompt: str) -> float:
            while True:
                try:
                    value = float(input(colored(prompt, "cyan")))
                    if value > 0:
                        return value
                    print(colored("Value must be positive!", "red"))
                except ValueError:
                    print(colored("Invalid number. Try again.", "red"))
        
        xy_sens = get_float("Enter X/Y sensitivity (from in-game settings): ")
        targeting_sens = get_float("Enter targeting/ADS sensitivity (from in-game settings): ")
        
        # Calcular escalas
        xy_scale = 10.0 / xy_sens
        targeting_scale = 1000.0 / (targeting_sens * xy_sens)
        
        # Guardar en config.json
        config_data = {
            "xy_sens": xy_sens,
            "targeting_sens": targeting_sens,
            "xy_scale": xy_scale,
            "targeting_scale": targeting_scale,
            "_comment": "Sensitivity calibration settings"
        }
        
        config_path = Path("lib/config/config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
        
        print(colored("✓ Sensitivity calibrated and saved!", "green"))
    
    def _select_capture_method(self) -> str:
        """Selecciona el método de captura"""
        print(colored("\n--- Screen Capture Method ---", "yellow"))
        print("1. BitBlt (Recommended) - Works with fullscreen games")
        print("2. MSS - Faster, but only works with borderless windowed")
        print("3. Auto - Try BitBlt first, fallback to MSS")
        
        methods = ['bitblt', 'mss', 'auto']
        
        while True:
            choice = input(colored("\nSelect method (1-3): ", "cyan"))
            if choice in ['1', '2', '3']:
                selected = methods[int(choice) - 1]
                print(colored(f"✓ Selected: {selected}", "green"))
                return selected
            print(colored("Invalid choice. Enter 1, 2, or 3.", "red"))
    
    def _select_mouse_method(self) -> str:
        """Selecciona el método de mouse"""
        print(colored("\n--- Mouse Input Method ---", "yellow"))
        print("1. DDXoft (Recommended) - Low detection, requires admin")
        print("2. Win32 - High detection, may not work in fullscreen")
        print("3. Auto - Try DDXoft first, fallback to Win32")
        
        methods = ['ddxoft', 'win32', 'auto']
        
        while True:
            choice = input(colored("\nSelect method (1-3): ", "cyan"))
            if choice in ['1', '2', '3']:
                selected = methods[int(choice) - 1]
                print(colored(f"✓ Selected: {selected}", "green"))
                return selected
            print(colored("Invalid choice. Enter 1, 2, or 3.", "red"))
    
    def _ask_yes_no(self, question: str) -> bool:
        """Pregunta sí/no"""
        while True:
            response = input(colored(f"{question} (y/n): ", "cyan")).strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            print(colored("Please enter 'y' or 'n'.", "red"))
    
    def _save_config(self, profile: str, capture: str, mouse: str):
        """Guarda la configuración del usuario"""
        from lib.config.config_manager import config
        
        config.set_user_setting('active_profile', profile)
        config.set_user_setting('capture_method', capture)
        config.set_user_setting('mouse_method', mouse)
        
        logger.info("User configuration saved", "CALIBRATION")

def run_calibration():
    """Función helper para ejecutar la calibración"""
    wizard = CalibrationWizard()
    wizard.run()