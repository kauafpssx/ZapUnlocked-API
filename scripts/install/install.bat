@echo off
setlocal enabledelayedexpansion
title ZapUnlocked API - Instalacao
cd /d "%~dp0..\.."

:: ── gum auto-install ────────────────────────────────────────────────────────
where gum >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando gum...
    winget install charmbracelet.gum --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
)

echo.
gum style --foreground "212" --border-foreground "212" --border rounded --align center --width 42 --padding "0 2" "ZapUnlocked API  .  Instalacao"
echo.

:: ── Python ──────────────────────────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% equ 0 (
    gum log --level info "Python encontrado"
) else (
    gum log --level warn "Instalando Python via winget..."
    winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    if !errorlevel! equ 0 (
        gum log --level info "Python instalado"
    ) else (
        gum log --level error "Python nao encontrado — instale em python.org"
        pause & exit /b 1
    )
)

:: ── Venv ────────────────────────────────────────────────────────────────────
gum spin --spinner dot --title "Criando ambiente virtual..." -- python -m venv .venv
if %errorlevel% neq 0 (
    gum log --level error "Falha ao criar ambiente virtual"
    pause & exit /b 1
)
gum log --level info "Ambiente virtual criado"

:: ── Requirements ────────────────────────────────────────────────────────────
gum spin --spinner dot --title "Instalando requirements..." -- .venv\Scripts\python.exe -m pip install --upgrade pip -r requirements.txt -q
if %errorlevel% neq 0 (
    gum log --level error "Falha ao instalar requirements"
    pause & exit /b 1
)
gum log --level info "Requirements instalados"

:: ── Windows-Specific: python-magic-bin ────────────────────────────────────────
gum spin --spinner dot --title "Instalando python-magic-bin..." -- .venv\Scripts\python.exe -m pip install python-magic-bin>=0.4.14 -q

:: ── Done ────────────────────────────────────────────────────────────────────
echo.
gum style --foreground "42" --border-foreground "42" --border rounded --align center --width 42 --padding "0 2" "Instalacao concluida!" "Execute: scripts\run\run.bat"
echo.
pause
