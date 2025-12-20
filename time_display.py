# time_display.py - Time rendering animation
# Dec 2025

import uasyncio as asyncio
import neodisplay
from dispman import BaseAnimation
import time_keeper

# Display Modes
HH_MM = 0
HH_MM_SS = 1

class TimeDisplay(BaseAnimation):
    """
    Displays the current time.
    Offers multiple formats:
      - 00:00 (HH:MM) - standard, centered, colored digits & colon
      - 00:00 xx (HH:MM SS) - with small seconds
    """
    _instance = None

    @classmethod
    def inst(cls):
        return cls._instance

    def __init__(self):
        super().__init__()
        if TimeDisplay._instance is not None:
            raise RuntimeError("TimeDisplay already initialized")
        TimeDisplay._instance = self
            
        self.mode = HH_MM
        self.color = neodisplay.WHITE
        self.colon_color = neodisplay.WHITE
        self.seconds_color = neodisplay.WHITE
        self.twelve_hour = True

    def set_mode(self, mode):
        self.mode = mode

    def set_color(self, color):
        self.color = color
        
    def set_colon_color(self, color):
        self.colon_color = color
        
    def set_seconds_color(self, color):
        self.seconds_color = color
        
    def set_12hr(self, is_12hr):
        self.twelve_hour = is_12hr

    async def run(self):
        while not self.stopped:
            if self.paused:
                await asyncio.sleep_ms(100)
                continue

            self._draw()
            self._display.show()
            
            # Update frequency: 5 times a second is enough for seconds to feel responsive
            await asyncio.sleep_ms(200)

    def _draw(self):
        t = time_keeper.get_time()
        
        if isinstance(t, str):
            self._display.fill(neodisplay.BLACK)
            self._draw_message(t)
            return
            
        h, m, s = t
        
        # 12-hour conversion
        if self.twelve_hour:
            if h == 0:
                h = 12
            elif h > 12:
                h -= 12
        
        self._display.fill(neodisplay.BLACK)
        
        if self.mode == HH_MM:
            self._draw_hh_mm(h, m)
        elif self.mode == HH_MM_SS:
            self._draw_hh_mm_ss(h, m, s)

    def _draw_message(self, text):
        # Draw text centered using small font (3x5)
        # Width per char is 3 pixels + 1 spacing = 4 pixels
        width = len(text) * 4 - 1
        x = (self._display.width - width) // 2
        # Center vertically: Height is 5. Display height is 8.
        y = 1 
        
        self._display.write_text(x, y, text, neodisplay.RED, font=neodisplay.NeoDisplay.FONT_SMALL)

    def _draw_hh_mm(self, h, m):
        # Format: HH:MM centered
        
        if self.twelve_hour:
            s_h = "{:d}".format(h)
        else:
            s_h = "{:02d}".format(h)
        s_m = "{:02d}".format(m)
        
        # Fix the placement of the digits so that the display doesn't jump around. 

        ix0 = 3
        if len(s_h) == 1: ix0 = 9
        self._display.write_text(ix0, 1, s_h, self.color)
        
        # Draw Colon
        self._draw_colon(15, 1, self.colon_color)
        
        # Draw Minute
        self._display.write_text(17, 1, s_m, self.color)

    def _draw_hh_mm_ss(self, h, m, s):
        # Format: HH:MM ss with tight packing
        
        if self.twelve_hour:
            s_h = "{:d}".format(h)
        else:
            s_h = "{:02d}".format(h)
        s_m = "{:02d}".format(m)
        s_s = "{:02d}".format(s)
               
        # Draw H
        if len(s_h) == 1:
            self._display.draw_char(5, 1, s_h[0], self.color)
        else:
            self._display.draw_char_tight(0, 1, s_h[0], self.color)
            self._display.draw_char(5, 1, s_h[1], self.color)   
                
        # Colon
        self._draw_colon(11, 1, self.colon_color)
        
        # Draw MM
        x = 13
        for i, char in enumerate(s_m):
            self._display.draw_char(x, 1, char, self.color, font=neodisplay.NeoDisplay.FONT_LARGE)
            x += 6

        # Draw SS
        x = 25
        for i, char in enumerate(s_s):
            self._display.draw_char(x, 3, char, self.seconds_color, font=neodisplay.NeoDisplay.FONT_SMALL)
            x += 4 

    def _draw_colon(self, x, y, color):
        # Draw single column colon
        # New design: 2 pixels total
        self._display.pixel(x, 3, color)
        self._display.pixel(x, 5, color)

    def _draw_digit_tight(self, x, y, char, color):
        # Fetch packed integer from tuple
        idx = ord(char) - 32
        if idx < 0 or idx >= len(neodisplay.FONT_5x7):
            idx = ord('?') - 32
        
        val = neodisplay.FONT_5x7[idx]
        
        # Unpack 5 bytes
        glyph = [
            (val >> 32) & 0xFF,
            (val >> 24) & 0xFF,
            (val >> 16) & 0xFF,
            (val >> 8) & 0xFF,
            val & 0xFF
        ]
        
        # Calculate visual bounds
        start_col = 0
        end_col = len(glyph)
        
        while start_col < end_col and glyph[start_col] == 0:
            start_col += 1
        while end_col > start_col and glyph[end_col-1] == 0:
            end_col -= 1
            
        # Draw
        for i in range(start_col, end_col):
            col_byte = glyph[i]
            draw_x = x + (i - start_col)
            if draw_x >= self._display.width: break
            
            for row in range(7):
                if (col_byte >> row) & 1:
                    self._display.pixel(draw_x, y + row, color)
                    
        return x + (end_col - start_col)


def get_time_display():
    """Get the singleton instance. Create if not exists."""
    td = TimeDisplay.inst()
    if td is None:
        td = TimeDisplay()
    return td