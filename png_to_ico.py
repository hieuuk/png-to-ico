"""
PNG to ICO Converter & Favicon Set Generator
A simple cross-platform GUI application to convert PNG files to ICO format
and generate complete favicon sets for web projects.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, ttk
from pathlib import Path
import json
import subprocess
import sys
import re
import io

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


class PngToIcoConverter:
    def __init__(self):
        # Use TkinterDnD if available, otherwise standard Tk
        if HAS_DND:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        self.root.title("PNG to ICO Converter & Favicon Generator")
        self.root.geometry("600x700")
        self.root.resizable(True, True)

        # Background color for apple-touch-icon (default white)
        self.bg_color = "#ffffff"
        # Manifest colors
        self.theme_color = "#ffffff"
        self.manifest_bg_color = "#ffffff"

        self.selected_file = None
        self.file_prefix = ""  # Prefix for generated file names

        # ICO tab state
        self.ico_selected_file = None
        self.ico_preview_image = None  # Keep reference to prevent garbage collection

        # Batch mode state
        self.batch_files = []

        # ICO size options (all enabled by default)
        self.ico_sizes = {
            16: tk.BooleanVar(value=True),
            32: tk.BooleanVar(value=True),
            48: tk.BooleanVar(value=True),
            64: tk.BooleanVar(value=True),
            128: tk.BooleanVar(value=True),
            256: tk.BooleanVar(value=True),
        }

        # Favicon preview image reference
        self.favicon_preview_image = None

        # Folder icon preview image reference
        self.folder_preview_image = None

        # Last generated HTML snippet for clipboard
        self.last_html_snippet = ""

        self.setup_ui()

    def setup_ui(self):
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Simple ICO conversion
        self.ico_tab = tk.Frame(self.notebook, padx=15, pady=15)
        self.notebook.add(self.ico_tab, text="PNG to ICO")

        # Tab 2: Favicon set generation
        self.favicon_tab = tk.Frame(self.notebook, padx=15, pady=15)
        self.notebook.add(self.favicon_tab, text="Favicon Set")

        # Tab 3: Folder icon
        self.folder_tab = tk.Frame(self.notebook, padx=15, pady=15)
        self.notebook.add(self.folder_tab, text="Folder Icon")

        self.setup_ico_tab()
        self.setup_favicon_tab()
        self.setup_folder_tab()

        # Warning if dependencies missing
        if Image is None:
            messagebox.showwarning(
                "Missing Dependency",
                "Pillow is not installed. Please run:\npip install Pillow"
            )

    def setup_ico_tab(self):
        """Setup the simple ICO conversion tab with preview and batch support."""
        # Main container with two columns
        main_frame = tk.Frame(self.ico_tab)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left column: File selection and options
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Drop zone
        self.drop_frame = tk.Frame(
            left_frame,
            relief=tk.RIDGE,
            bd=2,
            bg="#f0f0f0",
            height=80
        )
        self.drop_frame.pack(fill=tk.X, pady=(0, 10))
        self.drop_frame.pack_propagate(False)

        # Drop zone label
        drop_text = "Drag & Drop PNG here" if HAS_DND else "Click 'Select PNG' below"
        self.drop_label = tk.Label(
            self.drop_frame,
            text=drop_text,
            font=("Arial", 11),
            bg="#f0f0f0",
            fg="#666666"
        )
        self.drop_label.pack(expand=True)

        # Enable drag and drop if available
        if HAS_DND:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self.on_drop_ico)
            self.drop_label.drop_target_register(DND_FILES)
            self.drop_label.dnd_bind('<<Drop>>', self.on_drop_ico)

        # Button frame
        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        # Select single file button
        self.select_btn = tk.Button(
            btn_frame,
            text="Select PNG",
            command=self.select_file_ico,
            font=("Arial", 9),
            padx=10,
            pady=3
        )
        self.select_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Batch select button
        self.batch_btn = tk.Button(
            btn_frame,
            text="Batch Select",
            command=self.select_batch_files,
            font=("Arial", 9),
            padx=10,
            pady=3
        )
        self.batch_btn.pack(side=tk.LEFT)

        # Selected file label
        self.ico_file_label = tk.Label(
            left_frame,
            text="No file selected",
            font=("Arial", 9),
            fg="#666666",
            anchor="w"
        )
        self.ico_file_label.pack(fill=tk.X, pady=(0, 10))

        # ICO Size Options
        size_frame = tk.LabelFrame(left_frame, text="ICO Sizes to Include", padx=10, pady=5)
        size_frame.pack(fill=tk.X, pady=(0, 10))

        # Create checkboxes in two rows
        size_row1 = tk.Frame(size_frame)
        size_row1.pack(fill=tk.X)
        size_row2 = tk.Frame(size_frame)
        size_row2.pack(fill=tk.X)

        sizes_list = list(self.ico_sizes.keys())
        for i, size in enumerate(sizes_list[:3]):
            cb = tk.Checkbutton(
                size_row1,
                text=f"{size}px",
                variable=self.ico_sizes[size],
                font=("Arial", 9)
            )
            cb.pack(side=tk.LEFT, padx=(0, 15))

        for size in sizes_list[3:]:
            cb = tk.Checkbutton(
                size_row2,
                text=f"{size}px",
                variable=self.ico_sizes[size],
                font=("Arial", 9)
            )
            cb.pack(side=tk.LEFT, padx=(0, 15))

        # Convert button
        self.convert_btn = tk.Button(
            left_frame,
            text="Convert to ICO",
            command=self.do_conversion,
            font=("Arial", 10),
            padx=20,
            pady=8,
            state=tk.DISABLED
        )
        self.convert_btn.pack(pady=(5, 10))

        # Status label
        self.status_label = tk.Label(
            left_frame,
            text="" if HAS_DND else "Note: Install tkinterdnd2 for drag & drop",
            font=("Arial", 9),
            fg="#888888"
        )
        self.status_label.pack()

        # Right column: Preview
        right_frame = tk.LabelFrame(main_frame, text="Preview", padx=10, pady=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))

        # Preview canvas
        self.ico_preview_canvas = tk.Canvas(
            right_frame,
            width=150,
            height=150,
            bg="#f8f8f8",
            relief=tk.SUNKEN,
            bd=1
        )
        self.ico_preview_canvas.pack(pady=(0, 5))

        # Preview info label
        self.ico_preview_info = tk.Label(
            right_frame,
            text="Select a file\nto preview",
            font=("Arial", 8),
            fg="#888888",
            justify=tk.CENTER
        )
        self.ico_preview_info.pack()

    def setup_favicon_tab(self):
        """Setup the favicon set generation tab."""
        # Create scrollable frame for all content
        canvas = tk.Canvas(self.favicon_tab)
        scrollbar = ttk.Scrollbar(self.favicon_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # File selection section with preview
        file_frame = tk.LabelFrame(scrollable_frame, text="Source PNG", padx=10, pady=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        # Top row: file label and browse button
        file_row = tk.Frame(file_frame)
        file_row.pack(fill=tk.X)

        self.file_label = tk.Label(
            file_row,
            text="No file selected",
            font=("Arial", 9),
            fg="#666666",
            anchor="w"
        )
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # Bind tooltip for full path
        self.file_label.bind("<Enter>", self.show_file_tooltip)
        self.file_label.bind("<Leave>", self.hide_file_tooltip)
        self.file_tooltip = None

        select_btn = tk.Button(
            file_row,
            text="Browse...",
            command=self.select_source_file
        )
        select_btn.pack(side=tk.RIGHT)

        # Preview row
        preview_row = tk.Frame(file_frame)
        preview_row.pack(fill=tk.X, pady=(10, 0))

        self.favicon_preview_canvas = tk.Canvas(
            preview_row,
            width=100,
            height=100,
            bg="#f8f8f8",
            relief=tk.SUNKEN,
            bd=1
        )
        self.favicon_preview_canvas.pack(side=tk.LEFT, padx=(0, 10))

        preview_info = tk.Label(
            preview_row,
            text="Drag & drop or browse\nto select source image",
            font=("Arial", 8),
            fg="#888888",
            justify=tk.LEFT
        )
        preview_info.pack(side=tk.LEFT, anchor="w")

        # Enable drag and drop on the entire favicon tab if available
        if HAS_DND:
            file_frame.drop_target_register(DND_FILES)
            file_frame.dnd_bind('<<Drop>>', self.on_drop_favicon)

        # Options section
        options_frame = tk.LabelFrame(scrollable_frame, text="Options", padx=10, pady=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))

        # Background color picker for apple-touch-icon
        color_frame = tk.Frame(options_frame)
        color_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            color_frame,
            text="Apple Touch Icon Background:",
            font=("Arial", 9)
        ).pack(side=tk.LEFT)

        self.color_preview = tk.Frame(
            color_frame,
            width=25,
            height=25,
            bg=self.bg_color,
            relief=tk.SUNKEN,
            bd=1
        )
        self.color_preview.pack(side=tk.LEFT, padx=(10, 5))

        self.color_label = tk.Label(
            color_frame,
            text=self.bg_color,
            font=("Arial", 9),
            width=8
        )
        self.color_label.pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            color_frame,
            text="Choose",
            command=self.choose_color
        ).pack(side=tk.LEFT)

        # Manifest theme_color picker
        theme_frame = tk.Frame(options_frame)
        theme_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            theme_frame,
            text="Manifest Theme Color:",
            font=("Arial", 9)
        ).pack(side=tk.LEFT)

        self.theme_color_preview = tk.Frame(
            theme_frame,
            width=25,
            height=25,
            bg=self.theme_color,
            relief=tk.SUNKEN,
            bd=1
        )
        self.theme_color_preview.pack(side=tk.LEFT, padx=(10, 5))

        self.theme_color_label = tk.Label(
            theme_frame,
            text=self.theme_color,
            font=("Arial", 9),
            width=8
        )
        self.theme_color_label.pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            theme_frame,
            text="Choose",
            command=self.choose_theme_color
        ).pack(side=tk.LEFT)

        # Manifest background_color picker
        manifest_bg_frame = tk.Frame(options_frame)
        manifest_bg_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            manifest_bg_frame,
            text="Manifest Background Color:",
            font=("Arial", 9)
        ).pack(side=tk.LEFT)

        self.manifest_bg_preview = tk.Frame(
            manifest_bg_frame,
            width=25,
            height=25,
            bg=self.manifest_bg_color,
            relief=tk.SUNKEN,
            bd=1
        )
        self.manifest_bg_preview.pack(side=tk.LEFT, padx=(10, 5))

        self.manifest_bg_label = tk.Label(
            manifest_bg_frame,
            text=self.manifest_bg_color,
            font=("Arial", 9),
            width=8
        )
        self.manifest_bg_label.pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            manifest_bg_frame,
            text="Choose",
            command=self.choose_manifest_bg_color
        ).pack(side=tk.LEFT)

        # File name prefix with validation
        prefix_frame = tk.Frame(options_frame)
        prefix_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            prefix_frame,
            text="File Name Prefix:",
            font=("Arial", 9)
        ).pack(side=tk.LEFT)

        self.prefix_entry = tk.Entry(
            prefix_frame,
            font=("Arial", 9),
            width=20
        )
        self.prefix_entry.pack(side=tk.LEFT, padx=(10, 5))
        # Bind validation on key release
        self.prefix_entry.bind("<KeyRelease>", self.validate_prefix)

        self.prefix_hint = tk.Label(
            prefix_frame,
            text="(a-z, 0-9, - only)",
            font=("Arial", 8),
            fg="#888888"
        )
        self.prefix_hint.pack(side=tk.LEFT)

        # Info text
        info_text = """Generated files:
  • favicon.ico (16, 32, 48px)
  • favicon-16x16.png, favicon-32x32.png
  • android-chrome-192x192.png, android-chrome-512x512.png
  • apple-touch-icon.png (180px, with background)
  • manifest.json, favicon.html"""
        info_label = tk.Label(
            options_frame,
            text=info_text,
            font=("Arial", 8),
            fg="#555555",
            justify=tk.LEFT,
            anchor="w"
        )
        info_label.pack(fill=tk.X, pady=(10, 0))

        # Generate button
        btn_frame = tk.Frame(scrollable_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        self.generate_btn = tk.Button(
            btn_frame,
            text="Generate Favicon Set",
            command=self.generate_favicon_set,
            font=("Arial", 11),
            padx=30,
            pady=10
        )
        self.generate_btn.pack()

        # Status
        self.favicon_status = tk.Label(
            scrollable_frame,
            text="",
            font=("Arial", 9)
        )
        self.favicon_status.pack()

        # Copy HTML button (initially hidden)
        self.copy_html_frame = tk.Frame(scrollable_frame)
        self.copy_html_frame.pack(fill=tk.X, pady=(10, 0))

        self.copy_html_btn = tk.Button(
            self.copy_html_frame,
            text="📋 Copy HTML to Clipboard",
            command=self.copy_html_to_clipboard,
            font=("Arial", 9),
            padx=15,
            pady=5
        )
        # Don't pack yet - will show after generation

    def setup_folder_tab(self):
        """Setup the folder icon tab."""
        # Check if Windows
        is_windows = sys.platform == 'win32'

        if not is_windows:
            warning_label = tk.Label(
                self.folder_tab,
                text="This feature is only available on Windows.",
                font=("Arial", 11),
                fg="#cc0000"
            )
            warning_label.pack(expand=True)
            return

        # Main container with two columns
        main_frame = tk.Frame(self.folder_tab)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left column: Drop zone and controls
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Drop zone
        self.folder_drop_frame = tk.Frame(
            left_frame,
            relief=tk.RIDGE,
            bd=2,
            bg="#f0f0f0",
            height=80
        )
        self.folder_drop_frame.pack(fill=tk.X, pady=(0, 10))
        self.folder_drop_frame.pack_propagate(False)

        # Drop zone label
        drop_text = "Drag & Drop Folder here" if HAS_DND else "Click 'Select Folder' below"
        self.folder_drop_label = tk.Label(
            self.folder_drop_frame,
            text=drop_text,
            font=("Arial", 11),
            bg="#f0f0f0",
            fg="#666666"
        )
        self.folder_drop_label.pack(expand=True)

        # Enable drag and drop if available
        if HAS_DND:
            self.folder_drop_frame.drop_target_register(DND_FILES)
            self.folder_drop_frame.dnd_bind('<<Drop>>', self.on_drop_folder)
            self.folder_drop_label.drop_target_register(DND_FILES)
            self.folder_drop_label.dnd_bind('<<Drop>>', self.on_drop_folder)

        # Select button
        self.select_folder_btn = tk.Button(
            left_frame,
            text="Select Folder",
            command=self.select_folder,
            font=("Arial", 10),
            padx=20,
            pady=5
        )
        self.select_folder_btn.pack()

        # Subfolder checkbox
        self.process_subfolders = tk.BooleanVar(value=False)
        self.subfolder_check = tk.Checkbutton(
            left_frame,
            text="Also process first-level subfolders",
            variable=self.process_subfolders,
            font=("Arial", 9)
        )
        self.subfolder_check.pack(pady=(10, 5))

        # Info text
        info_text = """How it works:
  1. Looks for folder.ico in the folder
  2. If not found, converts folder.png
  3. Creates desktop.ini for the icon
  4. Sets Windows file attributes

Note: Refresh Explorer (F5) to see changes."""

        info_label = tk.Label(
            left_frame,
            text=info_text,
            font=("Arial", 8),
            fg="#555555",
            justify=tk.LEFT,
            anchor="w"
        )
        info_label.pack(fill=tk.X, pady=(5, 0))

        # Status label
        self.folder_status = tk.Label(
            left_frame,
            text="" if HAS_DND else "Note: Install tkinterdnd2 for drag & drop",
            font=("Arial", 9),
            fg="#888888"
        )
        self.folder_status.pack(pady=(10, 0))

        # Right column: Preview
        right_frame = tk.LabelFrame(main_frame, text="Icon Preview", padx=10, pady=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))

        # Preview canvas
        self.folder_preview_canvas = tk.Canvas(
            right_frame,
            width=128,
            height=128,
            bg="#f8f8f8",
            relief=tk.SUNKEN,
            bd=1
        )
        self.folder_preview_canvas.pack(pady=(0, 5))

        # Preview info label
        self.folder_preview_info = tk.Label(
            right_frame,
            text="Icon will appear\nhere after update",
            font=("Arial", 8),
            fg="#888888",
            justify=tk.CENTER
        )
        self.folder_preview_info.pack()

        # Folder path label
        self.folder_path_label = tk.Label(
            right_frame,
            text="",
            font=("Arial", 8),
            fg="#333333",
            wraplength=130
        )
        self.folder_path_label.pack(pady=(5, 0))

    def validate_prefix(self, event=None):
        """Validate prefix input - allow only alphanumeric, hyphens, underscores."""
        current = self.prefix_entry.get()
        # Remove invalid characters
        valid = re.sub(r'[^a-zA-Z0-9\-_]', '', current)
        if current != valid:
            # Get cursor position
            pos = self.prefix_entry.index(tk.INSERT)
            self.prefix_entry.delete(0, tk.END)
            self.prefix_entry.insert(0, valid)
            # Restore cursor position (adjusted for removed chars)
            new_pos = max(0, pos - (len(current) - len(valid)))
            self.prefix_entry.icursor(new_pos)
            # Flash hint in red briefly
            self.prefix_hint.config(fg="#cc0000")
            self.root.after(500, lambda: self.prefix_hint.config(fg="#888888"))

    def show_file_tooltip(self, event):
        """Show tooltip with full file path."""
        if self.selected_file:
            self.file_tooltip = tk.Toplevel(self.root)
            self.file_tooltip.wm_overrideredirect(True)
            self.file_tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(
                self.file_tooltip,
                text=self.selected_file,
                background="#ffffe0",
                relief=tk.SOLID,
                borderwidth=1,
                font=("Arial", 8)
            )
            label.pack()

    def hide_file_tooltip(self, event):
        """Hide the file path tooltip."""
        if self.file_tooltip:
            self.file_tooltip.destroy()
            self.file_tooltip = None

    def choose_color(self):
        """Open color chooser dialog for apple-touch-icon background."""
        color = colorchooser.askcolor(
            initialcolor=self.bg_color,
            title="Choose Background Color"
        )
        if color[1]:
            self.bg_color = color[1]
            self.color_preview.config(bg=self.bg_color)
            self.color_label.config(text=self.bg_color)

    def choose_theme_color(self):
        """Open color chooser dialog for manifest theme color."""
        color = colorchooser.askcolor(
            initialcolor=self.theme_color,
            title="Choose Theme Color"
        )
        if color[1]:
            self.theme_color = color[1]
            self.theme_color_preview.config(bg=self.theme_color)
            self.theme_color_label.config(text=self.theme_color)

    def choose_manifest_bg_color(self):
        """Open color chooser dialog for manifest background color."""
        color = colorchooser.askcolor(
            initialcolor=self.manifest_bg_color,
            title="Choose Manifest Background Color"
        )
        if color[1]:
            self.manifest_bg_color = color[1]
            self.manifest_bg_preview.config(bg=self.manifest_bg_color)
            self.manifest_bg_label.config(text=self.manifest_bg_color)

    def select_source_file(self):
        """Select source PNG for favicon generation."""
        file_path = filedialog.askopenfilename(
            title="Select PNG File",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if file_path:
            self.set_source_file(file_path)

    def set_source_file(self, file_path):
        """Set the source file for favicon generation."""
        path = Path(file_path)
        if path.suffix.lower() != '.png':
            messagebox.showerror("Error", "Please select a PNG file.")
            return
        self.selected_file = file_path
        # Truncate display if too long
        display_name = path.name
        if len(display_name) > 40:
            display_name = display_name[:37] + "..."
        self.file_label.config(text=display_name, fg="#000000")

        # Update preview
        self.update_favicon_preview(file_path)

    def update_favicon_preview(self, file_path):
        """Update the favicon tab preview with the selected image."""
        if Image is None or ImageTk is None:
            return
        try:
            img = Image.open(file_path)
            # Resize to fit preview canvas (100x100)
            img.thumbnail((100, 100), Image.LANCZOS)
            self.favicon_preview_image = ImageTk.PhotoImage(img)
            self.favicon_preview_canvas.delete("all")
            # Center the image
            x = 50
            y = 50
            self.favicon_preview_canvas.create_image(x, y, image=self.favicon_preview_image)
        except Exception:
            pass

    def on_drop_favicon(self, event):
        """Handle dropped files for favicon tab."""
        file_path = event.data
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        self.set_source_file(file_path)

    def on_drop_ico(self, event):
        """Handle dropped files for ICO tab."""
        file_path = event.data
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        self.set_ico_file(file_path)

    def set_ico_file(self, file_path):
        """Set file for ICO conversion with preview."""
        path = Path(file_path)
        if path.suffix.lower() != '.png':
            messagebox.showerror("Error", "Please select a PNG file.")
            return

        self.ico_selected_file = file_path
        self.batch_files = []  # Clear batch mode

        # Update label
        display_name = path.name
        if len(display_name) > 35:
            display_name = display_name[:32] + "..."
        self.ico_file_label.config(text=display_name, fg="#000000")

        # Enable convert button
        self.convert_btn.config(state=tk.NORMAL)

        # Update preview
        self.update_ico_preview(file_path)

        # Update drop zone text
        self.drop_label.config(text="✓ File loaded", fg="#228B22")

    def update_ico_preview(self, file_path):
        """Update the ICO tab preview with the selected image."""
        if Image is None or ImageTk is None:
            return
        try:
            img = Image.open(file_path)
            orig_size = img.size
            # Resize to fit preview canvas (150x150)
            img.thumbnail((150, 150), Image.LANCZOS)
            self.ico_preview_image = ImageTk.PhotoImage(img)
            self.ico_preview_canvas.delete("all")
            # Center the image
            x = 75
            y = 75
            self.ico_preview_canvas.create_image(x, y, image=self.ico_preview_image)

            # Update info label
            self.ico_preview_info.config(
                text=f"Original: {orig_size[0]}×{orig_size[1]}px",
                fg="#333333"
            )
        except Exception as e:
            self.ico_preview_info.config(text=f"Preview error", fg="#cc0000")

    def select_batch_files(self):
        """Select multiple PNG files for batch conversion."""
        file_paths = filedialog.askopenfilenames(
            title="Select PNG Files",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if file_paths:
            self.batch_files = list(file_paths)
            self.ico_selected_file = None  # Clear single file mode

            # Update label
            self.ico_file_label.config(
                text=f"{len(self.batch_files)} files selected",
                fg="#000000"
            )

            # Enable convert button
            self.convert_btn.config(state=tk.NORMAL)

            # Update preview with first file
            if self.batch_files:
                self.update_ico_preview(self.batch_files[0])
                self.ico_preview_info.config(
                    text=f"Showing 1 of {len(self.batch_files)}",
                    fg="#333333"
                )

            # Update drop zone text
            self.drop_label.config(text=f"✓ {len(self.batch_files)} files", fg="#228B22")

    def on_drop_folder(self, event):
        """Handle dropped folders for Folder Icon tab."""
        folder_path = event.data
        if folder_path.startswith('{') and folder_path.endswith('}'):
            folder_path = folder_path[1:-1]
        self.apply_folder_icon(folder_path)

    def select_folder(self):
        """Open folder dialog to select folder for icon setting."""
        folder_path = filedialog.askdirectory(
            title="Select Folder"
        )
        if folder_path:
            self.apply_folder_icon(folder_path)

    def apply_folder_icon(self, folder_path: str):
        """Apply folder icon to the given folder."""
        if Image is None:
            messagebox.showerror(
                "Error",
                "Pillow is not installed. Please run:\npip install Pillow"
            )
            return

        path = Path(folder_path)

        if not path.exists():
            messagebox.showerror("Error", f"Folder not found: {folder_path}")
            return

        if not path.is_dir():
            messagebox.showerror("Error", "Please select a folder, not a file.")
            return

        self.folder_status.config(text="Processing...", fg="blue")
        self.root.update()

        processed = 0
        errors = []
        last_ico_path = None  # Track the last successfully applied icon

        # Process the main folder
        result, ico_path = self.process_single_folder(path)
        if result is True:
            processed += 1
            last_ico_path = ico_path
        elif result is not None:
            errors.append(f"{path.name}: {result}")

        # Process subfolders if checkbox is checked
        if self.process_subfolders.get():
            for subfolder in path.iterdir():
                if subfolder.is_dir():
                    result, ico_path = self.process_single_folder(subfolder)
                    if result is True:
                        processed += 1
                        if last_ico_path is None:
                            last_ico_path = ico_path
                    elif result is not None:
                        errors.append(f"{subfolder.name}: {result}")

        # Show results
        if processed > 0 and not errors:
            self.folder_status.config(
                text=f"Set icon for {processed} folder(s). Refresh Explorer (F5).",
                fg="green"
            )
            # Update drop zone
            self.folder_drop_label.config(text="✓ Icon applied!", fg="#228B22")
            # Update preview with the applied icon
            if last_ico_path:
                self.update_folder_icon_preview(last_ico_path, path.name)
            messagebox.showinfo(
                "Success",
                f"Folder icon set for {processed} folder(s).\n\n"
                "You may need to refresh Windows Explorer (F5) to see the changes."
            )
        elif processed > 0 and errors:
            self.folder_status.config(
                text=f"Set {processed} icon(s), {len(errors)} error(s)",
                fg="orange"
            )
            # Still show preview for successful ones
            if last_ico_path:
                self.update_folder_icon_preview(last_ico_path, path.name)
            error_list = "\n".join(errors[:5])
            if len(errors) > 5:
                error_list += f"\n... and {len(errors) - 5} more"
            messagebox.showwarning(
                "Partial Success",
                f"Set icon for {processed} folder(s).\n\nErrors:\n{error_list}"
            )
        else:
            self.folder_status.config(text="No folders processed", fg="red")
            if errors:
                messagebox.showerror("Error", errors[0])

    def update_folder_icon_preview(self, ico_path: Path, folder_name: str):
        """Update the folder icon preview with the applied icon."""
        if Image is None or ImageTk is None:
            return
        try:
            # Open ICO file and get the largest size available
            img = Image.open(ico_path)
            # ICO files may have multiple sizes; get the largest
            if hasattr(img, 'n_frames') and img.n_frames > 1:
                # Try to find the largest frame
                best_size = 0
                best_frame = 0
                for i in range(img.n_frames):
                    img.seek(i)
                    if img.size[0] > best_size:
                        best_size = img.size[0]
                        best_frame = i
                img.seek(best_frame)

            # Resize to fit preview canvas (128x128)
            img = img.copy()
            img.thumbnail((128, 128), Image.LANCZOS)

            # Convert to RGBA if needed for proper display
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            self.folder_preview_image = ImageTk.PhotoImage(img)
            self.folder_preview_canvas.delete("all")
            # Center the image
            x = 64
            y = 64
            self.folder_preview_canvas.create_image(x, y, image=self.folder_preview_image)

            # Update info labels
            self.folder_preview_info.config(
                text=f"Icon applied!",
                fg="#228B22"
            )
            # Truncate folder name if too long
            display_name = folder_name
            if len(display_name) > 18:
                display_name = display_name[:15] + "..."
            self.folder_path_label.config(text=display_name)

        except Exception as e:
            self.folder_preview_info.config(text="Preview error", fg="#cc0000")

    def process_single_folder(self, folder_path: Path):
        """
        Process a single folder to set its icon.
        Returns tuple: (result, ico_path) where result is True on success,
        error message string on failure, None if skipped.
        """
        ico_path = folder_path / "folder.ico"
        png_path = folder_path / "folder.png"

        # Check for existing ico
        if ico_path.exists():
            result = self.set_folder_icon(folder_path, ico_path)
            return (result, ico_path) if result is True else (result, None)

        # Check for png to convert
        if png_path.exists():
            try:
                img = Image.open(png_path)
                # Standard folder icon sizes
                sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
                img.save(ico_path, format='ICO', sizes=sizes)
                result = self.set_folder_icon(folder_path, ico_path)
                return (result, ico_path) if result is True else (result, None)
            except Exception as e:
                return (f"Failed to convert PNG: {str(e)}", None)

        # No icon source found
        return ("No folder.ico or folder.png found", None)

    def set_folder_icon(self, folder_path: Path, ico_path: Path):
        """
        Create desktop.ini and set folder attributes.
        Returns True on success, error message on failure.
        """
        desktop_ini = folder_path / "desktop.ini"

        try:
            # If desktop.ini exists, remove its attributes first so we can overwrite
            if desktop_ini.exists():
                subprocess.run(
                    ['attrib', '-s', '-h', '-r', str(desktop_ini)],
                    capture_output=True,
                    text=True
                )

            # Write desktop.ini
            content = f"[.ShellClassInfo]\nIconResource={ico_path.name},0\n"
            desktop_ini.write_text(content, encoding='utf-8')

            # Set attributes on folder (make it a system folder)
            subprocess.run(
                ['attrib', '+s', str(folder_path)],
                capture_output=True,
                text=True
            )

            # Set attributes on desktop.ini (system + hidden)
            subprocess.run(
                ['attrib', '+s', '+h', str(desktop_ini)],
                capture_output=True,
                text=True
            )

            return True

        except PermissionError:
            return "Permission denied (try running as administrator)"
        except Exception as e:
            return str(e)

    def select_file_ico(self):
        """Open file dialog to select PNG file for ICO conversion."""
        file_path = filedialog.askopenfilename(
            title="Select PNG File",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if file_path:
            self.set_ico_file(file_path)

    def get_selected_sizes(self):
        """Get list of selected ICO sizes."""
        sizes = []
        for size, var in self.ico_sizes.items():
            if var.get():
                sizes.append((size, size))
        return sizes

    def do_conversion(self):
        """Perform the ICO conversion (single or batch)."""
        sizes = self.get_selected_sizes()
        if not sizes:
            messagebox.showerror("Error", "Please select at least one ICO size.")
            return

        if self.batch_files:
            self.convert_batch(sizes)
        elif self.ico_selected_file:
            self.convert_to_ico(self.ico_selected_file, sizes)

    def convert_batch(self, sizes):
        """Convert multiple PNG files to ICO."""
        if Image is None:
            messagebox.showerror(
                "Error",
                "Pillow is not installed. Please run:\npip install Pillow"
            )
            return

        # Ask for output directory
        output_dir = filedialog.askdirectory(
            title="Select Output Directory for ICO Files"
        )

        if not output_dir:
            return

        output_path = Path(output_dir)

        self.status_label.config(text="Converting...", fg="blue")
        self.root.update()

        success = 0
        failed = 0

        for file_path in self.batch_files:
            try:
                path = Path(file_path)
                img = Image.open(path)
                output_file = output_path / (path.stem + ".ico")
                img.save(output_file, format='ICO', sizes=sizes)
                success += 1
            except Exception:
                failed += 1

        if failed == 0:
            self.status_label.config(text=f"Converted {success} files!", fg="green")
            messagebox.showinfo("Success", f"Converted {success} ICO files to:\n{output_dir}")
        else:
            self.status_label.config(text=f"{success} OK, {failed} failed", fg="orange")
            messagebox.showwarning(
                "Partial Success",
                f"Converted {success} files.\n{failed} files failed."
            )

    def convert_to_ico(self, file_path: str, sizes=None):
        """Convert PNG file to ICO."""
        if Image is None:
            messagebox.showerror(
                "Error",
                "Pillow is not installed. Please run:\npip install Pillow"
            )
            return

        if sizes is None:
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

        path = Path(file_path)

        if not path.exists():
            messagebox.showerror("Error", f"File not found: {file_path}")
            return

        if path.suffix.lower() != '.png':
            messagebox.showerror("Error", "Please select a PNG file.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save ICO File",
            initialdir=path.parent,
            initialfile=path.stem + ".ico",
            defaultextension=".ico",
            filetypes=[("ICO files", "*.ico")]
        )

        if not output_path:
            return

        try:
            self.status_label.config(text="Converting...", fg="blue")
            self.root.update()

            img = Image.open(path)
            img.save(output_path, format='ICO', sizes=sizes)

            size_str = ", ".join(f"{s[0]}px" for s in sizes)
            self.status_label.config(text=f"Saved: {Path(output_path).name}", fg="green")
            messagebox.showinfo(
                "Success",
                f"ICO file saved to:\n{output_path}\n\nSizes included: {size_str}"
            )

        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed:\n{str(e)}")
            self.status_label.config(text="Conversion failed", fg="red")

    def copy_html_to_clipboard(self):
        """Copy the generated HTML snippet to clipboard."""
        if self.last_html_snippet:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.last_html_snippet)
            self.root.update()  # Required for clipboard to persist

            # Visual feedback
            original_text = self.copy_html_btn.cget("text")
            self.copy_html_btn.config(text="✓ Copied!")
            self.root.after(1500, lambda: self.copy_html_btn.config(text=original_text))

    def generate_favicon_set(self):
        """Generate complete favicon set."""
        if Image is None:
            messagebox.showerror(
                "Error",
                "Pillow is not installed. Please run:\npip install Pillow"
            )
            return

        if not self.selected_file:
            messagebox.showerror("Error", "Please select a source PNG file first.")
            return

        # Ask for output directory
        output_dir = filedialog.askdirectory(
            title="Select Output Directory for Favicon Set"
        )

        if not output_dir:
            return

        output_path = Path(output_dir)

        try:
            self.favicon_status.config(text="Generating...", fg="blue")
            self.root.update()

            # Get prefix from entry (already validated)
            prefix = self.prefix_entry.get().strip()

            # Open source image
            img = Image.open(self.selected_file)

            # Ensure image has alpha channel for transparency handling
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            generated_files = []

            # Generate favicon.ico (multi-size)
            ico_filename = f"{prefix}favicon.ico"
            ico_path = output_path / ico_filename
            img.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48)])
            generated_files.append(ico_filename)

            # Generate PNG favicons
            png_sizes = {
                "favicon-16x16.png": 16,
                "favicon-32x32.png": 32,
                "android-chrome-192x192.png": 192,
                "android-chrome-512x512.png": 512,
            }

            for base_filename, size in png_sizes.items():
                filename = f"{prefix}{base_filename}"
                resized = img.resize((size, size), Image.LANCZOS)
                resized.save(output_path / filename, format='PNG')
                generated_files.append(filename)

            # Generate apple-touch-icon (180x180 with background, no transparency)
            apple_size = 180
            apple_filename = f"{prefix}apple-touch-icon.png"
            apple_icon = self.create_apple_touch_icon(img, apple_size)
            apple_icon.save(output_path / apple_filename, format='PNG')
            generated_files.append(apple_filename)

            # Generate manifest.json with customizable colors
            manifest_filename = f"{prefix}manifest.json"
            manifest = {
                "name": "",
                "short_name": "",
                "icons": [
                    {
                        "src": f"/{prefix}android-chrome-192x192.png",
                        "sizes": "192x192",
                        "type": "image/png"
                    },
                    {
                        "src": f"/{prefix}android-chrome-512x512.png",
                        "sizes": "512x512",
                        "type": "image/png"
                    }
                ],
                "theme_color": self.theme_color,
                "background_color": self.manifest_bg_color,
                "display": "standalone"
            }

            manifest_path = output_path / manifest_filename
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)
            generated_files.append(manifest_filename)

            # Generate HTML snippet with customizable theme color
            html_filename = f"{prefix}favicon.html"
            self.last_html_snippet = f"""<!-- Favicon -->
<link rel="icon" type="image/x-icon" href="/{prefix}favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/{prefix}favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/{prefix}favicon-16x16.png">

<!-- Apple Touch Icon -->
<link rel="apple-touch-icon" sizes="180x180" href="/{prefix}apple-touch-icon.png">

<!-- Android Chrome -->
<link rel="manifest" href="/{prefix}manifest.json">
<meta name="theme-color" content="{self.theme_color}">
"""

            html_path = output_path / html_filename
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(self.last_html_snippet)
            generated_files.append(html_filename)

            self.favicon_status.config(
                text=f"Generated {len(generated_files)} files!",
                fg="green"
            )

            # Show copy HTML button
            self.copy_html_btn.pack()

            # Show success message with file list
            files_list = "\n".join(f"  • {f}" for f in generated_files)
            messagebox.showinfo(
                "Success",
                f"Favicon set generated in:\n{output_dir}\n\nFiles created:\n{files_list}"
            )

        except Exception as e:
            messagebox.showerror("Error", f"Generation failed:\n{str(e)}")
            self.favicon_status.config(text="Generation failed", fg="red")

    def create_apple_touch_icon(self, img: 'Image.Image', size: int) -> 'Image.Image':
        """Create apple-touch-icon with solid background (no transparency)."""
        # Parse background color
        bg_color = self.bg_color.lstrip('#')
        r = int(bg_color[0:2], 16)
        g = int(bg_color[2:4], 16)
        b = int(bg_color[4:6], 16)

        # Create background
        background = Image.new('RGB', (size, size), (r, g, b))

        # Resize source image
        resized = img.resize((size, size), Image.LANCZOS)

        # If image has alpha, composite it onto background
        if resized.mode == 'RGBA':
            background.paste(resized, (0, 0), resized)
        else:
            background.paste(resized, (0, 0))

        return background

    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    app = PngToIcoConverter()
    app.run()


if __name__ == "__main__":
    main()
