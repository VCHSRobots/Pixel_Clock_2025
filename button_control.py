import uasyncio as asyncio
import time
from machine import Pin

import neodisplay
import animations
import dispman
import time_display
import settings_manager

# Button Constants
BUTTON_PIN = 17 

# Button Timing Constants
DEBOUNCE_MS = 50
SHORT_PRESS_MS = 500  # Max duration for short press
LONG_PRESS_MS = 2000  # Min duration for brightness mode
SETUP_PRESS_MS = 10000 # Min duration for setup mode
BRIGHTNESS_STEP = 0.05
BRIGHTNESS_DELAY_MS = 100

class ButtonController:
    _instance = None

    @classmethod
    def inst(cls):
        return cls._instance

    def __init__(self):
        if ButtonController._instance is not None:
            raise RuntimeError("ButtonController already initialized")
        ButtonController._instance = self
        
        self.pin = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
        self._brightness_direction = 1 # 1 for up, -1 for down

    async def start(self):
        """Main loop for button monitoring."""
        print("ButtonController: Started on GPIO ", BUTTON_PIN)
        
        # State: 'IDLE', 'BRIGHTNESS_WAIT'
        state = 'IDLE'

        while True:
            if state == 'IDLE':
                # Wait for press
                if not self.pin.value(): # Active Low
                    # Debounce
                    await asyncio.sleep_ms(DEBOUNCE_MS)
                    if not self.pin.value():
                        # Confirmed press
                        duration = await self._measure_press_duration()
                        
                        if duration >= SETUP_PRESS_MS:
                             await self._trigger_setup()
                             await self._wait_for_release()
                        elif duration >= LONG_PRESS_MS:
                             print("Button: Long Press -> Brightness Mode")
                             state = 'BRIGHTNESS_WAIT'
                             # Infinite message
                             anim = animations.MessageDisplay("Adj BRT", duration=0, color=neodisplay.YELLOW)
                             dispman.get_display_manager().play_immediate(anim)
                             last_activity_ticks = time.ticks_ms()
                        else:
                             print("Button: Short Press -> Status")
                             await self._trigger_status()
                    
            elif state == 'BRIGHTNESS_WAIT':
                # Check for timeout (10 seconds)
                if time.ticks_diff(time.ticks_ms(), last_activity_ticks) > 10000:
                    print("Button: Timeout -> Exit Brightness Mode")
                    state = 'IDLE'
                    dispman.get_display_manager().stop_foreground() # Stop the "Adj BRT" message
                    continue

                # Check for press
                if not self.pin.value():
                     await asyncio.sleep_ms(DEBOUNCE_MS)
                     if not self.pin.value():
                         # This is the adjustment press!
                         print("Button: Adjustment Press")
                         last_activity_ticks = time.ticks_ms() # Reset timeout
                         
                         await self._adjust_brightness_loop()
                         
                         # After adjustment loop returns (user released), we save and exit
                         state = 'IDLE'
                         self._save_brightness()
                         # Static "Saved" message for 2 seconds
                         anim = animations.MessageDisplay("Saved", duration=2.0, color=neodisplay.GREEN)
                         dispman.get_display_manager().play_immediate(anim)

            await asyncio.sleep_ms(20)

    async def _wait_for_release(self):
        """Waits for the button to be released."""
        while not self.pin.value():
            await asyncio.sleep_ms(20)

    async def _measure_press_duration(self):
        """Measures how long the button is held. Returns duration in ms."""
        start_ticks = time.ticks_ms()
        
        while not self.pin.value(): # While held low
            current_ticks = time.ticks_ms()
            diff = time.ticks_diff(current_ticks, start_ticks)
            
            # Special Case: Immediate Trigger for Setup
            if diff >= SETUP_PRESS_MS:
                return diff # Return immediately to trigger setup
            
            await asyncio.sleep_ms(20)
            
        end_ticks = time.ticks_ms()
        return time.ticks_diff(end_ticks, start_ticks)

    async def _adjust_brightness_loop(self):
        """Cycle brightness while button is held."""
        # While button is pressed, change brightness
        display = neodisplay.get_display()
        
        while not self.pin.value(): # active low
            current = display.brightness()
            new_val = current + (BRIGHTNESS_STEP * self._brightness_direction)
            
            # Bounce at limits
            if new_val >= 1.0:
                new_val = 1.0
                self._brightness_direction = -1
            elif new_val <= 0.05: # Don't go to absolute 0/black
                new_val = 0.05
                self._brightness_direction = 1
                
            display.brightness(new_val)
            display.show() # Force update to see effect immediately? 
            # Note: DisplayManager loop might be calling show(), but changing brightness prop is enough
            # unless we want visual feedback *right now*. 
            # If TimeDisplay is running in background, it will pick up brightness next tick.
            # But we might want a solid color or something to start? 
            # The prompt says "brightness to slowly change".
            
            await asyncio.sleep_ms(BRIGHTNESS_DELAY_MS)
        
        print(f"Button: Final Brightness {display.brightness()}")

    def _save_brightness(self):
        val = neodisplay.get_display().brightness()
        settings_manager.get_settings_manager().update({"brightness": val})
        print("Button: Settings Saved")

    async def _trigger_status(self):
        import netcomm
        nm = netcomm.get_netcomm()
        
        text = ""
        color = neodisplay.BLUE
        
        if nm.is_connected():
            text = f"IP: {nm.get_ip()}"
        else:
            text = "No Connection"
            color = neodisplay.RED
            
        anim = animations.ScrollingText(text, color=color, loops=1, starting_x=10, pause_on_entry=3.0)
        dispman.get_display_manager().play_immediate(anim)

    async def _trigger_setup(self):
        print("Button: Very Long Press -> Setup Mode")
        display = neodisplay.get_display()
        display.brightness(1.0)
        anim = animations.MessageDisplay("SETUP", duration=5.0, color=neodisplay.MAGENTA)
        dispman.get_display_manager().play_immediate(anim)
        await anim.wait_for_finish()
        display.brightness(0.05)
        # Setup is a stub for now. Use loops=3 to indicate 'mode' active for a bit then exit.

def get_button_controller():
    """Get the singleton instance. If not exists, create it."""
    bc = ButtonController.inst()
    if bc is None:
        bc = ButtonController()
    return bc
