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
    --foreground "196" --border-foreground "196" \
    --border rounded --align center \
    --width 42 --padding "0 2" \
    "ZapUnlocked API  ·  Desinstalação"
echo ""

# ── Confirmação ───────────────────────────────────────────────────────────────
gum confirm "Remover ambiente virtual e cache?" || exit 0

echo ""

# ── Venv ─────────────────────────────────────────────────────────────────────
gum spin --spinner dot --title "Removendo ambiente virtual..." -- rm -rf .venv
gum log --level info "Ambiente virtual removido"

# ── Cache ─────────────────────────────────────────────────────────────────────
gum spin --spinner dot --title "Limpando cache Python..." -- \
    bash -c "find . -type d -name '__pycache__' -not -path './.git/*' -exec rm -rf {} + 2>/dev/null; \
             find . -name '*.pyc' -not -path './.git/*' -delete 2>/dev/null; true"
gum log --level info "Cache limpo"

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
gum style \
    --foreground "42" --border-foreground "42" \
    --border rounded --align center \
    --width 42 --padding "0 2" \
    "✔ Desinstalação concluída!"
echo ""
