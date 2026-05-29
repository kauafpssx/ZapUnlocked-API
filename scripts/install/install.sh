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

# ── Alwaysdata detection ───────────────────────────────────────────────────
_ALWAYSDATA=false
[ -n "$ALWAYSDATA_ACCOUNT" ] && _ALWAYSDATA=true
[ -f /etc/alwaysdata ] && _ALWAYSDATA=true
hostname -f 2>/dev/null | grep -qi 'alwaysdata' && _ALWAYSDATA=true
uname -r 2>/dev/null | grep -qi 'alwaysdata' && _ALWAYSDATA=true

# ── Venv + Requirements ─────────────────────────────────────────────────────
if $_ALWAYSDATA; then
    gum log --level info "Alwaysdata detectado — instalando sem pip (install_wheel.py)"
    rm -rf .venv
else
    # Servidor normal: venv com pip interno
    gum log --level info "Criando ambiente virtual..."
    python3 -m venv .venv 2>/dev/null || {
        gum log --level error "Falha ao criar ambiente virtual"
        exit 1
    }
    gum log --level info "Ambiente virtual criado"
    _PIP=.venv/bin/python -m pip
    $_PIP install --upgrade pip -q
fi

# ── Helpers ──────────────────────────────────────────────────────────────────
# Resolve a melhor versao via Simple API HTML (curl+grep, sem Python carregar JSON grande)
_resolve_ver() {
    local pkg=$1 constraint=$2 min_ver name_pat
    # Extrai a versao minima do constraint (ex: ">=0.115.0" → "0.115.0")
    if echo "$constraint" | grep -q '>='; then
        min_ver=$(echo "$constraint" | sed 's/.*>=//' | sed 's/[^0-9.]//g' | sed 's/\.$//')
    else
        min_ver="0.0.0"
    fi
    # Normaliza nome: wheel usa _ no lugar de -
    name_pat=$(echo "$pkg" | sed 's/-/[-_]/g')
    curl -sS "https://pypi.org/simple/$pkg/" 2>/dev/null | \
        grep -oP "${name_pat}-\K\d[\d.]*[a-zA-Z0-9]*(?=-py|-cp|-none)" | \
        sort -V | \
        awk -v min="$min_ver" 'BEGIN{split(min,a,"."); m=a[1]*1000000+a[2]*1000+a[3]} {split($0,b,"."); v=b[1]*1000000+b[2]*1000+b[3]} v >= m' | \
        tail -1
}

# Pega um campo do JSON de versao especifica (JSON pequeno, so 1 versao)
_get_json_field() {
    local pkg=$1 ver=$2 expr=$3
    curl -sS "https://pypi.org/pypi/$pkg/$ver/json" 2>/dev/null | \
        python3 -c "import sys,json; print($(echo "$expr" | sed "s/{ver}/'$ver'/"))"
}

# Pega URL da wheel (prioriza py3)
_get_wheel_url() {
    local pkg=$1 ver=$2
    curl -sS "https://pypi.org/pypi/$pkg/$ver/json" 2>/dev/null | \
        python3 -c "
import sys,json
d=json.load(sys.stdin)
for f in d.get('urls') or []:
    if f.get('packagetype')=='bdist_wheel' and f.get('python_version','') in ('py3','py2.py3','none',''):
        print(f['url']); sys.exit(0)
for f in d.get('urls') or []:
    if f.get('packagetype')=='bdist_wheel':
        print(f['url']); sys.exit(0)
for f in d.get('releases',{}).get('$ver',[]):
    if f.get('packagetype')=='bdist_wheel':
        print(f['url']); sys.exit(0)
"
}

# Pega deps (non-extra)
_get_deps() {
    local pkg=$1 ver=$2
    curl -sS "https://pypi.org/pypi/$pkg/$ver/json" 2>/dev/null | \
        python3 -c "
import sys,json
d=json.load(sys.stdin)
for r in d['info'].get('requires_dist') or []:
    r=r.strip()
    if 'extra ==' in r: continue
    if ';' in r: r=r.split(';')[0].strip()
    if r: print(r)
"
}

_instalar_um() {
    local pkg=$1 ver=$2 url
    url=$(_get_wheel_url "$pkg" "$ver")
    [ -z "$url" ] && { gum log --level warn "  Sem wheel para $pkg $ver"; return 1; }
    python3 "$ROOT/scripts/install/install_wheel.py" "$url" "$SITE_PKG"
}

# ── Instala requirements ────────────────────────────────────────────────────
if $_ALWAYSDATA; then
    SITE_PKG="$ROOT/.local_lib"
    mkdir -p "$SITE_PKG"
    _QUEUE=()
    _SEEN=""

    _enqueue() {
        local spec=$1
        echo "$_SEEN" | tr ' ' '\n' | grep -qxF "$spec" && return
        _SEEN="$_SEEN $spec"
        _QUEUE+=("$spec")
    }

    # Popula fila inicial com os requisitos de requirements.txt
    while IFS= read -r line; do
        line=$(echo "$line" | sed 's/#.*//' | xargs)
        [ -z "$line" ] && continue
        echo "$line" | grep -qi 'imageio-ffmpeg' && continue
        _enqueue "$line"
    done < <(grep -v '^[[:space:]]*#' requirements.txt)

    # Processa fila
    i=0
    while [ $i -lt ${#_QUEUE[@]} ]; do
        spec="${_QUEUE[$i]}"
        ((i++))
        gum log --level info "  $spec"

        # Extrai nome da spec
        pkg=$(echo "$spec" | sed 's/\[.*\]//' | sed 's/[><=!~].*//' | xargs)

        # Resolve versao (curl + grep — sem Python carregar JSON grande)
        constraint=$(echo "$spec" | sed 's/^[a-zA-Z0-9._-]*//')
        ver=$(_resolve_ver "$pkg" "$constraint")
        [ -z "$ver" ] && { gum log --level warn "  Nao resolveu versao para $spec"; continue; }

        # Verifica se ja instalado
        [ -d "$SITE_PKG/${pkg}-${ver}.dist-info" ] && { gum log --level info "  $pkg==$ver  ja instalado"; continue; }

        # Instala
        for attempt in 1 2 3; do
            if _instalar_um "$pkg" "$ver"; then
                # Depois de instalar, coleta deps e enfileira
                while IFS= read -r dep; do
                    [ -n "$dep" ] && _enqueue "$dep"
                done < <(_get_deps "$pkg" "$ver")
                break
            fi
            gum log --level warn "  Tentativa $attempt/3 falhou, retentando..."
        done || gum log --level warn "  Pulado apos 3 tentativas: $spec"
    done

    gum log --level info "Requirements instalados"

    # ffmpeg estatico
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
else
    gum spin --spinner dot --title "Instalando requirements..." -- \
        $_PIP install -r requirements.txt --no-cache-dir -q || {
        gum log --level error "Falha ao instalar requirements"
        exit 1
    }
    gum log --level info "Requirements instalados"
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
