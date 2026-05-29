#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
cd "$ROOT_DIR"

# ── Start ──────────────────────────────────────────────────────────────
ui_banner
ui_tags "$ICON_REMOVE" "REMOVE"
ui_sep
ui_task "Uninstalling ZapUnlocked API"

# ── Confirm ───────────────────────────────────────────────────────────
gum confirm "Remover ambiente virtual e cache?" || {
    ui_log_info "Operação cancelada"
    exit 0
}

# ── Venv ───────────────────────────────────────────────────────────────
ui_progress 30 "Removendo ambiente virtual..."
gum spin --spinner dot --title "Removendo .venv..." -- rm -rf .venv
ui_log_ok "Ambiente virtual removido"

# ── Cache ──────────────────────────────────────────────────────────────
ui_progress 70 "Limpando cache Python..."
gum spin --spinner dot --title "Limpando __pycache__..." -- \
    bash -c "find . -type d -name '__pycache__' -not -path './.git/*' -exec rm -rf {} + 2>/dev/null; \
             find . -name '*.pyc' -not -path './.git/*' -delete 2>/dev/null; true"
ui_log_ok "Cache limpo"

# ── Done ───────────────────────────────────────────────────────────────
ui_progress 100 "Uninstall complete"
ui_sep
ui_footer "Desinstalação concluída!"
