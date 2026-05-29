@echo off
setlocal enabledelayedexpansion
title ZapUnlocked API - Gerar Secrets
cd /d "%~dp0..\.."

:: ── UI Header ─────────────────────────────────────────────────────────
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  ". '%~dp0..\lib\common.ps1'; Show-Banner; Show-Tags -Icon '⚙' -Label 'GEN ENV'; Show-Sep; Show-Task 'Generating environment secrets'"

where gum >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] gum nao encontrado - execute scripts\install\install.bat primeiro
    pause & exit /b 1
)

:: ── Gerar secrets via PowerShell ──────────────────────────────────────
powershell -NoProfile -Command ^
    "$rng = New-Object System.Security.Cryptography.RNGCryptoServiceProvider;" ^
    "$b = New-Object byte[] 32; $rng.GetBytes($b);" ^
    "'zu_' + [BitConverter]::ToString($b).Replace('-','').ToLower()" ^
    > "%TEMP%\zap_apikey.tmp"
set /p API_KEY= < "%TEMP%\zap_apikey.tmp"
del "%TEMP%\zap_apikey.tmp" >nul 2>&1

powershell -NoProfile -Command ^
    "$rng = New-Object System.Security.Cryptography.RNGCryptoServiceProvider;" ^
    "$b = New-Object byte[] 32; $rng.GetBytes($b);" ^
    "'zu_sec_' + [BitConverter]::ToString($b).Replace('-','').ToLower()" ^
    > "%TEMP%\zap_secret.tmp"
set /p INTERNAL_SECRET= < "%TEMP%\zap_secret.tmp"
del "%TEMP%\zap_secret.tmp" >nul 2>&1

gum style --foreground "#42C292" "  ✓ API_KEY generated"
gum style --foreground "#42C292" "  ✓ INTERNAL_SECRET generated"

:: ── Exibir secrets ────────────────────────────────────────────────────
echo.
gum style --foreground "#6B7280" "  API_KEY"
gum style --foreground 42 --bold "  !API_KEY!"
echo.
gum style --foreground 240 "  INTERNAL_SECRET"
gum style --foreground 42 --bold "  !INTERNAL_SECRET!"
echo.

:: ── Salvar no .env ────────────────────────────────────────────────────
gum confirm "Salvar no arquivo .env?"
if %errorlevel% neq 0 (
    gum style --foreground 39 "  ◉ Secrets exibidas mas nao salvas"
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      ". '%~dp0..\lib\common.ps1'; Show-Sep; Show-Footer 'Operacao cancelada'"
    pause & exit /b 0
)

if exist ".env" (
    powershell -NoProfile -Command ^
        "$c = Get-Content '.env' -Raw -ErrorAction SilentlyContinue;" ^
        "if ($c -match 'API_KEY=') { $c = $c -replace '(?m)^API_KEY=.*', 'API_KEY=!API_KEY!' } else { $c = $c.TrimEnd() + [Environment]::NewLine + 'API_KEY=!API_KEY!' };" ^
        "if ($c -match 'INTERNAL_SECRET=') { $c = $c -replace '(?m)^INTERNAL_SECRET=.*', 'INTERNAL_SECRET=!INTERNAL_SECRET!' } else { $c = $c.TrimEnd() + [Environment]::NewLine + 'INTERNAL_SECRET=!INTERNAL_SECRET!' };" ^
        "Set-Content '.env' $c.TrimEnd() -Encoding utf8"
    gum style --foreground 42 "  ✓ Existing .env updated"
) else if exist ".env.example" (
    copy .env.example .env >nul
    powershell -NoProfile -Command ^
        "$c = Get-Content '.env' -Raw;" ^
        "$c = $c -replace '(?m)^API_KEY=.*', 'API_KEY=!API_KEY!';" ^
        "$c = $c -replace '(?m)^INTERNAL_SECRET=.*', 'INTERNAL_SECRET=!INTERNAL_SECRET!';" ^
        "Set-Content '.env' $c.TrimEnd() -Encoding utf8"
    gum style --foreground 42 "  ✓ Created from .env.example"
) else (
    (echo API_KEY=!API_KEY!& echo INTERNAL_SECRET=!INTERNAL_SECRET!) > .env
    gum style --foreground 42 "  ✓ Created new .env"
)

:: ── Done ──────────────────────────────────────────────────────────────
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  ". '%~dp0..\lib\common.ps1'; Show-Sep; Show-Footer 'Secrets salvas em .env'"
pause
