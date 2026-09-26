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


def list_projects(owner_user_id: str) -> list[ProjectRecord]:
    items = [item for item in _load_raw() if item.get("owner_user_id") == owner_user_id]
    items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return [ProjectRecord(**item) for item in items]


def get_project(project_id: str, owner_user_id: str) -> ProjectRecord | None:
    for item in _load_raw():
        if item.get("id") == project_id and item.get("owner_user_id") == owner_user_id:
            return ProjectRecord(**item)
    return None


def save_project(
    payload: ProjectPayload,
    owner_user_id: str,
    project_id: str | None = None,
) -> ProjectRecord | None:
    items = _load_raw()
    now = _now()

    if project_id:
        for index, item in enumerate(items):
            if item.get("id") == project_id and item.get("owner_user_id") == owner_user_id:
                updated = {
                    **item,
                    **payload.model_dump(),
                    "updated_at": now,
                }
                items[index] = updated
                _save_raw(items)
                return ProjectRecord(**updated)
        return None

    created = {
        "id": uuid4().hex[:12],
        "owner_user_id": owner_user_id,
        "created_at": now,
        "updated_at": now,
        **payload.model_dump(),
    }

    items.append(created)
    _save_raw(items)

    return ProjectRecord(**created)
