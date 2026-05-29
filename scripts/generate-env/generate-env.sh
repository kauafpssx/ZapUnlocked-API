#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
cd "$ROOT_DIR"

# ── Start ──────────────────────────────────────────────────────────────
ui_banner
ui_tags "$ICON_GEN" "GEN ENV"
ui_sep
ui_task "Generating environment secrets"

# ── Gerar secrets ─────────────────────────────────────────────────────
gen_hex() {
    if command -v openssl &>/dev/null; then
        openssl rand -hex 32
    else
        python3 -c "import secrets; print(secrets.token_hex(32))"
    fi
}

API_KEY="zu_$(gen_hex)"
INTERNAL_SECRET="zu_sec_$(gen_hex)"

ui_log_ok "API_KEY generated"
ui_log_ok "INTERNAL_SECRET generated"

# ── Portable sed in-place ─────────────────────────────────────────────
_sed_inplace() {
    local pattern=$1 file=$2
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "$pattern" "$file"
    else
        sed -i "$pattern" "$file"
    fi
}

# ── Exibir secrets ────────────────────────────────────────────────────
echo ""
gum style --foreground "#6B7280" "  API_KEY"
gum style --foreground "#42C292" --bold "  $API_KEY"
echo ""
gum style --foreground "#6B7280" "  INTERNAL_SECRET"
gum style --foreground "#42C292" --bold "  $INTERNAL_SECRET"
echo ""

# ── Salvar no .env ────────────────────────────────────────────────────
gum confirm "Salvar no arquivo .env?" || {
    ui_log_info "Secrets exibidas mas não salvas"
    ui_sep
    ui_footer "Operação cancelada"
    exit 0
}

if [ -f ".env" ]; then
    if grep -q "^API_KEY=" .env; then
        _sed_inplace "s|^API_KEY=.*|API_KEY=$API_KEY|" .env
    else
        echo "API_KEY=$API_KEY" >> .env
    fi

    if grep -q "^INTERNAL_SECRET=" .env; then
        _sed_inplace "s|^INTERNAL_SECRET=.*|INTERNAL_SECRET=$INTERNAL_SECRET|" .env
    else
        echo "INTERNAL_SECRET=$INTERNAL_SECRET" >> .env
    fi
    ui_log_ok "Existing .env updated"
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        _sed_inplace "s|^API_KEY=.*|API_KEY=$API_KEY|" .env
        _sed_inplace "s|^INTERNAL_SECRET=.*|INTERNAL_SECRET=$INTERNAL_SECRET|" .env
        ui_log_ok "Created from .env.example"
    else
        printf "API_KEY=%s\nINTERNAL_SECRET=%s\n" "$API_KEY" "$INTERNAL_SECRET" > .env
        ui_log_ok "Created new .env"
    fi
fi

# ── Done ───────────────────────────────────────────────────────────────
ui_sep
ui_footer "Secrets salvas em .env"
