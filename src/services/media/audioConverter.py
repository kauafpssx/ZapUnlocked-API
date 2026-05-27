import asyncio
import re
import subprocess
from pathlib import Path
from src.utils.logger import logger
from src.services.media.utils import get_ffmpeg_path


async def convert_audio(input_path: str, target_format: str = "ogg") -> tuple[str, int]:
    """
    Converte áudio para diferentes formatos para teste de compatibilidade iOS.
    Formatos suportados: ogg (opus), mp3, wav, m4a (aac)
    """
    path = Path(input_path)
    output_path = path.with_suffix(f".{target_format}")

    logger.info(f"🔄 Convertendo áudio para {target_format.upper()}: {path.name}")

    # Configurações baseadas no formato
    if target_format == "ogg":
        cmd = [
            "ffmpeg", "-i", str(input_path),
            "-vn", "-ac", "1", "-ar", "48000",
            "-acodec", "libopus", "-b:a", "64k", "-vbr", "on", "-compression_level", "10",
            "-f", "ogg", "-avoid_negative_ts", "make_zero", "-y", str(output_path)
        ]
    elif target_format == "mp3":
        cmd = [
            "ffmpeg", "-i", str(input_path),
            "-vn", "-acodec", "libmp3lame", "-q:a", "2", "-y", str(output_path)
        ]
    elif target_format == "wav":
        cmd = [
            "ffmpeg", "-i", str(input_path),
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1", "-y", str(output_path)
        ]
    elif target_format == "m4a":
        cmd = [
            "ffmpeg", "-i", str(input_path),
            "-vn",
            "-acodec", "aac",
            "-b:a", "64k",
            "-threads", "0",
            "-movflags", "+faststart",
            "-f", "mp4",
            "-y", "--", str(output_path)
        ]
    else:
        raise ValueError(f"Formato {target_format} não suportado.")

    try:
        def run_ffmpeg():
            resolved = [get_ffmpeg_path()] + cmd[1:]
            return subprocess.run(resolved, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        result = await asyncio.to_thread(run_ffmpeg)

        if result.returncode != 0:
            logger.error(f"❌ Erro FFmpeg ({result.returncode}): {result.stderr}")
            raise Exception(f"FFmpeg error: {result.stderr}")

        # Duração via ffmpeg -i (stderr) — não depende de ffprobe
        def get_duration() -> int:
            probe = subprocess.run(
                [get_ffmpeg_path(), "-i", str(output_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", probe.stderr)
            if match:
                h, m, s = int(match.group(1)), int(match.group(2)), float(match.group(3))
                return int(h * 3600 + m * 60 + s)
            return 0

        try:
            duration = await asyncio.to_thread(get_duration)
        except Exception:
            duration = 0
        logger.info(f"✅ Conversão concluída! Duração: {duration}s")

        return str(output_path), duration
    except Exception as e:
        logger.error(f"❌ Falha na conversão para {target_format}: {str(e)}")
        raise e


async def convert_to_m4a(input_path: str) -> tuple[str, int]:
    return await convert_audio(input_path, "m4a")


async def convert_to_ogg(input_path: str) -> tuple[str, int]:
    return await convert_audio(input_path, "m4a")
