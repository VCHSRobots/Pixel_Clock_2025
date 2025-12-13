import uasyncio as asyncio
import neodisplay
import dispman  
import time_display  
import animations

from dispman import DisplayManager

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
    # Use animations.ScrollingText
    scroll_anim = animations.ScrollingText("Hello World!", color=neodisplay.MAGENTA, loops=1)
    mgr.queue_for_play(scroll_anim)
  
    
    # Text finishes, system automatically returns to Clock.
    await mgr.wait_idle()  
    await asyncio.sleep(5)

    # later, schedule a one-shot animation:
    # Use animations.BouncingBox (using color list for multi-color effect similar to old anim_bounce_rect)
    special = animations.BouncingBox(color=[neodisplay.GREEN, neodisplay.RED, neodisplay.BLUE], 
                                     change_color_on_bounce=True)
    mgr.queue_for_play(special)
    
    # Let it run for 2 seconds then kill it
    await asyncio.sleep(2) # NOTE: BouncingBox is infinite by default, so we must stop it manually or let it run
    print("Testing stop_foreground()...")
    mgr.stop_foreground()
    
    # keep other tasks running, web server, etc.
    while True:
        await asyncio.sleep(1)



