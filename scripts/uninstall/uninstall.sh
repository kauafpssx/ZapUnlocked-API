#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
cd "$ROOT_DIR"

# ── Start ──────────────────────────────────────────────────────────────
clear
ui_banner
ui_tags "$ICON_REMOVE" "REMOVE"
ui_sep
ui_task "Uninstalling ZapUnlocked API"

# ── Confirm ───────────────────────────────────────────────────────────
gum confirm "Remove virtual environment, vendor and cache?" || {
    ui_log_info "Operation canceled"
    exit 0
}

# ── Venv ───────────────────────────────────────────────────────────────
if [ -d ".venv" ]; then
    gum spin --spinner dot --title "Removing .venv..." -- rm -rf .venv
    ui_log_ok "Virtual environment removed"
fi

# ── Vendor (internal method) ──────────────────────────────────────────
if [ -d "vendor" ]; then
    gum spin --spinner dot --title "Removing vendor..." -- rm -rf vendor
    ui_log_ok "vendor removed"
fi

# ── Cache ──────────────────────────────────────────────────────────────
gum spin --spinner dot --title "Cleaning __pycache__..." -- \
    bash -c "find . -type d -name '__pycache__' -not -path './.git/*' -exec rm -rf {} + 2>/dev/null; \
             find . -name '*.pyc' -not -path './.git/*' -delete 2>/dev/null; true"
ui_log_ok "Cache cleaned"

# ── Done ───────────────────────────────────────────────────────────────
ui_sep
ui_footer "Uninstall complete!"
