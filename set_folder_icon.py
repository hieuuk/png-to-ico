#!/usr/bin/env python3
"""
Set Folder Icon - Standalone utility to set custom icons for Windows folders
Looks for folder.ico or folder.png in the target folder and applies it as the folder icon.
"""

import argparse
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None


# Required sizes that a folder ICO must contain
REQUIRED_FOLDER_ICO_SIZES = {16, 32, 48, 256}
# Full set of sizes to generate when creating/regenerating folder ICOs
FOLDER_ICO_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def get_ico_sizes(ico_path: Path):
    """Get the set of widths contained in an ICO file."""
    if Image is None:
        return set()
    try:
        img = Image.open(ico_path)
        sizes = set()
        if hasattr(img, 'n_frames') and img.n_frames > 1:
            for i in range(img.n_frames):
                img.seek(i)
                sizes.add(img.size[0])
        else:
            sizes.add(img.size[0])
        return sizes
    except Exception:
        return set()


def set_folder_icon(folder_path: Path, ico_path: Path, use_absolute_path: bool = False):
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

        # Write desktop.ini with relative or absolute path to ico
        if use_absolute_path:
            icon_ref = str(ico_path.resolve())
        else:
            icon_ref = ico_path.name
        content = f"[.ShellClassInfo]\nIconResource={icon_ref},0\n"
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


def process_single_folder(folder_path: Path, use_absolute_path: bool = False, verbose: bool = False):
    """
    Process a single folder to set its icon.
    Returns tuple: (result, ico_path) where result is True on success,
    error message string on failure, None if skipped.
    """
    if Image is None:
        return ("Pillow is not installed. Please run: pip install Pillow", None)

    ico_path = folder_path / "folder.ico"
    png_path = folder_path / "folder.png"

    # Check for existing ico
    if ico_path.exists():
        if verbose:
            print(f"  Found existing folder.ico")
        # Check if ICO has all required sizes
        existing_sizes = get_ico_sizes(ico_path)
        missing_sizes = REQUIRED_FOLDER_ICO_SIZES - existing_sizes

        if missing_sizes and png_path.exists():
            if verbose:
                print(f"  ICO missing required sizes: {sorted(missing_sizes)}")
                print(f"  Regenerating from folder.png...")
            # Regenerate ICO from PNG with full sizes
            try:
                img = Image.open(png_path)
                img.save(ico_path, format='ICO', sizes=FOLDER_ICO_SIZES)
                if verbose:
                    print(f"  Regenerated folder.ico with all sizes")
            except Exception as e:
                return (f"Failed to regenerate ICO: {str(e)}", None)

        result = set_folder_icon(folder_path, ico_path, use_absolute_path)
        return (result, ico_path) if result is True else (result, None)

    # Check for png to convert
    if png_path.exists():
        if verbose:
            print(f"  Found folder.png, converting to ICO...")
        try:
            img = Image.open(png_path)
            img.save(ico_path, format='ICO', sizes=FOLDER_ICO_SIZES)
            if verbose:
                print(f"  Created folder.ico")
            result = set_folder_icon(folder_path, ico_path, use_absolute_path)
            return (result, ico_path) if result is True else (result, None)
        except Exception as e:
            return (f"Failed to convert PNG: {str(e)}", None)

    # No icon source found
    return ("No folder.ico or folder.png found", None)


def apply_folder_icon(folder_path: str, recursive: bool = False, use_absolute_path: bool = False, verbose: bool = False):
    """Apply folder icon to the given folder and optionally its immediate subfolders."""
    if sys.platform != 'win32':
        print("Error: This tool only works on Windows.", file=sys.stderr)
        return False

    if Image is None:
        print("Error: Pillow is not installed. Please run: pip install Pillow", file=sys.stderr)
        return False

    path = Path(folder_path)

    if not path.exists():
        print(f"Error: Folder not found: {folder_path}", file=sys.stderr)
        return False

    if not path.is_dir():
        print(f"Error: Path is not a folder: {folder_path}", file=sys.stderr)
        return False

    processed = 0
    errors = []

    # Process the main folder
    if verbose:
        print(f"\nProcessing: {path}")
    result, ico_path = process_single_folder(path, use_absolute_path, verbose)
    if result is True:
        processed += 1
        if verbose:
            print(f"  ✓ Icon applied successfully")
    elif result is not None:
        errors.append(f"{path.name}: {result}")
        if verbose:
            print(f"  ✗ {result}")

    # Process subfolders if recursive option is enabled
    if recursive:
        for subfolder in path.iterdir():
            if subfolder.is_dir():
                if verbose:
                    print(f"\nProcessing subfolder: {subfolder.name}")
                result, ico_path = process_single_folder(subfolder, use_absolute_path, verbose)
                if result is True:
                    processed += 1
                    if verbose:
                        print(f"  ✓ Icon applied successfully")
                elif result is not None:
                    errors.append(f"{subfolder.name}: {result}")
                    if verbose:
                        print(f"  ✗ {result}")

    # Print summary
    print()
    if processed > 0 and not errors:
        print(f"✓ Successfully set icon for {processed} folder(s).")
        print("  Refresh Windows Explorer (F5) to see the changes.")
        return True
    elif processed > 0 and errors:
        print(f"⚠ Set icon for {processed} folder(s), but {len(errors)} failed:")
        for error in errors[:5]:
            print(f"  • {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")
        return False
    else:
        print("✗ No folders were processed.")
        if errors:
            print(f"Error: {errors[0]}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Set custom icon for Windows folders using folder.ico or folder.png",
        epilog="""
How it works:
  1. Looks for folder.ico in the target folder
  2. Validates ICO has required sizes (16, 32, 48, 256)
  3. If sizes are missing, regenerates from folder.png
  4. If no ICO found, converts folder.png to folder.ico
  5. Creates/updates desktop.ini with the icon reference
  6. Sets Windows system and hidden attributes

Note: You may need to refresh Windows Explorer (F5) to see the icon changes.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'folder_path',
        help='Path to the folder to set icon for'
    )
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Also process immediate subfolders (first level only)'
    )
    parser.add_argument(
        '-a', '--absolute',
        action='store_true',
        help='Use absolute path in desktop.ini (default: relative path)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed processing information'
    )

    args = parser.parse_args()

    success = apply_folder_icon(
        args.folder_path,
        recursive=args.recursive,
        use_absolute_path=args.absolute,
        verbose=args.verbose
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
