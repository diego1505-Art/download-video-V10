import os
import shutil
import time
import uuid
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, send_file, send_from_directory
from werkzeug.utils import secure_filename

from config import (
    DOWNLOAD_FOLDER,
    LOCAL_MEDIA_TTL_SECONDS,
    LOCAL_MEDIA_MAX_ENTRIES,
    ALLOWED_LOCAL_EXTENSIONS,
    PREVIEWABLE_EXTENSIONS,
)
from utils import has_ffmpeg, is_http_url
from playlist import download_media, get_frontend_config

app = Flask(__name__)

DOWNLOAD_FOLDER.mkdir(exist_ok=True)
LOCAL_MEDIA_REGISTRY: dict[str, tuple[Path, float]] = {}


def is_allowed_local_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in ALLOWED_LOCAL_EXTENSIONS


def copy_local_media(source_path: Path) -> dict[str, str]:
    safe_name = secure_filename(source_path.name) or f"local-{uuid.uuid4().hex}{source_path.suffix.lower()}"
    destination = DOWNLOAD_FOLDER / f"{uuid.uuid4().hex[:8]}-{safe_name}"
    shutil.copy2(source_path, destination)
    return {
        "filename": destination.name,
        "filepath": str(destination),
        "file_url": f"/media/{destination.name}",
    }


def cleanup_local_media_registry() -> None:
    now = time.time()
    expired_tokens = [
        token
        for token, (_, created_at) in LOCAL_MEDIA_REGISTRY.items()
        if now - created_at > LOCAL_MEDIA_TTL_SECONDS
    ]
    for token in expired_tokens:
        LOCAL_MEDIA_REGISTRY.pop(token, None)

    if len(LOCAL_MEDIA_REGISTRY) <= LOCAL_MEDIA_MAX_ENTRIES:
        return

    tokens_by_age = sorted(
        LOCAL_MEDIA_REGISTRY.items(),
        key=lambda item: item[1][1],
    )
    overflow = len(LOCAL_MEDIA_REGISTRY) - LOCAL_MEDIA_MAX_ENTRIES
    for token, _ in tokens_by_age[:overflow]:
        LOCAL_MEDIA_REGISTRY.pop(token, None)


def register_local_media(source_path: Path) -> dict[str, str]:
    cleanup_local_media_registry()
    token = uuid.uuid4().hex
    LOCAL_MEDIA_REGISTRY[token] = (source_path.resolve(), time.time())
    return {
        "filename": source_path.name,
        "filepath": str(source_path),
        "file_url": f"/media-local/{token}",
    }


@app.route("/")
def index():
    return render_template("dowload.html", has_ffmpeg=has_ffmpeg())


@app.route("/check-ffmpeg")
def check_ffmpeg():
    return jsonify({"has_ffmpeg": has_ffmpeg()})


@app.route("/config")
def frontend_config():
    """Retourne la liste statique des formats, qualités et langues au frontend."""
    payload = get_frontend_config()
    payload["has_ffmpeg"] = has_ffmpeg()
    return jsonify(payload)


@app.route("/media/<path:filename>")
def serve_media(filename: str):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=False)


@app.route("/media-local/<token>")
def serve_local_media(token: str):
    cleanup_local_media_registry()
    entry = LOCAL_MEDIA_REGISTRY.get(token)
    if entry is None:
        abort(404)
    source_path, _ = entry
    if not source_path.is_file():
        LOCAL_MEDIA_REGISTRY.pop(token, None)
        abort(404)
    LOCAL_MEDIA_REGISTRY[token] = (source_path, time.time())
    return send_file(source_path, as_attachment=False)


@app.route("/open-folder")
def open_folder():
    try:
        os.startfile(str(DOWNLOAD_FOLDER))  # type: ignore[attr-defined]
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/upload-local", methods=["POST"])
def upload_local():
    try:
        file = request.files.get("file")
        if file is None or not file.filename:
            return jsonify({"success": False, "error": "Aucun fichier local recu."}), 400

        suffix = Path(file.filename).suffix.lower()
        if suffix not in ALLOWED_LOCAL_EXTENSIONS:
            return jsonify({"success": False, "error": "Format de fichier non supporte."}), 400

        safe_name = secure_filename(file.filename) or f"local-{uuid.uuid4().hex}{suffix}"
        stored_name = f"{uuid.uuid4().hex[:8]}-{safe_name}"
        destination = DOWNLOAD_FOLDER / stored_name
        file.save(destination)

        return jsonify(
            {
                "success": True,
                "filename": stored_name,
                "file_url": f"/media/{stored_name}",
                "source_type": "local",
                "source_label": file.filename,
                "message": "Fichier local charge avec succes.",
                "previewable": Path(stored_name).suffix.lower() in PREVIEWABLE_EXTENSIONS,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"Upload local impossible: {e}"}), 500


@app.route("/url-options", methods=["POST"])
def url_options():
    """Retourne le profil d'options pour la premiere URL (multi-sites)."""
    try:
        data = request.get_json() or {}
        url = (data.get("url") or "").strip()
        print(f"[url-options] url={url or '(vide)'}", flush=True)
        if not url:
            return jsonify({"success": False, "error": "URL manquante."}), 400
        from url_expanders import options_payload
        payload = options_payload(url)
        print(
            f"[url-options] site={payload.get('site_id')} "
            f"available={payload.get('available')} "
            f"options={len(payload.get('options') or [])}",
            flush=True,
        )
        return jsonify(payload)
    except Exception as e:
        print(f"[url-options] ERREUR: {e}", flush=True)
        return jsonify({"success": False, "error": f"Erreur système: {e}"}), 500


@app.route("/expand-url", methods=["POST"])
def expand_url_route():
    """Expand une URL source en liste d'URLs selon les options du site."""
    try:
        data = request.get_json() or {}
        url = (data.get("url") or "").strip()
        if not url:
            return jsonify({"success": False, "error": "URL manquante."}), 400
        options = data.get("options") or {}
        # Compat ancien client
        if "current_only" in data and "scope" not in options:
            options["scope"] = "season" if data.get("current_only") else "all"
            options["current_only"] = bool(data.get("current_only"))

        print(f"[expand-url] url={url} options={options}", flush=True)
        from url_expanders import expand_url
        result = expand_url(url, options)
        status = 200 if result.success else 400
        print(
            f"[expand-url] success={result.success} site={result.site_id} "
            f"count={result.count or len(result.urls)} error={result.error}",
            flush=True,
        )
        return jsonify(result.to_dict()), status
    except Exception as e:
        print(f"[expand-url] ERREUR: {e}", flush=True)
        return jsonify({"success": False, "error": f"Erreur système: {e}"}), 500


@app.route("/fetch-episodes", methods=["POST"])
def fetch_episodes():
    """Alias historique → /expand-url (Franime)."""
    try:
        data = request.get_json() or {}
        url = (data.get("url") or "").strip()
        if not url:
            return jsonify({"success": False, "error": "URL manquante."}), 400
        options = {
            "scope": "season" if data.get("current_only") else "all",
            "current_only": bool(data.get("current_only")),
        }
        print(f"[fetch-episodes] url={url} options={options}", flush=True)
        from url_expanders import expand_url
        result = expand_url(url, options)
        status = 200 if result.success else 400
        print(
            f"[fetch-episodes] success={result.success} count={result.count or len(result.urls)} "
            f"error={result.error}",
            flush=True,
        )
        return jsonify(result.to_dict()), status
    except Exception as e:
        print(f"[fetch-episodes] ERREUR: {e}", flush=True)
        return jsonify({"success": False, "error": f"Erreur système: {e}"}), 500


@app.route("/download", methods=["POST"])
def download():
    try:
        data = request.get_json() or {}
        # Nettoyage agressif de l'URL pour supprimer les retours a la ligne accidentels
        source_value = data.get("url", "").strip().replace("\n", "").replace("\r", "")
        download_type = data.get("type", "video")
        quality = data.get("quality", "best")
        video_format = data.get("video_format", "mp4")
        audio_format = data.get("audio_format", "mp3")
        language = data.get("language") or None
        if isinstance(language, str):
            language = language.strip() or None
        write_subtitles = bool(data.get("write_subtitles", True))
        print(
            f"[download] type={download_type} quality={quality} vfmt={video_format} afmt={audio_format} lang={language or '(auto)'} url={source_value or '(vide)'}",
            flush=True,
        )

        if not source_value:
            return jsonify({"success": False, "error": "Merci de renseigner une URL ou un chemin local."}), 400

        local_path = Path(source_value).expanduser()
        if not is_http_url(source_value) and is_allowed_local_file(local_path):
            registered = register_local_media(local_path)
            return jsonify(
                {
                    "success": True,
                    "message": "Fichier local pret sans copie.",
                    "filename": registered["filename"],
                    "file_url": registered["file_url"],
                    "source_type": "local",
                    "source_label": str(local_path),
                    "previewable": local_path.suffix.lower() in PREVIEWABLE_EXTENSIONS,
                }
            )

        if not is_http_url(source_value):
            return jsonify({"success": False, "error": "URL invalide ou chemin local introuvable."}), 400

        result = download_media(
            source_value,
            output_path=str(DOWNLOAD_FOLDER),
            download_type=download_type,
            quality=quality,
            video_format=video_format,
            audio_format=audio_format,
            language=language,
            write_subtitles=write_subtitles,
        )

        filename = result.get("filename")
        relative_path = result.get("relative_path") or filename
        
        if result.get("skipped"):
            reason = result.get("reason")
            if reason == "already_exists":
                reason_msg = "Déjà téléchargé."
            elif reason == "page_blocked":
                reason_msg = "Page bloquée par le serveur distant."
            else:
                reason_msg = "Introuvable ou indisponible."
            return jsonify({
                "success": True,
                "skipped": True,
                "reason": reason,
                "message": f"Episode sauté : {reason_msg}",
                "filename": filename,
                "source_label": source_value
            })

        if not filename:
            return jsonify({"success": False, "error": result.get("error", "Fichier telecharge mais introuvable.")}), 500

        from urllib.parse import urlparse

        domain = urlparse(source_value).netloc.replace("www.", "") or "remote"
        previewable = Path(filename).suffix.lower() in PREVIEWABLE_EXTENSIONS
        payload = {
            "success": True,
            "message": f"Telecharge depuis {domain} : {filename}",
            "filename": filename,
            "file_url": f"/media/{relative_path}",
            "source_type": domain,
            "source_label": source_value,
            "previewable": previewable,
            "storage_folder": result.get("folder"),
        }

        if download_type == "audio":
            payload["message"] = f"Audio telecharge : {filename}"
        elif not previewable:
            payload["message"] = f"Telecharge : {filename} (apercu non supporte par le navigateur)"

        return jsonify(payload)

    except Exception as e:
        error_msg = str(e)
        if "ffmpeg" in error_msg.lower() or "ffprobe" in error_msg.lower():
            return jsonify(
                {
                    "success": False,
                    "error": "FFmpeg est requis mais n'est pas installe. Installe FFmpeg pour continuer.",
                    "is_ffmpeg_error": True,
                }
            ), 500
        return jsonify({"success": False, "error": f"Echec du telechargement: {error_msg}"}), 500


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DowFlow — Multi-Site Media Downloader")
    print("=" * 60)
    print("\nServeur démarré sur http://127.0.0.1:5001")
    print("Ctrl+C pour arrêter\n")
    app.run(debug=False, host="127.0.0.1", port=5001)
