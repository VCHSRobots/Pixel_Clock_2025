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
import test_manager
import alarm_manager
import time_keeper

async def main():
    gc.collect()
    startup_ready = asyncio.Event() # Synchronization for startup animations
    print("Main: System Startup")
    print(f"Free Mem: {gc.mem_free()}")
    
    display = neodisplay.get_display()

    # --- IMMEDIATE STARTUP ANIMATION ---
    # Show life as soon as possible
    mgr = dispman.get_display_manager()
    print("Main: Playing immediate startup animation...")
    rainbow = animations.Rainbow(speed=2) 
    mgr.play_immediate(rainbow)
    await asyncio.sleep(1)
    # -----------------------------------

    # --- SETUP MODE CHECK ---
    # Check if we should enter Setup Mode
    # Condition: Date is Invalid (< 2020, defaults to 2000 on battery loss/reset)
    #            AND `ssid.json` is missing.
    import os
    import rtc_module
    
    ssid_exists = False
    try:
        os.stat("ssid.json")
        ssid_exists = True
    except:
        ssid_exists = False
        
    rtc = rtc_module.get_rtc()
    # Time format: (year, month, day, hour, min, sec, wday, doy)
    now = rtc.get_time()
    year = now[0]

    # Check Test Mode
    settings = settings_manager.get_settings_manager()
    val_year = test_manager.apply_test_time(rtc, settings)
    if val_year:
        year = val_year
    
    if test_manager.is_ntp_disabled():
         print("Startup: NTP Sync explicitly DISABLED by Test Config")
    
    print(f"Startup Check: Year={year}, Creds={ssid_exists}")
    
    if not ssid_exists and year < 2020:
        print("Startup: Entering SETUP MODE")
        import setup_mode
        await setup_mode.run_setup()
        # setup_mode.run_setup() should arguably never return as it resets, 
        # but if it does, we probably shouldn't continue typical boot.
        return 
    # ------------------------
    
    
    # Load Device Name
    device_name = "NeoDisplay Clock"
    try:
        import json
        # Try to load name from ssid.json if it exists
        with open("ssid.json", "r") as f:
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
    
    # Apply rotation
    display.set_rotation(settings.get("rotation", False))
    
    # Set mode from settings
    clock_display.set_mode(settings.get("mode", time_display.HH_MM))
    clock_display.set_blink_mode(settings.get("colon_blink_mode", 0))
    
    # mgr already initialized above
    mgr.set_background(clock_display)
    
    ns = netcomm.get_netcomm()
    
    # Check if we have credentials for Network/Web
    if ns.has_credentials():
        print("Main: Network Credentials Found -> Starting Network & Web Server")
        ns.start()

        # Check for Invalid Time + Connection Wait
        if year < 2020:
             print("Startup: Time invalid, waiting for WiFi to sync...")
             wait_count = 0
             warning_triggered = False
             
             # Wait up to 5 seconds before complaining
             while not ns.is_connected() and wait_count < 50: # 50 * 0.1s = 5s
                 await asyncio.sleep(0.1)
                 wait_count += 1
                 
             # If still not connected, complain
             if not ns.is_connected():
                 print("Startup: WiFi not ready, showing NO wifi warning")
                 # Static custom animation (Red/Blue, fitted)
                 no_wifi_anim = animations.NoWifiAnim() 
                 mgr.play_immediate(no_wifi_anim)
                 warning_triggered = True
                 
                 # Wait indefinitely for connection
                 while not ns.is_connected():
                     await asyncio.sleep(0.5)
             
             # Connected!
             if warning_triggered:
                 print("Startup: WiFi Connected! Stopping warning.")
                 mgr.stop_foreground()
                 
             # Sync Time Immediately
             print("Startup: Syncing NTP...")
             try:
                ns.sync_time()
                print("Startup: NTP Sync Request Sent")
             except Exception as e:
                print(f"Startup: NTP Sync Error {e}")
        
        async def announce_ip():
            while not ns.is_connected():
                await asyncio.sleep(1)
            
            ip = ns.get_ip()
            print(f"Main: IP Address Assigned: {ip}")
            
            # Wait for startup animations to finish so we don't get cut off
            await startup_ready.wait()
            
            # Scroll IP Address
            import animations
            # Using loop=2 to show it twice then return to clock
            scroll = animations.ScrollingText(f"IP: {ip}", color=neodisplay.GREEN, speed=0.1, loops=2)
            mgr.play_immediate(scroll)
            
        asyncio.create_task(announce_ip())

        # Allow animation to play during startup
        await asyncio.sleep(3)
        mgr.stop_foreground() # Revert to background (clock)
        startup_ready.set()
        
        # Start Web Server
        gc.collect()
        print(f"Free Mem before Server: {gc.mem_free()}")
        # Use keyword argument to be explicit and potentially avoid positional mismatch issues
        server = web_server.WebServer(device_name=device_name)
        print("Startup: Starting Web Server...")
        await server.start()
        print("Startup: Web Server Started")
    else:
        print("Main: Offline Mode (No SSID) -> Skipping Network & Web Server")
        # Just wait for animation then stop it
        await asyncio.sleep(3)
        mgr.stop_foreground()
        startup_ready.set()
    
    # Start Button Controller
    btn_ctrl = button_control.get_button_controller()
    asyncio.create_task(btn_ctrl.start())
    
    # Start Alarm Manager
    am = alarm_manager.get_alarm_manager()
    tk = time_keeper.get_time_keeper()
    
    # Run forever
    while True:
        gc.collect()
        am.update()
        dt = tk.get_full_dict()
        am.check_alarms(dt)
        await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        import persistent_logger
        import sys
        
        # Format the error
        err_msg = f"CRITICAL CRASH: {e}"
        print(err_msg)
        sys.print_exception(e) # Print traceback to serial
        
        try:
            persistent_logger.log(err_msg)
            # Optional: Log traceback details if possible, but keeping it simple for now
        except:
            print("Failed to log crash to persistent storage")

        # Wait for logs to flush and user to possibly see output
        import time
        import machine
        print("Rebooting in 5 seconds...")
        time.sleep(5)
        machine.reset()
    finally:
        asyncio.new_event_loop()
