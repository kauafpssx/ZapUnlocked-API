@echo off
setlocal enabledelayedexpansion
title ZapUnlocked API - Generate Secrets
cd /d "%~dp0..\.."
cls

:: -- UI Header --
powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Show-Banner; Show-Tags -Task genenv; Show-Sep; Show-Task 'Generating environment secrets'"

where gum >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] gum not found - run scripts\install\install.bat first
    pause & exit /b 1
)

:: -- Generate secrets via PowerShell --
powershell -NoProfile -Command "$rng = New-Object System.Security.Cryptography.RNGCryptoServiceProvider; $b = New-Object byte[] 32; $rng.GetBytes($b); 'zu_' + [BitConverter]::ToString($b).Replace('-','').ToLower()" > "%TEMP%\zap_apikey.tmp"
set /p API_KEY= < "%TEMP%\zap_apikey.tmp"
del "%TEMP%\zap_apikey.tmp" >nul 2>&1

powershell -NoProfile -Command "$rng = New-Object System.Security.Cryptography.RNGCryptoServiceProvider; $b = New-Object byte[] 32; $rng.GetBytes($b); 'zu_sec_' + [BitConverter]::ToString($b).Replace('-','').ToLower()" > "%TEMP%\zap_secret.tmp"
set /p INTERNAL_SECRET= < "%TEMP%\zap_secret.tmp"
del "%TEMP%\zap_secret.tmp" >nul 2>&1

powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Write-Ok 'API_KEY generated'"
powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Write-Ok 'INTERNAL_SECRET generated'"

:: -- Display secrets --
echo.
gum style --foreground "#6B7280" "  API_KEY"
gum style --foreground 42 --bold "  !API_KEY!"
echo.
gum style --foreground 240 "  INTERNAL_SECRET"
gum style --foreground 42 --bold "  !INTERNAL_SECRET!"
echo.

:: -- Save to .env --
gum confirm "Save to .env file?"
if %errorlevel% neq 0 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Write-Warn 'Secrets displayed but not saved'"
    powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Show-Sep; Show-Footer 'Operation canceled'"
    pause & exit /b 0
)

if exist ".env" (
    powershell -NoProfile -Command "$c = Get-Content '.env' -Raw -ErrorAction SilentlyContinue; if ($c -match 'API_KEY=') { $c = $c -replace '(?m)^API_KEY=.*', 'API_KEY=!API_KEY!' } else { $c = $c.TrimEnd() + [Environment]::NewLine + 'API_KEY=!API_KEY!' }; if ($c -match 'INTERNAL_SECRET=') { $c = $c -replace '(?m)^INTERNAL_SECRET=.*', 'INTERNAL_SECRET=!INTERNAL_SECRET!' } else { $c = $c.TrimEnd() + [Environment]::NewLine + 'INTERNAL_SECRET=!INTERNAL_SECRET!' }; Set-Content '.env' $c.TrimEnd() -Encoding utf8"
    powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Write-Ok 'Existing .env updated'"
) else if exist ".env.example" (
    copy .env.example .env >nul
    powershell -NoProfile -Command "$c = Get-Content '.env' -Raw; $c = $c -replace '(?m)^API_KEY=.*', 'API_KEY=!API_KEY!'; $c = $c -replace '(?m)^INTERNAL_SECRET=.*', 'INTERNAL_SECRET=!INTERNAL_SECRET!'; Set-Content '.env' $c.TrimEnd() -Encoding utf8"
    powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Write-Ok 'Created from .env.example'"
) else (
    (echo API_KEY=!API_KEY!& echo INTERNAL_SECRET=!INTERNAL_SECRET!) > .env
    powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Write-Ok 'Created new .env'"
)

:: -- Done --
powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%~dp0..\lib\common.ps1'; Show-Sep; Show-Footer 'Secrets saved to .env'"
pause
