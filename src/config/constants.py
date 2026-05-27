import os
import sys
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

# Ensure directories exist
auth_dir.mkdir(parents=True, exist_ok=True)
data_dir.mkdir(parents=True, exist_ok=True)
temp_dir.mkdir(parents=True, exist_ok=True)

print(f"📁 Diretório de autenticação: {auth_dir}")
print(f"📁 Diretório de dados (chats): {data_dir}")

PORT = int(os.getenv("PORT", 3000))
API_KEY = os.getenv("API_KEY")
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET")

AUTH_DIR = str(auth_dir)
DATA_DIR = str(data_dir)
TEMP_DIR = str(temp_dir)

WHATSAPP_CONFIG = {
    # Placeholder for config that matches Baileys behavior
}
RECONNECT_DELAY = 5
