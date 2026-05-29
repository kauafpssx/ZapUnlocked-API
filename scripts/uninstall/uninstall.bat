@echo off
setlocal enabledelayedexpansion
title ZapUnlocked API - Desinstalacao
cd /d "%~dp0..\.."

:: ── UI Header ─────────────────────────────────────────────────────────
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  ". '%~dp0..\lib\common.ps1'; Show-Banner; Show-Tags -Icon '✕' -Label 'REMOVE'; Show-Sep; Show-Task 'Uninstalling ZapUnlocked API'"

where gum >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] gum nao encontrado - execute install.bat primeiro
    pause & exit /b 1
)

gum confirm "Remover ambiente virtual e cache?"
if %errorlevel% neq 0 (
    gum style --foreground "#A855F7" "  ◉ Operacao cancelada"
    pause & exit /b 0
)

:: ── Venv ──────────────────────────────────────────────────────────────
gum spin --spinner dot --title "Removendo ambiente virtual..." -- cmd /c "rmdir /s /q .venv"
gum style --foreground "#42C292" "  ✓ Ambiente virtual removido"

:: ── Cache ─────────────────────────────────────────────────────────────
gum spin --spinner dot --title "Limpando cache Python..." -- cmd /c "for /d /r . %%d in (__pycache__) do if exist \"%%d\" rmdir /s /q \"%%d\" & del /s /q *.pyc"
gum style --foreground "#42C292" "  ✓ Cache limpo"

:: ── Done ──────────────────────────────────────────────────────────────
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  ". '%~dp0..\lib\common.ps1'; Show-Sep; Show-Footer 'Desinstalacao concluida!'"
pause
