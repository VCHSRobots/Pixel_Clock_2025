import uasyncio as asyncio
import neodisplay
import dispman  
import time_display  
import animations

PIN_NUM = 16  # Change as needed

if neodisplay.NeoDisplay.inst() is None:
    display = neodisplay.NeoDisplay(PIN_NUM, brightness=0.1)
else:
    display = neodisplay.NeoDisplay.inst()

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


async def main2():
    print("Starting NeoDisplay Demo with DisplayManager...")
    d = NeoDisplay.inst()
    
    # Initialize Manager with a default background task (Pulse)
    pulse = animations.Pulse(color=(10, 10, 10))
    mgr = DisplayManager(d, default_anim=pulse)
    
    # 1. Immediate: Scroll Welcome
    print("Playing Welcome (Immediate)...")
    # Using animations.ScrollingText instead of direct d.scroll_msg (assuming d.scroll_msg was an old method, 
    # but d.scroll_msg isn't an animation class, it's a method on display? 
    # Actually wait, d.scroll_msg doesn't exist in neodisplay.py seen earlier? 
    # Let's check neodisplay.py. Ah, neodisplay.py was partially read or I assumed.
    # But wait, the user's previous code used d.scroll_msg in main2?
    # Line 152: mgr.play_immediate(d.scroll_msg, "Welcome!", color=neodisplay.GREEN)
    # If d.scroll_msg is a function that loops, it might work with mgr if mgr accepts coroutines.
    # But dispman expect animation objects usually? 
    # checking dispman.DisplayManager...
    # The user didn't show me dispman.py detailed interface for queue/play_immediate.
    # Standardizing on Animation objects is safer.
    
    welcome_anim = animations.ScrollingText("Welcome!", color=neodisplay.GREEN, loops=1)
    mgr.play_immediate(welcome_anim)
    
    # Give it time to start
    await asyncio.sleep(2)
    
    # 2. Queue up some animations
    print("Queueing animations...")
    # Use finite animations so we can see the queue working
    mgr.queue_for_play(animations.ScrollingText("Message 1 (Queued)", color=neodisplay.MAGENTA, loops=1))
    mgr.queue_for_play(animations.ScrollingText("Message 2 (Queued)", color=neodisplay.BLUE, loops=1))
    
    # Wait for them to finish (approx)
    await asyncio.sleep(10)
    
    # 3. Interrupt with Immediate
    print("Interrupting with Immediate Scroll...")
    urgent_anim = animations.ScrollingText("URGENT!", color=neodisplay.RED, loops=1)
    mgr.play_immediate(urgent_anim)
    
    # 4. Let it settle back to default
    await asyncio.sleep(5)
    print("Should be running default pulse now...")
    
    while True:
        await asyncio.sleep(1)
