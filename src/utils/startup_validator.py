import sys
import os
import socket
import importlib

# (pip_name, import_name)
_REQUIRED = [
    ("fastapi",          "fastapi"),
    ("uvicorn",          "uvicorn"),
    ("pydantic",         "pydantic"),
    ("python-dotenv",    "dotenv"),
    ("neonize",          "neonize"),
    ("Pillow",           "PIL"),
    ("python-magic",     "magic"),
    ("ffmpeg-python",    "ffmpeg"),
    ("requests",         "requests"),
    ("httpx",            "httpx"),
    ("qrcode",           "qrcode"),
    ("loguru",           "loguru"),
    ("psutil",           "psutil"),
]

_OPTIONAL = [
    ("imageio-ffmpeg",   "imageio_ffmpeg"),
]


def validate_dependencies() -> None:
    missing = []
    for pip_name, import_name in _REQUIRED:
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(pip_name)

    for pip_name, import_name in _OPTIONAL:
        try:
            importlib.import_module(import_name)
        except ImportError:
            pass

    if missing:
        lines = [
            "",
            "=" * 60,
            "❌  DEPENDÊNCIAS FALTANDO — o app não pode iniciar.",
            "=" * 60,
        ]
        for pkg in missing:
            lines.append(f"  • {pkg}")
        lines += [
            "",
            "Execute para instalar tudo:",
            "  .venv/bin/pip install -r requirements.txt",
            "",
            "Depois inicie com:",
            "  bash scripts/run/run.sh",
            "=" * 60,
            "",
        ]
        print("\n".join(lines), file=sys.stderr)
        sys.exit(1)


def is_alwaysdata() -> bool:
    """
    Detecta se estamos rodando em um servidor Alwaysdata.
    Usado pelo install.sh e pelo warm_up_ffmpeg para decidir
    se instala imageio-ffmpeg (normal) ou baixa ffmpeg estatico.
    """
    # 1. Variavel de ambiente tipica do Alwaysdata
    if os.getenv("ALWAYSDATA_ACCOUNT"):
        return True
    # 2. Arquivo marcador
    if os.path.isfile("/etc/alwaysdata"):
        return True
    # 3. Hostname termina com alwaysdata.net ou alwaysdata.com
    try:
        fqdn = socket.getfqdn().lower()
        if fqdn.endswith((".alwaysdata.net", ".alwaysdata.com")):
            return True
    except Exception:
        pass
    return False
