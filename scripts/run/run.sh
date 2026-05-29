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
ui_log_ok "Port 8300 free"

# ── Detect installation method ────────────────────────────────────────
_RELOAD="--reload"

if __alwaysdata_check; then
    _RELOAD=""
    export MALLOC_ARENA_MAX=1
    export PYTHONMALLOC=malloc
    # Ensure libmagic.so.1 is on the dynamic linker path (needed by python-magic / neonize)
    for _libdir in /usr/lib/x86_64-linux-gnu /usr/lib/aarch64-linux-gnu /usr/lib /usr/local/lib; do
        if [ -f "$_libdir/libmagic.so.1" ]; then
            export LD_LIBRARY_PATH="$_libdir${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
            break
        fi
    done
fi

if [ -d "$ROOT_DIR/vendor" ]; then
    export PYTHONPATH="$ROOT_DIR/vendor${PYTHONPATH:+:$PYTHONPATH}"
fi

# ── Detect uvicorn command ──────────────────────────────────────────
if python3 -c "import uvicorn" &>/dev/null; then
    CMD="python3 -m uvicorn"
    ui_log_ok "Usando python3 -m uvicorn ($(python3 -c 'import uvicorn; print(uvicorn.__file__)'))"
elif [ -f ".venv/bin/uvicorn" ]; then
    CMD=".venv/bin/uvicorn"
    ui_log_ok "Usando .venv/bin/uvicorn"
elif command -v uvicorn &>/dev/null; then
    CMD="uvicorn"
    ui_log_ok "Usando uvicorn global"
else
    ui_log_err "uvicorn not found — run install.sh first"
    exit 1
fi

# ── Start ──────────────────────────────────────────────────────────────
ui_sep
ui_log_info "Server listening on http://[::]:8300"
ui_log_info "Press Ctrl+C to stop"
echo ""
echo ""

$CMD main:app --host '::' --port 8300 --proxy-headers --forwarded-allow-ips '::1' $_RELOAD --log-level info
