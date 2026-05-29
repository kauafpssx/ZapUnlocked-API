@echo off
setlocal enabledelayedexpansion
title ZapUnlocked API - Instalacao
cd /d "%~dp0..\.."

:: ── UI Header ─────────────────────────────────────────────────────────
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  ". '%~dp0..\lib\common.ps1'; Show-Banner; Show-Tags -Icon '⬇' -Label 'INSTALL'; Show-Sep; Show-Task 'Installing ZapUnlocked API'"

:: ── gum auto-install ──────────────────────────────────────────────────
where gum >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando gum...
    winget install charmbracelet.gum --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
)

:: ── Python ────────────────────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% equ 0 (
    gum style --foreground "#42C292" "  ✓ Python encontrado"
) else (
    gum style --foreground "#A855F7" "  ◉ Instalando Python..."
    winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    if !errorlevel! equ 0 (
        gum style --foreground "#42C292" "  ✓ Python instalado"
    ) else (
        gum style --foreground "#EF4444" "  ✖ Python nao encontrado — instale em python.org"
        pause & exit /b 1
    )
)

:: ── Venv ──────────────────────────────────────────────────────────────
gum spin --spinner dot --title "Criando ambiente virtual..." -- python -m venv .venv
if %errorlevel% neq 0 (
    gum style --foreground "#EF4444" "  ✖ Falha ao criar ambiente virtual"
    pause & exit /b 1
)
gum style --foreground "#42C292" "  ✓ Ambiente virtual criado"

:: ── Requirements ──────────────────────────────────────────────────────
gum spin --spinner dot --title "Instalando requirements..." -- .venv\Scripts\python.exe -m pip install --upgrade pip -r requirements.txt -q
if %errorlevel% neq 0 (
    gum style --foreground "#EF4444" "  ✖ Falha ao instalar requirements"
    pause & exit /b 1
)
gum style --foreground "#42C292" "  ✓ Requirements instalados"

:: ── Windows-Specific: python-magic-bin ────────────────────────────────
gum spin --spinner dot --title "Instalando python-magic-bin..." -- .venv\Scripts\python.exe -m pip install python-magic-bin>=0.4.14 -q
gum style --foreground "#42C292" "  ✓ python-magic-bin instalado"

:: ── Done ──────────────────────────────────────────────────────────────
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  ". '%~dp0..\lib\common.ps1'; Show-Sep; Show-Footer 'Instalacao concluida!'"
pause
