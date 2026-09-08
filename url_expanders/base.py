from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OptionDef:
    """Une option affichée dans le panneau « Options de la premiere URL »."""

    key: str
    label: str
    kind: str  # "toggle" | "select" | "number" | "text"
    default: Any
    help_text: str = ""
    choices: list[dict[str, Any]] = field(default_factory=list)  # [{value, label}]
    min_value: int | None = None
    max_value: int | None = None
    enabled: bool = True
    placeholder: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "key": self.key,
            "label": self.label,
            "kind": self.kind,
            "default": self.default,
            "help": self.help_text,
            "enabled": self.enabled,
        }
        if self.choices:
            payload["choices"] = self.choices
        if self.min_value is not None:
            payload["min"] = self.min_value
        if self.max_value is not None:
            payload["max"] = self.max_value
        if self.placeholder:
            payload["placeholder"] = self.placeholder
        return payload


@dataclass
class SiteProfile:
    site_id: str
    label: str
    available: bool
    options: list[OptionDef]
    help_text: str = ""


@dataclass
class ExpandResult:
    success: bool
    urls: list[str] = field(default_factory=list)
    count: int = 0
    title: str = ""
    site_id: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "success": self.success,
            "urls": self.urls,
            "count": self.count or len(self.urls),
            "title": self.title,
            "site_id": self.site_id,
            # Compat UI historique
            "anime_title": self.title,
        }
        if self.error:
            payload["error"] = self.error
        return payload
