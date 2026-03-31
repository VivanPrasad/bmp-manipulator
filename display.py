import tkinter as tk # Main GUI
from os import path
from tkinter import ttk, filedialog # Theme, opening files
from utils import Error, Settings, Color # Utility classes

from parser import BMPImage, read_bmp_file, read_cmpt365_file, compress_bmp_file # Parse BMPImage
from threading import Thread # Image loading 
from time import perf_counter # Load timing
# ----------------------------- CONST DEFINITIONS ---------------------------- #
BUTTON_PADDING = (20,10)

# ============================= PUBLIC INTERFACE ============================= #
class Root:
    """The main Program class for all the GUI logic. 
    Creates a Tkinter root window with the 'catppuccin' theme.
    Also creates the side bar and image display."""
    def mainloop(self) -> None:
        """Adapter pattern for mainloop from main.py."""
        self.widget.mainloop()
    
    def get_settings(self) -> Settings:
        """Public method to retrieve user settings."""
        return self.side_bar.feature.settings
    
    def open_bmp_file(self) -> None:
        """Adapter pattern for open_bmp_file for the ImageDisplayUI instance."""
        self.image_display.open_bmp_file()
    def open_cmpt_file(self) -> None:
        """Adapter pattern for open_cmpt_file for the ImageDisplayUI instance."""
        self.image_display.open_cmpt_file()
    def compress_bmp_file(self) -> None:
        """Adapter pattern for compress_bmp_file for the ImageDisplayUI instance."""
        self.image_display.compress_bmp_file()
    def is_image_loading(self) -> bool:
        """Verifies if there is an image displayed currently or not in O(1)."""
        return self.image_display.is_loading

    def __init__(self) -> None:
        self.widget = tk.Tk()
        self.widget.tk.call('source', 'theme/catppuccin.tcl')
        self.widget.title("BMP Reader")
        self.widget.geometry("1280x720")
        self.widget.pack_propagate(False)  # Prevent resizing of the root window
        self.style = ttk.Style(self.widget)
        self.style.theme_use('catppuccin')
        self.image_display = ImageDisplayUI(self)
        self.side_bar = SideBarUI(self)
        self.side_bar.pack()
        self.image_display.pack()
        self.mainloop() # Start the main loop of the tkinter application
# ----------------------------- UTILITY CLASSES ------------------------------ #
class BaseUI:
    """BaseUI interface logic to be inherited. Contains a tk frame, 
    labelled or not."""
    frame: ttk.Labelframe | tk.Frame
    def pack(self) -> None:
        """Packs the main frame of the UI."""
        pass
    def hide(self) -> None:
        """Hides necessary information onto the frame UI."""
        pass
    def show(self, bmp: BMPImage) -> None:
        """Displays necessary information onto the frame UI"""
        pass
    def __init__(self) -> None:
        pass
def get_file_size_text(file_size: int) -> str:
        KB = 1024; MB = 1048576
        """Returns a formatted string for the file size."""
        if file_size > MB:  # Convert B to MB if larger than 1 MB
            return f"File Size: {file_size >> 20} MB ({file_size:,} B)"
        elif file_size > KB:  # Convert B to KB if larger than 1 KB
            return f"File Size: {file_size >> 10} KB ({file_size:,} B)"
        return f"File Size: {file_size} B"
# ----------------------------- DISPLAY CLASSES ------------------------------ #
class MetadataUI(BaseUI):
    """MetadataUI class contains the labels in a frame for displaying 
    the BMP image metadata. Yippee!!"""

    def hide(self) -> None:
        self.file_size_label.pack_forget()
        self.width_label.pack_forget()
        self.height_label.pack_forget()
        self.bits_per_pixel_label.pack_forget()
        self.no_file_label.pack( # Show no file
            side="top", anchor="w", padx=5, pady=3)
    
    def show(self, bmp: BMPImage) -> None:
        self.file_size_label.config(
            text=get_file_size_text(bmp.file_size))
        self.width_label.config(text=f"Width: {bmp.width} px")
        self.height_label.config(text=f"Height: {bmp.height} px")
        self.bits_per_pixel_label.config(
            text=f"Bits per Pixel: {bmp.bits_per_pixel} bit\
{'s' if bmp.bits_per_pixel > 1 else ' '}")
        self.no_file_label.pack_forget() # Hide no file
        self.file_size_label.pack(side="top", anchor="w", padx=5, pady=2)
        self.width_label.pack(side="top", anchor="w", padx=5, pady=2)
        self.height_label.pack(side="top", anchor="w", padx=5, pady=2)
        self.bits_per_pixel_label.pack(side="top", anchor="w", padx=5, pady=2)

    def pack(self) -> None:
        self.frame.pack(side="top", anchor="w", fill="x", padx=10, pady=10)

    def __init__(self, root: tk.Frame) -> None:
        self.bmp_image: BMPImage | None = None  # Holds the BMPImage object
        self.frame = ttk.Labelframe(root, text="Metadata", padding=(20, 10))
        self.no_file_label = ttk.Label(
            self.frame, text="No File Opened", foreground=Color.OVERLAY)
        self.file_size_label = ttk.Label(
            self.frame, text="File Size: 0 B", foreground=Color.PINK)
        self.width_label = ttk.Label(self.frame, text="Width: 0 px")
        self.height_label = ttk.Label(self.frame, text="Height: 0 px")
        self.bits_per_pixel_label = ttk.Label(
            self.frame, text="Bits per Pixel: 0 bits", foreground="grey")
        self.hide()

class FeatureUI(BaseUI):
    """FeatureUI class contains basically all the user controls to manipulate
    the BMP image in a frame."""

    def hide(self) -> None:
        self.brightness_label.pack_forget()
        self.brightness_slider.pack_forget()
        self.scale_label.pack_forget()
        self.scale_slider.pack_forget()
        self.red_check.pack_forget()
        self.green_check.pack_forget()
        self.blue_check.pack_forget()
        self.apply_button.pack_forget()
        self.no_file_label.pack(side="top", anchor="w", padx=5, pady=3)

    def show(self, bmp: BMPImage) -> None:
        self.no_file_label.pack_forget() # Hide no file label
        self.brightness_label.pack(anchor="w")
        self.brightness_slider.pack(side="top", anchor="w",expand=1,fill="x")
        self.scale_label.pack(anchor="w")
        self.scale_slider.pack(side="top", anchor="w",expand=1,fill="x")
        self.red_check.pack(
            side="left", anchor="w", padx=3, pady=3,expand=1,fill="x")
        self.green_check.pack(
            side="left", anchor="w", padx=3, pady=3,expand=1,fill="x")
        self.blue_check.pack(
            side="left", anchor="w", padx=3, pady=3,expand=1,fill="x")
        self.apply_button.pack(
            side="bottom",anchor="center", padx=5, pady=3)
    
    def pack(self) -> None:
        self.frame.pack(side="top", anchor="w", fill="x", padx=10, pady=10)
    
    def update_apply_button(self) -> None:
        channels: Settings.Channels = (self.red.get(),self.green.get(),self.blue.get())
        current: Settings.Data = (self.brightness.get(),self.scale.get(),channels)
        last: Settings.Data = self.settings.get()
        if last == current:
            self.apply_button["state"] = "disabled"
            return
        self.apply_button["state"] = "normal"

    def apply_changes(self) -> None:
        """Attempts to apply changes to the image. If unable to, no changes occur."""
        channels: Settings.Channels = (self.red.get(),self.green.get(),self.blue.get())
        current: Settings.Data = (self.brightness.get(),self.scale.get(),channels)
        last: Settings.Data = self.settings.get()
        if not self.root.is_image_loading() and last != current:
            self.apply_button["state"] = "disabled"
            self.settings = Settings(current)
            self.root.image_display.redraw() 
        
    def __init__(self, root: Root, frame: tk.Frame) -> None:
        self.root = root  # Unsafely saves the root for handling image later
        self.settings = Settings() # Default setting data
        self.brightness = tk.IntVar(value=self.settings.brightness)
        self.scale = tk.IntVar(value=self.settings.scale)
        self.red = tk.BooleanVar(value=self.settings.channels[0])
        self.green = tk.BooleanVar(value=self.settings.channels[1])
        self.blue = tk.BooleanVar(value=self.settings.channels[2])

        self.frame = ttk.Labelframe(frame, text="Features", padding=(20, 10))
        self.no_file_label = ttk.Label(
            self.frame, text="No File Opened", foreground=Color.OVERLAY)
        self.brightness_label = ttk.Label(
            self.frame,text=f"Brightness ({self.brightness.get()}%)",foreground=Color.YELLOW)
        self.brightness_slider = ttk.Scale(self.frame,
            variable=self.brightness,from_=0,to=100, 
            command=lambda event: ( 
                self.brightness.set(int(self.brightness_slider.get())),
                self.brightness_label.config(text=f"Brightness ({self.brightness.get()}%)"),
                self.brightness_label.update(),
                self.update_apply_button()
            ))
        self.scale_label = ttk.Label(
            self.frame,text=f"Scale ({self.scale.get()}%)",foreground=Color.GREEN)
        self.scale_slider = ttk.Scale(
            self.frame, variable=self.scale, from_=0, to=100, 
            command=lambda event: (
                self.scale.set(int(self.scale_slider.get())),
                self.scale_label.config(text=f"Scale ({self.scale.get()}%)"),
                self.scale_label.update(),
                self.update_apply_button()
            ))
        self.red_check = ttk.Checkbutton(
            self.frame, text="R", variable=self.red, 
            command=self.update_apply_button)
        self.green_check = ttk.Checkbutton(
            self.frame, text="G", variable=self.green, 
            command=self.update_apply_button)
        self.blue_check = ttk.Checkbutton(
            self.frame, text="B", variable=self.blue, 
            command=self.update_apply_button)
        self.apply_button = ttk.Button(self.frame, text="Apply", 
            command=self.apply_changes, padding=(0,0),state="disabled")
        self.hide()

class CompressUI(BaseUI):
    """CompressUI class that contains the buttons to compress the image."""
    def hide(self) -> None:
        self.compress_button.pack_forget()
        self.no_file_label.pack(side="top", anchor="w", padx=5, pady=3)
        self.original_size_label.pack_forget()
        self.compressed_size_label.pack_forget()
        self.ratio_label.pack_forget()
        self.time_label.pack_forget()


    def show(self, bmp: BMPImage) -> None:
        self.no_file_label.pack_forget() # Hide no file label
        self.original_size_label.pack(side="top", anchor="w", padx=5, pady=2)
        self.compressed_size_label.pack(side="top", anchor="w", padx=5, pady=2)
        self.ratio_label.pack(side="top", anchor="w", padx=5, pady=2)
        self.time_label.pack(side="top", anchor="w", padx=5, pady=2)
        self.compress_button.pack(side="top", anchor="w", padx=5, pady=3)

    def pack(self) -> None:
        self.frame.pack(side="top", anchor="w", fill="x", padx=10, pady=10)

    def __init__(self, root: Root, frame: tk.Frame) -> None:
        self.root = root  # Unsafely saves the root for handling image later
        self.frame = ttk.Labelframe(frame, text="Compression", padding=(20, 10))
        self.no_file_label = ttk.Label(
            self.frame, text="No File Opened", foreground=Color.OVERLAY)
        self.original_size_label = ttk.Label(
            self.frame, text="Original File Size: 0 B", foreground=Color.PEACH)
        self.compressed_size_label = ttk.Label(self.frame, text="Compressed File Size: 0 B", foreground=Color.PINK)
        self.ratio_label = ttk.Label(self.frame, text="Compression Ratio: 1:1", foreground=Color.MAUVE)
        self.time_label = ttk.Label(
            self.frame, text="Compression Time: 0 ms", foreground="grey")
        self.compress_button = ttk.Button(
            self.frame, text="Compress BMP..",
            style="Accent.TButton",command=root.compress_bmp_file)
        self.hide()
class Image:
    """Image adapter class that translates BMPImage to tk.PhotoImage on a tk.Canvas.
    Can be refactored later on for more features."""
    
    def center(self, event) -> None: #type: ignore
        """Centers image to the canvas after canvas <Configure> event."""
        self.canvas.coords(self.id, event.width//2, event.height//2) # type: ignore

    def draw_image(self) -> None:
        """Update the existing PhotoImage with new pixel data,
        line by line. Then, center it on the canvas!! O_O"""
        
        if not self.bmp_image.is_valid():
            Error.popup(self.bmp_image._err) #type: ignore
            return
        
        self.photo_image: tk.PhotoImage = tk.PhotoImage(
            width=self.width, height=self.height)
        for y in range(self.height):
            line = " ".join(self.pixels[y*self.width:(y+1)*self.width])
            self.photo_image.put("{"+line+"}", to=(0, y))

        canvas_w, canvas_h = self.canvas.winfo_width(), self.canvas.winfo_height()

        self.id = self.canvas.create_image(self.width//2, # type: ignore
            self.height//2, image=self.photo_image, anchor="center") 
        self.canvas.bind("<Configure>", self.center)  # type: ignore
        self.center(type("Event", (), { #type: ignore
            "width": canvas_w, "height": canvas_h})())
    
    def get_image(self, settings: Settings) -> None:
        """Retrieves the BMPImage after passing setting data on the image."""
        self.width,self.height,self.pixels = self.bmp_image.get_image(settings)
    
    def __init__(self, canvas: tk.Canvas, bmp_image: BMPImage) -> None:
        """Constructs Image object from BMPImage"""
        self.canvas = canvas
        self.bmp_image = bmp_image
        self.photo_image: tk.PhotoImage
        self.id: int

class ImageDisplayUI:
    """ImageUI class that handles the display for the BMP image."""
    def _draw_image(self, start_time: float) -> None:
        """Private draw call, which starts the process for drawing the image."""
        if self.image is None: return
        self.loading_label.pack_forget()
        self.image.draw_image()
        self.file_path_name_label.config(text=f"{self.file_path_name}")
        self.file_path_name_label.pack(side="left",anchor="sw",padx=20,pady=20)
        load_time = 1000 * (perf_counter() - start_time)
        self.load_time_label.config(
            text=f"Loaded in {load_time:.0f} ms")
        self.load_time_label.pack(anchor="ne", side="right",
            padx=20, pady=20)
        self.canvas.update()
        self.is_loading = False

    def _get_image(self) -> None:
        """Retrieves the image data. Then, calls _draw_image to display the image."""
        if self.image is None: return
        start_time: float = perf_counter() # Start load time
        settings = self.root.get_settings()
        self.image.get_image(settings)
        self.root.widget.after(0, lambda: self._draw_image(start_time))
    
    def draw_image(self) -> None:
        """Displays a BMP image to the canvas!"""
        if not self.image: return
        self.canvas.unbind("<Configure>")
        self.is_loading = True
        self.loading_label.pack(side="bottom", anchor="e", 
            fill="both", expand=True, padx=20, pady=20)
        Thread(target=self._get_image, daemon=True).start()
        self.root.side_bar.show(self.image.bmp_image)
    
    def _clear_image(self) -> None:
        """Private clearing for image data, deallocates memory."""
        if self.image is None: return
        self.file_path_name_label.pack_forget()
        self.load_time_label.pack_forget()
        self.canvas.delete(self.image.id)
        del self.image
        self.image = None

    def clear(self) -> None:
        """Clears the image displayed to an empty canvas, and removes metadata."""
        self.root.side_bar.hide()
        self._clear_image()
        self.loading_label.pack_forget()
        self.file_path_name_label.config(text="")
        self.load_time_label.pack_forget()
        self.canvas.update()
        self.canvas.unbind("<Configure>")
    
    def redraw(self) -> None:
        """Redraw image displayed with applied setting changes.
        Only occurs if there is an image already displayed (BMP image data configured.)"""
        if self.image is None: return
        self.canvas.delete(self.image.id) # Deallocate previous image id space
        self.draw_image() # Settings are updated only, Image data remains the same.
        self.root.mainloop()
    
    def open_bmp_file(self) -> None:
        """Open a file dialog to select a BMP file and update the entry field.
        If the file is not a valid BMP image, display a specified error message."""
        last_file_path = self.file_path_name
        self.file_path_name: str = filedialog.askopenfilename(
            title="Open BMP Image",
            filetypes=[("BMP Image Files", "*.bmp"), ("All Files", "*.*")])
        if self.file_path_name == last_file_path or \
            self.file_path_name == "": return
        self.clear()
        bmp = read_bmp_file(self.file_path_name)
        if bmp is None: return
        self.image = Image(self.canvas,bmp) # Adapter class BMP -> tk.PhotoImage
        self.draw_image()
        self.root.mainloop()
    def open_cmpt_file(self) -> None:
        """Open a file dialog to select a CMPT365 file and update the entry field.
        If the file is not a valid CMPT365 image, display a specified error message."""
        last_file_path = self.file_path_name
        self.file_path_name: str = filedialog.askopenfilename(
            title="Open CMPT365 Image",
            filetypes=[("CMPT365 Image Files", "*.cmpt365"), ("All Files", "*.*")])
        if self.file_path_name == last_file_path or \
            self.file_path_name == "": return
        self.clear()
        bmp = read_cmpt365_file(self.file_path_name)
        if bmp is None: return
        self.image = Image(self.canvas,bmp)
        self.draw_image()
        self.root.mainloop()
    def compress_bmp_file(self) -> None:
        """Compresses the BMP image and displays it on the canvas."""
        if self.image is None: return
        file_path = filedialog.asksaveasfilename(
            title="Save Compressed Image",
            initialfile=self.file_path_name.split("/")[-1].split(".")[0] + ".cmpt365",
            defaultextension=".cmpt365",
            filetypes=[("CMPT365 Image Files", "*.cmpt365"), ("All Files", "*.*")])
        if file_path == "": return
        start_time = perf_counter()
        compress_bmp_file(self.image.bmp_image, file_path)
        compress_time = 1000 * (perf_counter() - start_time)
        self.root.side_bar.compress.original_size_label.config(
            text=get_file_size_text(self.image.bmp_image.file_size))
        compressed_size = path.getsize(file_path)
        self.root.side_bar.compress.compressed_size_label.config(
            text="Compressed " + get_file_size_text(compressed_size))
        self.root.side_bar.compress.ratio_label.config(
            text=f"Compression Ratio: {self.image.bmp_image.file_size / compressed_size:.1f}:1")
        self.root.side_bar.compress.time_label.config(
            text=f"Compression Time: {compress_time:.0f} ms")
        self.root.side_bar.compress.show(self.image.bmp_image)
    def pack(self) -> None:
        """Packs the main frame of the UI."""
        self.canvas.pack(side="left", anchor="center",
            padx=25, pady=25, fill="both", expand=True)
        
    def __init__(self, root: Root) -> None:
        self.root = root # Unsafely saves the root for handling image later
        self.canvas = tk.Canvas(bg=Color.MANTLE, bd=3, relief="ridge",
            highlightbackground=Color.LAVENDAR, highlightthickness=3)
        self.file_path_name = ""
        self.file_path_name_label = ttk.Label(
            self.canvas,text=f"{self.file_path_name}",
            foreground=Color.MAUVE)
        self.is_loading: bool = False
        self.loading_label = ttk.Label(self.canvas, text="Loading Image...", 
            foreground=Color.PEACH, anchor="center")
        self.load_time_label = ttk.Label(self.canvas,text="Loaded in 0.0s",
            foreground=Color.BLUE, anchor="ne")
        self.image: Image|None = None

class SideBarUI(BaseUI):
    """SideBarUI class that contains MetadataUI and FeatureUI objects."""
    def pack(self) -> None:
        self.frame.pack(side="left", anchor="w", fill="y", padx=20, pady=10)
        self.metadata.pack()
        self.feature.pack()
        self.compress.pack()
        self.open_bmp_button.pack(side="left",anchor="s", padx=5, pady=10,expand=1,fill="x")
        self.open_cmpt_button.pack(side="left",anchor="s", padx=5, pady=10,expand=1,fill="x")
    
    def hide(self) -> None:
        self.metadata.hide()
        self.feature.hide()
        self.compress.hide()
    
    def show(self, bmp: BMPImage) -> None:
        self.metadata.show(bmp)
        self.feature.show(bmp)
        self.compress.show(bmp)
    
    def __init__(self, root: Root) -> None:
        self.frame = tk.Frame(root.widget, bg=Color.BASE)
        self.metadata = MetadataUI(self.frame)
        self.feature = FeatureUI(root, self.frame)
        self.compress = CompressUI(root, self.frame)
        self.open_bmp_button = ttk.Button(self.frame, text="Open BMP..", 
            style="Accent.TButton", command=root.open_bmp_file, 
            padding=(5,5))
        self.open_cmpt_button = ttk.Button(self.frame, text="Open CMPT365..", 
            style="Accent.TButton", command=root.open_cmpt_file, 
            padding=(5,5))
# ---------------------------------------------------------------------------- #
