"""
Extracteur générique par navigateur (Playwright + Chrome).
Fallback automatique pour tout site non supporté par yt-dlp.

Responsabilités séparées :
  - extract_streams()      : ouvre le navigateur, retourne les URLs brutes
  - _validate_stream()     : valide qu'une URL est réellement téléchargeable
  - _best_stream()         : choisit la meilleure parmi les URLs validées
  - download_with_browser(): orchestre le tout et télécharge
"""
from __future__ import annotations
import re, os, shutil, tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from config import BROWSER_HEADLESS

# ── Patterns de flux vidéo ───────────────────────────────────────────────────
STREAM_PATTERNS = [
    re.compile(r"sibnet\.ru/shell\.php",     re.I),
    re.compile(r"filemoon\.\w+/[ve]/",       re.I),
    re.compile(r"sendvid\.com/[a-z0-9]+",    re.I),
    re.compile(r"vidmoly\.\w+/[we]/",        re.I),
    re.compile(r"doodstream\.com/[de]/",     re.I),
    re.compile(r"streamtape\.com/[ve]/",     re.I),
    re.compile(r"voe\.sx/[el]/",             re.I),
    re.compile(r"mixdrop\.\w+/[ef]/",        re.I),
    re.compile(r"mp4upload\.com/embed",      re.I),
    re.compile(r"ok\.ru/videoembed",         re.I),
    re.compile(r"\.m3u8(\?|$)",             re.I),
    re.compile(r"\.mpd(\?|$)",              re.I),
]

STREAM_BLACKLIST = [
    re.compile(r"sibnet\.ru/(export|sbcount|time)", re.I),
    re.compile(r"\.ts(\?|$)",               re.I),  # fragments individuels
]

MEDIA_CONTENT_TYPES = {
    "mpegurl", "x-mpegurl", "vnd.apple.mpegurl", "dash+xml", "mp2t",
}

SKIP_HOSTS = {
    "google-analytics", "googletagmanager", "doubleclick",
    "googlesyndication", "adsbygoogle", "amazon-adsystem",
    "facebook.com", "twitter.com", "sentry.io",
    "fonts.google", "gstatic.com", "clarity.ms",
    "adskeeper", "bidgear", "a-ads.com", "betweendigital",
    "yandex.ru", "mail.ru", "hotjar", "amplitude",
}

# Priorité de sélection du stream (plus bas = meilleur)
STREAM_PRIORITY = {
    "shell.php": 0,   # sibnet player page → yt-dlp sait extraire
    ".m3u8":     1,   # HLS direct
    ".mpd":      2,   # DASH direct
}


def _skip(url: str) -> bool:
    return url.startswith("blob:") or any(h in url for h in SKIP_HOSTS)


def _is_stream(url: str) -> bool:
    if any(b.search(url) for b in STREAM_BLACKLIST): return False
    return any(p.search(url) for p in STREAM_PATTERNS)


def _stream_priority(url: str) -> int:
    for key, score in STREAM_PRIORITY.items():
        if key in url: return score
    return 9


def _validate_stream(url: str) -> bool:
    """
    Vérifie rapidement qu'une URL est accessible avant de lancer yt-dlp dessus.
    Évite de passer un embed ou une URL non-finale au téléchargeur.
    """
    try:
        import urllib.request
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": f"{urlparse(url).scheme}://{urlparse(url).netloc}/",
        }

        req = urllib.request.Request(url, method="HEAD", headers=headers)
        resp = urllib.request.urlopen(req, timeout=8)
        return getattr(resp, "status", 200) < 400
    except Exception:
        try:
            import urllib.request

            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": f"{urlparse(url).scheme}://{urlparse(url).netloc}/",
                "Range": "bytes=0-0",
            }
            req = urllib.request.Request(url, method="GET", headers=headers)
            resp = urllib.request.urlopen(req, timeout=8)
            return getattr(resp, "status", 200) < 400
        except Exception:
            return False


def _find_chrome() -> str | None:
    import platform
    if platform.system() == "Windows":
        for base in ["PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"]:
            p = os.path.join(os.environ.get(base, ""), "Google", "Chrome", "Application", "chrome.exe")
            if os.path.isfile(p): return p
    elif platform.system() == "Darwin":
        p = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.isfile(p): return p
    else:
        for cmd in ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium"):
            f = shutil.which(cmd)
            if f: return f
    return None


def _chrome_user_data_dir() -> str | None:
    import platform
    if platform.system() == "Windows":
        return os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")
    if platform.system() == "Darwin":
        return os.path.expanduser("~/Library/Application Support/Google/Chrome")
    return os.path.expanduser("~/.config/google-chrome")


def _copy_chrome_profile_light(udata: str) -> str:
    """
    Copie uniquement les fichiers de cookies/session (pas le cache ni les shaders).
    Beaucoup plus rapide que de copier tout Default/.
    """
    tmp = tempfile.mkdtemp(prefix="dowflow_")
    dst_default = os.path.join(tmp, "Default")
    os.makedirs(dst_default, exist_ok=True)

    src_default = os.path.join(udata, "Default")
    # Seulement les fichiers nécessaires aux cookies et à l'authentification
    files_to_copy = ["Cookies", "Login Data", "Local State", "Preferences", "Web Data"]
    for fname in files_to_copy:
        src = os.path.join(src_default, fname)
        if os.path.isfile(src):
            try: shutil.copy2(src, os.path.join(dst_default, fname))
            except Exception: pass

    # Copier Local State (hors Default)
    ls = os.path.join(udata, "Local State")
    if os.path.isfile(ls):
        try: shutil.copy2(ls, os.path.join(tmp, "Local State"))
        except Exception: pass

    return tmp


def extract_streams(page_url: str, wait_seconds: int = 30) -> list[str]:
    """
    Charge page_url dans Chrome, intercepte les flux vidéo.
    Retourne une liste d'URLs triées par priorité.
    NB : ne lance PAS d'installation runtime — c'est la responsabilité de start.bat.
    """
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
    except ImportError:
        raise RuntimeError("Playwright non installé. Lance : pip install playwright && playwright install chromium")

    found: list[str] = []

    def on_request(req):
        url = req.url
        if _skip(url) or url in found: return
        if _is_stream(url):
            print(f"  [browser] ✓ {url[:110]}")
            found.append(url)

    def on_response(resp):
        url = resp.url
        if _skip(url) or url.startswith("blob:") or url in found: return
        ct = resp.headers.get("content-type", "").lower()
        if any(t in ct for t in MEDIA_CONTENT_TYPES):
            print(f"  [browser] ✓ (ct) {url[:100]}")
            found.append(url)

    chrome = _find_chrome()
    udata  = _chrome_user_data_dir()
    tmp    = None

    with sync_playwright() as pw:
        args = ["--no-sandbox", "--disable-blink-features=AutomationControlled"]

        # Profil léger (cookies seulement) si Chrome disponible
        if chrome and udata and os.path.isdir(os.path.join(udata, "Default")):
            tmp = _copy_chrome_profile_light(udata)
            ctx = pw.chromium.launch_persistent_context(
                tmp, headless=BROWSER_HEADLESS, executable_path=chrome,
                args=args, no_viewport=True)
            page = ctx.new_page()
        else:
            browser = pw.chromium.launch(
                headless=BROWSER_HEADLESS, executable_path=chrome or None, args=args)
            ctx = browser.new_context(viewport={"width": 1280, "height": 720})
            page = ctx.new_page()

        page.on("request",  on_request)
        page.on("response", on_response)

        try:
            page.goto(page_url, wait_until="domcontentloaded", timeout=45_000)
        except PwTimeout:
            pass

        # Clics play courants
        page.wait_for_timeout(2_000)
        for sel in [
            "button:has-text('Regarder')", "button:has-text('Watch')",
            "button:has-text('Play')",     "button:has-text('Lire')",
            ".btn-play", "#play-button",   ".play-btn",
        ]:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.click(timeout=2_000)
                    page.wait_for_timeout(1_500)
                    break
            except Exception:
                pass

        for sel in ["video", "iframe[src]", "[class*='player']"]:
            try: page.wait_for_selector(sel, timeout=10_000); break
            except Exception: pass

        for sel in ["video", ".vjs-big-play-button", "[class*='play']"]:
            try:
                el = page.query_selector(sel)
                if el: el.click(timeout=2_000); break
            except Exception: pass

        # Attente avec sortie anticipée dès qu'on a un stream validé
        for i in range(wait_seconds):
            page.wait_for_timeout(1_000)
            if found and i >= 4: break

        # Dernier recours DOM
        if not found:
            html = page.content()
            for pat in [r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*',
                        r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*']:
                for m in re.findall(pat, html):
                    if m not in found: found.append(m)
            try:
                srcs = page.eval_on_selector_all(
                    "video, video source",
                    "els => els.map(e => e.src||e.getAttribute('src')).filter(Boolean)")
                for s in srcs:
                    if s and s not in found: found.append(s)
            except Exception: pass

        ctx.close()

    if tmp:
        try: shutil.rmtree(tmp, ignore_errors=True)
        except Exception: pass

    # Trier par priorité
    found.sort(key=_stream_priority)
    return found


def _best_stream(streams: list[str]) -> str | None:
    """Valide chaque stream dans l'ordre et retourne le premier accessible."""
    for url in streams:
        print(f"  [browser] Validation : {url[:90]}")
        if _validate_stream(url):
            print(f"  [browser] ✓ Choisi : {url[:90]}")
            return url
        print(f"  [browser] ✗ Inaccessible, suivant...")
    return None


def _resolve_ffmpeg_dir() -> str | None:
    if shutil.which("ffmpeg") and shutil.which("ffprobe"): return None
    p = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages" / \
        "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ffmpeg-8.1.1-full_build" / "bin"
    return str(p) if (p / "ffmpeg.exe").exists() else None


def _build_video_format(quality: str) -> str:
    quality_map = {
        "best": "bestvideo+bestaudio/best",
        "ultra": "bestvideo[height<=2160]+bestaudio/best[height<=2160]/best",
        "qhd": "bestvideo[height<=1440]+bestaudio/best[height<=1440]/best",
        "high": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "medium": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
        "low": "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
    }
    return quality_map.get(quality, quality_map["best"])


def download_with_browser(url: str, output_path: str = "downloads",
                           download_type: str = "video", quality: str = "best") -> dict[str, Any]:
    """
    Point d'entrée : extrait les streams via navigateur, valide, puis télécharge.
    """
    import yt_dlp

    os.makedirs(output_path, exist_ok=True)
    print(f"  [browser] Extraction depuis : {url}")

    streams = extract_streams(url)
    if not streams:
        raise ValueError(f"Aucun flux vidéo trouvé sur {url}. Le site est peut-être protégé par login ou DRM.")

    stream_url = _best_stream(streams)
    if not stream_url:
        raise ValueError(f"Streams trouvés mais inaccessibles : {streams[:3]}")

    parsed  = urlparse(url)
    referer = f"{parsed.scheme}://{parsed.netloc}/"
    slug    = re.sub(r"[^\w\-]", "-", parsed.path.strip("/").replace("/", "-"))[:60] or "video"

    ffmpeg_dir = _resolve_ffmpeg_dir()
    has_ffmpeg = bool(ffmpeg_dir) or (bool(shutil.which("ffmpeg")) and bool(shutil.which("ffprobe")))

    ydl_opts: dict[str, Any] = {
        "format":   _build_video_format(quality) if download_type != "audio" else "bestaudio/best",
        "outtmpl":  os.path.join(output_path, f"{slug}.%(ext)s"),
        "quiet":    False,
        "noplaylist": True,
        "concurrent_fragment_downloads": 16,
        "retries":  10,
        "fragment_retries": 10,
        "http_chunk_size": 10 * 1024 * 1024,
        "http_headers": {
            "Referer":    referer,
            "Origin":     referer.rstrip("/"),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
    }
    if ffmpeg_dir: ydl_opts["ffmpeg_location"] = ffmpeg_dir
    if has_ffmpeg and download_type != "audio": ydl_opts["merge_output_format"] = "mp4"
    if shutil.which("aria2c"):
        ydl_opts["external_downloader"] = "aria2c"
        ydl_opts["external_downloader_args"] = [
            "--max-connection-per-server=16", "--split=16",
            "--min-split-size=1M", "--continue=true",
        ]

    # Snapshot des fichiers avant pour détecter le nouveau fichier créé
    before_mtime: dict[str, float] = {
        f: os.path.getmtime(os.path.join(output_path, f))
        for f in os.listdir(output_path)
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(stream_url, download=True)

    # Sélection fiable : fichier nouveau OU modifié, trié par mtime décroissant
    candidates = []
    for f in os.listdir(output_path):
        fp = os.path.join(output_path, f)
        mt = os.path.getmtime(fp)
        if f not in before_mtime or mt > before_mtime[f]:
            ext = os.path.splitext(f)[1].lower()
            if ext not in {".part", ".ytdl", ".jpg", ".jpeg", ".png", ".webp", ".description"}:
                candidates.append((mt, fp))

    candidates.sort(reverse=True)
    selected = candidates[0][1] if candidates else None

    return {
        "title":      slug,
        "filepath":   selected,
        "filename":   os.path.basename(selected) if selected else None,
        "stream_url": stream_url,
    }
