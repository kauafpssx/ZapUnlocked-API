#!/bin/bash
echo "==================================================="
echo "[ZapUnlocked API] - Iniciando Servidor..."
echo "==================================================="

echo "[1/3] Verificando processos antigos na porta 8000..."
PID=$(lsof -t -i:8000 2>/dev/null)
if [ ! -z "$PID" ]; then
    echo "[!] Processo $PID encontrado na porta 8000. Encerrando processo..."
    kill -9 $PID
fi

echo "[2/3] Aguardando liberacao da porta..."
sleep 2

echo "[3/3] Iniciando Uvicorn com logs e auto-reload..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info
