from tkinter import messagebox # Error reporting

class Error:
    """My custom error class that displays errors from a tuple[str,str
    consisting of a title and message. Constant tuples for reference and use.
    This does not have to be mainly parsing errors, but also faulty user inputs."""
    Message = tuple[str,str]
    """An error message type formatted as (title, message)."""

    OK = ("","")
    """Use this message for when no errors are found."""

    # User Errors
    INVALID_PATH = ("File Not Found","The file never existed... right?!?")
    INVALID_TYPE = ("Invalid File Type","Not a BMP file :(\nTry again!")
    INVALID_SETTINGS = ("Invalid Settings", "Not sure what you did, but the features \
configured are invalid.\nPlease restart the application and retry :3")
    
    # Parse Errors
    UNSUPPORTED = ("Unsupported BMP File", "I cannot support this file...")
    INVALID_SIZE = ("Invalid File Size","This file is soooo tiny :/")
    FILE_SIZE_MISMATCH = ("File Size Mismatch",
        "The file size does not match the bytes read T_T\nIt may be corrupt?")
    INVALID_OFFSET = ("Invalid Data Offset",
        "The data offset for pixel data is out of range :C")
    INVALID_DIM = ("Invalid Dimensions","The BMP pixel data went out of range D:")
    INVALID_COLOR_TABLE = ("Invalid Color Table", "The BMP color table was too small :()")
    CORRUPT = ("Uh Oh","There was some weird stuff while reading the BMP file :0")
    """Use this message for when undefined behaviour is found when parsing."""

    @staticmethod
    def popup(msg: Message) -> None:
        """Displays a provided Error.Message as a popup."""
        messagebox.showerror(msg[0],msg[1]) # type: ignore

class Settings:
    """Settings class to store the feature data from the user.
    Currently, this object stores data such as brightness, 
    scale and RGB channels."""

    Channels = tuple[bool,bool,bool]
    """The RGB channels in the form (red, green, blue)"""
    Data = tuple[int,int,Channels]
    """The setting data in the form (brightness, scale, (red, green, blue))."""
    DEFAULT_SETTINGS: Data = (100,100,(True,True,True))
    """Default settings for original brightness and scalel; all color channels enabled."""

    def is_valid(self) -> bool:
        """Verifies that the current settings applied are valid.
        NOTE: Channels are always valid."""
        if self.brightness < 0 or self.brightness > 100: return False
        if self.scale < 0 or self.scale > 100: return False
        return True
    def get(self) -> Data:
        """Retrieves the tuple of formatted setting data."""
        return (self.brightness,self.scale,self.channels)
    
    def __init__(self, data: Data = DEFAULT_SETTINGS) -> None:
        """Initializes settings with the default data. You can also pass through data."""
        self.brightness, self.scale, self.channels = data

class Color:
    
    RGB = tuple[int, int, int] 
    """The RGB type in the form (r, g, b)."""
    nRGB = tuple[float, float, float] # normalized (r,g,b)
    """The normalized RGB type in the form (r, g, b) ranging between 0.0 and 1.0."""
    nYUV = tuple[float, float, float] # normalized (y,u,v)
    """The normalized YUV type in the form (y, u, v) ranging between 0.0 and 1.0."""
    Hex = str
    """Hex string, formatted as #000000 to #ffffff."""

    TO_NORMAL = 0.00392156862
    """A normalizing constant that normalizes any uint8 (max of 255)."""

    PINK = "#f5c2e7"
    RED = "#f38ba8"
    PEACH = "#fab387"
    YELLOW = "#f9e2af"
    GREEN = "#a6e3a1"
    BLUE = "#89b4fa"
    MAUVE = "#cba6f7"
    LAVENDAR = "#b4befe"
    TEXT = "#cdd6f4"
    SUBTEXT = "#a6adc8"
    OVERLAY = "#6c7086"
    SURFACE = "#313244"
    BASE = "#1e1e2e"
    MANTLE = "#181825"
    CRUST = "#11111b"

    @staticmethod
    def rgb_to_hex(rgb: RGB) -> Hex:
        """Returns the color in hexadecimal format."""
        r, g, b = rgb
        return f"#{r:02x}{g:02x}{b:02x}"
    @staticmethod
    def rgb_to_nyuv(rgb: RGB) -> nYUV:
        """Convert rgb values to normalized YUV. For brightness manipulation."""
        r,g,b = rgb
        # Normalize rgb (1/255)
        r *= Color.TO_NORMAL
        g *= Color.TO_NORMAL
        b *= Color.TO_NORMAL
        # Convert RGB to YUV
        y = 0.299*r + 0.587*g + 0.114*b
        u = -0.14713*r - 0.28886*g + 0.436*b
        v = 0.615*r - 0.51499*g - 0.10001*b
        return (y,u,v)
    @staticmethod
    def nyuv_to_rgb(nyuv: nYUV) -> RGB:
        """Covnerts normalized YUV back to normalized RGB."""
        y,u,v = nyuv
        r = y + 1.13983*v
        g = y - 0.39465*u - 0.58060*v
        b = y + 2.03211*u
        r = max(0, min(255, round(r*255.0)))
        g = max(0, min(255, round(g*255.0)))
        b = max(0, min(255, round(b*255.0)))
        return r,g,b

    @staticmethod
    def set_brightness(rgb: RGB, brightness: int) -> RGB:
        """Apply brightness to an RGB pixel by converting to yuv then back.
        Using YUV conversion from Wikipedia."""
        if brightness == 100 or brightness == 0: return rgb
        # We need a lightbulb in here...
        y,u,v = Color.rgb_to_nyuv(rgb)
        y *= brightness / 100.0
        u *= brightness / 100.0
        v *= brightness / 100.0
        # Convert normalized YUV back to RGB (clamped)
        return Color.nyuv_to_rgb((y,u,v))