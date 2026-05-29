#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"

# ── gum auto-install ─────────────────────────────────────────────────────────
if ! command -v gum &>/dev/null; then
    echo "Instalando gum..."
    mkdir -p "$HOME/.local/bin"
    GUM_TAG=$(curl -fsSL https://api.github.com/repos/charmbracelet/gum/releases/latest \
              | grep '"tag_name"' | cut -d'"' -f4)
    GUM_VER="${GUM_TAG#v}"
    case "$(uname -m)" in
        aarch64|arm64) ARCH="arm64" ;;
        *)             ARCH="x86_64" ;;
    esac
    curl -fsSL \
      "https://github.com/charmbracelet/gum/releases/download/${GUM_TAG}/gum_${GUM_VER}_Linux_${ARCH}.tar.gz" \
      | tar -xz -C /tmp/ 2>/dev/null
    mv /tmp/gum_*/gum "$HOME/.local/bin/gum"
    export PATH="$HOME/.local/bin:$PATH"
fi

# ─────────────────────────────────────────────────────────────────────────────

echo ""
gum style \
    --foreground "212" --border-foreground "212" \
    --border rounded --align center \
    --width 42 --padding "0 2" \
    "ZapUnlocked API  ·  Instalação"
echo ""

# Detect OS silently
if [[ "$OSTYPE" == "darwin"* ]]; then OS="macos"
elif [ -f /etc/os-release ]; then . /etc/os-release; OS=$ID
else OS=$(uname -s); fi

# ── Python ───────────────────────────────────────────────────────────────────
if command -v python3 &>/dev/null; then
    gum log --level info "Python encontrado"
else
    case $OS in
        macos)
            command -v brew &>/dev/null || gum spin --spinner dot --title "Instalando Homebrew..." -- \
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            gum spin --spinner dot --title "Instalando Python..." -- brew install python
            ;;
        ubuntu|debian|raspbian)
            gum spin --spinner dot --title "Instalando Python..." -- \
                sudo apt-get install -y python3 python3-pip python3-full
            ;;
        fedora|centos|rhel)
            gum spin --spinner dot --title "Instalando Python..." -- \
                sudo dnf install -y python3 python3-pip
            ;;
        arch|manjaro)
            gum spin --spinner dot --title "Instalando Python..." -- \
                sudo pacman -S --noconfirm python python-pip
            ;;
        *)
            gum log --level error "Python não encontrado — instale Python 3.10+ manualmente"
            exit 1
            ;;
    esac
    gum log --level info "Python instalado"
fi

# ── Venv ─────────────────────────────────────────────────────────────────────
gum spin --spinner dot --title "Criando ambiente virtual..." -- python3 -m venv .venv
if [ $? -ne 0 ]; then
    gum log --level error "Falha ao criar ambiente virtual"
    exit 1
fi
gum log --level info "Ambiente virtual criado"

# ── Requirements ─────────────────────────────────────────────────────────────
gum spin --spinner dot --title "Instalando requirements..." -- \
    .venv/bin/pip install --upgrade pip -r requirements.txt -q
if [ $? -ne 0 ]; then
    gum log --level error "Falha ao instalar requirements"
    exit 1
fi
gum log --level info "Requirements instalados"

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
gum style \
    --foreground "42" --border-foreground "42" \
    --border rounded --align center \
    --width 42 --padding "0 2" \
    "✔ Instalação concluída!" \
    "Execute: bash scripts/run/run.sh"
echo ""
