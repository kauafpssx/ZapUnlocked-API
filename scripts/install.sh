#!/bin/bash

# ======================================================
#    ZapUnlocked-API - Linux Global Installer
# ======================================================

echo "======================================================"
echo "   ZapUnlocked-API - Linux Global Installer"
echo "======================================================"

# 1. Detect OS and Package Manager
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    OS=$(uname -s)
fi

echo "[i] OS detectado: $OS"

# 2. Check Python 3 and system deps
if [ "$OS" == "macos" ]; then
    if ! command -v brew &> /dev/null; then
        echo "[i] Homebrew nao encontrado. Instalando..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    brew install python libmagic
else
    if ! command -v python3 &> /dev/null; then
        echo "[!] Python3 nao encontrado. Tentando instalar via $OS..."
        
        case $OS in
            ubuntu|debian|raspbian)
                sudo apt-get update
                sudo apt-get install -y python3 python3-pip python3-full libmagic1
                ;;
            fedora|centos|rhel)
                sudo dnf install -y python3 python3-pip file-devel
                ;;
            arch|manjaro)
                sudo pacman -S --noconfirm python python-pip file
                ;;
            alpine)
                sudo apk add --no-cache python3 py3-pip libmagic
                ;;
            *)
                echo "[!] Nao foi possivel detectar o gerenciador de pacotes para $OS."
                echo "[!] Tentando via Flatpak como fallback..."
                if command -v flatpak &> /dev/null; then
                    flatpak install flathub org.python.Python -y
                else
                    echo "[X] Erro: Instale o Python 3.10+ manualmente."
                    exit 1
                fi
                ;;
        esac
    fi
fi

# 3. Install Requirements
echo "[i] Instalando dependencias globais..."
python3 -m pip install --upgrade pip --break-system-packages 2>/dev/null || python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt --break-system-packages 2>/dev/null || python3 -m pip install -r requirements.txt

# 4. Final Run
echo "[V] Setup concluido. Iniciando API..."
python3 main.py
