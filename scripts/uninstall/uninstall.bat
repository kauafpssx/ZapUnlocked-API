@echo off
setlocal enabledelayedexpansion
title ZapUnlocked API - Desinstalacao
cd /d "%~dp0..\.."

where gum >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] gum nao encontrado - execute install.bat primeiro
    pause & exit /b 1
)

echo.
gum style --foreground "196" --border-foreground "196" --border rounded --align center --width 42 --padding "0 2" "ZapUnlocked API  .  Desinstalacao"
echo.

gum confirm "Remover ambiente virtual e cache?"
if %errorlevel% neq 0 ( exit /b 0 )

echo.

:: ── Venv ────────────────────────────────────────────────────────────────────
gum spin --spinner dot --title "Removendo ambiente virtual..." -- cmd /c "rmdir /s /q .venv"
gum log --level info "Ambiente virtual removido"

:: ── Cache ───────────────────────────────────────────────────────────────────
gum spin --spinner dot --title "Limpando cache Python..." -- cmd /c "for /d /r . %%d in (__pycache__) do if exist \"%%d\" rmdir /s /q \"%%d\" & del /s /q *.pyc"
gum log --level info "Cache limpo"

:: ── Done ────────────────────────────────────────────────────────────────────
echo.
gum style --foreground "42" --border-foreground "42" --border rounded --align center --width 42 --padding "0 2" "Desinstalacao concluida!"
echo.
pause
