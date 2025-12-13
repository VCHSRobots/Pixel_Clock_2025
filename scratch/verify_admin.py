
import sys
import unittest.mock
from unittest.mock import MagicMock

# Mock machine and neopixel modules
sys.modules['machine'] = MagicMock()
sys.modules['neopixel'] = MagicMock()

# Mock Pin and NeoPixel classes
pin_mock = MagicMock()
sys.modules['machine'].Pin = MagicMock(return_value=pin_mock)
sys.modules['machine'].Pin.OUT = 1

import asyncio
async def sleep_ms(ms):
    await asyncio.sleep(ms / 1000.0)
asyncio.sleep_ms = sleep_ms
sys.modules['uasyncio'] = asyncio

np_mock = MagicMock()
sys.modules['neopixel'].NeoPixel = MagicMock(return_value=np_mock)

# Now we can safely import user modules
import admin
import neodisplay
import dispman
import asyncio

async def test_logic():
    print("Running admin.test_manager()...")
    # admin.test_manager() runs asyncio.run() internally, which might conflict if we are already in an event loop.
    # But here we are just calling it from a script.
    # Wait, admin.test_manager calls asyncio.run(_test()). 
    # If I call it directly it should work.
    
    # We need to make sure NeoDisplay singleton is reset or initialized
    neodisplay.NeoDisplay._instance = None
    
    # Run the manager test
    # It prints to stdout, so we just want to ensure it doesn't crash 
    # and calls the right things on the mock.
    
    print("--- START admin.test_manager ---")
    admin.test_manager()
    print("--- END admin.test_manager ---")
    
    print("\nRunning admin.test_animations()...")
    print("--- START admin.test_animations ---")
    admin.test_animations()
    print("--- END admin.test_animations ---")

if __name__ == "__main__":
    # We don't need asyncio.run here because admin functions call it themselves
    try:
        # Just run the function
        # Note: calling asyncio.run() inside asyncio.run() is not allowed.
        # But here we are at top level.
        test_logic_sync = asyncio.new_event_loop().run_until_complete
        # Wait, admin.test_manager calls asyncio.run().
        # So we should just call admin.test_manager() directly.
        pass
    except Exception as e:
        print(f"Test Setup Error: {e}")

    # Reset asyncio touchiness if any
    
    print("Starting verification...")
    try:
        admin.test_manager()
        print("\ntest_manager PASSED (no crash)")
    except Exception as e:
        print(f"\ntest_manager FAILED: {e}")
        import traceback
        traceback.print_exc()
        
    try:
        admin.test_animations()
        print("\ntest_animations PASSED (no crash)")
    except Exception as e:
        print(f"\ntest_animations FAILED: {e}")
        import traceback
        traceback.print_exc()

    print("Verification Script Done.")
