@echo off
setlocal enabledelayedexpansion
title ZapUnlocked API - Servidor
cd /d "%~dp0..\.."

:: ── UI Header ─────────────────────────────────────────────────────────
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  ". '%~dp0..\lib\common.ps1'; Show-Banner; Show-Tags -Icon '▶' -Label 'RUN'; Show-Sep; Show-Task 'Starting ZapUnlocked API server'"

where gum >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] gum nao encontrado - execute install.bat primeiro
    pause & exit /b 1
)

if not exist ".venv\" (
    gum style --foreground "#EF4444" "  ✖ Ambiente virtual nao encontrado — execute install.bat primeiro"
    pause & exit /b 1
)
gum style --foreground "#42C292" "  ✓ Ambiente virtual encontrado"

for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| find ":8300" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
gum style --foreground "#42C292" "  ✓ Porta 8300 livre"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  ". '%~dp0..\lib\common.ps1'; Show-Sep"

call .venv\Scripts\activate.bat >nul 2>&1
.venv\Scripts\uvicorn.exe main:app --host "::" --port 8300 --proxy-headers --forwarded-allow-ips "::1" --reload --log-level info

pause
