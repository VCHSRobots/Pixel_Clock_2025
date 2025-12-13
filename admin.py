# admin.py - Utilities for control over the clock from the REPL
# Dec 2025, dlb with AI

import machine
import time
import asyncio
import neodisplay
from neodisplay import NeoDisplay


# Default Pin
PIN_NUM = 16

def get_d():
    """Get or create the NeoDisplay instance."""
    d = NeoDisplay.inst()
    if d is None:
        print(f"Initializing NeoDisplay on pin {PIN_NUM}...")
        try:
            d = NeoDisplay(PIN_NUM)
        except RuntimeError:
            # Race condition or it was just created
            d = NeoDisplay.inst()
    return d

def scroll(text="Scroll Test", color=neodisplay.GREEN, font=None, interval=0.05):
    """Scroll text and return. interval=delay in seconds."""
    d = get_d()
    print(f"Scrolling '{text}' (speed={interval})...")
    asyncio.run(d.scroll_msg(text, color, interval=interval, font=font))
    print("Scroll Done.")

def clear():
    """Clear the display."""
    d = get_d()
    d.fill(neodisplay.BLACK)
    d.show()
    print("Display cleared.")

def test_rgb(delay=0.5):
    """Cycle full screen Red, Green, Blue, White."""
    d = get_d()
    colors = [
        ('Red', neodisplay.RED),
        ('Green', neodisplay.GREEN),
        ('Blue', neodisplay.BLUE),
        ('White', neodisplay.WHITE),
    ]
    
    for name, c in colors:
        print(f"Showing {name}")
        d.fill(c)
        d.show()
        time.sleep(delay)
    
    clear()
    print("RGB Test Done.")

def test_corners():
    """Light up the 4 corners to verify orientation."""
    d = get_d()
    clear()
    
    w, h = NeoDisplay.WIDTH, NeoDisplay.HEIGHT
    
    corners = [
        (0, 0, neodisplay.RED, "Top-Left (Red)"),
        (w-1, 0, neodisplay.GREEN, "Top-Right (Green)"),
        (0, h-1, neodisplay.BLUE, "Bottom-Left (Blue)"),
        (w-1, h-1, neodisplay.YELLOW, "Bottom-Right (Yellow)"),
    ]
    
    for x, y, c, name in corners:
        print(f"Lighting {name} at ({x}, {y})")
        d.pixel(x, y, c)
        d.show()
        time.sleep(0.5)
        
    print("Corner Test Done.")

def test_text(text="Test", color=neodisplay.CYAN):
    """Write static text."""
    d = get_d()
    clear()
    print(f"Writing '{text}'")
    d.write_text(0, 1, text, color)
    d.show()

def set_pixel(x, y, color=neodisplay.WHITE):
    """Manually set a single pixel."""
    d = get_d()
    print(f"Setting ({x}, {y}) to {color}")
    d.pixel(x, y, color)
    d.show()
    
def brightness(val):
    """Set brightness (0.0 - 1.0)."""
    d = get_d()
    print(f"Setting brightness to {val}")
    d.brightness(val)
    d.show() # to apply

print("NeoDisplay Admin Loaded.")
print("Functions: clear(), test_rgb(), test_corners(), test_text(str), set_pixel(x,y,c), brightness(val)")
print("           scroll(str), test_manager(), test_animations(), test_colored_scroll()")

def test_manager():
    """Test DisplayManager queue/immediate logic."""
    from dispman import DisplayManager
    from animations import ScrollingText
    from animations import BouncingBox
    
    d = get_d()
    
    async def _test():
        print("Initializing Logic Manager...")
        default_anim = BouncingBox(color=neodisplay.YELLOW, size=2, speed=0.01)
        mgr = DisplayManager(default_anim)
        await asyncio.sleep(4)
        
        print("1. Queueing 2 messages (ScrollingText loops=1)...")
        mgr.queue_for_play(ScrollingText("Msg 1", speed=0.05, color=neodisplay.GREEN, loops=1))
        mgr.queue_for_play(ScrollingText("Msg 2", speed=0.075, color=neodisplay.BLUE, loops=1))
        
        print("   Waiting for them (approx 2 scrolls)...")
        await mgr.wait_idle()
        
        print("2. Testing Immediate Interrupt...")
        # Queue something that would take a while
        mgr.queue_for_play(ScrollingText("This should be cancelled", color=(50, 50, 50), loops=5))
        await asyncio.sleep(3) # Let it start
        
        print("   Interrupting now!")
        mgr.play_immediate(ScrollingText("INTERRUPT!", speed=0.02, color=neodisplay.RED, loops=2))
        await mgr.wait_idle()
        
        await asyncio.sleep(3)  # Go back to default
        print("Manager Test Complete.")
        mgr.stop()
        
    asyncio.run(_test())

def test_animations():
    """Test the new animations in animations.py."""
    from dispman import DisplayManager
    from animations import ScrollingText, BouncingBox
    
    d = get_d()
    # Mock default animation? No, just rely on foreground for test
    async def _run_tests():
        mgr = DisplayManager()
        print("1. Playing ScrollingText (queue, loops=1)...")
        anim1 = ScrollingText("Hello World!", color=neodisplay.MAGENTA, speed=0.08, loops=1)
        mgr.queue_for_play(anim1)
        
        # Wait until idle
        await mgr.wait_idle()
        print("   Scroll finished.")
        
        print("2. Playing BouncingBox (immediate)...")
        box = BouncingBox(color=neodisplay.YELLOW, size=2, speed=0.05)
        mgr.play_immediate(box)
        
        print("   Letting box run for 5 seconds...")
        await asyncio.sleep(5)
        
        print("Tests Complete. Stopping Manager.")
        mgr.stop()
        
    try:
        asyncio.run(_run_tests())
    except KeyboardInterrupt:
        mgr.stop()
        print("Interrupted.")

def test_colored_scroll():
    """Test the Multi-Colored Scrolling Text."""
    from dispman import DisplayManager
    from animations import ScrollingColoredText, ColorStringBuilder
    
    d = get_d()
    
    async def _run_test():
        mgr = DisplayManager()
        
        print("Building colored string...")
        sb = ColorStringBuilder()
        sb.add("R", neodisplay.RED)
        sb.add("G", neodisplay.GREEN)
        sb.add("B", neodisplay.BLUE)
        sb.add(" ", neodisplay.BLACK)
        sb.add("Cyber", neodisplay.CYAN)
        sb.add("Punk", neodisplay.MAGENTA)
        sb.add(" ", neodisplay.BLACK)
        sb.add("2025", neodisplay.YELLOW)
        
        print("Queueing ScrollingColoredText (loops=2)...")
        anim = ScrollingColoredText(sb, speed=0.08, loops=2)
        mgr.queue_for_play(anim)
        
        await mgr.wait_idle()
        print("Test Complete.")
        mgr.stop()

    try:
        asyncio.run(_run_test())
    except KeyboardInterrupt:
        print("Interrupted.")
