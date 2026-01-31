# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
pip install -r requirements.txt
python png_to_ico.py
```

## Dependencies

- **Pillow** (required): Image processing for PNG/ICO conversion
- **tkinterdnd2** (optional): Enables drag-and-drop functionality; app works without it

## Architecture

Single-file Python GUI application (`png_to_ico.py`, ~510 lines) using Tkinter.

**Main class:** `PngToIcoConverter`
- Initializes with TkinterDnD if available, falls back to standard Tk
- Two-tab interface:
  1. **ICO Converter tab**: Single PNG → ICO conversion (16, 32, 48px sizes embedded)
  2. **Favicon Set tab**: Generates complete favicon set (8 files including manifest.json and HTML snippet)

**Key methods:**
- `convert_to_ico()`: Handles single-file ICO conversion
- `generate_favicon_set()`: Creates full favicon set with configurable prefix and apple-touch-icon background color
- `create_apple_touch_icon()`: Generates 180x180 icon with solid background (converts RGBA to RGB)

**Image processing:** Uses Pillow's LANCZOS resampling for quality resizing. ICO files contain multiple embedded sizes.

## Generated Favicon Set

When using the Favicon Set Generator, outputs include:
- `favicon.ico` (multi-size: 16, 32, 48px)
- `favicon-16x16.png`, `favicon-32x32.png`
- `android-chrome-192x192.png`, `android-chrome-512x512.png`
- `apple-touch-icon.png` (180x180, solid background)
- `manifest.json` (Android PWA manifest)
- `favicon.html` (ready-to-use HTML link tags)
