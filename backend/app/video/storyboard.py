from pydantic import BaseModel, Field


class ScenePlan(BaseModel):
    index: int
    title: str
    visual: str
    camera: str
    motion: str
    lighting: str
    voice_over: str
    subtitle: str
    image_url: str | None = None
    duration_seconds: float = Field(default=3.0, ge=1.0, le=12.0)


class StoryboardPlan(BaseModel):
    brand_name: str
    topic: str
    hook: str
    creative_direction: str
    music_mood: str
    rhythm: str
    scenes: list[ScenePlan]
