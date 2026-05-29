import sys
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
