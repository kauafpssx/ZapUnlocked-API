@echo off
setlocal enabledelayedexpansion
title ZapUnlocked API - Uninstall
cd /d "%~dp0..\.."
cls

:: -- UI Header --
powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Show-Banner; Show-Tags -Task remove; Show-Sep; Show-Task 'Uninstalling ZapUnlocked API'"

where gum >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] gum not found - run install.bat first
    pause & exit /b 1
)

gum confirm "Remove .venv, vendor and cache?"
if %errorlevel% neq 0 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Write-Warn 'Operation canceled'"
    pause & exit /b 0
)

:: -- Venv --
if exist ".venv\" (
    gum spin --spinner dot --title "Removing .venv..." -- cmd /c "rmdir /s /q .venv"
    powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Write-Ok 'Virtual environment removed'"
)

:: -- Vendor --
if exist "vendor\" (
    gum spin --spinner dot --title "Removing vendor..." -- cmd /c "rmdir /s /q vendor"
    powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Write-Ok 'vendor removed'"
)

:: -- Cache --
gum spin --spinner dot --title "Cleaning Python cache..." -- cmd /c "for /d /r . %%d in (__pycache__) do if exist \"%%d\" rmdir /s /q \"%%d\" & del /s /q *.pyc"
powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Write-Ok 'Cache cleaned'"

:: -- Done --
powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Show-Sep; Show-Footer 'Uninstall complete!'"
pause
