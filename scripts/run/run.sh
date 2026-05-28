#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"

export PATH="$HOME/.local/bin:$PATH"

if ! command -v gum &>/dev/null; then
    echo "[ERRO] gum nao encontrado — execute install.sh primeiro"
    exit 1
fi

echo ""
gum style \
    --foreground "39" --border-foreground "39" \
    --border rounded --align center \
    --width 42 --padding "0 2" \
    "ZapUnlocked API  ·  Servidor"
echo ""

# ── Venv ─────────────────────────────────────────────────────────────────────
if [ ! -d ".venv" ]; then
    gum log --level error "Ambiente virtual não encontrado — execute install.sh primeiro"
    exit 1
fi
gum log --level info "Ambiente virtual encontrado"

# ── Port ─────────────────────────────────────────────────────────────────────
PID=$(lsof -t -i:8300 2>/dev/null)
if [ -n "$PID" ]; then
    kill -9 "$PID" 2>/dev/null
    sleep 1
fi
gum log --level info "Porta 8300 livre"

# ── Start ─────────────────────────────────────────────────────────────────────
echo ""
gum style --foreground "240" "  Iniciando servidor..."
echo ""

.venv/bin/uvicorn main:app --host '::' --port 8300 --proxy-headers --forwarded-allow-ips '::1' --reload --log-level info
