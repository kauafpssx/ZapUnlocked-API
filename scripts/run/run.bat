@echo off
setlocal enabledelayedexpansion
title ZapUnlocked API - Servidor
cd /d "%~dp0..\.."

where gum >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] gum nao encontrado - execute install.bat primeiro
    pause & exit /b 1
)

echo.
gum style --foreground "39" --border-foreground "39" --border rounded --align center --width 42 --padding "0 2" "ZapUnlocked API  .  Servidor"
echo.

if not exist ".venv\" (
    gum log --level error "Ambiente virtual nao encontrado — execute install.bat primeiro"
    pause & exit /b 1
)
gum log --level info "Ambiente virtual ativado"

for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| find ":8300" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
gum log --level info "Porta 8300 livre"

echo.
gum style --foreground "240" "  Iniciando servidor..."
echo.

call .venv\Scripts\activate.bat >nul 2>&1
.venv\Scripts\uvicorn.exe main:app --host "::" --port 8300 --proxy-headers --forwarded-allow-ips "::1" --reload --log-level info

pause
