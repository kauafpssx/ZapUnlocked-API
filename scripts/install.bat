@echo off
setlocal enabledelayedexpansion
title ZapUnlocked-API Installer

echo ======================================================
echo    ZapUnlocked-API - Windows Global Installer
echo ======================================================

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python nao encontrado. Tentando instalar...
    
    :: Try winget
    echo [i] Tentando via winget...
    winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
    if %errorlevel% equ 0 goto check_python
    
    :: Try choco fallback
    echo [!] winget falhou ou nao encontrado. Tentando Chocolatey...
    where choco >nul 2>&1
    if %errorlevel% equ 0 (
        choco install python -y
        goto check_python
    )
    
    echo [X] Erro: Nao foi possivel instalar o Python automaticamente.
    echo [!] Por favor, instale o Python 3.10+ manualmente em https://www.python.org/downloads/
    pause
    exit /b 1
)

:check_python
echo [V] Python detectado.

:: 2. Check Pip
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Instalando pip...
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python get-pip.py
    del get-pip.py
)

:: 3. Install Requirements Globais
echo [i] Instalando dependencias globais...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install python-magic-bin

:: 4. Final Audit
echo [V] Dependencias instaladas.

:: 5. Run API
echo [i] Iniciando ZapUnlocked-API...
python main.py
pause
