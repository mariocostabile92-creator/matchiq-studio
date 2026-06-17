import json
from datetime import datetime, timezone
from uuid import uuid4

from backend.app.core.config import STORAGE_DIR
from backend.app.schemas.campaign import CampaignPayload, CampaignRecord

CAMPAIGNS_FILE = STORAGE_DIR / "campaigns.json"


def _now():
    return datetime.now(timezone.utc)


def _load_raw() -> list[dict]:
    if not CAMPAIGNS_FILE.exists():
        return []

    try:
        return json.loads(CAMPAIGNS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_raw(items: list[dict]) -> None:
    CAMPAIGNS_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def list_campaigns() -> list[CampaignRecord]:
    items = _load_raw()
    items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return [CampaignRecord(**item) for item in items]


def get_campaign(campaign_id: str) -> CampaignRecord | None:
    for item in _load_raw():
        if item.get("id") == campaign_id:
            return CampaignRecord(**item)
    return None


def save_campaign(payload: CampaignPayload, campaign_id: str | None = None) -> CampaignRecord:
    items = _load_raw()
    now = _now()

    if campaign_id:
        for index, item in enumerate(items):
            if item.get("id") == campaign_id:
                updated = {
                    **item,
                    **payload.model_dump(),
                    "updated_at": now,
                }
                items[index] = updated
                _save_raw(items)
                return CampaignRecord(**updated)

    created = {
        "id": uuid4().hex[:12],
        "created_at": now,
        "updated_at": now,
        **payload.model_dump(),
    }

    items.append(created)
    _save_raw(items)
    return CampaignRecord(**created)
