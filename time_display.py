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
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, mode=HH_MM, color=neodisplay.WHITE, colon_color=neodisplay.WHITE, seconds_color=None, twelve_hour=True):
        super().__init__()
        if TimeDisplay._instance is None:
            TimeDisplay._instance = self
            
        self.mode = mode
        self.color = color
        self.colon_color = colon_color
        self.seconds_color = seconds_color if seconds_color is not None else color
        self.twelve_hour = twelve_hour

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
        h, m, s = time_keeper.get_time()
        
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

    def _draw_hh_mm(self, h, m):
        # Format: HH:MM centered
        
        if self.twelve_hour:
             s_h = "{:d}".format(h)
        else:
             s_h = "{:02d}".format(h)
        s_m = "{:02d}".format(m)
        
        # Width Calculation
        # write_text char width is 6 (5 + 1 spacing)
        w_h = len(s_h) * 6
        w_m = len(s_m) * 6
        
        # Colon space: 1px colon + 1px spacing before (implicit in H?) + 1px spacing after
        # H string via write_text has 1px trailing space.
        # We place colon there. 
        # Then we add 1px space.
        # Then M.
        # So width effectively: w_h (includes H's tail space) + 1 (tail space effectively used by colon? No, colon needs its own column)
        # H_block [space] : [space] M_block
        # w_h counts [H][space].
        # So width = w_h + 1 (colon) + 1 (space) + w_m
        
        w_colon_area = 2 
        total_w = w_h + w_colon_area + w_m
        
        start_x = (self._display.width - total_w) // 2
        
        # Draw Hour
        cursor = self._display.write_text(start_x, 1, s_h, self.color)
        
        # Draw Colon
        self._draw_colon(cursor, 1, self.colon_color)
        cursor += 2 # Advance past colon (1) and separation space (1)
        
        # Draw Minute
        self._display.write_text(cursor, 1, s_m, self.color)

    def _draw_hh_mm_ss(self, h, m, s):
        # Format: HH:MM ss with tight packing
        
        if self.twelve_hour:
             s_h = "{:d}".format(h)
        else:
             s_h = "{:02d}".format(h)
        s_m = "{:02d}".format(m)
        s_s = "{:02d}".format(s)
        
        # Calculate Widths
        # H group
        w_h = 0
        for c in s_h:
            w_h += (3 if c == '1' else 5)
        w_h += len(s_h) - 1 # Spacings between H digits
        
        # M group
        w_m = 0
        for c in s_m:
            w_m += (3 if c == '1' else 5)
        w_m += len(s_m) - 1
        
        # S group (Small font 3x5, width 3)
        w_s = 0
        for c in s_s:
            w_s += 3
        w_s += len(s_s) - 1
        
        # Total Layout: H + space + colon + space + M + space + space + S
        total_w = w_h + 1 + 1 + 1 + w_m + 2 + w_s
        
        start_x = (self._display.width - total_w) // 2
        
        x = start_x
        y_big = 1
        y_small = 2
        
        # Draw H
        for i, char in enumerate(s_h):
            x = self._draw_digit_tight(x, y_big, char, self.color)
            if i < len(s_h) - 1:
                x += 1
                
        # Colon
        x += 1
        self._draw_colon(x, y_big, self.colon_color)
        x += 2 # Colon(1) + Space(1)
        
        # Draw M
        for i, char in enumerate(s_m):
            x = self._draw_digit_tight(x, y_big, char, self.color)
            if i < len(s_m) - 1:
                x += 1
                
        # Gap
        x += 2
        
        # Draw S
        for i, char in enumerate(s_s):
            self._display.draw_char(x, y_small, char, self.seconds_color, font=neodisplay.NeoDisplay.FONT_SMALL)
            x += 3 
            if i < len(s_s) - 1:
                x += 1

    def _draw_colon(self, x, y, color):
        # Draw single column colon
        # New design: 2 pixels total
        self._display.pixel(x, y+2, color)
        self._display.pixel(x, y+5, color)

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
