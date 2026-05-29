@echo off
setlocal enabledelayedexpansion
title ZapUnlocked API - Server
cd /d "%~dp0..\.."

:: -- UI Header --
powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Show-Banner; Show-Tags -Task run; Show-Sep; Show-Task 'Starting ZapUnlocked API server'"

where gum >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] gum not found - run install.bat first
    pause & exit /b 1
)

if not exist ".venv\" (
    gum style --foreground "#EF4444" "  x Virtual environment not found - run install.bat first"
    pause & exit /b 1
)
gum style --foreground "#42C292" "  ok Virtual environment found"

for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| find ":8300" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
gum style --foreground "#42C292" "  ok Port 8300 free"

powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Show-Sep"

call .venv\Scripts\activate.bat >nul 2>&1
.venv\Scripts\uvicorn.exe main:app --host "::" --port 8300 --proxy-headers --forwarded-allow-ips "::1" --reload --log-level info

pause
