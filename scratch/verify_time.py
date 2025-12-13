
# scratch/verify_time.py
import sys
import os

# Mock MicroPython modules
from unittest.mock import MagicMock
import sys

# Mock uasyncio
mock_asyncio = MagicMock()
mock_asyncio.sleep_ms = MagicMock()
sys.modules['uasyncio'] = mock_asyncio

# Mock machine
mock_machine = MagicMock()
sys.modules['machine'] = mock_machine

# Mock neopixel
mock_neopixel = MagicMock()
sys.modules['neopixel'] = mock_neopixel

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__)) # scratch/
parent_dir = os.path.dirname(script_dir) # NeoDev/
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Try imports
try:
    import time_keeper
    import time_display
    import neodisplay
    print("Imports successful")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

# Check TimeKeeper
try:
    h, m, s = time_keeper.get_time()
    print(f"TimeKeeper working: {h}:{m}:{s}")
except Exception as e:
    print(f"TimeKeeper error: {e}")

# Check TimeDisplay instantiation and draw
try:
    # Initialize NeoDisplay (uses mocked machine/neopixel)
    nd = neodisplay.NeoDisplay(16)
    
    # Test HH:MM
    td = time_display.TimeDisplay(mode=time_display.HH_MM)
    # We can access the private _draw method or call run() (but run is async loop)
    # Let's call _draw() directly for testing logic
    td._draw() 
    print("Draw HH:MM success")
    
    # Test HH:MM SS
    td2 = time_display.TimeDisplay(mode=time_display.HH_MM_SS)
    td2._draw()
    print("Draw HH:MM SS success")
    
except Exception as e:
    print(f"TimeDisplay error: {e}")
    import traceback
    traceback.print_exc()
