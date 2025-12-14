import uasyncio as asyncio
import neodisplay
import dispman  
import time_display  
import animations
import web_server
import gc

from dispman import DisplayManager

async def main():
    gc.collect()
    print(f"Free Mem: {gc.mem_free()}")
    
    display = neodisplay.get_display()
    # Brightness will be set after loading settings

    # Default animation is the Clock (TimeDisplay)
    # Singleton usage
    clock = time_display.TimeDisplay.inst()
    
    # Load settings
    from settings_manager import SettingsManager
    settings = SettingsManager()
    
    # Apply settings
    display.brightness(settings.get("brightness", 0.5))
    clock.set_12hr(settings.get("12_hour_mode", False))
    clock.set_color(settings.get("digit_color", neodisplay.WHITE))
    clock.set_colon_color(settings.get("colon_color", neodisplay.WHITE))
    clock.set_seconds_color(settings.get("seconds_color", neodisplay.WHITE))
    
    # Set mode from settings
    clock.set_mode(settings.get("mode", time_display.HH_MM))
    
    mgr = dispman.DisplayManager(default_anim=clock)
    
    # Start Web Server
    gc.collect()
    print(f"Free Mem before Server: {gc.mem_free()}")
    server = web_server.WebServer(mgr, clock, settings)
    await server.start()

    # Start Button Controller
    import button_control
    btn_ctrl = button_control.ButtonController(mgr, clock, settings)
    asyncio.create_task(btn_ctrl.start())
    
    # Run forever
    while True:
        await asyncio.sleep(1)
