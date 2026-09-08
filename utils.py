import shutil
from pathlib import Path
from config import FFMPEG_FALLBACK_DIRS

def _resolve_ffmpeg_dir() -> str | None:
    """Retourne le chemin vers FFmpeg s'il est dans les dossiers de fallback, sinon None."""
    system_ffmpeg = shutil.which("ffmpeg")
    system_ffprobe = shutil.which("ffprobe")
    if system_ffmpeg and system_ffprobe:
        return None

    for path in FFMPEG_FALLBACK_DIRS:
        if (path / "ffmpeg.exe").exists() and (path / "ffprobe.exe").exists():
            return str(path)

    return None

def has_ffmpeg() -> bool:
    """Vérifie si FFmpeg et FFprobe sont disponibles."""
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return True
    return _resolve_ffmpeg_dir() is not None

def is_http_url(value: str) -> bool:
    """Vérifie si une chaîne est une URL HTTP(S)."""
    return value.startswith("http://") or value.startswith("https://")
