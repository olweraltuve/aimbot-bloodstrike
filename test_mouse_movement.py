"""
Test Mouse Movement Script
===========================

This script tests if SendInput mouse movement works on your system.
Run this BEFORE testing in-game to verify that the mouse movement method works.

Instructions:
1. Run this script: python test_mouse_movement.py
2. Watch your mouse cursor - it should move in a small circle
3. If the mouse moves, SendInput works on your system
4. If the mouse doesn't move, you need to use ddxoft method instead
"""

import ctypes
import time
import math

PUL = ctypes.POINTER(ctypes.c_ulong)

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("mi", MouseInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

def test_sendinput():
    print("=" * 60)
    print("Testing SendInput Mouse Movement")
    print("=" * 60)
    print("\nYour mouse should move in a small circle...")
    print("If it doesn't move, SendInput is blocked on your system.\n")
    
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    
    # Wait 3 seconds before starting
    for i in range(3, 0, -1):
        print(f"Starting in {i}...")
        time.sleep(1)
    
    print("\n[TEST] Moving mouse in circle pattern...")
    
    # Draw a circle with mouse movement
    radius = 50
    steps = 36  # 36 steps = 10 degrees each
    success_count = 0
    
    for i in range(steps):
        angle = (i / steps) * 2 * math.pi
        
        # Calculate movement for this step
        if i == 0:
            dx = int(radius * math.cos(angle))
            dy = int(radius * math.sin(angle))
        else:
            prev_angle = ((i-1) / steps) * 2 * math.pi
            prev_x = int(radius * math.cos(prev_angle))
            prev_y = int(radius * math.sin(prev_angle))
            curr_x = int(radius * math.cos(angle))
            curr_y = int(radius * math.sin(angle))
            dx = curr_x - prev_x
            dy = curr_y - prev_y
        
        # Use SendInput to move mouse
        ii_.mi = MouseInput(dx, dy, 0, 0x0001, 0, ctypes.pointer(extra))
        command = Input(ctypes.c_ulong(0), ii_)
        result = ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))
        
        if result == 1:
            success_count += 1
        
        print(f"Step {i+1}/{steps}: dx={dx:4d}, dy={dy:4d}, result={result}")
        time.sleep(0.05)  # 50ms delay between movements
    
    print("\n" + "=" * 60)
    print(f"Test Complete: {success_count}/{steps} movements successful")
    print("=" * 60)
    
    if success_count == steps:
        print("\n✅ SUCCESS! SendInput works perfectly on your system.")
        print("   You can use 'win32' method in mouse_config.py")
    elif success_count > 0:
        print("\n⚠️  PARTIAL SUCCESS! SendInput works but may be unreliable.")
        print("   Consider using 'ddxoft' method in mouse_config.py")
    else:
        print("\n❌ FAILED! SendInput is blocked on your system.")
        print("   You MUST use 'ddxoft' method in mouse_config.py")
        print("\n   To enable ddxoft:")
        print("   1. Open lib/config/mouse_config.py")
        print("   2. Change: MOUSE_METHOD = 'ddxoft'")
        print("   3. Restart the aimbot")
    
    print("\n")

if __name__ == "__main__":
    try:
        test_sendinput()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nThe test failed with an error.")
        print("You may need to run this script as Administrator.")
    
    input("\nPress ENTER to exit...")

