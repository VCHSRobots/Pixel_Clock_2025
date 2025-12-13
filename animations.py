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

    def stop(self):
        super().stop()
        
class BouncingBox(BaseAnimation):
    """
    A box that bounces around the screen.
    If colors is a list, it cycles through them on every bounce.
    """
    def __init__(self, color=neodisplay.BLUE, size=2, speed=0.05, change_color_on_bounce=False):
        super().__init__()
        self.colors = [color] if not isinstance(color, list) else color
        self.color_idx = 0
        self.current_color = self.colors[0]
        self.change_on_bounce = change_color_on_bounce or (len(self.colors) > 1)
        
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
            self._display.fill_rect(self.x, self.y, self.size, self.size, self.current_color)
            self._display.show()
            
            # Update position
            self.x += self.dx
            self.y += self.dy
            
            bounced = False
            # Bounce
            if self.x <= 0:
                self.x = 0
                self.dx = 1
                bounced = True
            elif self.x >= width - self.size:
                self.x = width - self.size
                self.dx = -1
                bounced = True
                
            if self.y <= 0:
                self.y = 0
                self.dy = 1
                bounced = True
            elif self.y >= height - self.size:
                self.y = height - self.size
                self.dy = -1
                bounced = True
            
            if bounced and self.change_on_bounce:
                self.color_idx = (self.color_idx + 1) % len(self.colors)
                self.current_color = self.colors[self.color_idx]
                
            await asyncio.sleep_ms(int(self.speed * 1000))

class ColorStringBuilder:
    """
    Helper to build a string with different colors for each segment.
    """
    def __init__(self):
        self._data = [] # List of (char, color) tuples

    def add(self, text, color):
        for char in text:
            self._data.append((char, color))
    
    def __len__(self):
        return len(self._data)
    
    def __getitem__(self, idx):
        return self._data[idx]
        
    def __iter__(self):
        return iter(self._data)

class ScrollingColoredText(BaseAnimation):
    """
    Scrolls multi-colored text.
    buffer: ColorStringBuilder instance or list of (char, color) tuples.
    """
    def __init__(self, buffer, speed=0.1, font=None, loops=None):
        super().__init__()
        self.buffer = buffer
        self.speed = speed
        self.font = font
        self.loops = loops
        
        if self.font is None:
            self.font = neodisplay.NeoDisplay.FONT_LARGE
            
        self.char_width = 6 if self.font == neodisplay.NeoDisplay.FONT_LARGE else 4
        self.total_width = len(buffer) * self.char_width
        
        # Y position centering
        if self.font == neodisplay.NeoDisplay.FONT_SMALL:
             self.y_pos = 2
        else:
             self.y_pos = 1

    async def run(self):
        start_x = self._display.width
        end_x = -self.total_width
        
        loops_remaining = self.loops
        current_x = start_x
        
        while not self.stopped:
            if self.paused:
                await asyncio.sleep_ms(100)
                continue

            self._display.fill(neodisplay.BLACK)
            
            # Draw visible characters
            # Optimization: could only draw chars that are on screen, 
            # but for 32 pixels width, simpler is fine.
            
            draw_cursor = current_x
            
            for char, color in self.buffer:
                # Basic culling
                if draw_cursor >= self._display.width:
                    break
                
                # We need to know width of char to know if we skip it off left
                # but draw_char handles clipping. We just need to advance cursor.
                # However, for speed, if draw_cursor + char_width < 0, we can skip drawing?
                # draw_char returns next x.
                
                # Check if completely off-screen left?
                # A 5x7 char is usually 5 wide + 1 space = 6.
                # 3x5 is 3 + 1 = 4.
                
                if draw_cursor < -6: # Safe margin
                    draw_cursor += self.char_width
                    continue

                draw_cursor = self._display.draw_char(draw_cursor, self.y_pos, char, color, font=self.font)
            
            self._display.show()
            
            current_x -= 1
            if current_x < end_x:
                current_x = start_x 
                if loops_remaining is not None:
                    loops_remaining -= 1
                    if loops_remaining <= 0:
                        self.stop()
                        return
            
            await asyncio.sleep_ms(int(self.speed * 1000))

class Pulse(BaseAnimation):
    """
    Simple heartbeat/pulse animation.
    """
    def __init__(self, color=neodisplay.WHITE, interval=1.0):
        super().__init__()
        self.color = color
        self.interval = interval
        
    async def run(self):
        while not self.stopped:
            if self.paused:
                await asyncio.sleep_ms(100)
                continue
                
            # Blink on
            self._display.pixel(0, 0, self.color)
            self._display.show()
            # Half interval on
            await asyncio.sleep_ms(int(self.interval * 500))
            
            # Blink off
            self._display.pixel(0, 0, neodisplay.BLACK)
            self._display.show()
            # Half interval off
            await asyncio.sleep_ms(int(self.interval * 500))
