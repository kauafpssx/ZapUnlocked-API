import os
import sys
import socket
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# Auth directory
default_auth_dir = BASE_DIR / "auth_info"

# System volume detection (Railway/Docker)
system_volume_path = Path("/data")
has_system_volume = sys.platform != "win32" and system_volume_path.exists()

default_data_dir = system_volume_path if has_system_volume else Path.cwd() / "data"
data_dir_env = os.getenv("DATA_DIR")
data_dir = Path(data_dir_env) if data_dir_env else default_data_dir

default_auth_from_sys = system_volume_path / "auth_info" if has_system_volume else default_auth_dir
auth_dir_env = os.getenv("AUTH_DIR")
auth_dir = Path(auth_dir_env) if auth_dir_env else default_auth_from_sys

temp_dir = BASE_DIR / "temp_media"

PORT = int(os.getenv("PORT", 8300))
API_KEY = os.getenv("API_KEY")
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET")

AUTH_DIR = str(auth_dir)
DATA_DIR = str(data_dir)
TEMP_DIR = str(temp_dir)

RECONNECT_DELAY = 5


def _is_alwaysdata() -> bool:
    if os.getenv("ALWAYSDATA_ACCOUNT"):
        return True
    if os.path.exists("/etc/alwaysdata"):
        return True
    try:
        if "alwaysdata" in socket.getfqdn().lower():
            return True
    except Exception:
        pass
    try:
        uname = subprocess.check_output(["uname", "-r"], timeout=1).decode().lower()
        if "alwaysdata" in uname:
            return True
    except Exception:
        pass
    return False


IS_ALWAYSDATA = _is_alwaysdata()
MAX_UPLOAD_SIZE_MB = 500 if IS_ALWAYSDATA else int(os.getenv("MAX_UPLOAD_SIZE_MB", "500"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

CLEANUP_MAX_AGE_DAYS = int(os.getenv("CLEANUP_MAX_AGE_DAYS", "7"))
CLEANUP_MAX_SIZE_MB = int(os.getenv("CLEANUP_MAX_SIZE_MB", "500"))
