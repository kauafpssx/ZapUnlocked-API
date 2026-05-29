@echo off
setlocal enabledelayedexpansion
title ZapUnlocked API - Instalacao
cd /d "%~dp0..\.."

:: ── UI Header ─────────────────────────────────────────────────────────
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  ". '%~dp0..\lib\common.ps1'; Show-Banner; Show-Tags -Icon '⬇' -Label 'INSTALL' -OsLabel 'Windows'; Show-Sep; Init-Header -Icon '⬇' -Label 'INSTALL' -OsLabel 'Windows'"

:: ── gum auto-install ──────────────────────────────────────────────────
where gum >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando gum...
    winget install charmbracelet.gum --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
)

:: ── Python ────────────────────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      ". '%~dp0..\lib\common.ps1'; Write-Info 'Instalando Python...'"
    winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    if !errorlevel! equ 0 (
        powershell -NoProfile -ExecutionPolicy Bypass -Command ^
          ". '%~dp0..\lib\common.ps1'; Write-Ok 'Python instalado'; Refresh-Header"
    ) else (
        powershell -NoProfile -ExecutionPolicy Bypass -Command ^
          ". '%~dp0..\lib\common.ps1'; Write-Err 'Python nao encontrado — instale em python.org'"
        pause & exit /b 1
    )
)

:: ── Venv ──────────────────────────────────────────────────────────────
gum spin --spinner dot --title "Criando ambiente virtual..." -- python -m venv .venv
if %errorlevel% neq 0 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      ". '%~dp0..\lib\common.ps1'; Write-Err 'Falha ao criar ambiente virtual'"
    pause & exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  ". '%~dp0..\lib\common.ps1'; Write-Ok 'Ambiente virtual criado'"

:: ── Requirements ──────────────────────────────────────────────────────
gum spin --spinner dot --title "Installing ZapUnlocked API" --show-output -- ^
    .venv\Scripts\python.exe -m pip install --upgrade pip -r requirements.txt -q
if %errorlevel% neq 0 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      ". '%~dp0..\lib\common.ps1'; Write-Err 'Falha ao instalar requirements'"
    pause & exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  ". '%~dp0..\lib\common.ps1'; Write-Ok 'Requirements instalados'; Refresh-Header"

:: ── Windows-Specific: python-magic-bin ────────────────────────────────
gum spin --spinner dot --title "Instalando python-magic-bin..." -- .venv\Scripts\python.exe -m pip install python-magic-bin>=0.4.14 -q
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  ". '%~dp0..\lib\common.ps1'; Write-Ok 'python-magic-bin instalado'; Refresh-Header"

:: ── Done ──────────────────────────────────────────────────────────────
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  ". '%~dp0..\lib\common.ps1'; Show-Sep; Show-Footer 'Instalacao concluida!'"
pause
