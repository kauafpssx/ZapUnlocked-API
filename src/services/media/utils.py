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

    # 1. imageio-ffmpeg: binário embutido, funciona sem instalação
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

    # 3. $HOME/.local/bin (instalação automática do install.sh)
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
        "ffmpeg não encontrado. Execute: pip install imageio-ffmpeg "
        "ou instale o ffmpeg manualmente: https://ffmpeg.org/download.html"
    )


def get_ffprobe_path() -> str:
    global _ffprobe_path
    if _ffprobe_path is not None:
        return _ffprobe_path

    # Tenta o mesmo diretório do ffmpeg (binários normalmente ficam juntos)
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
        "ffprobe não encontrado. Execute: pip install imageio-ffmpeg "
        "ou instale o ffmpeg manualmente: https://ffmpeg.org/download.html"
    )


def warm_up_ffmpeg() -> None:
    """Resolve e cacheia o path do ffmpeg no startup. Deve ser chamado uma vez."""
    try:
        path = get_ffmpeg_path()
        logger.info(f"🎬 ffmpeg pronto: {path}")
    except FileNotFoundError as e:
        hint = ""
        if is_alwaysdata():
            hint = " Rode: bash scripts/install/install.sh (baixa ffmpeg estatico em ~/.local/bin)"
        logger.warning(f"⚠️ {e}{hint}")


def run_ffmpeg_sync(cmd):
    """
    Executa o FFmpeg de forma síncrona para ser usado com asyncio.to_thread.
    Substitui automaticamente 'ffmpeg' pelo caminho resolvido.
    """
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
                logger.info(f"🗑️ Arquivo temporário removido: {path.name}")
            except Exception as e:
                logger.error(f"⚠️ Erro ao remover arquivo temporário: {str(e)}")


def get_file_size(file_path: str) -> int:
    path = Path(file_path)
    if path.exists() and path.is_file():
        return path.stat().st_size
    return 0
