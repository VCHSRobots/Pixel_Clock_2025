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

    def __init__(self, mode=HH_MM, color=neodisplay.WHITE, colon_color=neodisplay.WHITE, twelve_hour=True):
        super().__init__()
        if TimeDisplay._instance is None:
            TimeDisplay._instance = self
            
        self.mode = mode
        self.color = color
        self.colon_color = colon_color
        self.twelve_hour = twelve_hour

    def set_mode(self, mode):
        self.mode = mode

    def set_color(self, color):
        self.color = color
        
    def set_colon_color(self, color):
        self.colon_color = color
        
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
        # We draw manually to control colon color and spacing
        
        # Strings
        s_h = "{:02d}".format(h)
        s_m = "{:02d}".format(m)
        
        # Calculate width
        # Large font: char width 5 + 1 spacing = 6
        # Colon: visual 2 + 1 spacing (maybe 2 spacing?)
        # Let's use write_text logic mostly but split it up.
        
        # Standard spacing:
        # H(6) H(6) :(4) M(6) M(5) = 27 pixels wide roughly
        # 32 - 27 = 5 pixels remainder.
        # Start at x=2 or 3.
        
        # Let's compute x positions relative to a start 'x'
        # H1: x
        # H2: x + 6
        # Colon: x + 12
        # M1: x + 12 + 4? (Colon is usually 2px wide visual, plus spacing)
        
        # Let's simply center it nicely.
        start_x = 2
        
        # Draw Hour
        cursor = self._display.write_text(start_x, 1, s_h, self.color)
        
        # Draw Colon
        # Colon in 5x7 is usually width 5 (code returns 5 bytes).
        # But visually it's centered. neodisplay generic font:
        # ':' : [0x00, 0x36, 0x36, 0x00, 0x00]
        # We can draw it "tight" if we want, or just use write_text for convenience
        # if we are okay with the standard spacing.
        # write_text returns next cursor position (x + width + 1)
        
        # Let's just overwrite the colon position manually to change color.
        # If we print "12:00", the colon is the 3rd char.
        # For simplicity:
        
        # Draw Colon
        # 'space' between digits is 1px.
        # Previous cursor includes 1px trailing space.
        
        # Adjust cursor slightly for colon visual balance? 
        # Actually standard font spacing is fine for HH:MM.
        
        cursor = self._display.draw_char(cursor, 1, ":", self.colon_color)
        
        # Draw Minute
        cursor = self._display.write_text(cursor, 1, s_m, self.color)

    def _draw_hh_mm_ss(self, h, m, s):
        # Format: HH:MM ss
        # This is tight on 32 pixels.
        # We must use tight spacing.
        
        s_h = "{:02d}".format(h)
        s_m = "{:02d}".format(m)
        s_s = "{:02d}".format(s)
        
        # Layout strategy:
        # Try to fit everything starting at x=0
        
        x = 0
        y_big = 1
        y_small = 2 # Centered for 5-high font? 3x5 is 5 high. 8-5=3. y=1 means 1px top, 2px bottom. y=2 means 2px top, 1px bottom.
        
        # H1
        x = self._draw_digit_tight(x, y_big, s_h[0], self.color)
        x += 1 # 1px spacing
        
        # H2
        x = self._draw_digit_tight(x, y_big, s_h[1], self.color)
        
        # Colon (Tight)
        # 1px spacing before colon
        x += 1
        # Draw 2px colon manually
        self._display.pixel(x, y_big+1, self.colon_color)
        self._display.pixel(x, y_big+4, self.colon_color) 
        self._display.pixel(x+1, y_big+1, self.colon_color)
        self._display.pixel(x+1, y_big+4, self.colon_color)
        x += 2
        
        # M1
        x += 1 # 1px spacing
        x = self._draw_digit_tight(x, y_big, s_m[0], self.color)
        
        # M2
        x += 1
        x = self._draw_digit_tight(x, y_big, s_m[1], self.color)
        
        # Small Seconds
        x += 2 # Extra spacing?
        
        # S1
        x = self._display.draw_char(x, y_small, s_s[0], self.color, font=neodisplay.NeoDisplay.FONT_SMALL)
        # S2
        x = self._display.draw_char(x, y_small, s_s[1], self.color, font=neodisplay.NeoDisplay.FONT_SMALL)


    def _draw_digit_tight(self, x, y, char, color):
        # Determine width of digit
        # 1 is 3px wide. Others 5px.
        width = 5
        if char == '1':
            width = 3
            
        # Standard draw_char uses full 5 bytes for everything. 
        # We'll re-implement a simple drawer that knows '1' is skinny or just skips empty columns?
        # A simple "draw_char" that returns actual visual width would be better.
        
        # For now, let's just use the display's byte data but skip leading/trailing zeros?
        # neodisplay FONT_5x7['1'] is 00 42 7F 40 00.
        # That's 1px padding, 3px data, 1px padding.
        # If we want TIGHT packing, we should strip that padding.
        
        glyph = neodisplay.FONT_5x7.get(char, neodisplay.FONT_5x7['?'])
        
        # Find start and end columns that are not 0
        start_col = 0
        end_col = len(glyph)
        
        # Strip leading
        while start_col < end_col and glyph[start_col] == 0:
            start_col += 1
            
        # Strip trailing
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
