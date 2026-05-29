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
    # Versao exata: retorna diretamente sem consultar Simple API
    if echo "$constraint" | grep -qE '^[[:space:]]*=='; then
        echo "$constraint" | sed 's/.*==//' | tr -d '[:space:]'
        return
    fi
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

# Pega URL da wheel compativel com Python/plataforma atual
_get_wheel_url() {
    local pkg=$1 ver=$2
    curl -sS "https://pypi.org/pypi/$pkg/$ver/json" 2>/dev/null | \
        python3 -c "
import sys,json,platform
d=json.load(sys.stdin)
pv=sys.version_info
cp='cp%d%d'%(pv.major,pv.minor)
mach=platform.machine().lower()
plat_pats=['x86_64','amd64'] if mach in('x86_64','amd64') else (['aarch64','arm64'] if mach in('aarch64','arm64') else [mach])
def ok(fn):
    fn=fn.lower()
    return 'linux' in fn and any(p in fn for p in plat_pats)
files=[f for f in(d.get('urls') or []) if f.get('packagetype')=='bdist_wheel']
for f in files:
    fn=f.get('filename','')
    if f.get('python_version','')==cp and ok(fn): print(f['url']);sys.exit(0)
for f in files:
    fn=f.get('filename','')
    if 'abi3' in fn and ok(fn): print(f['url']);sys.exit(0)
for f in files:
    if f.get('python_version','') in('py3','py2.py3','none',''): print(f['url']);sys.exit(0)
for f in files:
    print(f['url']);sys.exit(0)
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
    SITE_PKG="$ROOT/vendor"
    rm -rf "$SITE_PKG" "$ROOT/wheels"
    mkdir -p "$SITE_PKG" "$ROOT/wheels"

    # Versoes fixas testadas no Alwaysdata (pydantic 1.x evita pydantic-core v2)
    python3 - "$SITE_PKG" "$ROOT/wheels" <<'PY'
import json, os, subprocess, sys, urllib.request
from pathlib import Path

TARGET = Path(sys.argv[1])
WHEELS = Path(sys.argv[2])

# Lista curada: versoes testadas, sem imageio-ffmpeg (117 MB), sem pydantic-core v2
PKGS = [
    ("fastapi",             "0.115.14", "py3-none-any"),
    ("starlette",           "0.46.2",   "py3-none-any"),
    ("pydantic",            "1.10.24",  "cp313"),
    ("typing-extensions",   "4.15.0",   "py3-none-any"),
    ("anyio",               "4.9.0",    "py3-none-any"),
    ("sniffio",             "1.3.1",    "py3-none-any"),
    ("idna",                "3.10",     "py3-none-any"),
    ("uvicorn",             "0.34.3",   "py3-none-any"),
    ("click",               "8.2.1",    "py3-none-any"),
    ("h11",                 "0.16.0",   "py3-none-any"),
    ("python-dotenv",       "1.1.1",    "py3-none-any"),
    ("requests",            "2.32.4",   "py3-none-any"),
    ("urllib3",             "2.5.0",    "py3-none-any"),
    ("certifi",             "2025.6.15","py3-none-any"),
    ("charset-normalizer",  "3.4.2",    "cp313"),
    ("httpx",               "0.28.1",   "py3-none-any"),
    ("httpcore",            "1.0.9",    "py3-none-any"),
    ("loguru",              "0.7.3",    "py3-none-any"),
    ("qrcode",              "8.2",      "py3-none-any"),
    ("Pillow",              "11.3.0",   "cp313"),
    ("python-magic",        "0.4.27",   "py3-none-any"),
    ("ffmpeg-python",       "0.2.0",    "py3-none-any"),
    ("future",              "1.0.0",    "py3-none-any"),
    ("neonize",             "0.3.18.post0", None),

    # Deps do neonize (nao instaladas automaticamente)
    ("protobuf",            "7.34.1",   None),
    ("linkpreview",         "0.11.0",   "py3-none-any"),
    ("beautifulsoup4",      "4.13.4",   "py3-none-any"),
    ("soupsieve",           "2.7",      "py3-none-any"),
    ("phonenumbers",        "8.13.52",  "py3-none-any"),
    ("segno",               "1.6.1",    "py3-none-any"),
    ("tqdm",                "4.67.1",   "py3-none-any"),
    ("aiocontextvars",      "0.2.2",    "py3-none-any"),
]

def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)

def pick(pkg, ver, tag):
    urls = fetch(f"https://pypi.org/pypi/{pkg}/{ver}/json")["urls"]
    # 1. tag especifico + linux x86_64
    if tag:
        for f in urls:
            n = f["filename"]
            if n.endswith(".whl") and tag in n and "x86_64" in n and ("manylinux" in n or "musllinux" in n):
                return f["url"], n
        for f in urls:
            n = f["filename"]
            if n.endswith(".whl") and tag in n:
                return f["url"], n
    # 2. pure python
    for f in urls:
        n = f["filename"]
        if n.endswith(".whl") and "py3-none-any" in n:
            return f["url"], n
    # 3. qualquer wheel
    for f in urls:
        if f["filename"].endswith(".whl"):
            return f["url"], f["filename"]
    raise RuntimeError(f"sem wheel: {pkg}=={ver}")

failed = []
for pkg, ver, tag in PKGS:
    try:
        url, name = pick(pkg, ver, tag)
        out = WHEELS / name
        print(f"  {pkg}=={ver}", flush=True)
        subprocess.check_call(["curl", "-fsSL", "--retry", "3", "--retry-delay", "2", "-o", str(out), url])
        subprocess.check_call(["unzip", "-q", "-o", str(out), "-d", str(TARGET)])
        out.unlink(missing_ok=True)
    except Exception as e:
        print(f"  FALHOU {pkg}=={ver}: {e}", flush=True)
        failed.append(pkg)

# psutil: abi3 especifico (cp313t causa _Py_MergeZeroLocalRefcount)
import subprocess as sp, shutil
shutil.rmtree(str(TARGET / "psutil"), ignore_errors=True)
for d in TARGET.glob("psutil-*.dist-info"):
    shutil.rmtree(str(d), ignore_errors=True)
data = fetch("https://pypi.org/pypi/psutil/7.0.0/json")
for f in data["urls"]:
    n = f["filename"]
    if n.endswith(".whl") and "abi3" in n and "manylinux" in n and "x86_64" in n:
        out = WHEELS / n
        print(f"  psutil==7.0.0 (abi3)", flush=True)
        sp.check_call(["curl", "-fsSL", "--retry", "3", "--retry-delay", "2", "-o", str(out), f["url"]])
        sp.check_call(["unzip", "-q", "-o", str(out), "-d", str(TARGET)])
        out.unlink(missing_ok=True)
        break

if failed:
    print(f"AVISOS: falharam {failed}", flush=True)
PY

    rm -rf "$ROOT/wheels"
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
