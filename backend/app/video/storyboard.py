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

    # MatchIQ Studio V4.2 - Cinematic Director fields
    emotion: str = Field(default="curiosity")
    objective: str = Field(default="hold attention")
    hook_strength: int = Field(default=82, ge=0, le=100)

    transition: str = Field(default="cinematic_cut")
    transition_speed: str = Field(default="medium")
    camera_curve: str = Field(default="ease_in_out")
    zoom_level: float = Field(default=1.08, ge=1.0, le=1.6)
    motion_speed: str = Field(default="medium")
    parallax_depth: str = Field(default="medium")

    text_animation: str = Field(default="word_reveal")
    text_emphasis: list[str] = Field(default_factory=list)
    subtitle_position: str = Field(default="center")
    subtitle_style: str = Field(default="bold_caps")

    voice_pause_before: float = Field(default=0.15, ge=0, le=2)
    voice_pause_after: float = Field(default=0.20, ge=0, le=2)
    voice_emphasis: str = Field(default="natural")
    voice_energy: str = Field(default="medium")

    music_intensity: str = Field(default="medium")
    beat_sync: bool = Field(default=True)

    color_grade: str = Field(default="sport_tech_dark")
    glow: str = Field(default="medium")
    grain: str = Field(default="subtle")
    vignette: str = Field(default="medium")
    particles: str = Field(default="light")
    blur_style: str = Field(default="cinematic_depth")

    retention_note: str = Field(default="Keep the visual change noticeable in the first second.")
    director_note: str = Field(default="Make the scene feel premium, fast and emotionally clear.")


class StoryboardPlan(BaseModel):
    brand_name: str
    topic: str
    hook: str
    creative_direction: str
    music_mood: str
    rhythm: str
    scenes: list[ScenePlan]

    # MatchIQ Studio V4.2 - Reel quality metadata
    reel_formula: str = Field(default="Hook -> Problem -> Authority -> Proof -> CTA")
    target_platform: str = Field(default="vertical_social")
    target_format: str = Field(default="9:16")
    retention_strategy: str = Field(default="Strong first line, frequent visual changes, clean CTA.")
    overall_hook_score: int = Field(default=86, ge=0, le=100)
    emotional_score: int = Field(default=84, ge=0, le=100)
    pacing_score: int = Field(default=86, ge=0, le=100)
    cta_score: int = Field(default=78, ge=0, le=100)
