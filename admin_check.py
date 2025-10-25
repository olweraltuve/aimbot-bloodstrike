"""
Admin Permission Check and Elevation for Windows
This module provides functions to check for administrator privileges
and request elevation if needed for the AI Program_t application.
"""

import ctypes
import os
import sys
import subprocess
import platform
from termcolor import colored

def is_admin():
    """
    Check if the current process has administrator privileges.
    
    Returns:
        bool: True if running as administrator, False otherwise
    """
    try:
        # Method 1: Check using ctypes (Windows)
        if platform.system() == 'Windows':
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            # On non-Windows systems, check for root/sudo
            return os.geteuid() == 0
    except Exception as e:
        print(f"[WARNING] Failed to check admin status: {e}")
        return False

def request_admin_elevation():
    """
    Request administrator privileges by restarting the script with UAC prompt.
    
    Returns:
        bool: True if elevation was requested, False if already admin or failed
    """
    if is_admin():
        return False  # Already running as admin
    
    print(colored("[INFO] Administrator privileges required for optimal performance", "yellow"))
    print(colored("[INFO] Requesting elevation via UAC...", "yellow"))
    
    try:
        # Get the current script path
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
        
        # Request UAC elevation
        ctypes.windll.shell32.ShellExecuteW(
            None,  # hwnd
            "runas",  # operation (run as administrator)
            sys.executable,  # executable (Python interpreter)
            f'"{script}" {params}',  # parameters
            None,  # working directory
            1  # nShow (SW_SHOWNORMAL)
        )
        
        print(colored("[SUCCESS] Admin elevation requested. Please accept UAC prompt.", "green"))
        return True
        
    except Exception as e:
        print(colored(f"[ERROR] Failed to request admin elevation: {e}", "red"))
        print(colored("[INFO] You can run the application as administrator manually", "yellow"))
        return False

def check_and_request_admin():
    """
    Main function to check admin status and request elevation if needed.
    
    Returns:
        bool: True if running as admin or elevation successful, False otherwise
    """
    if is_admin():
        print(colored("[SUCCESS] Running with administrator privileges", "green"))
        return True
    
    print(colored("[WARNING] Running without administrator privileges", "yellow"))
    print(colored("[INFO] Some features may not work optimally:", "yellow"))
    print(colored("  - Low-level mouse input simulation", "yellow"))
    print(colored("  - Screen capture in fullscreen applications", "yellow"))
    print(colored("  - System-level optimizations", "yellow"))
    
    # Ask user if they want to elevate
    try:
        response = input(colored("Do you want to restart with admin privileges? (y/N): ", "cyan")).strip().lower()
        if response in ['y', 'yes']:
            if request_admin_elevation():
                sys.exit(0)  # Exit current process, elevated one will start
            else:
                print(colored("[INFO] Continuing without admin privileges...", "yellow"))
                return False
        else:
            print(colored("[INFO] Continuing without admin privileges...", "yellow"))
            return False
    except (KeyboardInterrupt, EOFError):
        print(colored("\n[INFO] Continuing without admin privileges...", "yellow"))
        return False

def get_admin_benefits():
    """
    Returns a description of benefits when running with admin privileges.
    """
    benefits = [
        "Enhanced mouse input simulation for better anti-cheat compatibility",
        "Improved screen capture in fullscreen applications",
        "Better system resource management",
        "Reduced input latency",
        "Compatibility with more game protection systems"
    ]
    return benefits

if __name__ == "__main__":
    # Test the admin check functionality
    print("Admin Permission Check Test")
    print(f"Running as admin: {is_admin()}")
    
    if not is_admin():
        print("Benefits of admin privileges:")
        for benefit in get_admin_benefits():
            print(f"  - {benefit}")
        
        if input("Test elevation? (y/N): ").lower() == 'y':
            check_and_request_admin()