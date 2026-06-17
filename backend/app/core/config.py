from pathlib import Path

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
