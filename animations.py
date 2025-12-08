# animations.py - Animation classes for NeoDisplay
# Dec 2025

import uasyncio as asyncio
from dispman import BaseAnimation
import neodisplay

class ScrollingText(BaseAnimation):
    """
    Scrolls text from right to left across the display.
    """
    def __init__(self, text, color=neodisplay.WHITE, speed=0.1, font=None, loops=None):
        super().__init__()
        self.text = text
        self.color = color
        self.speed = speed
        self.font = font
        self.loops = loops # None or 0 = infinite
        
        # Calculate width immediately or in run? 
        # In run ensures we have display ref if it were ever dynamic, but it isn't really.
        # We need the display to calculate width if we want to support different fonts properly
        # but neodisplay constants are available.
        
        if self.font is None:
            self.font = neodisplay.NeoDisplay.FONT_LARGE
            
        self.char_width = 6 if self.font == neodisplay.NeoDisplay.FONT_LARGE else 4
        self.total_width = len(text) * self.char_width

        # Y position centering
        if self.font == neodisplay.NeoDisplay.FONT_SMALL:
             self.y_pos = 2
        else:
             self.y_pos = 1

    async def run(self):
        # Start off-screen right
        start_x = self._display.width
        # End off-screen left
        end_x = -self.total_width
        
        loops_remaining = self.loops
        
        current_x = start_x
        
        while not self.stopped:
            if self.paused:
                await asyncio.sleep_ms(100)
                continue

            self._display.fill(neodisplay.BLACK)
            self._display.write_text(current_x, self.y_pos, self.text, self.color, font=self.font)
            self._display.show()
            
            current_x -= 1
            if current_x < end_x:
                current_x = start_x # Loop around
                if loops_remaining is not None:
                    loops_remaining -= 1
                    if loops_remaining <= 0:
                        self.stop()
                        return
            
            await asyncio.sleep_ms(int(self.speed * 1000))


class BouncingBox(BaseAnimation):
    """
    A box that bounces around the screen.
    """
    def __init__(self, color=neodisplay.BLUE, size=2, speed=0.05):
        super().__init__()
        self.color = color
        self.size = size
        self.speed = speed
        
        self.x = 0
        self.y = 0
        self.dx = 1
        self.dy = 1
        
    async def run(self):
        width = self._display.width
        height = self._display.height
        
        while not self.stopped:
            if self.paused:
                await asyncio.sleep_ms(100)
                continue
                
            self._display.fill(neodisplay.BLACK)
            self._display.fill_rect(self.x, self.y, self.size, self.size, self.color)
            self._display.show()
            
            # Update position
            self.x += self.dx
            self.y += self.dy
            
            # Bounce
            if self.x <= 0:
                self.x = 0
                self.dx = 1
            elif self.x >= width - self.size:
                self.x = width - self.size
                self.dx = -1
                
            if self.y <= 0:
                self.y = 0
                self.dy = 1
            elif self.y >= height - self.size:
                self.y = height - self.size
                self.dy = -1
                
            await asyncio.sleep_ms(int(self.speed * 1000))
