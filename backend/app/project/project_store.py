import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from backend.app.core.config import STORAGE_DIR
from backend.app.schemas.project import ProjectPayload, ProjectRecord

PROJECTS_FILE = STORAGE_DIR / "projects.json"


def _now():
    return datetime.now(timezone.utc)


def _load_raw() -> list[dict]:
    if not PROJECTS_FILE.exists():
        return []

    try:
        return json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_raw(items: list[dict]) -> None:
    PROJECTS_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def list_projects() -> list[ProjectRecord]:
    items = _load_raw()
    items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return [ProjectRecord(**item) for item in items]


def get_project(project_id: str) -> ProjectRecord | None:
    for item in _load_raw():
        if item.get("id") == project_id:
            return ProjectRecord(**item)
    return None


def save_project(payload: ProjectPayload, project_id: str | None = None) -> ProjectRecord:
    items = _load_raw()
    now = _now()

    if project_id:
        for index, item in enumerate(items):
            if item.get("id") == project_id:
                updated = {
                    **item,
                    **payload.model_dump(),
                    "updated_at": now,
                }
                items[index] = updated
                _save_raw(items)
                return ProjectRecord(**updated)

    created = {
        "id": uuid4().hex[:12],
        "created_at": now,
        "updated_at": now,
        **payload.model_dump(),
    }

    items.append(created)
    _save_raw(items)

    return ProjectRecord(**created)