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

# ── Port ─────────────────────────────────────────────────────────────────────
PID=$(lsof -t -i:8300 2>/dev/null)
if [ -n "$PID" ]; then
    kill -9 "$PID" 2>/dev/null
    sleep 1
fi
gum log --level info "Porta 8300 livre"

# ── Alwaysdata: configura antes da deteccao de uvicorn ───────────────────────
_RELOAD="--reload"
_IS_AD=false
[ -n "$ALWAYSDATA_ACCOUNT" ] && _IS_AD=true
[ -f /etc/alwaysdata ] && _IS_AD=true
hostname -f 2>/dev/null | grep -qi 'alwaysdata' && _IS_AD=true

if $_IS_AD; then
    _RELOAD=""
    export MALLOC_ARENA_MAX=1
    export PYTHONMALLOC=malloc
    export PYTHONPATH="$ROOT/vendor${PYTHONPATH:+:$PYTHONPATH}"
fi

# ── Detectar comando uvicorn ────────────────────────────────────────────────
if [ -f ".venv/bin/uvicorn" ]; then
    CMD=".venv/bin/uvicorn"
    gum log --level info "Usando .venv"
elif command -v uvicorn &>/dev/null; then
    CMD="uvicorn"
    gum log --level info "Usando uvicorn global"
elif python3 -c "import uvicorn" &>/dev/null; then
    CMD="python3 -m uvicorn"
    gum log --level info "Usando python3 -m uvicorn"
else
    gum log --level error "uvicorn nao encontrado — execute install.sh primeiro"
    exit 1
fi

# ── Start ─────────────────────────────────────────────────────────────────────
echo ""
gum style --foreground "240" "  Iniciando servidor..."
echo ""

$CMD main:app --host '::' --port 8300 --proxy-headers --forwarded-allow-ips '::1' $_RELOAD --log-level info
