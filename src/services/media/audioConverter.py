import asyncio
import re
import subprocess
from pathlib import Path
from src.utils.logger import logger
from src.services.media.utils import get_ffmpeg_path


async def convert_audio(input_path: str, target_format: str = "ogg") -> tuple[str, int]:
    """
    Convert audio to different formats for iOS compatibility.
    Supported formats: ogg (opus), mp3, wav, m4a (aac)
    """
    path = Path(input_path)
    output_path = path.with_suffix(f".{target_format}")

    logger.info(f"🔄 Converting audio to {target_format.upper()}: {path.name}")

    # Format-specific settings
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
        raise ValueError(f"Unsupported format: {target_format}.")

    try:
        def run_ffmpeg():
            resolved = [get_ffmpeg_path()] + cmd[1:]
            return subprocess.run(resolved, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        result = await asyncio.to_thread(run_ffmpeg)

        if result.returncode != 0:
            logger.error(f"❌ FFmpeg error ({result.returncode}): {result.stderr}")
            raise Exception(f"FFmpeg error: {result.stderr}")

        # Get duration from ffmpeg -i (stderr) — no ffprobe dependency
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
        logger.info(f"✅ Conversion complete. Duration: {duration}s")

        return str(output_path), duration
    except Exception as e:
        logger.error(f"❌ Audio conversion to {target_format} failed: {str(e)}")
        raise e

