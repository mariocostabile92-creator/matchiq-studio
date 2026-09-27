from pathlib import Path

import os
from urllib.parse import urlsplit

BASE_DIR = Path(__file__).resolve().parents[3]

FRONTEND_DIR = BASE_DIR / "frontend"
STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
RENDERS_DIR = STORAGE_DIR / "renders"
ASSETS_DIR = STORAGE_DIR / "assets"

for folder in [UPLOADS_DIR, RENDERS_DIR, ASSETS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

APP_NAME = "MatchIQ Studio"
APP_VERSION = "0.1.0"


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise RuntimeError(f"{name} must be true or false")
    return normalized == "true"


def _env_list(name: str, default: str) -> tuple[str, ...]:
    values = tuple(item.strip() for item in os.getenv(name, default).split(",") if item.strip())
    if not values or any("*" in item for item in values):
        raise RuntimeError(f"{name} must contain an explicit non-wildcard allowlist")
    return values


SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", True)
CORS_ALLOWED_ORIGINS = _env_list(
    "CORS_ALLOWED_ORIGINS", "https://studio.matchiq.it.com",
)
ALLOWED_HOSTS = _env_list("ALLOWED_HOSTS", "studio.matchiq.it.com")

for _origin in CORS_ALLOWED_ORIGINS:
    _parsed_origin = urlsplit(_origin)
    if (
        _origin == "null"
        or _parsed_origin.scheme not in {"http", "https"}
        or not _parsed_origin.netloc
        or _parsed_origin.path
        or _parsed_origin.query
        or _parsed_origin.fragment
        or "*" in _origin
    ):
        raise RuntimeError("CORS_ALLOWED_ORIGINS must contain exact HTTP(S) origins")
