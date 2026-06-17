from datetime import datetime
from pydantic import BaseModel, Field


class CampaignPayload(BaseModel):
    name: str = Field(default="Nuova campagna")
    project_id: str | None = None
    objective: str = Field(default="Awareness")
    audience: str = Field(default="Creator, founder e team marketing")
    status: str = Field(default="draft")
    channels: list[str] = Field(default_factory=lambda: ["Instagram", "TikTok", "LinkedIn"])
    content_plan: list[dict] = Field(default_factory=list)
    notes: str = Field(default="")


class CampaignRecord(CampaignPayload):
    id: str
    created_at: datetime
    updated_at: datetime


class CampaignListResponse(BaseModel):
    success: bool
    campaigns: list[CampaignRecord]


class CampaignSaveResponse(BaseModel):
    success: bool
    message: str
    campaign: CampaignRecord
