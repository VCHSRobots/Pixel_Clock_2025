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
FONT_5x7 = {
    'A': [0x7E, 0x11, 0x11, 0x11, 0x7E],
    'B': [0x7F, 0x49, 0x49, 0x49, 0x36],
    'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
    'D': [0x7F, 0x41, 0x41, 0x22, 0x1C],
    'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
    'F': [0x7F, 0x09, 0x09, 0x09, 0x01],
    'G': [0x3E, 0x41, 0x49, 0x49, 0x7A],
    'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],
    'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
    'J': [0x20, 0x40, 0x41, 0x3F, 0x01],
    'K': [0x7F, 0x08, 0x14, 0x22, 0x41],
    'L': [0x7F, 0x40, 0x40, 0x40, 0x40],
    'M': [0x7F, 0x02, 0x0C, 0x02, 0x7F],
    'N': [0x7F, 0x04, 0x08, 0x10, 0x7F],
    'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
    'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
    'Q': [0x3E, 0x41, 0x51, 0x21, 0x5E],
    'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
    'S': [0x46, 0x49, 0x49, 0x49, 0x31],
    'T': [0x01, 0x01, 0x7F, 0x01, 0x01],
    'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],
    'V': [0x1F, 0x20, 0x40, 0x20, 0x1F],
    'W': [0x3F, 0x40, 0x38, 0x40, 0x3F],
    'X': [0x63, 0x14, 0x08, 0x14, 0x63],
    'Y': [0x07, 0x08, 0x70, 0x08, 0x07],
    'Z': [0x61, 0x51, 0x49, 0x45, 0x43],
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
    '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
    '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
    '2': [0x42, 0x61, 0x51, 0x49, 0x46],
    '3': [0x21, 0x41, 0x45, 0x4B, 0x31],
    '4': [0x18, 0x14, 0x12, 0x7F, 0x10],
    '5': [0x27, 0x45, 0x45, 0x45, 0x39],
    '6': [0x3C, 0x4A, 0x49, 0x49, 0x30],
    '7': [0x01, 0x71, 0x09, 0x05, 0x03],
    '8': [0x36, 0x49, 0x49, 0x49, 0x36],
    '9': [0x06, 0x49, 0x49, 0x29, 0x1E],
    '!': [0x00, 0x00, 0x5F, 0x00, 0x00],
    '.': [0x00, 0x00, 0x03, 0x00, 0x00],
    ',': [0x00, 0x00, 0x07, 0x00, 0x00], 
    ':': [0x00, 0x36, 0x36, 0x00, 0x00],
    ';': [0x00, 0x36, 0x37, 0x00, 0x00],
    '?': [0x02, 0x01, 0x51, 0x09, 0x06],
    '-': [0x08, 0x08, 0x08, 0x08, 0x08],
    '_': [0x40, 0x40, 0x40, 0x40, 0x40],
    '+': [0x08, 0x08, 0x3E, 0x08, 0x08],
    '=': [0x14, 0x14, 0x14, 0x14, 0x14],
    '/': [0x20, 0x10, 0x08, 0x04, 0x02],
    '(': [0x00, 0x1C, 0x22, 0x41, 0x00],
    ')': [0x00, 0x41, 0x22, 0x1C, 0x00],
    '"': [0x00, 0x03, 0x00, 0x03, 0x00],
    "'": [0x00, 0x03, 0x00, 0x00, 0x00],
    '@': [0x32, 0x49, 0x79, 0x41, 0x3E],
    '#': [0x14, 0x7F, 0x14, 0x7F, 0x14],
    'a': [0x20, 0x54, 0x54, 0x54, 0x78],
    'b': [0x7F, 0x48, 0x44, 0x44, 0x38],
    'c': [0x38, 0x44, 0x44, 0x44, 0x20],
    'd': [0x38, 0x44, 0x44, 0x48, 0x7F],
    'e': [0x38, 0x54, 0x54, 0x54, 0x18],
    'f': [0x08, 0x7E, 0x09, 0x01, 0x02],
    'g': [0x0C, 0x52, 0x52, 0x52, 0x3E],
    'h': [0x7F, 0x08, 0x04, 0x04, 0x78],
    'i': [0x00, 0x44, 0x7D, 0x40, 0x00],
    'j': [0x20, 0x40, 0x44, 0x3D, 0x00],
    'k': [0x7F, 0x10, 0x28, 0x44, 0x00],
    'l': [0x00, 0x41, 0x7F, 0x40, 0x00],
    'm': [0x7C, 0x04, 0x18, 0x04, 0x78],
    'n': [0x7C, 0x08, 0x04, 0x04, 0x78],
    'o': [0x38, 0x44, 0x44, 0x44, 0x38],
    'p': [0x7C, 0x14, 0x14, 0x14, 0x08],
    'q': [0x08, 0x14, 0x14, 0x18, 0x7C],
    'r': [0x7C, 0x08, 0x04, 0x04, 0x08],
    's': [0x48, 0x54, 0x54, 0x54, 0x20],
    't': [0x04, 0x3F, 0x44, 0x40, 0x20],
    'u': [0x3C, 0x40, 0x40, 0x20, 0x7C],
    'v': [0x1C, 0x20, 0x40, 0x20, 0x1C],
    'w': [0x3C, 0x40, 0x30, 0x40, 0x3C],
    'x': [0x44, 0x28, 0x10, 0x28, 0x44],
    'y': [0x0C, 0x50, 0x50, 0x50, 0x3C],
    'z': [0x44, 0x64, 0x54, 0x4C, 0x44],
}

# 3x5 Small Font
FONT_3x5 = {
    'A': [0x1E, 0x05, 0x1E], 
    'B': [0x1F, 0x15, 0x0A],
    'C': [0x0E, 0x11, 0x11],
    'D': [0x1F, 0x11, 0x0E],
    'E': [0x1F, 0x15, 0x11],
    'F': [0x1F, 0x05, 0x01],
    'G': [0x0E, 0x15, 0x1D],
    'H': [0x1F, 0x04, 0x1F],
    'I': [0x11, 0x1F, 0x11],
    'J': [0x10, 0x10, 0x0F],
    'K': [0x1F, 0x04, 0x1B],
    'L': [0x1F, 0x10, 0x10],
    'M': [0x1F, 0x02, 0x1F],
    'N': [0x1F, 0x02, 0x1C],
    'O': [0x0E, 0x11, 0x0E],
    'P': [0x1F, 0x05, 0x02],
    'Q': [0x0E, 0x13, 0x1E],
    'R': [0x1F, 0x05, 0x1A],
    'S': [0x12, 0x15, 0x09],
    'T': [0x01, 0x1F, 0x01],
    'U': [0x1F, 0x10, 0x1F],
    'V': [0x0F, 0x10, 0x0F],
    'W': [0x1F, 0x08, 0x1F],
    'X': [0x1B, 0x04, 0x1B],
    'Y': [0x03, 0x1C, 0x03],
    'Z': [0x19, 0x15, 0x13],
    '0': [0x0F, 0x11, 0x0F],
    '1': [0x00, 0x1F, 0x00],
    '2': [0x19, 0x15, 0x12],
    '3': [0x11, 0x15, 0x1F],
    '4': [0x07, 0x04, 0x1F],
    '5': [0x17, 0x15, 0x09],
    '6': [0x0E, 0x15, 0x08],
    '7': [0x01, 0x19, 0x07],
    '8': [0x0A, 0x15, 0x0A],
    '9': [0x02, 0x15, 0x0E],
    ' ': [0x00, 0x00, 0x00],
    '.': [0x10, 0x00, 0x00],
    '!': [0x00, 0x2F, 0x00],
}

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
    def draw_char(self, x, y, char, color, font=None):
        """Draw a single character. font=LARGE or SMALL, large by default."""

        if font is None:
            font = NeoDisplay.FONT_LARGE

        glyph_data = FONT_5x7
        height = 7
        
        if font == NeoDisplay.FONT_SMALL:
            glyph_data = FONT_3x5
            height = 5
            char = char.upper()
            
        if char not in glyph_data:
            return x # Skip unknown
        
        glyph = glyph_data[char]
        
        for col_idx, col_byte in enumerate(glyph):
            if x + col_idx >= NeoDisplay.WIDTH: break
            if x + col_idx < 0: continue
            
            for row_idx in range(height):
                if (col_byte >> row_idx) & 1:
                    self.pixel(x + col_idx, y + row_idx, color)
        
        return x + len(glyph) + 1 # Return next cursor pos (width + 1 spacing)

    def write_text(self, x, y, text, color, font=None):
        """Write string starting at x,y. font=LARGE or SMALL, large by default."""

        if font is None:
            font = NeoDisplay.FONT_LARGE

        cursor_x = x
        for char in text:
            cursor_x = self.draw_char(cursor_x, y, char, color, font)

def get_display():
    """Get the singleton instance of the display."""
    return NeoDisplay.inst()    
