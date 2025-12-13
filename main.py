import uasyncio as asyncio
import neodisplay
import dispman  
import time_display  

PIN_NUM = 16  # Change as needed

if neodisplay.NeoDisplay.inst() is None:
    display = neodisplay.NeoDisplay(PIN_NUM, brightness=0.1)
else:
    display = neodisplay.NeoDisplay.inst()

async def anim_scroll_text():
    """Scrolls text with punctuation."""
    d = NeoDisplay.inst()
    text = "Hello World! (123) abc"
    colors = [neodisplay.RED, neodisplay.GREEN, neodisplay.BLUE, neodisplay.YELLOW, neodisplay.CYAN, neodisplay.MAGENTA]
    color_idx = 0
    
    while True:
        # Draw text
        d.fill(neodisplay.BLACK)
        d.write_text(0, 1, text, colors[color_idx])
        d.show()
        
        # Scroll loop
        for _ in range(len(text) * 6 + NeoDisplay.WIDTH): 
            d.scroll_left(1)
            d.show()
            await asyncio.sleep(0.05)
            
        color_idx = (color_idx + 1) % len(colors)
        await asyncio.sleep(0.5)

async def anim_small_text():
    """Scrolls text using the small 3x5 font."""
    d = NeoDisplay.inst()
    text = "Small Font 3x5!"
    color = (200, 200, 200)
    
    while True:
        d.fill(neodisplay.BLACK)
        d.write_text(0, 2, text, color, font=NeoDisplay.FONT_SMALL) # Centered vertically (2 offset)
        d.show()
        
        for _ in range(len(text) * 4 + NeoDisplay.WIDTH): # Width is roughly 3+1=4 per char
            d.scroll_left(1)
            d.show()
            await asyncio.sleep(0.05)
        await asyncio.sleep(0.5)

async def anim_bounce_rect():
    """Bounces a rectangle around the screen."""
    d = NeoDisplay.inst()
    w, h = 4, 4
    x, y = 0, 0
    dx, dy = 1, 1
    color = neodisplay.GREEN
    
    while True:
        d.fill(neodisplay.BLACK)
        d.fill_rect(x, y, w, h, color)
        d.show()
        
        x += dx
        y += dy
        
        if x <= 0 or x + w >= NeoDisplay.WIDTH:
            dx = -dx
            x += dx 
            color = neodisplay.RED
        
        if y <= 0 or y + h >= NeoDisplay.HEIGHT:
            dy = -dy
            y += dy
            color = neodisplay.BLUE
            
        await asyncio.sleep(0.1)

from dispman import DisplayManager

async def clock_tick_mock(d):
    """A mock default animation (e.g. Clock) that runs forever."""
    # Just blink a pixel to show it's alive while idle
    while True:
        d.pixel(0, 0, (10, 10, 10))
        d.show()
        await asyncio.sleep(0.5)
        d.pixel(0, 0, neodisplay.BLACK)
        d.show()
        await asyncio.sleep(0.5)

async def main():
    display = neodisplay.get_display()
    display.brightness = 1.0

    # Default animation is the Clock (TimeDisplay)
    # Singleton usage
    clock = time_display.TimeDisplay.inst()
    # Ensure default defaults
    clock.set_mode(time_display.HH_MM)
    clock.set_color(neodisplay.WHITE)
    
    mgr = dispman.DisplayManager(default_anim=clock)
    
    # 1. Run Clock (HH:MM) for a few seconds
    print("Showing Clock (HH:MM)...")
    await asyncio.sleep(5)

    # 2. Change Clock Mode to HH_MM_SS via API
    print("Changing Clock Mode to HH:MM SS...")
    clock.set_mode(time_display.HH_MM_SS)
    clock.set_color(neodisplay.CYAN)
    
    # Let that run for a bit
    await asyncio.sleep(5)
    
    # 3. Trigger "Pop up" Scrolling Text
    print("Queueing Scrolling Text Popup...")
    from animations import ScrollingText
    scroll_anim = ScrollingText("Hello World!", color=neodisplay.MAGENTA, loops=1)
    mgr.queue_for_play(scroll_anim)
  
    
    # Text finishes, system automatically returns to Clock.
    await mgr.wait_idle()  
    await asyncio.sleep(5)

    # later, schedule a one-shot animation:
    special = dispman.BouncingDotAnimation(None, color=(50, 50, 0))
    mgr.queue_for_play(special)
    
    # Let it run for 2 seconds then kill it
    await asyncio.sleep(2)
    print("Testing stop_foreground()...")
    mgr.stop_foreground()
    
    # keep other tasks running, web server, etc.
    while True:
        await asyncio.sleep(1)


async def main2():
    print("Starting NeoDisplay Demo with DisplayManager...")
    d = NeoDisplay.inst()
    
    # Initialize Manager with a default background task
    mgr = DisplayManager(d, default_anim=clock_tick_mock)
    
    # 1. Immediate: Scroll Welcome
    print("Playing Welcome (Immediate)...")
    mgr.play_immediate(d.scroll_msg, "Welcome!", color=neodisplay.GREEN)
    
    # Give it time to start
    await asyncio.sleep(2)
    
    # 2. Queue up some animations
    print("Queueing animations...")
    # Use finite animations so we can see the queue working
    mgr.queue(d.scroll_msg, "Message 1 (Queued)", color=neodisplay.MAGENTA)
    mgr.queue(d.scroll_msg, "Message 2 (Queued)", color=neodisplay.BLUE)
    
    # Wait for them to finish (approx)
    await asyncio.sleep(10)
    
    # 3. Interrupt with Immediate
    print("Interrupting with Immediate Scroll...")
    mgr.play_immediate(d.scroll_msg, "URGENT!", color=neodisplay.RED)
    
    # 4. Let it settle back to default
    await asyncio.sleep(5)
    print("Should be running default clock now...")
    
    while True:
        await asyncio.sleep(1)

