from utils import Error, Settings, Color
import os # File info
# ------------------------------ TYPE DEFINITIONS ---------------------------- #
Pixels = list[Color.Hex] 
"""A list of hex values for each pixel."""
PixelData = tuple[int, int, Pixels] 
"""Pixel data of an image in the format: (width, height, pixels)."""
# ------------------------------- PARSER CLASSES ----------------------------- #
class Compressor:
    """Ultra-aggressive lossless compression for maximum file size reduction."""
    @staticmethod
    def encode(data: bytes) -> bytes:
        """Encode data LZW, otherwise fallback to uncompressed with small header."""
        best_data = b'\x00' + data  # Fallback
        best_size = len(best_data)
        compressed = Compressor._lzw_compress(data)
        if len(compressed) < best_size:
            best_size = len(compressed)
            best_data = bytes([0x01]) + compressed
        return best_data
    
    @staticmethod 
    def _lzw_compress(data: bytes) -> bytes:
        """Simplified LZW compression with fixed bit width."""
        dictionary = {bytes([i]): i for i in range(256)}
        next_code = 256
        max_code = 2**16
        
        result: list[int] = []
        current = bytes()
        
        for byte in data:
            new_string = current + bytes([byte])
            if new_string in dictionary:
                current = new_string
            else:
                result.append(dictionary[current])
                if next_code <= max_code:
                    dictionary[new_string] = next_code
                    next_code += 1
                current = bytes([byte])
        
        if current: result.append(dictionary[current])
        
        compressed = bytearray()
        compressed.extend(len(data).to_bytes(4, 'little'))
        compressed.extend(len(result).to_bytes(4, 'little'))
        
        for code in result:
            compressed.extend(code.to_bytes(2, 'little'))
        
        return bytes(compressed)
    
    @staticmethod
    def decode(data: bytes) -> bytes:
        """Decode data compressed with multiple aggressive techniques."""
        format_flag = data[0]

        match format_flag:
            case 0x0:
                return data[1:]  # Uncompressed
            case 0x1:
                return Compressor._lzw_decompress(data[1:])
            case _:
                Error.popup(Error.CORRUPT)
                return b''
    
    @staticmethod
    def _lzw_decompress(data: bytes) -> bytes:
        """Simplified LZW decompression with fixed bit width."""
        original_length = int.from_bytes(data[0:4], 'little')
        num_codes = int.from_bytes(data[4:8], 'little')
        
        if len(data) < 8 + (num_codes * 2): return b''
        
        # Read codes as 16-bit values
        codes: list[int] = []
        offset = 8
        for _ in range(num_codes):
            code = int.from_bytes(data[offset:offset+2], 'little')
            codes.append(code)
            offset += 2
        
        dictionary = {i: bytes([i]) for i in range(256)}
        next_code = 256
        
        if not codes: return b''
        codeword = bytearray()
        s = dictionary[codes[0]]
        codeword.extend(s)
        
        for code in codes[1:]:
            if code in dictionary:
                c = dictionary[code]
            elif code == next_code:
                c = s + s[:1]
            else: break
            codeword.extend(c)
            if next_code < 2**16:
                dictionary[next_code] = s + c[:1]
                next_code += 1
            s = c

        return bytes(codeword[:original_length])
        
class BMPImage:
    """BMPImage class to hold the data for displaying BMP metadata frame."""

    def bits(self, offset: int, n: int = 1) -> int:
        """Get `n` bits. Only use for `n` < 8."""
        byte_offset = offset >> 3
        bit_offset = offset & 7
        shift = 8 - bit_offset - n
        return (self._raw_bytes[byte_offset] >> shift) & ((1 << n) - 1)
    
    def uint(self, offset: int, n: int = 4) -> int:
        """Get `n` bytes as unsigned int. Good for `n` > 4."""
        return int.from_bytes(self._raw_bytes[offset:offset+n],"little")
    
    def _parse_header(self) -> None:
        """Reads header of the BMPImage file."""
        # Signature
        self.signature = self._raw_bytes[0:2].decode(errors="ignore")
        if not self.signature == "BM": 
            self._err = Error.INVALID_TYPE
            return
        # File Size
        self.file_size = self.uint(2)
        if self.file_size != self._os_file_size: 
            self._err = Error.FILE_SIZE_MISMATCH
            return
        # Data Offset
        self.data_offset = self.uint(10)
        if self.data_offset > self.file_size: 
            self._err = Error.INVALID_OFFSET
            return
        
    def _parse_info_header(self) -> None:
        """Parses info header of the BMPImage file."""
        if not self.is_valid(): return
        self.width = self.uint(18)
        self.height = self.uint(22)
        self.bits_per_pixel = self.uint(28,2)
        if not self.bits_per_pixel in {1,4,8,24}:
            self._err = Error.UNSUPPORTED
            return
        self.colors_used = self.uint(46)
    
    def _scale_pixel_data(self, pixels: Pixels, scale: int) -> PixelData:
        """Scales the pixel data by a given scale factor."""
        if scale == 0: return (0,0,[])
        width = self.width
        height = self.height
        if scale == 100: return (width, height, pixels)
        w_scale: int = round(width * scale/100.0)
        h_scale: int = round(height * scale/100.0)
        new_pixels: list[Color.Hex] = ["#000000"] * (w_scale * h_scale)
        x_scale: float = width / w_scale
        y_scale: float = height / h_scale
        for y in range(h_scale):
            for x in range(w_scale):
                old_x: int = int(x * x_scale)
                old_y: int = int(y * y_scale)
                new_i = y * w_scale + x
                old_i = old_y * width + old_x
                new_pixels[new_i] = pixels[old_i]
        return (w_scale,h_scale,new_pixels)
    
    def _get_color_table(self, settings: Settings) -> list[Color.Hex]:
        """Reads color table using the BMP bytes."""
        color_table: list[Color.Hex] = []
        
        red, green, blue = settings.channels
        brightness = settings.brightness
        offset: int = 54
        # Read the table_bytes and set the red, green, blue channels 
        # (pass reserved) for each entry in the table of colors_used size.
        for _ in range(self.colors_used):
            b = self.uint(offset,1) if (blue and brightness) else 0
            g = self.uint(offset+1,1) if (green and brightness) else 0
            r = self.uint(offset+2,1) if (red and brightness) else 0
            # Reserved byte is ignored
            rgb = Color.set_brightness((r, g, b), brightness)
            color = Color.rgb_to_hex(rgb)
            color_table.append(color)
            offset += 4
        return color_table

    def _get_pixel_data_with_table(self, settings: Settings) -> Pixels:
        """Retrieves pixel data after applying user's `settings` for indexed pixels."""
        pixels: list[Color.Hex] = ["#000000"] * (self.width * self.height)
        color_table = self._get_color_table(settings)
        colors = self.colors_used
        row_bits = self.width * self.bits_per_pixel
        row_bytes = (row_bits + 7) // 8
        padding = (4 - (row_bytes % 4)) % 4
        if settings.brightness == 0 or settings.channels == (False,False,False):
            return pixels
        for y in range(self.height):
            row_offset = self.data_offset + (self.height-1 - y) * (row_bytes + padding)
            bit_offset = row_offset * 8
            for x in range(self.width):
                pixel_bit_offset = (x * self.bits_per_pixel) + bit_offset
                if pixel_bit_offset > (self.file_size << 3):
                    self._err = Error.INVALID_DIM
                    return []
                pixel_index = self.bits(pixel_bit_offset, self.bits_per_pixel)
                if pixel_index > colors:
                    self._err = Error.INVALID_COLOR_TABLE
                    return []
                color = color_table[pixel_index]
                pixels[y*self.width + x] = color
        return pixels

    def _get_pixel_data_with_rgb(self, settings: Settings) -> Pixels:
        """Retrieves pixel data after applying user's `settings` for RGB pixels."""
        pixels: list[Color.Hex] = ["#000000"] * (self.width * self.height)
        bytes_per_pixel = 3
        bytes_per_row = self.width * bytes_per_pixel
        padding = (4 - (bytes_per_row % 4)) % 4
        red,green,blue = settings.channels
        brightness = settings.brightness
        if brightness == 0 or settings.channels == (False,False,False):
            return pixels
        for y in range(self.height):
            row_offset = self.data_offset + (self.height - y - 1) * (bytes_per_row + padding)
            offset = row_offset
            for x in range(self.width):
                if (offset + 3) > self.file_size:
                    self._err = Error.INVALID_DIM
                    return []
                b = self.uint(offset,1) if blue else 0
                g = self.uint(offset+1,1) if green else 0
                r = self.uint(offset+2,1) if red else 0

                rgb = Color.set_brightness((r,g,b), brightness)
                color = Color.rgb_to_hex(rgb)
                pixels[y*self.width + x] = color
                offset += 3
        return pixels
    
    def get_image(self, settings: Settings) -> PixelData:
        """Returns pixel data from the BMP bytes after applying the user `settings` to it."""
        pixels: Pixels
        if not self.is_valid(): return (0,0,[])
        if not settings.is_valid():
            self._err = Error.INVALID_SETTINGS
            return (0,0,[])
        if self.bits_per_pixel in {1,4,8}: # 1, 4, 8 bits_per_pixel
            pixels = self._get_pixel_data_with_table(settings)
        elif self.bits_per_pixel == 24: # 24 bits_per_pixel
            pixels = self._get_pixel_data_with_rgb(settings)
        else:
            self._err = Error.UNSUPPORTED # second-pass error
            return (0,0,[])
        if not self.is_valid(): return (0,0,[])
        return self._scale_pixel_data(pixels, settings.scale)
    
    def is_valid(self) -> bool:
        """Checks whether the error trace is OK.\n
        Internal/external reference."""
        return self._err == Error.OK
    
    def get_raw_bytes(self) -> bytes:
        """Returns the raw bytes of the BMP file."""
        return self._raw_bytes
    
    def get_pixel_data(self) -> bytes:
        """Returns just the pixel data portion of the BMP file."""
        if not self.is_valid():
            return b''
        return self._raw_bytes[self.data_offset:]
    
    def get_header_data(self) -> bytes:
        """Returns just the header portion of the BMP file."""
        if not self.is_valid(): return b''
        return self._raw_bytes[:self.data_offset]
    
    def compress(self) -> bytes:
        """Compresses the BMP file and returns the raw bytes."""
        if not self.is_valid(): return b''
        
        pixel_data = self._raw_bytes[self.data_offset:]
        
        # Minimal header - only essential data (13 bytes total)
        header = bytearray()
        header.extend(b'CM')  # Signature
        header.extend(self.width.to_bytes(2, 'little'))
        header.extend(self.height.to_bytes(2, 'little'))  
        header.append(self.bits_per_pixel)
        header.extend(self.colors_used.to_bytes(2, 'little'))
        header.extend(self._raw_bytes[54:54 + self.colors_used * 4])
        header.extend(self.data_offset.to_bytes(2, 'little'))
        
        return bytes(header) + Compressor.encode(pixel_data)

    def __init__(self, raw_bytes: bytes) -> None:
        """*Attempts* to parse a supported BMP file from `raw_bytes`. Use `is_valid()`
        to verify that the file is a BMP file and that no errors are found.\n
        NOTE: Initializing a BMP file *does not* parse color table and pixel data."""
        self._err: Error.Message = Error.OK # Error trace
        self._raw_bytes: bytes = raw_bytes
        self._os_file_size: int = len(raw_bytes) # verify actual file size
        
        # Header
        self.signature: str
        self.file_size: int
        self.data_offset: int
        self._parse_header()

        # Info Header
        self.width: int
        self.height: int
        self.bits_per_pixel: int
        self.colors_used: int
        self._parse_info_header()

        # Color Table
        # Pixel Data
        # dynamically read when applying user settings to pixel_data

class CMPT365Image:
    """CMPT365Image, which is a compressed BMPImage using the """
    def is_valid(self) -> bool:
        """Checks whether the error trace is OK."""
        return self._err == Error.OK
    
    def decompress(self) -> BMPImage | None:
        """Decompresses the ultra-compact CMPT365 file into BMP bytes."""
        if not self.is_valid(): return None
        offset = 2  # Skip "CM"
        width = int.from_bytes(self._raw_bytes[offset:offset+2], 'little')
        offset += 2
        height = int.from_bytes(self._raw_bytes[offset:offset+2], 'little')
        offset += 2
        bits_per_pixel = self._raw_bytes[offset]
        offset += 1
        colors_used = int.from_bytes(self._raw_bytes[offset:offset+2], 'little')
        offset += 2
        color_table = self._raw_bytes[offset:offset + colors_used * 4]
        offset += colors_used * 4
        data_offset = int.from_bytes(self._raw_bytes[offset:offset+2], 'little')
        offset += 2
        
        header = self._get_bmp_header(width, height, bits_per_pixel, colors_used, color_table, data_offset)
        decompressed = Compressor.decode(self._raw_bytes[offset:])

        # Combine header and pixels
        reconstructed_bmp = header + decompressed
        
        # Create BMPImage
        bmp_image = BMPImage(reconstructed_bmp)
        if not bmp_image.is_valid():
            self._err = Error.CORRUPT
            return None
        return bmp_image


    def _get_bmp_header(self, width: int, height: int, bits_per_pixel: int, 
                        colors_used: int, color_table: bytes, data_offset: int) -> bytes:
        """Reconstruct minimal BMP header."""
        header = bytearray(data_offset)
        
        # BMP file header (14 bytes)
        header[0:2] = b'BM'  # BM Signature instead of CM
        
        # Calculate image size
        row_size = ((width * bits_per_pixel + 31) // 32) * 4
        image_size = row_size * height
        file_size = data_offset + image_size
        
        header[2:6] = file_size.to_bytes(4, 'little')
        header[6:10] = (0).to_bytes(4, 'little')  # Reserved
        header[10:14] = data_offset.to_bytes(4, 'little')
        
        # DIB header (40 bytes minimum)
        if data_offset >= 54:
            header[14:18] = (40).to_bytes(4, 'little')
            header[18:22] = width.to_bytes(4, 'little')
            header[22:26] = height.to_bytes(4, 'little')
            header[26:28] = (1).to_bytes(2, 'little')
            header[28:30] = bits_per_pixel.to_bytes(2, 'little')
            header[30:34] = (0).to_bytes(4, 'little')  # Compression
            header[34:38] = image_size.to_bytes(4, 'little')
            header[38:42] = (2835).to_bytes(4, 'little')
            header[42:46] = (2835).to_bytes(4, 'little')
            header[46:50] = colors_used.to_bytes(4, 'little')
            header[50:54] = (0).to_bytes(4, 'little')  #Important colors
            header[54:54 + colors_used * 4] = color_table
        
        return bytes(header)
    def __init__(self, raw_bytes: bytes) -> None:
        """*Attempts* to parse a supported CMPT365 file from `raw_bytes`.\n
        If the file is not a valid CMPT365 file, an error is set in `_err`.
        Use `is_valid()` to verify that the file is a CMPT365 file."""
        self._raw_bytes = raw_bytes
        self._err: Error.Message = Error.OK # Error trace
        self.signature = self._raw_bytes[0:2].decode(errors="ignore")
        if not self.signature == "CM": # CMPT365 signature
            self._err = Error.INVALID_TYPE
            return
# ============================= PUBLIC INTERFACE ============================= #
def read_bmp_file(file_path: str) -> BMPImage | None: #type: ignore
    """Reads a BMP file and returns a BMPImage object.\n
    If the file is *not* a valid BMP image, returns `None`."""
    with open(file_path, "rb") as file:
        file_size = os.path.getsize(file_path)
        if file_size < 54: # Minimum 14 B Header + 40 B InfoHeader
            Error.popup(Error.INVALID_SIZE)
            return None
        raw_bytes = file.read(file_size)
        bmp_image = BMPImage(raw_bytes)
        if not bmp_image.is_valid(): 
            Error.popup(bmp_image._err) # type: ignore
            return None
        return bmp_image


def compress_bmp_file(bmp_image: BMPImage, file_path: str) -> CMPT365Image | None:
    """Compresses a given BMP file into a CMPT365 file at a given `file_path`."""
    if not bmp_image.is_valid():
        return None
    compressed_data = bmp_image.compress()
        
    # Write compressed data to file
    with open(file_path, 'wb') as file:
        file.write(compressed_data)
        
    # Return CMPT365Image object
    cmpt365_image = CMPT365Image(compressed_data)
    if not cmpt365_image.is_valid():
        return None
    return cmpt365_image

def read_cmpt365_file(file_path: str) -> BMPImage | None:
    """Reads a CMPT365 file, decompresses it into a BMP file and reads it.\n
    This is analogous to reading a BMP file, with an extra decompression step.\n
    If the file is *not* a valid CMPT365 file or BMP image could *not* be 
    recovered, this method returns `None`."""
    # To be implemented.
    with open(file_path, "rb") as file:
        file_size = os.path.getsize(file_path)
        raw_bytes = file.read(file_size)
        cmpt_image = CMPT365Image(raw_bytes)
        if not cmpt_image.is_valid(): 
            Error.popup(cmpt_image._err) # type: ignore
            return None
        return cmpt_image.decompress()
# ---------------------------------------------------------------------------- #
