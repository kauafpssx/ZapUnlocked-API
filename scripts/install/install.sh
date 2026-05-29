#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"

# ── gum auto-install ─────────────────────────────────────────────────────────
export PATH="$HOME/.local/bin:$PATH"
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

# ── Alwaysdata detection ───────────────────────────────────────────────────
_ALWAYSDATA=false
[ -n "$ALWAYSDATA_ACCOUNT" ] && _ALWAYSDATA=true
[ -f /etc/alwaysdata ] && _ALWAYSDATA=true
hostname -f 2>/dev/null | grep -qi 'alwaysdata' && _ALWAYSDATA=true

# ── Requirements ─────────────────────────────────────────────────────────────
gum spin --spinner dot --title "Atualizando pip..." -- .venv/bin/pip install --upgrade pip -q

if $_ALWAYSDATA; then
    gum log --level info "Alwaysdata detectado — instalando em modo economia de RAM"

    # 1. Instala cada pacote sem dependencias (um por vez, evita OOM)
    while IFS= read -r pkg || [ -n "$pkg" ]; do
        pkg=$(echo "$pkg" | sed 's/#.*//' | xargs)
        [ -z "$pkg" ] && continue
        gum spin --spinner dot --title "$pkg" -- \
            .venv/bin/pip install --no-cache-dir --no-deps "$pkg" -q || exit 1
    done < <(grep -v '^\s*#' requirements.txt)

    # 2. ffmpeg estatico se necessario
    if ! command -v ffmpeg &>/dev/null; then
        TMP_DIR=$(mktemp -d "$HOME/.ffmpeg_extract_XXXXX")
        gum spin --spinner dot --title "Baixando ffmpeg estatico (~120 MB)..." -- \
            bash -c "curl -fsSL 'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz' | tar -xJ -C '$TMP_DIR'" || exit 1
        find "$TMP_DIR" -name 'ffmpeg' -type f -exec mv {} "$HOME/.local/bin/ffmpeg" \;
        find "$TMP_DIR" -name 'ffprobe' -type f -exec mv {} "$HOME/.local/bin/ffprobe" \;
        rm -rf "$TMP_DIR"
        chmod +x "$HOME/.local/bin/ffmpeg" "$HOME/.local/bin/ffprobe"
    else
        gum log --level info "ffmpeg ja no sistema"
    fi

    # 3. Resolve dependencias faltantes via pip check
    gum log --level info "Resolvendo dependencias..."
    while true; do
        missing=$(.venv/bin/pip check 2>/dev/null | grep 'requires')
        [ -z "$missing" ] && break
        echo "$missing" | while IFS= read -r line; do
            # Extrai cada dependencia (ex: "fastapi 0.136.3 requires starlette>=0.46.0" -> "starlette")
            for dep in $(echo "$line" | sed 's/.*requires //' | tr ',' '\n' | sed 's/\[.*\]//' | sed 's/[<>=!~].*//' | xargs); do
                [ -z "$dep" ] && continue
                gum spin --spinner dot --title "  $dep" -- \
                    .venv/bin/pip install --no-cache-dir "$dep" -q || exit 1
            done
        done
    done

    gum log --level info "Requirements instalados"
else
    # Servidor normal: instala tudo de uma vez (rapido)
    gum spin --spinner dot --title "Instalando requirements..." -- \
        .venv/bin/pip install -r requirements.txt --no-cache-dir -q
    if [ $? -eq 0 ]; then
        gum log --level info "Requirements instalados"
    else
        gum log --level error "Falha ao instalar requirements"
        exit 1
    fi
fi

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
gum style \
    --foreground "42" --border-foreground "42" \
    --border rounded --align center \
    --width 42 --padding "0 2" \
    "✔ Instalação concluída!" \
    "Execute: bash scripts/run/run.sh"
echo ""
