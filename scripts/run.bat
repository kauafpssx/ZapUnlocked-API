@echo off
echo ===================================================
echo [ZapUnlocked API] - Iniciando Servidor...
echo ===================================================

echo [1/3] Verificando processos antigos na porta 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    echo [!] Processo %%a encontrado na porta 8000. Encerrando processo...
    taskkill /f /pid %%a >nul 2>&1
)

echo [2/3] Aguardando liberacao da porta...
timeout /t 2 /nobreak >nul

echo [3/3] Iniciando Uvicorn com logs e auto-reload...
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info

pause
