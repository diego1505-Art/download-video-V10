"""Expansion d'une URL source en liste d'URLs téléchargeables (multi-sites)."""
from __future__ import annotations

from urllib.parse import urlparse

from .base import ExpandResult, OptionDef, SiteProfile
from . import franime, youtube, generic

_EXPANDERS = [
    franime,
    youtube,
    generic,  # toujours en dernier (fallback)
]


def _host(url: str) -> str:
    return (urlparse(url).netloc or "").lower().replace("www.", "")


def detect_profile(url: str) -> SiteProfile:
    host = _host(url)
    for mod in _EXPANDERS:
        profile = mod.profile_for(url, host)
        if profile is not None:
            return profile
    return SiteProfile(
        site_id="unknown",
        label="Site inconnu",
        available=False,
        options=[],
        help_text="Aucune expansion automatique pour ce domaine.",
    )


def expand_url(url: str, options: dict | None = None) -> ExpandResult:
    url = (url or "").strip()
    if not url:
        return ExpandResult(success=False, error="URL manquante.")

    host = _host(url)
    opts = options or {}

    for mod in _EXPANDERS:
        if mod.supports(url, host):
            return mod.expand(url, opts)

    return ExpandResult(
        success=False,
        error="Aucune méthode d'expansion pour ce site.",
    )


def options_payload(url: str) -> dict:
    profile = detect_profile(url)
    return {
        "success": True,
        "site_id": profile.site_id,
        "label": profile.label,
        "available": profile.available,
        "help_text": profile.help_text,
        "options": [opt.to_dict() for opt in profile.options],
        "defaults": {opt.key: opt.default for opt in profile.options},
    }
