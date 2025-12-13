# neodisplay.py -- Provides a class for controlling a NeoPixel display.
# Dec 2025, dlb with AI 
# Updated #01
 
import machine
import neopixel
import uasyncio as asyncio

# The NeoDisplay class provides a simple interface for controlling a NeoPixel display.
# It can be used to display text and animations. 
#
# The display is organized logically as a grid of pixels, the origin being at the top left.
# The X direction is horizontal with increasing values to the right.
# The Y direction is vertical with increasing values going down.
#
# Drawing outside of the margins of the display will not result in an error, but the
# data is lost.  The coordinates are not wrapped.
#
# The display size and underlying layout is hardcoded for speed.  The size and 
# layout can be changed in the _coord function.

PIN_NUM = 16

# Color Constants
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
WHITE = (255, 255, 255)
OFF = BLACK

# Minimal 5x7 Font
FONT_5x7 = (
    0x0000000000, 0x00005F0000, 0x0007070000, 0x147F147F14, 0x242A7F2A12, 0x2313086462, 0x3649552250, 0x0000030000,
    0x001C224100, 0x0041221C00, 0x14083E0814, 0x08083E0808, 0x0050300000, 0x0808080808, 0x0060600000, 0x2010080402,
    0x3E4141413E, 0x00427F4000, 0x6251494946, 0x2241494936, 0x1814127F10, 0x2745454539, 0x3C4A494930, 0x0371090503,
    0x3649494936, 0x264949493E, 0x0036360000, 0x0056360000, 0x0814224100, 0x1414141414, 0x0041221408, 0x0201510906,
    0x324979413E, 0x7E1111117E, 0x7F49494936, 0x3E41414122, 0x7F4141413E, 0x7F49494941, 0x7F09090901, 0x3E4141493A,
    0x7F0808087F, 0x00417F4100, 0x2040413F01, 0x7F08142241, 0x7F40404040, 0x7F020C027F, 0x7F0408107F, 0x3E4141413E,
    0x7F09090906, 0x3E4151215E, 0x7F09192946, 0x0649494930, 0x01017F0101, 0x3F4040403F, 0x1F2040201F, 0x3F4038403F,
    0x6314081463, 0x0708700807, 0x6151494543, 0x007F414100, 0x0204081020, 0x0041417F00, 0x0402010204, 0x4040404040,
    0x0001020400, 0x2054545478, 0x7F48444438, 0x3844444420, 0x384444487F, 0x3854545418, 0x087E090102, 0x085454543C,
    0x7F08040478, 0x00487D4000, 0x002040443D, 0x7F10284400, 0x00417F4000, 0x7C04780478, 0x7C08040478, 0x3844444438,
    0x7C14141408, 0x081414187C, 0x7C08040408, 0x4854545420, 0x043F444020, 0x3C4040207C, 0x1C2040201C, 0x3C4030403C,
    0x4428102844, 0x0C5050503C, 0x4464544C44, 0x0008364100, 0x00007F0000, 0x0041360800, 0x1008081008, 0x001E1E1E00
)

# 3x5 Small Font
FONT_3x5 = (
    0x000000, 0x001700, 0x030003, 0x1F0A1F, 0x121F09, 0x090412, 0x0A151D, 0x000300,
    0x0E1100, 0x110E00, 0x150E15, 0x040E04, 0x100800, 0x040404, 0x001000, 0x180403,
    0x1F111F, 0x021F00, 0x191512, 0x11150A, 0x07041F, 0x171509, 0x0E1509, 0x011D03,
    0x0A150A, 0x12150E, 0x000A00, 0x100A00, 0x040A11, 0x0A0A0A, 0x110A04, 0x011502,
    0x0E1516, 0x1E051E, 0x1F150A, 0x0E110A, 0x1F110E, 0x1F1515, 0x1F0505, 0x0E1119,
    0x1F041F, 0x001F00, 0x08100F, 0x1F041B, 0x1F1010, 0x1F021F, 0x1F011E, 0x0E110E,
    0x1F0502, 0x0E111E, 0x1F051A, 0x121509, 0x011F01, 0x1F101F, 0x0F180F, 0x1F081F,
    0x1B041B, 0x071C07, 0x191513, 0x1F1100, 0x030418, 0x111F00, 0x020102, 0x101010,
    0x010200, 0x1E051E, 0x1F150A, 0x0E110A, 0x1F110E, 0x1F1515, 0x1F0505, 0x0E1119,
    0x1F041F, 0x001F00, 0x08100F, 0x1F041B, 0x1F1010, 0x1F021F, 0x1F011E, 0x0E110E,
    0x1F0502, 0x0E111E, 0x1F051A, 0x121509, 0x011F01, 0x1F101F, 0x0F180F, 0x1F081F,
    0x1B041B, 0x071C07, 0x191513, 0x041F11, 0x001B00, 0x111F04, 0x010201
)

class NeoDisplay:
    """ Class to display text and animations on a NeoPixel display."""

    # Class Constants.  Change Display Size Below if necessary.
    WIDTH = 32
    HEIGHT = 8
    N = WIDTH * HEIGHT
    FONT_LARGE = 1
    FONT_SMALL = 2
    
    _instance = None

    @classmethod
    def inst(cls):
        """Returns the singleton instance of the display."""
        return cls._instance

    def __init__(self, pin_num, brightness=0.25):
        if NeoDisplay._instance is not None:
             raise RuntimeError("NeoDisplay already initialized")
        NeoDisplay._instance = self

        self.pin = machine.Pin(pin_num, machine.Pin.OUT)
        self.np = neopixel.NeoPixel(self.pin, NeoDisplay.N)
        self._brightness = brightness
        self._current_task = None
        self.pixels = [0] * NeoDisplay.N 

        # Ensure black on start
        self.fill(BLACK)
        self.show()

    @property
    def width(self):
        """ Width of the display. (Read Only)"""
        return NeoDisplay.WIDTH

    @property
    def height(self):
        """ Height of the display. (Read Only)"""
        return NeoDisplay.HEIGHT

    @property
    def n(self):
        """ Total number of pixels in the display. (Read Only)"""
        return NeoDisplay.N

    def brightness(self, value=None):
        """ Sets the brightness of the display (0-1). If the value is None, the current brightness is returned.
        The new setting only takes effect after the next show() call."""
        if value is None:
            return self._brightness
        self._brightness = min(1.0, max(0.0, value))
        return self._brightness  

    def show(self):
        """Update the physical pixels, by applying brightness and transmitting to the actual display."""
        f = min(1.0, max(0.0, self._brightness))
        for i in range(NeoDisplay.N):
            r, g, b = self.pixels[i] 
            r, g, b = (int(r * f) & 0xFF, int(g * f) & 0xFF, int(b * f) & 0xFF)
            self.np[i] = (r, g, b)
        self.np.write()
    
    def _coord(self, x, y):
        """
        Convert logical x,y to physical index.
        Hardcoded for performance. This code assumes the starting pixel is the 
        bottom right and that the display is organized in a series of columns,
        each connected to each other in a zigzag pattern.  Edit the code below
        to account for different layouts. 
        """

        if x < 0 or x >= NeoDisplay.WIDTH or y < 0 or y >= NeoDisplay.HEIGHT:
            return -1

        x = NeoDisplay.WIDTH - 1 - x 
        y = NeoDisplay.HEIGHT - 1 - y
        idx = x * NeoDisplay.HEIGHT
        if (x % 2 == 1): idx += (NeoDisplay.HEIGHT - 1 - y)   # We are on a backwards column
        else:            idx += y
        return idx  

    def pixel(self, x, y, color=None):
        """Set valid pixel to colors. If color is None, return current color. 
        Out of bounds ignored on write, returns black on read."""
        idx = self._coord(x, y)
        if idx >= 0:
            if color is None:
                return self.pixels[idx]
            else:
                self.pixels[idx] = color 
        return BLACK

    def fill(self, color):
        """Fill display with color"""
        for i in range(self.n):
            self.pixels[i] = color 

    def clear(self): 
        """ Clear display to black."""
        self.fill(BLACK)

    def draw_line(self, x1, y1, x2, y2, color):
        """Draw line using Bresenham's algorithm."""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            self.pixel(x1, y1, color)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def draw_rect(self, x, y, w, h, color):
        """Draw rectangle outline."""
        self.draw_line(x, y, x + w - 1, y, color)
        self.draw_line(x + w - 1, y, x + w - 1, y + h - 1, color)
        self.draw_line(x + w - 1, y + h - 1, x, y + h - 1, color)
        self.draw_line(x, y + h - 1, x, y, color)

    def fill_rect(self, x, y, w, h, color):
        """Draw filled rectangle."""
        for i in range(x, x + w):
            self.draw_line(i, y, i, y + h - 1, color)

    # --- Scrolling & Shifting ---
    # REFACTORED: Now uses logical pixel getting/setting to be layout-agnostic.
    # This is slower than direct buffer manipulation but correct for zig-zag/rotated layouts.

    def shift_left(self, pixels=1, bg_color=BLACK):
        """Shift content left, fill right with bg_color."""
        pixels = min(max(pixels, 0), NeoDisplay.WIDTH)
        if pixels == 0: return
        for y in range(NeoDisplay.HEIGHT):
            for x in range(NeoDisplay.WIDTH - pixels):
                c = self.pixel(x + pixels, y)
                self.pixel(x, y, c)
            for x in range(NeoDisplay.WIDTH - pixels, NeoDisplay.WIDTH):
                self.pixel(x, y, bg_color)

    def shift_right(self, pixels=1, bg_color=BLACK):
        """Shift content right."""
        pixels = min(max(pixels, 0), NeoDisplay.WIDTH)
        if pixels == 0: return
        for y in range(NeoDisplay.HEIGHT):
            for x in range(NeoDisplay.WIDTH - 1, pixels - 1, -1):
                c = self.pixel(x - pixels, y)
                self.pixel(x, y, c)
            for x in range(pixels):
                self.pixel(x, y, bg_color)

    def shift_up(self, pixels=1, bg_color=BLACK):
        """Shift content up."""
        pixels = min(max(pixels, 0), NeoDisplay.HEIGHT)
        if pixels == 0: return
        for y in range(NeoDisplay.HEIGHT - pixels):
            for x in range(NeoDisplay.WIDTH):
                c = self.pixel(x, y + pixels)
                self.pixel(x, y, c)
        for y in range(NeoDisplay.HEIGHT - pixels, NeoDisplay.HEIGHT):
            for x in range(NeoDisplay.WIDTH):
                self.pixel(x, y, bg_color)

    def shift_down(self, pixels=1, bg_color=BLACK):
        """Shift content down."""
        pixels = min(max(pixels, 0), NeoDisplay.HEIGHT)
        if pixels == 0: return
        for y in range(NeoDisplay.HEIGHT - 1, pixels - 1, -1):
            for x in range(NeoDisplay.WIDTH):
                c = self.pixel(x, y - pixels)
                self.pixel(x, y, c)
        for y in range(pixels):
            for x in range(NeoDisplay.WIDTH):
                self.pixel(x, y, bg_color)

    def scroll_left(self, pixels=1):
        """Scroll left with wrap around."""
        pixels = min(max(pixels, 0), NeoDisplay.WIDTH)
        if pixels == 0: return
        for y in range(NeoDisplay.HEIGHT):
            # Capture wrapped part
            wrapped = [self.pixel(i, y) for i in range(pixels)]
            # Shift body
            for x in range(NeoDisplay.WIDTH - pixels):
                self.pixel(x, y, self.pixel(x + pixels, y))
            # Restore wrapped
            for i in range(pixels):
                self.pixel(NeoDisplay.WIDTH - pixels + i, y, wrapped[i])

    def scroll_right(self, pixels=1):
        """Scroll right with wrap around."""
        pixels = min(max(pixels, 0), NeoDisplay.WIDTH)
        if pixels == 0: return
        for y in range(NeoDisplay.HEIGHT):
            wrapped = [self.pixel(NeoDisplay.WIDTH - pixels + i, y) for i in range(pixels)]
            for x in range(NeoDisplay.WIDTH - 1, pixels - 1, -1):
                self.pixel(x, y, self.pixel(x - pixels, y))
            for i in range(pixels):
                self.pixel(i, y, wrapped[i])

    # --- Text ---
    def draw_glyph(self, x, y, glyph_bits, height=7, color=(255, 0, 0)):
        """Draw a glyph from it's bits at (x, y) with given color."""
        if glyph_bits is None:
            return 
        if height == 7:
            glyph_data = [(glyph_bits >> 32) & 0xFF, (glyph_bits >> 24) & 0xFF, (glyph_bits >> 16) & 0xFF, (glyph_bits >> 8) & 0xFF, glyph_bits & 0xFF]
        elif height == 5:
            glyph_data = [(glyph_bits >> 16) & 0xFF, (glyph_bits >> 8) & 0xFF, glyph_bits & 0xFF]
        else:
            return

        for col_idx, col_byte in enumerate(glyph_data):
            if x + col_idx >= NeoDisplay.WIDTH: break
            if x + col_idx < 0: continue
            
            for row_idx in range(height):
                if y + row_idx >= NeoDisplay.HEIGHT: break
                if y + row_idx < 0: continue
                
                if (col_byte >> row_idx) & 1:
                    self.pixel(x + col_idx, y + row_idx, color) 

    def draw_char(self, x, y, char, color, font=None):
        """Draw a single character. font=LARGE or SMALL, large by default."""

        if font is None:
            font = NeoDisplay.FONT_LARGE
        idx = ord(char) - 32
        
        if font == NeoDisplay.FONT_SMALL:
            height = 5
            width = 3
            if idx < 0 or idx >= len(FONT_3x5):
                return x # Skip unknown
            glyph_bits = FONT_3x5[idx]
        elif font == NeoDisplay.FONT_LARGE:
            height = 7      
            width = 5
            if idx < 0 or idx >= len(FONT_5x7):
                return x # Skip unknown
            glyph_bits = FONT_5x7[idx]
        else:
            return x # Skip unknown font
        
        # Draw the glyph
        self.draw_glyph(x, y, glyph_bits, height, color)
        
        return x + width + 1 # Return next cursor pos (width + 1 spacing)

                
    def write_text(self, x, y, text, color, font=None):
        """Write string starting at x,y. font=LARGE or SMALL, large by default."""

        if font is None:
            font = NeoDisplay.FONT_LARGE

        cursor_x = x
        for char in text:
            cursor_x = self.draw_char(cursor_x, y, char, color, font)
        return cursor_x

def get_display():
    """Get the singleton instance of the display. Create it if it doesn't exist."""
    d = NeoDisplay.inst()
    if d is None:
        print(f"Initializing NeoDisplay on pin {PIN_NUM}...")
        try:
            d = NeoDisplay(PIN_NUM)
        except RuntimeError:
            # Race condition or it was just created
            d = NeoDisplay.inst()
    return d
