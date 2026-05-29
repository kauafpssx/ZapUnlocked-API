@echo off
setlocal enabledelayedexpansion
title ZapUnlocked API - Installation
cd /d "%~dp0..\.."

cls
:: -- UI Header --
powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Show-Banner; Show-Tags -Task install -OsLabel Windows; Show-Sep; Init-Header -Task install -OsLabel Windows"

:: -- Python --
python --version >nul 2>&1
if %errorlevel% neq 0 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Write-Info 'Installing Python...'"
    winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    if !errorlevel! equ 0 (
        powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Write-Ok 'Python installed'"
    ) else (
        powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Write-Err 'Python not found - install from python.org'"
        pause & exit /b 1
    )
)

:: -- Venv --
gum spin --spinner dot --title "Creating virtual environment..." -- python -m venv .venv
if %errorlevel% neq 0 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Write-Err 'Failed to create virtual environment'"
    pause & exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Write-Ok 'Virtual environment created'"

:: -- Requirements --
.venv\Scripts\python.exe -m pip install --upgrade pip -r requirements.txt -q
if %errorlevel% neq 0 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Write-Err 'Failed to install requirements'"
    pause & exit /b 1
)
.venv\Scripts\python.exe scripts\install\install_pip_ui.py

:: -- Windows-Specific: python-magic-bin --
.venv\Scripts\python.exe -m pip install python-magic-bin>=0.4.14 -q
.venv\Scripts\python.exe scripts\install\install_pip_ui.py --magic

:: -- Generate env --
powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Show-Sep"
gum confirm "Generate .env file now?" --default=false --affirmative "Yes" --negative "No"
if %errorlevel% equ 0 (
    call scripts\generate-env\generate-env.bat
    goto :eof
)

:: -- Done --
powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Show-Sep; Show-Footer 'Installation complete!'"
pause
