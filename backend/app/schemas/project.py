from datetime import datetime
from pydantic import BaseModel, Field


class ProjectPayload(BaseModel):
    name: str = Field(default="Nuovo progetto")
    brand_name: str = Field(default="MatchIQ Studio")
    title: str = Field(default="")
    topic: str = Field(default="")
    tone: str = Field(default="cinematic")
    duration_seconds: int = Field(default=20)
    call_to_action: str = Field(default="")
    storyboard: dict | None = None
    last_render_url: str | None = None


class ProjectRecord(ProjectPayload):
    id: str
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    success: bool
    projects: list[ProjectRecord]


class ProjectSaveResponse(BaseModel):
    success: bool
    message: str
    project: ProjectRecord
