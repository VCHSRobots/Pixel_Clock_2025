import uasyncio as asyncio
import neodisplay
import dispman  
import time_display  
import animations
import web_server

from dispman import DisplayManager

async def main():
    display = neodisplay.get_display()
    # Fix: brightness is a method, not a property
    display.brightness(1.0)

    # Default animation is the Clock (TimeDisplay)
    # Singleton usage
    clock = time_display.TimeDisplay.inst()
    # Ensure default defaults
    clock.set_mode(time_display.HH_MM)
    clock.set_color(neodisplay.WHITE)
    
    mgr = dispman.DisplayManager(default_anim=clock)
    
    # Start Web Server
    server = web_server.WebServer(mgr, clock)
    await server.start()
    
    # Run forever
    while True:
        await asyncio.sleep(1)
