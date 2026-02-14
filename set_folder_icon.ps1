#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Set custom icon for Windows folders
.DESCRIPTION
    PowerShell wrapper for set_folder_icon.py that handles virtual environment activation
.PARAMETER FolderPath
    Path to the folder to set icon for
.PARAMETER Recursive
    Also process immediate subfolders
.PARAMETER Absolute
    Use absolute path in desktop.ini (default: relative)
.PARAMETER Verbose
    Show detailed processing information
.EXAMPLE
    .\set_folder_icon.ps1 "C:\My Folder"
.EXAMPLE
    .\set_folder_icon.ps1 -Recursive -Verbose "C:\My Folder"
#>

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$FolderPath,

    [Parameter(Mandatory=$false)]
    [switch]$Recursive,

    [Parameter(Mandatory=$false)]
    [switch]$Absolute,

    [Parameter(Mandatory=$false)]
    [switch]$Verbose
)

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Path to the Python script
$PythonScript = Join-Path $ScriptDir "set_folder_icon.py"

# Check if Python script exists
if (-not (Test-Path $PythonScript)) {
    Write-Error "Python script not found: $PythonScript"
    exit 1
}

# Check for virtual environment and activate it
$VenvPath = Join-Path $ScriptDir "venv"
$VenvActivate = Join-Path $VenvPath "Scripts\Activate.ps1"

if (Test-Path $VenvActivate) {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & $VenvActivate
} else {
    Write-Host "No virtual environment found, using system Python..." -ForegroundColor Yellow
}

# Build Python command arguments
$PythonArgs = @($PythonScript, $FolderPath)

if ($Recursive) {
    $PythonArgs += "--recursive"
}

if ($Absolute) {
    $PythonArgs += "--absolute"
}

if ($Verbose) {
    $PythonArgs += "--verbose"
}

# Run the Python script
Write-Host "Running set_folder_icon.py..." -ForegroundColor Cyan
& python $PythonArgs

# Capture exit code
$ExitCode = $LASTEXITCODE

# Deactivate virtual environment if it was activated
if (Test-Path $VenvActivate) {
    deactivate
}

exit $ExitCode
