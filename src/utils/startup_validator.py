import sys
import os
import socket
from pathlib import Path
import importlib.util

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
        if importlib.util.find_spec(import_name) is None:
            missing.append(pip_name)

    if missing:
        install_cmd = (
            "bash scripts/install/install.sh"
            if is_alwaysdata()
            else ".venv/bin/pip install -r requirements.txt"
        )
        lines = [
            "",
            "=" * 60,
            "❌  MISSING DEPENDENCIES — the app cannot start.",
            "=" * 60,
        ]
        for pkg in missing:
            lines.append(f"  • {pkg}")
        lines += [
            "",
            "Run to install everything:",
            f"  {install_cmd}",
            "",
            "Then start with:",
            "  bash scripts/run/run.sh",
            "=" * 60,
            "",
        ]
        print("\n".join(lines), file=sys.stderr)
        sys.exit(1)


def is_alwaysdata() -> bool:
    """
    Detect if running on an Alwaysdata server.
    Used by install.sh, warm_up_ffmpeg and direct execution blocking.
    """
    # 1. Typical Alwaysdata environment variable
    if os.getenv("ALWAYSDATA_ACCOUNT"):
        return True
    # 2. Marker file
    if os.path.isfile("/etc/alwaysdata"):
        return True
    # 3. Hostname ends with alwaysdata.net or alwaysdata.com
    try:
        fqdn = socket.getfqdn().lower()
        if fqdn.endswith((".alwaysdata.net", ".alwaysdata.com")):
            return True
    except Exception:
        pass
    # 4. Contents of /etc/hostname
    try:
        if Path("/etc/hostname").read_text().strip().endswith(".alwaysdata.net"):
            return True
    except Exception:
        pass
    # 5. $HOME/admin directory (created by Alwaysdata for service logs)
    try:
        if Path(os.path.expanduser("~/admin/logs/services")).is_dir():
            return True
    except Exception:
        pass
    # 6. Kernel version contains "alwaysdata" (e.g.: 6.18.30-alwaysdata)
    try:
        if "alwaysdata" in os.uname().release.lower():
            return True
    except Exception:
        pass
    return False
