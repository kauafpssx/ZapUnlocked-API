#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"

export PATH="$HOME/.local/bin:$PATH"

if ! command -v gum &>/dev/null; then
    echo "[ERRO] gum nao encontrado — execute scripts/install/install.sh primeiro"
    exit 1
fi

# ── Gerar secrets ─────────────────────────────────────────────────────────────
gen_hex() {
    if command -v openssl &>/dev/null; then
        openssl rand -hex 32
    else
        python3 -c "import secrets; print(secrets.token_hex(32))"
    fi
}

API_KEY="zu_$(gen_hex)"
INTERNAL_SECRET="zu_sec_$(gen_hex)"

# ── Header ────────────────────────────────────────────────────────────────────
echo ""
gum style \
    --foreground "212" --border-foreground "212" \
    --border rounded --align center \
    --width 42 --padding "0 2" \
    "ZapUnlocked API  ·  Gerar Secrets"
echo ""

# ── Exibir secrets ────────────────────────────────────────────────────────────
gum style --foreground "240" "  API_KEY"
gum style --foreground "42" --bold "  $API_KEY"
echo ""
gum style --foreground "240" "  INTERNAL_SECRET"
gum style --foreground "42" --bold "  $INTERNAL_SECRET"
echo ""

# ── Salvar no .env ────────────────────────────────────────────────────────────
gum confirm "Salvar no arquivo .env?" || {
    echo ""
    gum style --foreground "240" "  Secrets exibidas mas não salvas."
    echo ""
    exit 0
}

if [ -f ".env" ]; then
    # Substituir se já existir
    if grep -q "^API_KEY=" .env; then
        sed -i "s|^API_KEY=.*|API_KEY=$API_KEY|" .env
    else
        echo "API_KEY=$API_KEY" >> .env
    fi

    if grep -q "^INTERNAL_SECRET=" .env; then
        sed -i "s|^INTERNAL_SECRET=.*|INTERNAL_SECRET=$INTERNAL_SECRET|" .env
    else
        echo "INTERNAL_SECRET=$INTERNAL_SECRET" >> .env
    fi
else
    # Criar .env do zero
    if [ -f ".env.example" ]; then
        cp .env.example .env
        sed -i "s|^API_KEY=.*|API_KEY=$API_KEY|" .env
        sed -i "s|^INTERNAL_SECRET=.*|INTERNAL_SECRET=$INTERNAL_SECRET|" .env
    else
        printf "API_KEY=%s\nINTERNAL_SECRET=%s\n" "$API_KEY" "$INTERNAL_SECRET" > .env
    fi
fi

echo ""
gum style \
    --foreground "42" --border-foreground "42" \
    --border rounded --align center \
    --width 42 --padding "0 2" \
    "✔ Secrets salvas em .env"
echo ""
