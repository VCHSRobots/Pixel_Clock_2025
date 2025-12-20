import uasyncio as asyncio
import neodisplay
import dispman  
import animations
import time_display  
import settings_manager
import button_control
import web_server
import netcomm
import gc

async def main():
    gc.collect()
    print("Main: System Startup")
    print(f"Free Mem: {gc.mem_free()}")
    
    display = neodisplay.get_display()
    
    # Load Device Name
    device_name = "NeoDisplay Clock"
    try:
        import json
        with open("device_name.json", "r") as f:
            data = json.load(f)
            device_name = data.get("name", "NeoDisplay Clock")
    except:
        pass
        
    print(f"Startup: {device_name}")
    import persistent_logger
    persistent_logger.log(f"Startup: {device_name}")

    # Default animation is the Clock (TimeDisplay)
    # Singleton usage
    clock_display = time_display.get_time_display()
    
    # Load settings
    settings = settings_manager.get_settings_manager()
    
    # Apply settings
    display.brightness(settings.get("brightness", 0.5))
    clock_display.set_12hr(settings.get("12_hour_mode", False))
    clock_display.set_color(settings.get("digit_color", neodisplay.WHITE))
    clock_display.set_colon_color(settings.get("colon_color", neodisplay.WHITE))
    clock_display.set_seconds_color(settings.get("seconds_color", neodisplay.WHITE))
    
    # Set mode from settings
    clock_display.set_mode(settings.get("mode", time_display.HH_MM))
    
    mgr = dispman.get_display_manager()
    mgr.set_background(clock_display)
    
    # Startup Animation - Rainbow
    print("Main: Playing startup animation...")
    rainbow = animations.Rainbow(speed=2) 
    mgr.play_immediate(rainbow)
    
    ns = netcomm.get_netcomm()
    ns.start()

    async def announce_ip():
        while not ns.is_connected():
            await asyncio.sleep(1)
        print(f"Main: IP Address Assigned: {ns.get_ip()}")
    asyncio.create_task(announce_ip())
    
    # Allow animation to play during startup
    await asyncio.sleep(3)
    mgr.stop_foreground() # Revert to background (clock)
    
    # Start Web Server
    gc.collect()
    print(f"Free Mem before Server: {gc.mem_free()}")
    # Use keyword argument to be explicit and potentially avoid positional mismatch issues
    server = web_server.WebServer(device_name=device_name)
    await server.start()

    # Start Button Controller
    btn_ctrl = button_control.get_button_controller()
    asyncio.create_task(btn_ctrl.start())
    
    # Run forever
    while True:
        await asyncio.sleep(1)
