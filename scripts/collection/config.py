"""Shared constants, UI helpers, and base config for collection generation."""

import json
import os
import sys
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Project root ─────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_FILE = PROJECT_ROOT / "ZapUnlocked.collection.json"

# ── Fix Windows console encoding for Unicode ─────────────────────────────
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── UI Style (matching scripts/lib/common.sh / common.ps1) ──────────────
_PURPLE = "\033[38;2;139;61;255m"
_GREEN  = "\033[38;2;66;194;146m"
_YELLOW = "\033[38;2;245;158;11m"
_RED    = "\033[38;2;239;68;68m"
_GRAY   = "\033[38;2;107;114;128m"
_WHITE  = "\033[38;2;233;213;255m"
_RESET  = "\033[0m"

_START_TIME = time.time()

def _elapsed() -> str:
    diff = time.time() - _START_TIME
    mins = int(diff // 60)
    secs = int(diff % 60)
    return f"{mins}m{secs}s" if mins else f"{secs}s"

def ui_banner():
    """Print ZapUnlocked ASCII banner (purple)."""
    print("")
    for line in [
        r"███████╗ █████╗ ██████╗ ██╗   ██╗███╗   ██╗██╗      ██████╗  ██████╗██╗  ██╗███████╗██████╗        █████╗ ██████╗ ██╗",
        r"╚══███╔╝██╔══██╗██╔══██╗██║   ██║████╗  ██║██║     ██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗      ██╔══██╗██╔══██╗██║",
        r"  ███╔╝ ███████║██████╔╝██║   ██║██╔██╗ ██║██║     ██║   ██║██║     █████╔╝ █████╗  ██║  ██║█████╗███████║██████╔╝██║",
        r" ███╔╝  ██╔══██║██╔═══╝ ██║   ██║██║╚██╗██║██║     ██║   ██║██║     ██╔═██╗ ██╔══╝  ██║  ██║╚════╝██╔══██║██╔═══╝ ██║",
        r"███████╗██║  ██║██║     ╚██████╔╝██║ ╚████║███████╗╚██████╔╝╚██████╗██║  ██╗███████╗██████╔╝      ██║  ██║██║     ██║",
        r"╚══════╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═════╝       ╚═╝  ╚═╝╚═╝     ╚═╝",
    ]:
        print(f"{_PURPLE}{line}{_RESET}")
    print("")

def ui_tags(icon: str, label: str, os_label: str = ""):
    """Print PY version + task tags (like common.sh ui_tags)."""
    py = f"{sys.version_info.major}.{sys.version_info.minor}"
    tag_py  = f"{_PURPLE}[{_RESET}PY {py}{_PURPLE}]{_RESET}"
    tag_icon = f"{_PURPLE}[{_RESET}{icon} {label}{_PURPLE}]{_RESET}"
    parts = [tag_py, "  ", tag_icon]
    if os_label:
        parts += ["  ", f"{_PURPLE}[{_RESET}{os_label}{_PURPLE}]{_RESET}"]
    print("".join(parts))

def ui_sep():
    """Print a separator line."""
    print(f"{_GRAY}{'─' * 68}{_RESET}")

def ui_task(label: str):
    """Print a task section header."""
    print("")
    print(f"{_WHITE}  {label}{_RESET}")

def ui_info(msg: str):  print(f"  {_PURPLE}◉{_RESET} {msg}")
def ui_ok(msg: str):    print(f"  {_GREEN}✓{_RESET} {msg}")
def ui_warn(msg: str):  print(f"  {_YELLOW}⚠{_RESET} {msg}")
def ui_err(msg: str):   print(f"  {_RED}✖{_RESET} {msg}")
def ui_step(msg: str):  print(f"  {_GRAY}·{_RESET} {msg}")

def ui_footer(msg: str):
    """Print a footer with elapsed time."""
    print("")
    print(f"{_GREEN}✓{_RESET} {msg}  ({_elapsed()})")
    print("")

# ── Collection variables (Postman v2.1 / Insomnia) ─────────────────────
COLLECTION_VARS = [
    {"key": "BASE_URL",      "value": "http://localhost:8300",  "type": "default"},
    {"key": "API_KEY",       "value": "",                        "type": "secret"},
    {"key": "PHONE",         "value": "",                        "type": "default"},
    {"key": "WEBHOOK_NAME",  "value": "my-webhook",              "type": "default"},
    {"key": "IP",            "value": "192.168.1.100",           "type": "default"},
]

# ── Fields to SKIP in generated examples (too verbose / rarely used) ─────
SKIP_FIELDS = set()
