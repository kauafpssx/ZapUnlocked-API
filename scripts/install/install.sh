#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
cd "$ROOT_DIR"

# ── Detect OS & environment ─────────────────────────────────────────
if [[ "$OSTYPE" == "darwin"* ]]; then OS="macos"
elif [ -f /etc/os-release ]; then . /etc/os-release; OS=$ID
else OS=$(uname -s); fi

_ALWAYSDATA=false; __alwaysdata_check && _ALWAYSDATA=true

if $_ALWAYSDATA; then
    OS_LABEL="Alwaysdata"
elif [[ "$OS" == "macos" ]]; then
    OS_LABEL="macOS"
else
    OS_LABEL="Linux"
fi

# ── Start ──────────────────────────────────────────────────────────────
clear
ui_banner
ui_tags "$ICON_INSTALL" "INSTALL" "$OS_LABEL"
ui_sep
ui_init_header "$ICON_INSTALL" "INSTALL" "$OS_LABEL"

# ── Python ─────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    case $OS in
        macos)
            command -v brew &>/dev/null ||             gum spin --spinner dot --title "Installing Homebrew..." -- \
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            gum spin --spinner dot --title "Installing Python..." -- brew install python
            ;;
        ubuntu|debian|raspbian)
            gum spin --spinner dot --title "Installing Python..." -- \
                sudo apt-get install -y python3 python3-pip python3-full
            ;;
        fedora|centos|rhel)
            gum spin --spinner dot --title "Installing Python..." -- \
                sudo dnf install -y python3 python3-pip
            ;;
        arch|manjaro)
            gum spin --spinner dot --title "Installing Python..." -- \
                sudo pacman -S --noconfirm python python-pip
            ;;
        *)
            ui_log_err "Python not found — install Python 3.10+ manually"
            exit 1
            ;;
    esac
    ui_log_ok "Python installed"
fi

# ── Installation method ──────────────────────────────────────────────
_USE_INTERNAL=false

if $_ALWAYSDATA; then
    _USE_INTERNAL=true
elif [[ "$OS" != "macos" ]]; then
    ui_log_step "Choose installation method:"
    METHOD=$(gum choose \
        "📦 Offline (direct wheels, no venv)" \
        "🐍 pip (via virtual environment)")
    echo ""
    if [[ "$METHOD" == *"Offline"* ]]; then
        _USE_INTERNAL=true
        echo -e "  \e[38;2;66;194;146m✓\e[0m Offline selected"
    else
        echo -e "  \e[38;2;66;194;146m✓\e[0m pip selected"
    fi
fi

# ── Internal method (offline wheels) ─────────────────────────────────
if $_USE_INTERNAL; then
    rm -rf .venv
    SITE_PKG="$ROOT_DIR/vendor"
    rm -rf "$SITE_PKG" "$ROOT_DIR/wheels"
    mkdir -p "$SITE_PKG" "$ROOT_DIR/wheels"

    python3 - "$SITE_PKG" "$ROOT_DIR/wheels" <<'PY'
import json, os, subprocess, sys, urllib.request
from pathlib import Path

TARGET = Path(sys.argv[1])
WHEELS = Path(sys.argv[2])

PKGS = [
    ("fastapi",             "0.115.14", "py3-none-any"),
    ("starlette",           "0.46.2",   "py3-none-any"),
    ("annotated-types",     "0.7.0",    "py3-none-any"),
    ("pydantic-core",       "2.27.2",   "cp313"),
    ("pydantic",            "2.10.0",   "py3-none-any"),
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
    if tag:
        for f in urls:
            n = f["filename"]
            if n.endswith(".whl") and tag in n and "x86_64" in n and ("manylinux" in n or "musllinux" in n):
                return f["url"], n
        for f in urls:
            n = f["filename"]
            if n.endswith(".whl") and tag in n:
                return f["url"], n
    for f in urls:
        n = f["filename"]
        if n.endswith(".whl") and "py3-none-any" in n:
            return f["url"], n
    for f in urls:
        if f["filename"].endswith(".whl"):
            return f["url"], f["filename"]
    raise RuntimeError(f"no wheel: {pkg}=={ver}")

G = '\033[92m'
Y = '\033[93m'
R = '\033[0m'

failed = []
for pkg, ver, tag in PKGS:
    try:
        url, name = pick(pkg, ver, tag)
        out = WHEELS / name
        print(f"  {G}✓{R} {pkg} ({ver})", flush=True)
        subprocess.check_call(["curl", "-fsSL", "--retry", "3", "--retry-delay", "2", "-o", str(out), url])
        subprocess.check_call(["unzip", "-q", "-o", str(out), "-d", str(TARGET)])
        out.unlink(missing_ok=True)
    except Exception as e:
        print(f"  {Y}⚠{R} {pkg} ({ver}): {e}", flush=True)
        failed.append(pkg)

import subprocess as sp, shutil
shutil.rmtree(str(TARGET / "psutil"), ignore_errors=True)
for d in TARGET.glob("psutil-*.dist-info"):
    shutil.rmtree(str(d), ignore_errors=True)
data = fetch("https://pypi.org/pypi/psutil/7.0.0/json")
for f in data["urls"]:
    n = f["filename"]
    if n.endswith(".whl") and "abi3" in n and "manylinux" in n and "x86_64" in n:
        out = WHEELS / n
        print(f"  {G}✓{R} psutil (7.0.0)", flush=True)
        sp.check_call(["curl", "-fsSL", "--retry", "3", "--retry-delay", "2", "-o", str(out), f["url"]])
        sp.check_call(["unzip", "-q", "-o", str(out), "-d", str(TARGET)])
        out.unlink(missing_ok=True)
        break

if failed:
    print(f"  {Y}⚠{R} Failed: {', '.join(failed)}", flush=True)
PY

    rm -rf "$ROOT_DIR/wheels"
    ui_log_ok "Requirements installed"

    # Verify python-magic can load libmagic.so.1 (needed by neonize)
    _MAGIC_OK=false
    PYTHONPATH="$SITE_PKG" python3 -c "import magic" &>/dev/null && _MAGIC_OK=true

    if ! $_MAGIC_OK; then
        # Search common Debian/Ubuntu library paths
        _LIBMAGIC_DIR=""
        for _d in /usr/lib/x86_64-linux-gnu /usr/lib/aarch64-linux-gnu /usr/lib /usr/local/lib; do
            if [ -f "$_d/libmagic.so.1" ]; then
                _LIBMAGIC_DIR="$_d"
                break
            fi
        done

        if [ -n "$_LIBMAGIC_DIR" ]; then
            # Persist so run.sh and the app can pick it up
            grep -q "^LD_LIBRARY_PATH=" "$ROOT_DIR/.env" 2>/dev/null \
                || echo "LD_LIBRARY_PATH=$_LIBMAGIC_DIR" >> "$ROOT_DIR/.env"
            export LD_LIBRARY_PATH="$_LIBMAGIC_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
            PYTHONPATH="$SITE_PKG" python3 -c "import magic" &>/dev/null \
                && ui_log_ok "libmagic found at $_LIBMAGIC_DIR" \
                || ui_log_warn "libmagic found at $_LIBMAGIC_DIR but magic still fails — check installation"
        else
            ui_log_warn "libmagic not found — run: sudo apt-get install libmagic1"
        fi
    else
        ui_log_ok "python-magic OK"
    fi

    if ! command -v ffmpeg &>/dev/null; then
        TMP_DIR=$(mktemp -d "$HOME/.ffmpeg_extract_XXXXX")
        gum spin --spinner dot --title "Downloading static ffmpeg (~120 MB)..." -- \
            bash -c "curl -fsSL 'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz' | tar -xJ -C '$TMP_DIR'" || exit 1
        find "$TMP_DIR" -name 'ffmpeg' -type f -exec mv {} "$HOME/.local/bin/ffmpeg" \;
        find "$TMP_DIR" -name 'ffprobe' -type f -exec mv {} "$HOME/.local/bin/ffprobe" \;
        rm -rf "$TMP_DIR"
        chmod +x "$HOME/.local/bin/ffmpeg" "$HOME/.local/bin/ffprobe"
        ui_log_ok "ffmpeg installed"
    else
        ui_log_ok "ffmpeg already on system"
    fi

# ── Standard pip method ──────────────────────────────────────────────
else
    python3 -m venv .venv 2>/dev/null || {
        ui_log_err "Failed to create virtual environment"
        exit 1
    }
    ui_log_ok "Virtual environment created"
    _PIP=.venv/bin/python -m pip
    $_PIP install --upgrade pip -q

    gum spin --spinner dot --title "Installing requirements..." -- \
        $_PIP install -r requirements.txt --no-cache-dir -q || {
        ui_log_err "Failed to install requirements"
        exit 1
    }
    ui_log_ok "Requirements installed"
fi

# ── Generate env ────────────────────────────────────────────────────────
ui_sep
echo ""
if gum confirm "Generate .env file now?" --default=false --affirmative "Yes" --negative "No"; then
    bash scripts/generate-env/generate-env.sh
    exit 0
fi

# ── Done ───────────────────────────────────────────────────────────────
ui_sep
ui_footer "Installation complete!"
