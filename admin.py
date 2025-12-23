# admin.py - Utilities for control over the clock from the REPL
# Dec 2025, dlb with AI

import machine
import time
import asyncio
import neodisplay
from neodisplay import NeoDisplay

def scroll(text="Scroll Test", color=neodisplay.GREEN, font=None, interval=0.05):
    """Scroll text and return. interval=delay in seconds."""
    d = neodisplay.get_display()
    print(f"Scrolling '{text}' (speed={interval})...")
    asyncio.run(d.scroll_msg(text, color, interval=interval, font=font))
    print("Scroll Done.")

def clear():
    """Clear the display."""
    d = neodisplay.get_display()
    d.fill(neodisplay.BLACK)
    d.show()
    print("Display cleared.")

def test_rgb(delay=0.5):
    """Cycle full screen Red, Green, Blue, White."""
    d = neodisplay.get_display()
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
    d = neodisplay.get_display()
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
    d = neodisplay.get_display()
    clear()
    print(f"Writing '{text}'")
    d.write_text(0, 1, text, color)
    d.show()

def set_pixel(x, y, color=neodisplay.WHITE):
    """Manually set a single pixel."""
    d = neodisplay.get_display()
    print(f"Setting ({x}, {y}) to {color}")
    d.pixel(x, y, color)
    d.show()
    
def brightness(val):
    """Set brightness (0.0 - 1.0)."""
    d = neodisplay.get_display()
    print(f"Setting brightness to {val}")
    d.brightness(val)
    d.show() # to apply

print("NeoDisplay Admin Loaded.")
print("Functions: clear(), test_rgb(), test_corners(), test_text(str), set_pixel(x,y,c), brightness(val)")
print("           scroll(str), test_manager(), test_animations(), test_colored_scroll()")
print("           test_pulse(), test_bouncing_box(), test_scrolling_text(), test_rainbow()")

def char(c):
    """Write a single character."""
    d = neodisplay.get_display()
    clear()
    print(f"Writing '{c}'")
    d.write_text(0, 1, c, neodisplay.CYAN)
    d.show()

def test_manager():
    """Test DisplayManager queue/immediate logic."""
    from dispman import DisplayManager
    from animations import ScrollingText
    from animations import BouncingBox
    
    d = neodisplay.get_display()
    
    async def _test():
        print("Initializing Logic Manager...")
        default_anim = BouncingBox(color=neodisplay.YELLOW, size=2, speed=0.01)
        mgr = dispman.get_display_manager(default_anim)
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
    
    d = neodisplay.get_display()
    # Mock default animation? No, just rely on foreground for test
    async def _run_tests():
        mgr = dispman.get_display_manager()
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
    
    d = neodisplay.get_display()
    
    async def _run_test():
        mgr = dispman.get_display_manager()
        
        
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

def test_pulse(color=neodisplay.RED, count=5):
    """Test the Pulse animation."""
    from dispman import DisplayManager
    from animations import Pulse
       
    async def _run():
        mgr = dispman.get_display_manager()
        print(f"Testing Pulse (count={count})...")
        # Pulse doesn't have a 'loops' count in __init__, so we play it and wait or check implementation.
        # Looking at animations.py, Pulse loop is "while not self.stopped".
        # So we queue it, let it run for a bit/cancel it, or we can't really "count" pulses easily 
        # unless we modify Pulse or just sleep for (interval * 2 * count).
        # Pulse interval is 1.0 (500ms on, 500ms off).
        
        # Actually animations.Pulse takes interval param. default 1.0.
        anim = Pulse(color=color, interval=0.5) # slightly faster for test
        mgr.play_immediate(anim)
        
        # Calculate duration: count * (0.5 on + 0.5 off)??
        # Pulse implementation: 500ms on, 500ms off. Hardcoded sleep_ms(500).
        # Wait, let's re-read Pulse implementation in animations.py.
        # It has self.interval but uses hardcoded 500ms sleeps.
        # That's a bug or unfinished feature in Pulse. 
        # I should probably fix Pulse first if I want to test it properly, 
        # but the prompt is "Add functions to test". 
        # I'll stick to running it for a duration.
        
        duration = count * 1.0 # 1 sec per pulse approx
        await asyncio.sleep(duration)
        
        mgr.stop()
        print("Pulse Test Done.")

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        print("Interrupted.")

def test_bouncing_box(color=neodisplay.BLUE, size=2, duration=10):
    """Test the Bouncing Box animation."""
    from dispman import DisplayManager
    from animations import BouncingBox
    
    async def _run():
        mgr = dispman.get_display_manager()
        print(f"Testing BouncingBox for {duration} seconds...")
        anim = BouncingBox(color=color, size=size, speed=0.05)
        mgr.play_immediate(anim)
        
        await asyncio.sleep(duration)
        
        mgr.stop()
        print("BouncingBox Test Done.")
        
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        print("Interrupted.")

def test_scrolling_text(text="Hello World", color=neodisplay.CYAN, loops=2):
    """Test the Scrolling Text animation."""
    from dispman import DisplayManager
    from animations import ScrollingText
    
    async def _run():
        mgr = dispman.get_display_manager()
        print(f"Testing ScrollingText: '{text}' (loops={loops})...")
        anim = ScrollingText(text, color=color, speed=0.08, loops=loops)
        mgr.queue_for_play(anim)
        
        await mgr.wait_idle()
        
        mgr.stop()
        print("ScrollingText Test Done.")

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        print("Interrupted.")

def test_rainbow(duration=10, speed=2, scale=5, brightness=0.2):
    """Test the Rainbow animation."""
    from dispman import DisplayManager
    from animations import Rainbow  
    
    async def _run():
        mgr = dispman.get_display_manager()
        print(f"Testing Rainbow for {duration} seconds...")
        anim = Rainbow(speed=speed, scale=scale, brightness=brightness)
        mgr.play_immediate(anim)
        
        await asyncio.sleep(duration)
        
        mgr.stop()
        print("Rainbow Test Done.")

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        print("Interrupted.")

def run():
    """Start the main application loop."""
    print("Starting Main Application...")
    import gc
    gc.collect()
    import main
    try:
        asyncio.run(main.main())
    except KeyboardInterrupt:
        print("Main Application Stopped.")

def test_message(msg="Hi!", duration=3, color=neodisplay.GREEN):
    """Test MessageDisplay animation."""
    from dispman import DisplayManager
    from animations import MessageDisplay
    
    async def _run():
        mgr = dispman.get_display_manager()
        print(f"Testing MessageDisplay: '{msg}' for {duration}s...")
        
        # Test 1: Plain string
        anim = MessageDisplay(msg, duration=duration, color=color)
        mgr.play_immediate(anim)
        await mgr.wait_idle()
        
        print("Test 1 Done.")
        await asyncio.sleep(1)
        
        # Test 2: Colored list (manual construction for test)
        print("Testing Colored Message...")
        colored_msg = [
            ('H', neodisplay.RED),
            ('e', neodisplay.ORANGE),
            ('l', neodisplay.YELLOW),
            ('l', neodisplay.GREEN),
            ('o', neodisplay.BLUE)
        ]
        anim2 = MessageDisplay(colored_msg, duration=3)
        mgr.queue_for_play(anim2)
        await mgr.wait_idle()
        
        print("Message Test Complete.")
        mgr.stop()

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        print("Interrupted.")

def reset_rtc():
    """Resets the External RTC (DS3231) to 2000-01-01 00:00:00."""
    try:
        import rtc_module
        rtc = rtc_module.get_rtc()
        if not rtc.is_working():
            print("RTC Module Not Detected!")
            return
            
        # (year, month, day, hour, minute, second, weekday, yearday)
        # 2000-01-01 was Saturday (5? 6?)
        # Let's verify weekday for 2000-01-01.
        # Python: Monday=0. Saturday=5.
        
        # Reset to Midnight Jan 1 2000
        tm = (2000, 1, 1, 0, 0, 0, 5, 1)
        
        rtc.set_time(tm)
        print("RTC Reset to 2000-01-01 00:00:00.")
        
        # Verify
        check = rtc.get_time()
        print(f"RTC Verification Read: {check}")
        
    except Exception as e:
        print(f"Failed to reset RTC: {e}")

def test_ntp():
    """Test NTP retrieval without setting RTC."""
    import netcomm
    import ntptime
    import time
    
    nc = netcomm.get_netcomm()
    if not nc.is_connected():
        print("Network not connected. Status:", nc.get_status_str())
        
    try:
        print("Querying NTP (pool.ntp.org)...")
        t = ntptime.get_ntp_time()
        print(f"NTP Epoch: {t}")
        
        tm = time.localtime(t)
        # year, month, day, hour, minute, second, weekday, yearday
        print(f"NTP Localtime (UTC): {tm[0]}-{tm[1]:02d}-{tm[2]:02d} {tm[3]:02d}:{tm[4]:02d}:{tm[5]:02d}")
    except Exception as e:
        print(f"NTP Failed: {e}")

def debug_time_calc():
    """Debug time calculation pipeline."""
    import time
    import rtc_module
    import settings_manager
    
    rtc = rtc_module.get_rtc()
    settings = settings_manager.get_settings_manager()
    
    # 1. RTC Read
    t_rtc = rtc.get_time()
    print(f"1. RTC Tuples (UTC): {t_rtc}")
    
    # 2. Mktime
    try:
        utc_seconds = time.mktime(t_rtc)
        print(f"2. UTC Seconds: {utc_seconds}")
    except Exception as e:
        print(f"2. Mktime Failed: {e}")
        return

    # 3. Offset
    offset = settings.get("timezone_offset", -8)
    print(f"3. Offset: {offset}")
    
    local_seconds = utc_seconds + (offset * 3600)
    print(f"4. Local Seconds (Standard): {local_seconds}")
    
    # 4. DST
    # Copy _is_dst_us logic briefly or test it
    t = time.localtime(local_seconds)
    print(f"5. Local Tuple (Standard): {t}")
    
    # DST Check
    # We need to access TimeKeeper's logic, or replicate it
    import time_keeper
    tk = time_keeper.get_time_keeper()
    is_dst = tk._is_dst_us(local_seconds)
    print(f"6. Is DST? {is_dst}")
    
    if is_dst:
        local_seconds += 3600
        print(f"7. Local Seconds (DST): {local_seconds}")
        
    final_t = time.localtime(local_seconds)
    print(f"8. Final Tuple: {final_t}")

def reset():
    """Reset the device to factory defaults."""
    import os
    import machine
    
    print("Resetting device to factory defaults...")
    try :
        os.remove("ssid.json")
    except:
        pass
    reset_rtc()
    print("Clock will go into setup mode.")

def reboot():
    """Reboot the device."""
    import machine
    machine.reset() 