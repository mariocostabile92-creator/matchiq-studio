from pydantic import BaseModel, Field

from backend.app.video.storyboard import StoryboardPlan
from backend.app.video.storyboard import ScenePlan


class ReelCreateRequest(BaseModel):
    brand_name: str = Field(default="MatchIQ Studio")
    title: str = Field(default="Una persona. Un intero team creativo.")
    topic: str = Field(default="Founder story")
    tone: str = Field(default="cinematic")
    visual_style: str = Field(default="auto")
    pacing: str = Field(default="balanced")
    duration_seconds: int = Field(default=18, ge=8, le=45)
    call_to_action: str = Field(default="Scopri il progetto")
    music_enabled: bool = Field(default=False)
    music_volume: float = Field(default=0.08, ge=0, le=1)
    voice_enabled: bool = Field(default=True)
    voice_volume: float = Field(default=0.95, ge=0, le=1)
    voice_style: str = Field(default="studio")
    voice_rate: int = Field(default=-1, ge=-4, le=3)


class ReelJobResponse(BaseModel):
    success: bool
    message: str
    job_id: str


class ReelStatusResponse(BaseModel):
    success: bool
    status: str
    message: str
    progress: int = 0
    render_url: str | None = None
    filename: str | None = None
    error: str | None = None


class StoryboardRenderRequest(BaseModel):
    storyboard: StoryboardPlan
    tone: str = Field(default="cinematic")
    visual_style: str = Field(default="auto")
    pacing: str = Field(default="balanced")
    music_enabled: bool = Field(default=False)
    music_volume: float = Field(default=0.08, ge=0, le=1)
    voice_enabled: bool = Field(default=True)
    voice_volume: float = Field(default=0.95, ge=0, le=1)
    voice_style: str = Field(default="studio")
    voice_rate: int = Field(default=-1, ge=-4, le=3)


class SceneRegenerateRequest(BaseModel):
    scene: ScenePlan
    brand_name: str = Field(default="MatchIQ Studio")
    topic: str = Field(default="Founder Story")
    variant_seed: int = Field(default=0, ge=0, le=99)

