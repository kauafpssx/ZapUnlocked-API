import subprocess
import shutil
import sys
from pathlib import Path
from src.utils.logger import logger
from src.utils.startup_validator import is_alwaysdata

_ffmpeg_path: str | None = None
_ffprobe_path: str | None = None

_WINDOWS_EXTRA_PATHS = [
    r"C:\ffmpeg\bin",
    r"C:\Program Files\ffmpeg\bin",
    r"C:\Program Files (x86)\ffmpeg\bin",
    r"C:\ProgramData\chocolatey\bin",
]


def get_ffmpeg_path() -> str:
    global _ffmpeg_path
    if _ffmpeg_path is not None:
        return _ffmpeg_path

    # 1. imageio-ffmpeg: bundled binary, works without system install
    try:
        import imageio_ffmpeg
        _ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        logger.debug(f"✅ ffmpeg via imageio-ffmpeg: {_ffmpeg_path}")
        return _ffmpeg_path
    except Exception:
        pass

    # 2. PATH do sistema
    found = shutil.which("ffmpeg")
    if found:
        _ffmpeg_path = found
        return _ffmpeg_path

    # 3. $HOME/.local/bin (auto-installed by install.sh)
    home_local = Path.home() / ".local" / "bin" / "ffmpeg"
    if home_local.exists():
        _ffmpeg_path = str(home_local)
        return _ffmpeg_path

    # 4. Caminhos comuns no Windows
    exe = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    for base in _WINDOWS_EXTRA_PATHS:
        candidate = Path(base) / exe
        if candidate.exists():
            _ffmpeg_path = str(candidate)
            return _ffmpeg_path

    raise FileNotFoundError(
        "ffmpeg not found. Run: pip install imageio-ffmpeg "
        "or install ffmpeg manually: https://ffmpeg.org/download.html"
    )


def get_ffprobe_path() -> str:
    global _ffprobe_path
    if _ffprobe_path is not None:
        return _ffprobe_path

    # Try the same directory as ffmpeg (binaries are usually co-located)
    try:
        ffmpeg = get_ffmpeg_path()
        candidate = Path(ffmpeg).parent / ("ffprobe.exe" if sys.platform == "win32" else "ffprobe")
        if candidate.exists():
            _ffprobe_path = str(candidate)
            return _ffprobe_path
    except Exception:
        pass

    found = shutil.which("ffprobe")
    if found:
        _ffprobe_path = found
        return _ffprobe_path

    exe = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"
    for base in _WINDOWS_EXTRA_PATHS:
        candidate = Path(base) / exe
        if candidate.exists():
            _ffprobe_path = str(candidate)
            return _ffprobe_path

    raise FileNotFoundError(
        "ffprobe not found. Run: pip install imageio-ffmpeg "
        "or install ffmpeg manually: https://ffmpeg.org/download.html"
    )


def warm_up_ffmpeg() -> None:
    """Resolve and cache the ffmpeg path at startup. Should be called once."""
    try:
        path = get_ffmpeg_path()
        logger.info(f"🎬 ffmpeg ready: {path}")
    except FileNotFoundError as e:
        hint = ""
        if is_alwaysdata():
            hint = " Run: bash scripts/install/install.sh (downloads static ffmpeg to ~/.local/bin)"
        logger.warning(f"⚠️ {e}{hint}")


def run_ffmpeg_sync(cmd):
    """Run FFmpeg synchronously for use with asyncio.to_thread. Auto-resolves 'ffmpeg' to the cached path."""
    if cmd and cmd[0] == "ffmpeg":
        cmd = [get_ffmpeg_path()] + cmd[1:]
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )


def cleanup(file_path: str):
    if file_path:
        path = Path(file_path)
        if path.exists() and path.is_file():
            try:
                path.unlink()
                logger.info(f"🗑️ Temp file removed: {path.name}")
            except Exception as e:
                logger.error(f"⚠️ Failed to remove temp file: {str(e)}")


def get_file_size(file_path: str) -> int:
    path = Path(file_path)
    if path.exists() and path.is_file():
        return path.stat().st_size
    return 0
