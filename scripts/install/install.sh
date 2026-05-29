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
gum spin --spinner dot --title "Atualizando pip..." -- .venv/bin/pip install --upgrade pip -q

while IFS= read -r pkg || [ -n "$pkg" ]; do
    pkg=$(echo "$pkg" | sed 's/#.*//' | xargs)
    [ -z "$pkg" ] && continue
    if [ "$pkg" = "Pillow" ]; then
        gum spin --spinner dot --title "$pkg (binário)" -- \
            .venv/bin/pip install "$pkg" --no-cache-dir --only-binary :all: -q
        rc=$?
    elif echo "$pkg" | grep -q "imageio-ffmpeg"; then
        if command -v ffmpeg &>/dev/null; then
            gum log --level info "ffmpeg já instalado no sistema — pulando $pkg"
            rc=0
        else
            TMP_DIR=$(mktemp -d "$HOME/.ffmpeg_extract_XXXXX")
            gum spin --spinner dot --title "Baixando ffmpeg estático (~120 MB)..." -- \
                bash -c "curl -fsSL 'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz' | tar -xJ -C '$TMP_DIR'"
            find "$TMP_DIR" -name 'ffmpeg' -type f -exec mv {} "$HOME/.local/bin/ffmpeg" \;
            find "$TMP_DIR" -name 'ffprobe' -type f -exec mv {} "$HOME/.local/bin/ffprobe" \;
            rm -rf "$TMP_DIR"
            rc=$?
            chmod +x "$HOME/.local/bin/ffmpeg" "$HOME/.local/bin/ffprobe"
        fi
    else
        gum spin --spinner dot --title "$pkg" -- \
            .venv/bin/pip install "$pkg" --no-cache-dir -q
        rc=$?
    fi
    if [ $rc -ne 0 ]; then
        gum log --level error "Falha ao instalar: $pkg"
        exit $rc
    fi
done < <(grep -v '^\s*#' requirements.txt)

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
