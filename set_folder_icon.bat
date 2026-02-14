@echo off
REM Batch file wrapper for set_folder_icon.py with automatic venv activation

setlocal enabledelayedexpansion

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"

REM Check if virtual environment exists and activate it
if exist "%SCRIPT_DIR%venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "%SCRIPT_DIR%venv\Scripts\activate.bat"
) else (
    echo No virtual environment found, using system Python...
)

REM Run the Python script with all arguments passed through
python "%SCRIPT_DIR%set_folder_icon.py" %*

REM Capture exit code
set EXIT_CODE=%ERRORLEVEL%

REM Deactivate venv if it was activated
if exist "%SCRIPT_DIR%venv\Scripts\deactivate.bat" (
    call deactivate
)

exit /b %EXIT_CODE%
