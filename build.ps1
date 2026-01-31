# Build PNG to ICO Converter as executable

# Install PyInstaller if not present
pip install pyinstaller

# Build the executable
pyinstaller --onefile --windowed --name "PngToIcoConverter" png_to_ico.py

Write-Host "Build complete. Executable is in the 'dist' folder." -ForegroundColor Green
