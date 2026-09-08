import os
import re
import shutil
from typing import Any
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yt_dlp

from config import (
    VIDEO_EXTENSIONS,
    AUDIO_EXTENSIONS,
    VIDEO_OUTPUT_FORMATS,
    AUDIO_OUTPUT_FORMATS,
    VIDEO_QUALITIES,
    LANGUAGES,
    normalize_language,
    detect_language_from_url,
)
from utils import _resolve_ffmpeg_dir

IGNORED_EXTENSIONS = {".part", ".ytdl", ".jpg", ".jpeg", ".png", ".webp", ".description"}
VALID_DOWNLOAD_TYPES = {"audio", "video"}
CONTAINER_SEGMENTS = {"anime", "watch", "video", "videos", "embed", "episode", "show"}

# ── Backward-compat : map anciennes clés de qualité vers VIDEO_QUALITIES ─────
_LEGACY_QUALITY_MAP = {
    "best": "best",
    "ultra": "2160p",
    "qhd": "1440p",
    "high": "1080p",
    "medium": "720p",
    "low": "480p",
    "360": "360p",
    "240": "240p",
}


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "media"


def _derive_series_slug(parsed_url) -> str:
    raw_segments = [segment for segment in parsed_url.path.split("/") if segment.strip()]
    segments = [_slugify(segment) for segment in raw_segments if _slugify(segment)]
    if not segments:
        return "remote"
    if len(segments) >= 2 and segments[0] in CONTAINER_SEGMENTS:
        return segments[1]
    return segments[-1]


def _build_output_folder(url: str, base_output_path: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace("www.", "") or "remote"

    if domain in {"youtube.com", "m.youtube.com", "youtu.be"}:
        return os.path.join(base_output_path, "youtube")

    query = parse_qs(parsed.query)
    folder_parts = [_slugify(domain.replace(".", "-")), _derive_series_slug(parsed)]

    stable_id = None
    for key in ("anime_id", "series_id", "show_id", "id"):
        values = query.get(key)
        if values and values[0].strip():
            stable_id = _slugify(values[0])
            break
    if stable_id:
        folder_parts.append(f"id-{stable_id}")

    season_value = None
    for key in ("s", "season"):
        values = query.get(key)
        if values and values[0].strip():
            season_value = _slugify(values[0])
            break
    if season_value:
        folder_parts.append(f"s-{season_value}")

    folder_name = "-".join(part for part in folder_parts if part)
    return os.path.join(base_output_path, folder_name)


def _relative_download_path(filepath: str, base_output_path: str) -> str:
    return os.path.relpath(filepath, start=base_output_path).replace("\\", "/")


def _collect_created_files(output_path: str, before_files: set[str]) -> list[str]:
    created_files: list[str] = []
    for name in os.listdir(output_path):
        full_path = os.path.join(output_path, name)
        if os.path.isfile(full_path) and name not in before_files:
            created_files.append(full_path)
    created_files.sort(key=os.path.getmtime, reverse=True)
    return created_files


def _candidate_filepaths_from_info(info: dict[str, Any], output_path: str) -> list[str]:
    candidates: list[str] = []

    requested_downloads = info.get("requested_downloads")
    if isinstance(requested_downloads, list):
        for item in requested_downloads:
            if isinstance(item, dict):
                filepath = item.get("filepath")
                if isinstance(filepath, str) and filepath:
                    candidates.append(filepath)

    for key in ("filepath", "_filename"):
        value = info.get(key)
        if isinstance(value, str) and value:
            candidates.append(value)

    title = info.get("title")
    ext = info.get("ext")
    if isinstance(title, str) and title:
        if isinstance(ext, str) and ext:
            candidates.append(os.path.join(output_path, f"{title}.{ext}"))
        for known_ext in sorted(VIDEO_EXTENSIONS | AUDIO_EXTENSIONS):
            candidates.append(os.path.join(output_path, f"{title}{known_ext}"))

    unique_candidates: list[str] = []
    seen: set[str] = set()
    for path in candidates:
        normalized = os.path.normpath(path)
        if normalized not in seen:
            unique_candidates.append(normalized)
            seen.add(normalized)

    return unique_candidates


def _pick_media_file(created_files: list[str], download_type: str) -> str | None:
    allowed_exts = AUDIO_EXTENSIONS if download_type == "audio" else VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

    for path in created_files:
        suffix = os.path.splitext(path)[1].lower()
        if suffix in IGNORED_EXTENSIONS:
            continue
        if suffix in allowed_exts:
            return path

    for path in created_files:
        suffix = os.path.splitext(path)[1].lower()
        if suffix not in IGNORED_EXTENSIONS:
            return path

    return None


def _resolve_downloaded_file(info: dict[str, Any], created_files: list[str], output_path: str, download_type: str) -> str | None:
    for candidate in _candidate_filepaths_from_info(info, output_path):
        if os.path.isfile(candidate):
            suffix = os.path.splitext(candidate)[1].lower()
            if suffix not in IGNORED_EXTENSIONS:
                return candidate

    return _pick_media_file(created_files, download_type)


# ──────────────────────────────────────────────────────────────────────────────
# NOUVEAU : Construction du format yt-dlp à partir des nouvelles options
# ──────────────────────────────────────────────────────────────────────────────

def _resolve_quality_key(raw_quality: str) -> str:
    """Convertit une clé de qualité (legacy ou nouvelle) vers la clé canonique VIDEO_QUALITIES."""
    q = (raw_quality or "best").strip().lower()
    if q in VIDEO_QUALITIES:
        return q
    if q in _LEGACY_QUALITY_MAP:
        return _LEGACY_QUALITY_MAP[q]
    # ex: "1080" -> "1080p"
    if q.rstrip("p") in {str(k.rstrip("p")) for k in VIDEO_QUALITIES}:
        for k in VIDEO_QUALITIES:
            if k.rstrip("p") == q.rstrip("p"):
                return k
    return "best"


def _build_video_format_string(quality_key: str, video_format_key: str, has_ffmpeg: bool) -> str:
    """Construit le `format` yt-dlp pour la vidéo en fonction de la qualité + conteneur."""
    q_key = _resolve_quality_key(quality_key)
    q_meta = VIDEO_QUALITIES.get(q_key, VIDEO_QUALITIES["best"])
    max_height = q_meta["max_height"]

    f_meta = VIDEO_OUTPUT_FORMATS.get(video_format_key, VIDEO_OUTPUT_FORMATS["best"])
    v_ext = f_meta["vcodec"]
    a_ext = f_meta["acodec"]
    container = f_meta["container"]

    if not has_ffmpeg:
        # Pas de merge possible → format single-file avec conteneur MP4 de préférence
        ext_filter = f"[ext={container}]" if container else ""
        height_filter = f"[height<={max_height}]" if max_height else ""
        return (
            f"best{ext_filter}{height_filter}[acodec!=none]/"
            f"best{ext_filter}[acodec!=none]/"
            f"best[acodec!=none]/best"
        )

    # Avec ffmpeg : bestvideo + bestaudio
    v_ext_f = f"[ext={v_ext}]" if v_ext else ""
    a_ext_f = f"[ext={a_ext}]" if a_ext else ""
    h_f = f"[height<={max_height}]" if max_height else ""

    best_split = f"bestvideo{v_ext_f}{h_f}+bestaudio{a_ext_f}"
    # Fallback moins restrictif si l'extension/codec n'existe pas
    fallback_split = f"bestvideo{h_f}+bestaudio"
    # Dernier recours : fichier single
    ext_fallback = f"[ext={container}]" if container else ""
    fallback_single = f"best{ext_fallback}{h_f}[acodec!=none]/best{ext_fallback}[acodec!=none]/best[acodec!=none]/best"

    return f"{best_split}/{fallback_split}/{fallback_single}"


def _build_audio_format_string(audio_format_key: str) -> str:
    """Format yt-dlp pour l'extraction audio."""
    f_meta = AUDIO_OUTPUT_FORMATS.get(audio_format_key, AUDIO_OUTPUT_FORMATS["best"])
    codec = f_meta["codec"]
    if codec is None:
        return "bestaudio/best"
    # On préfère un format source compatible puis conversion via postprocessor FFmpeg
    return f"bestaudio[ext={codec}]/bestaudio/best"


def _build_audio_postprocessor(audio_format_key: str, has_ffmpeg: bool) -> dict[str, Any] | None:
    """Post-processeur FFmpegExtractAudio (retourne None si pas de ffmpeg ou format 'best')."""
    if not has_ffmpeg:
        return None
    f_meta = AUDIO_OUTPUT_FORMATS.get(audio_format_key, AUDIO_OUTPUT_FORMATS["best"])
    codec = f_meta["codec"]
    if codec is None:
        return None
    quality = f_meta["quality"]
    pp: dict[str, Any] = {
        "key": "FFmpegExtractAudio",
        "preferredcodec": codec,
    }
    if quality and quality > 0:
        pp["preferredquality"] = str(quality)
    return pp


def _build_subtitle_lang_options(lang_code: str | None) -> dict[str, Any]:
    """Options yt-dlp pour sous-titres / audio en fonction de la langue choisie."""
    opts: dict[str, Any] = {}
    if not lang_code:
        return opts

    # Convertit vf/vo multi-lang en liste de codes yt-dlp
    if lang_code == "multi":
        opts["writesubtitles"] = True
        opts["writeautomaticsub"] = True
        opts["subtitleslangs"] = list({k for k in LANGUAGES if len(k) <= 3 and k != "multi"})[:15]
        return opts

    codes = {lang_code, *LANGUAGES.get(lang_code, {}).get("aliases", set())}
    # Retient seulement les codes courts plausibles pour yt-dlp
    ytdlp_codes = sorted({c for c in codes if len(c) <= 3 and c not in {"vf", "vo", "multi"}})
    if not ytdlp_codes:
        return opts

    # Sous-titres : préférés dans la langue
    opts["writesubtitles"] = True
    opts["writeautomaticsub"] = True
    opts["subtitleslangs"] = ytdlp_codes

    # Préférence de piste audio (si plusieurs)
    opts["audioformat"] = "best"
    return opts


# ──────────────────────────────────────────────────────────────────────────────
# Point d'entrée principal (signature étendue, rétro-compat)
# ──────────────────────────────────────────────────────────────────────────────

def download_media(
    url,
    output_path="downloads",
    download_type="video",
    quality="best",
    video_format="mp4",
    audio_format="mp3",
    language: str | None = None,
    write_subtitles: bool = True,
) -> dict[str, Any]:
    """
    Point d'entrée unique :
      1. franime.fr  → extracteur dédié
      2. Sites yt-dlp → yt-dlp direct
      3. Autres       → extracteur navigateur générique

    Paramètres nouveaux (compatibilité ascendante conservée) :
      video_format   : clé dans VIDEO_OUTPUT_FORMATS (best/mp4/mkv/webm/mov/avi)
      audio_format   : clé dans AUDIO_OUTPUT_FORMATS (best/mp3/mp3_320/flac/wav/…)
      language       : code langue ISO (vf/vo/fr/en/es/…) ou None → auto
      write_subtitles: bool — active le téléchargement de sous-titres si disponible
    """
    import re as _re

    download_type = str(download_type).lower().strip()
    quality = str(quality).lower().strip()

    if download_type not in VALID_DOWNLOAD_TYPES:
        download_type = "video"

    # Fallback auto langue : détection via URL si non fournie
    resolved_lang = normalize_language(language) if language else detect_language_from_url(url)

    base_output_path = output_path
    target_output_path = _build_output_folder(url, base_output_path)
    os.makedirs(target_output_path, exist_ok=True)

    # ── Check existance ──────────────────────────────────────────────────────
    if _re.match(r"https?://(?:www\.)?franime\.fr/", url, _re.I):
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        slug = parsed.path.split('/')[-1] or "video"
        s = params.get('s', ['1'])[0]
        ep = params.get('ep', ['1'])[0]
        lang_tag = resolved_lang or params.get('lang', ['vo'])[0]
        filename_base = f"{slug}-s{s}-ep{ep}-{lang_tag}"

        for ext in VIDEO_EXTENSIONS | {".mp4", ".mkv", ".webm"}:
            potential_file = os.path.join(target_output_path, f"{filename_base}{ext}")
            if os.path.isfile(potential_file):
                print(f"  [skip] Déjà téléchargé dans {target_output_path}: {os.path.basename(potential_file)}")
                return {
                    "success": True,
                    "skipped": True,
                    "reason": "already_exists",
                    "filename": os.path.basename(potential_file),
                    "filepath": potential_file,
                }

    # ── 1. Franime ───────────────────────────────────────────────────────────
    if _re.match(r"https?://(?:www\.)?franime\.fr/", url, _re.I):
        try:
            from franime_extractor import download_franime
            result = download_franime(
                url,
                output_path=target_output_path,
                download_type=download_type,
                quality=quality,
                video_format=video_format,
                audio_format=audio_format,
                language=resolved_lang,
            )
        except ImportError:
            raise RuntimeError("franime_extractor.py introuvable.")
    else:
        # ── 2. yt-dlp standard ───────────────────────────────────────────────────
        try:
            result = _ydlp_download(
                url,
                output_path=target_output_path,
                download_type=download_type,
                quality=quality,
                video_format=video_format,
                audio_format=audio_format,
                language=resolved_lang,
                write_subtitles=write_subtitles,
            )
        except Exception as e:
            try:
                from yt_dlp.utils import UnsupportedError, ExtractorError
                is_unsupported = isinstance(e, (UnsupportedError, ExtractorError))
            except ImportError:
                is_unsupported = False

            if not is_unsupported:
                msg = str(e).lower()
                is_unsupported = any(k in msg for k in ("unsupported url", "no video formats", "unable to extract"))

            if is_unsupported:
                print("  [yt-dlp] Non supporté → extracteur navigateur générique")
                try:
                    from browser_extractor import download_with_browser
                    result = download_with_browser(
                        url,
                        output_path=target_output_path,
                        download_type=download_type,
                        quality=quality,
                    )
                except ImportError:
                    raise RuntimeError("browser_extractor.py introuvable.")
            else:
                raise

    filepath = result.get("filepath")
    if not filepath and result.get("reason") in {"not_found_or_blocked", "page_blocked"}:
        result["skipped"] = True
    if filepath:
        result["relative_path"] = _relative_download_path(filepath, base_output_path)
        result["filename"] = os.path.basename(filepath)
    result["folder"] = os.path.relpath(target_output_path, start=base_output_path).replace("\\", "/")
    if resolved_lang:
        result["language"] = resolved_lang
    return result


def _slugify_filename(value: str) -> str:
    import unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r"[^a-zA-Z0-9\._\- ]+", " ", value).strip()
    name = re.sub(r"\s+", "-", name)
    return name or "media"


def _ydlp_download(
    url,
    output_path="downloads",
    download_type="video",
    quality="best",
    video_format="mp4",
    audio_format="mp3",
    language: str | None = None,
    write_subtitles: bool = True,
) -> dict[str, Any]:
    """Téléchargement yt-dlp interne (version étendue)."""
    os.makedirs(output_path, exist_ok=True)

    ffmpeg_dir = _resolve_ffmpeg_dir()
    has_ffmpeg = bool(ffmpeg_dir) or (bool(shutil.which("ffmpeg")) and bool(shutil.which("ffprobe")))

    # ── Format + post-processeurs selon le type ───────────────────────────────
    if download_type == "audio":
        format_str = _build_audio_format_string(audio_format)
        postprocessor = _build_audio_postprocessor(audio_format, has_ffmpeg)
        postprocessors = [postprocessor] if postprocessor else []
        merge_output_format = None
    else:  # video
        format_str = _build_video_format_string(quality, video_format, has_ffmpeg)
        postprocessors = []
        f_meta = VIDEO_OUTPUT_FORMATS.get(video_format, VIDEO_OUTPUT_FORMATS["best"])
        container = f_meta["container"]
        if has_ffmpeg and container and f_meta["merge"]:
            merge_output_format = container
        else:
            merge_output_format = None

    # ── Options de langue / sous-titres ────────────────────────────────────────
    ydl_opts: dict[str, Any] = {
        "format": format_str,
        "outtmpl": os.path.join(output_path, "%(title).200s.%(ext)s").replace("\\", "/"),
        "quiet": False,
        "no_warnings": False,
        "postprocessors": postprocessors,
        "prefer_ffmpeg": has_ffmpeg,
        "merge_output_format": merge_output_format,
        "noplaylist": True,
        "concurrent_fragment_downloads": 16,
        "retries": 10,
        "fragment_retries": 10,
        "file_access_retries": 5,
        "socket_timeout": 30,
        "http_chunk_size": 10485760,
        "impersonate": "chrome",
    }

    if write_subtitles:
        ydl_opts.update(_build_subtitle_lang_options(language))

    if ffmpeg_dir:
        ydl_opts["ffmpeg_location"] = ffmpeg_dir

    # aria2c : téléchargeur externe plus rapide si disponible
    if shutil.which("aria2c"):
        ydl_opts["external_downloader"] = "aria2c"
        ydl_opts["external_downloader_args"] = [
            "--max-connection-per-server=16",
            "--split=16",
            "--min-split-size=1M",
            "--continue=true",
        ]
        print("  [aria2c] Téléchargeur rapide activé")

    before_files = set(os.listdir(output_path))

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # pyright: ignore[reportArgumentType]
            print(f"Downloading: {url}")
            print(
                f"Type: {download_type.upper()}"
                + (f" | Format: {video_format if download_type=='video' else audio_format}")
                + (f" | Quality: {quality.upper()}" if download_type == "video" else "")
                + (f" | Lang: {language}" if language else "")
            )
            info = ydl.extract_info(url, download=True)
            raw_title = info.get('title') or "download"
            print(f"Downloaded: {raw_title}")

        created_files = _collect_created_files(output_path, before_files)

        original_file = _resolve_downloaded_file(info, created_files, output_path, download_type)
        if original_file and os.path.isfile(original_file):
            dir_name = os.path.dirname(original_file)
            base_name = os.path.basename(original_file)
            name_part, extension = os.path.splitext(base_name)

            clean_name = _slugify_filename(name_part)
            new_file = os.path.join(dir_name, f"{clean_name}{extension}")

            if original_file != new_file:
                if os.path.exists(new_file):
                    os.remove(new_file)
                os.rename(original_file, new_file)
                selected_file = new_file
            else:
                selected_file = original_file
        else:
            selected_file = original_file

        return {
            "title": info.get("title") if isinstance(info, dict) else "download",
            "filepath": selected_file,
            "filename": os.path.basename(selected_file) if selected_file else None,
            "info": info,
        }
    except Exception as e:
        if "ffmpeg" in str(e).lower() or "ffprobe" in str(e).lower():
            print(f"\nFFmpeg Error: {e}")
            print("\nFFmpeg is required for audio conversion / container merge.")
            print("To install FFmpeg:")
            print("  - Download from: https://ffmpeg.org/download.html")
            print("  - Or use: choco install ffmpeg (requires admin)")
            print("  - Or use: winget install ffmpeg")
        else:
            print(f"Error: {e}")
        raise


# ─── Route /config expose au frontend les listes de formats / langues ────────

def get_frontend_config() -> dict[str, Any]:
    """Payload statique pour initialiser les sélecteurs frontend."""
    return {
        "video_formats": [
            {"key": k, "label": v["label"], "ext": v["ext"]}
            for k, v in VIDEO_OUTPUT_FORMATS.items()
        ],
        "audio_formats": [
            {"key": k, "label": v["label"], "ext": v["ext"]}
            for k, v in AUDIO_OUTPUT_FORMATS.items()
        ],
        "video_qualities": [
            {"key": k, "label": v["label"], "max_height": v["max_height"]}
            for k, v in VIDEO_QUALITIES.items()
        ],
        "languages": [
            {"code": k, "label": v["label"]}
            for k, v in LANGUAGES.items()
        ],
    }


if __name__ == "__main__":
    print("=" * 50)
    print("DowFlow - Multi-Site Media Downloader")
    print("=" * 50)

    video_url = input("Enter URL: ").strip()

    print("\nDownload Options:")
    print("1. Audio (choisir format)")
    print("2. Video (choisir format + qualite)")

    choice = input("\nSelect option (1-2): ").strip()

    if choice == "1":
        print("\nFormats audio disponibles :")
        for i, (k, v) in enumerate(AUDIO_OUTPUT_FORMATS.items(), 1):
            print(f"{i}. {v['label']}")
        try:
            af_choice = int(input("\nChoix format audio : ").strip())
            keys = list(AUDIO_OUTPUT_FORMATS.keys())
            audio_format = keys[af_choice - 1] if 1 <= af_choice <= len(keys) else "mp3"
        except ValueError:
            audio_format = "mp3"
        lang = input("Langue (code ISO ou vide=auto) : ").strip() or None
        download_media(video_url, download_type="audio", audio_format=audio_format, language=lang)
    else:
        print("\nFormats video disponibles :")
        for i, (k, v) in enumerate(VIDEO_OUTPUT_FORMATS.items(), 1):
            print(f"{i}. {v['label']}")
        try:
            vf_choice = int(input("\nChoix format video : ").strip())
            vkeys = list(VIDEO_OUTPUT_FORMATS.keys())
            video_format = vkeys[vf_choice - 1] if 1 <= vf_choice <= len(vkeys) else "mp4"
        except ValueError:
            video_format = "mp4"

        print("\nQualites disponibles :")
        qkeys = list(VIDEO_QUALITIES.keys())
        for i, k in enumerate(qkeys, 1):
            print(f"{i}. {VIDEO_QUALITIES[k]['label']}")
        try:
            q_choice = int(input("\nChoix qualite : ").strip())
            quality = qkeys[q_choice - 1] if 1 <= q_choice <= len(qkeys) else "best"
        except ValueError:
            quality = "best"
        lang = input("Langue (code ISO ou vide=auto) : ").strip() or None
        download_media(video_url, download_type="video", quality=quality,
                       video_format=video_format, language=lang)
