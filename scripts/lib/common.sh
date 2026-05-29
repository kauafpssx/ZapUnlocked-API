#!/bin/bash
#
# ZapUnlocked API — Common UI library
# Provides reusable UI components using Gum.
# Source this file in any script under scripts/.
#

set -e

# ── Paths ──────────────────────────────────────────────────────────────
_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$_LIB_DIR/../.." && pwd)"

# ── Gum auto-install ──────────────────────────────────────────────────
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
    echo "gum instalado"
fi

# ── Time tracking ─────────────────────────────────────────────────────
__START_TIME=$(date +%s%N 2>/dev/null || date +%s 2>/dev/null || echo 0)

__elapsed() {
    local now=$(date +%s%N 2>/dev/null || date +%s 2>/dev/null || echo 0)
    local diff=$(( (now - __START_TIME) / 1000000000 ))
    local min=$(( diff / 60 ))
    local sec=$(( diff % 60 ))
    [ "$min" -gt 0 ] && echo "${min}m${sec}s" || echo "${sec}s"
}

# ── Icon set ─────────────────────────────────────────────────────────
ICON_RUN="▶"
ICON_INSTALL="⬇"
ICON_REMOVE="✕"
ICON_GEN="⚙"

# ── System info ───────────────────────────────────────────────────────
__ram() {
    if command -v free &>/dev/null; then
        free -m 2>/dev/null | awk '/^Mem:/{printf "%d", $3/$2 * 100}'
    else
        echo "?"
    fi
}

__cpu() {
    if [[ "$OSTYPE" != "darwin"* ]] && command -v top &>/dev/null; then
        top -bn1 2>/dev/null | grep -i "cpu(s)" | awk '{printf "%d", 100 - $8}' || echo "?"
    else
        echo "?"
    fi
}

__py() {
    command -v python3 &>/dev/null && python3 --version 2>&1 | awk '{print $2}' || echo "N/A"
}

__up() {
    __elapsed
}

__alwaysdata_check() {
    [ -n "$ALWAYSDATA_ACCOUNT" ] && return 0
    [ -f /etc/alwaysdata ] && return 0
    hostname -f 2>/dev/null | grep -qi 'alwaysdata' && return 0
    uname -r 2>/dev/null | grep -qi 'alwaysdata' && return 0
    return 1
}

# ── UI Components ──────────────────────────────────────────────────────

ui_banner() {
    local P='\e[38;2;139;61;255m'
    local R='\e[0m'
    echo ""
    echo -e "${P}███████╗ █████╗ ██████╗ ██╗   ██╗███╗   ██╗██╗      ██████╗  ██████╗██╗  ██╗███████╗██████╗        █████╗ ██████╗ ██╗${R}"
    echo -e "${P}╚══███╔╝██╔══██╗██╔══██╗██║   ██║████╗  ██║██║     ██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗      ██╔══██╗██╔══██╗██║${R}"
    echo -e "${P}  ███╔╝ ███████║██████╔╝██║   ██║██╔██╗ ██║██║     ██║   ██║██║     █████╔╝ █████╗  ██║  ██║█████╗███████║██████╔╝██║${R}"
    echo -e "${P} ███╔╝  ██╔══██║██╔═══╝ ██║   ██║██║╚██╗██║██║     ██║   ██║██║     ██╔═██╗ ██╔══╝  ██║  ██║╚════╝██╔══██║██╔═══╝ ██║${R}"
    echo -e "${P}███████╗██║  ██║██║     ╚██████╔╝██║ ╚████║███████╗╚██████╔╝╚██████╗██║  ██╗███████╗██████╔╝      ██║  ██║██║     ██║${R}"
    echo -e "${P}╚══════╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═════╝       ╚═╝  ╚═╝╚═╝     ╚═╝${R}"
    echo ""
}

ui_tags() {
    local icon=$1 label=$2 os_label=$3
    local args=()
    args+=("$(gum style --border rounded --padding "0 1" --foreground "#C084FC" "PY $(__py)")")
    args+=("  ")
    args+=("$(gum style --border rounded --padding "0 1" --foreground "#8B3DFF" --bold "${icon} ${label}")")
    if [ -n "$os_label" ]; then
        args+=("  ")
        args+=("$(gum style --border rounded --padding "0 1" --foreground "#8B3DFF" "$os_label")")
    fi
    gum join --horizontal "${args[@]}"
}

ui_sep() {
    local line=""
    for ((i=0; i<68; i++)); do line+="─"; done
    gum style --foreground "#4B5563" "$line"
}

ui_task() {
    local label=$1
    echo ""
    gum style --foreground "#E9D5FF" --bold "  ${label}"
}

# ── Header state (for in-place refresh) ──────────────────────────────
__header_icon=""
__header_label=""
__header_os=""

ui_init_header() {
    __header_icon=$1
    __header_label=$2
    __header_os=$3
}

ui_refresh_header() {
    echo -ne "\e[5A\e[J"
    local args=()
    args+=("$(gum style --border rounded --padding "0 1" --foreground "#C084FC" "PY $(__py)")")
    args+=("  ")
    args+=("$(gum style --border rounded --padding "0 1" --foreground "#8B3DFF" --bold "${__header_icon} ${__header_label}")")
    if [ -n "$__header_os" ]; then
        args+=("  ")
        args+=("$(gum style --border rounded --padding "0 1" --foreground "#8B3DFF" "$__header_os")")
    fi
    gum join --horizontal "${args[@]}"
    ui_sep
}

ui_log_info()  { echo -e "  \e[38;2;168;85;247m◉\e[0m $1"; }
ui_log_ok()    { echo -e "  \e[38;2;66;194;146m✓\e[0m $1"; }
ui_log_warn()  { echo -e "  \e[38;2;245;158;11m⚠\e[0m $1"; }
ui_log_err()   { echo -e "  \e[38;2;239;68;68m✖\e[0m $1"; }
ui_log_step()  { echo -e "  \e[38;2;107;114;128m·\e[0m $1"; }

ui_footer() {
    echo ""
    gum style \
        --foreground "#42C292" --border-foreground "#8B3DFF" \
        --border rounded --align center \
        --width 46 --padding "0 1" \
        "✓ $1  ($(__elapsed))"
    echo ""
}
