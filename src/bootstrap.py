"""
Bootstrap — run once at process start, BEFORE importing app framework.

Handles platform-specific setup, path injection, dependency validation,
and deployment environment checks.
"""

import os
import sys
import asyncio
from pathlib import Path


def bootstrap():
    """
    Prepare the runtime environment for the ZapUnlocked API.

    Must be called from main.py after venv auto-activation (if any)
    and before any framework imports (FastAPI, uvicorn, etc.).
    """
    _this_dir = Path(__file__).resolve().parent.parent  # project root

    # ── libmagic on Windows ──────────────────────────────────
    if sys.platform == "win32":
        # Try to locate the magic/libmagic directory in site-packages.
        # We check several strategies because sys.executable differs
        # depending on whether uvicorn runs with --reload or not.
        _candidates = []

        # Strategy A: derive from sys.executable (venv/bin/python)
        _candidates.append(
            Path(sys.executable).parent.parent
            / "Lib" / "site-packages" / "magic" / "libmagic"
        )

        # Strategy B: walk site-packages directly
        try:
            import site
            for sp in site.getsitepackages():
                _candidates.append(Path(sp) / "magic" / "libmagic")
        except Exception:
            pass

        # Strategy C: look relative to this file (src/bootstrap.py)
        _candidates.append(
            _this_dir.parent / "Lib" / "site-packages" / "magic" / "libmagic"
        )

        _libmagic_dir = None
        for candidate in _candidates:
            if candidate.exists():
                _libmagic_dir = candidate
                break

        if _libmagic_dir:
            os.environ["PATH"] = str(_libmagic_dir) + os.pathsep + os.environ.get("PATH", "")
            try:
                os.add_dll_directory(str(_libmagic_dir))
            except AttributeError:
                pass  # Python < 3.8

    # ── Legacy .local_lib (lowest priority) ──────────────────
    _local_lib = _this_dir / ".local_lib"
    if _local_lib.is_dir():
        sys.path.insert(0, str(_local_lib))

    # ── vendor (highest priority) ────────────────────────────
    _vendor_dir = _this_dir / "vendor"
    if _vendor_dir.is_dir():
        sys.path.insert(0, str(_vendor_dir))

    # ── Dependency validation ────────────────────────────────
    from src.utils.startup_validator import is_alwaysdata, validate_dependencies

    validate_dependencies()

    # ── Alwaysdata guard ─────────────────────────────────────
    if is_alwaysdata() and sys.stdin.isatty():
        _print_alwaysdata_banner()
        sys.exit(1)

    # ── Windows event loop policy ────────────────────────────
    if sys.platform == "win32":
        try:
            if not isinstance(
                asyncio.get_event_loop_policy(),
                asyncio.WindowsProactorEventLoopPolicy,
            ):
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except Exception:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def _print_alwaysdata_banner() -> None:
    """Print a styled message explaining how to register this app as an Alwaysdata Service."""
    msg = (
        "\n"
        "╔══════════════════════════════════════════════════════╗\n"
        "║  ⚠  ALWAYSDATA — SERVICE REQUIRED                   ║\n"
        "╠══════════════════════════════════════════════════════╣\n"
        "║                                                      ║\n"
        "║  Port 8300-8499 is only accessible after             ║\n"
        "║  registering this app as a Service in the panel.     ║\n"
        "║                                                      ║\n"
        "║  Advanced › Services › Add a service                 ║\n"
        "║                                                      ║\n"
        "╠══════════════════════════════════════════════════════╣\n"
        "║  Field           Value                               ║\n"
        "║  ─────────────   ─────────────────────────────────   ║\n"
        "║  Name            ZapUnlocked-API                     ║\n"
        "║  Command         bash scripts/run/run.sh             ║\n"
        "║  Working dir     ZapUnlocked-API                     ║\n"
        "║  Env vars        PORT=8300                           ║\n"
        "║                                                      ║\n"
        "╚══════════════════════════════════════════════════════╝\n"
    )

    try:
        import subprocess
        subprocess.run(
            [
                "gum",
                "style",
                "--foreground", "214",
                "--border-foreground", "214",
                "--border", "rounded",
                "--align", "left",
                "--width", "58",
                "--padding", "1 2",
                "⚠  ALWAYSDATA — SERVICE REQUIRED\n",
                "Port 8300-8499 is only accessible after",
                "registering this app as a Service in the panel.\n",
                "Advanced › Services › Add a service\n",
                "──────────────────────────────────────────────",
                "Field           Value",
                "─────────────   ─────────────────────────────",
                "Name            ZapUnlocked-API",
                "Command         bash scripts/run/run.sh",
                "Working dir     ZapUnlocked-API",
                "Env vars        PORT=8300",
            ],
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        print(msg, file=sys.stderr)
