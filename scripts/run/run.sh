#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
cd "$ROOT_DIR"

# ── Start ──────────────────────────────────────────────────────────────
ui_banner
ui_tags "$ICON_RUN" "RUN"
ui_sep
ui_task "Starting ZapUnlocked API server"

# ── Port ───────────────────────────────────────────────────────────────
PID=$(lsof -t -i:8300 2>/dev/null)
if [ -n "$PID" ]; then
    kill -9 "$PID" 2>/dev/null
    sleep 1
fi
ui_log_ok "Porta 8300 livre"

# ── Alwaysdata: configura antes da deteccao de uvicorn ────────────────
_RELOAD="--reload"
_IS_AD=false
__alwaysdata_check && _IS_AD=true

if $_IS_AD; then
    _RELOAD=""
    export MALLOC_ARENA_MAX=1
    export PYTHONMALLOC=malloc
    export PYTHONPATH="$ROOT/vendor${PYTHONPATH:+:$PYTHONPATH}"
fi

# ── Detectar comando uvicorn ──────────────────────────────────────────
if [ -f ".venv/bin/uvicorn" ]; then
    CMD=".venv/bin/uvicorn"
    ui_log_ok "Usando .venv/bin/uvicorn"
elif command -v uvicorn &>/dev/null; then
    CMD="uvicorn"
    ui_log_ok "Usando uvicorn global"
elif python3 -c "import uvicorn" &>/dev/null; then
    CMD="python3 -m uvicorn"
    ui_log_ok "Usando python3 -m uvicorn"
else
    ui_log_err "uvicorn não encontrado — execute install.sh primeiro"
    exit 1
fi

# ── Start ──────────────────────────────────────────────────────────────
ui_sep
ui_log_info "Servidor ouvindo em http://[::]:8300"
ui_log_info "Pressione Ctrl+C para parar"
echo ""
echo ""

$CMD main:app --host '::' --port 8300 --proxy-headers --forwarded-allow-ips '::1' $_RELOAD --log-level info
