from pathlib import Path

from backend.app.ai.creative_director import build_storyboard
from backend.app.render.reel_renderer import render_storyboard


def build_reel(
    brand_name: str,
    title: str,
    topic: str,
    tone: str,
    duration_seconds: int,
    call_to_action: str,
    visual_style: str = "auto",
    pacing: str = "balanced",
    music_enabled: bool = False,
    music_volume: float = 0.08,
    voice_enabled: bool = True,
    voice_volume: float = 0.95,
    voice_style: str = "studio",
    voice_rate: int = -1,
    on_progress=None,
) -> tuple[str, Path]:
    storyboard = build_storyboard(
        brand_name=brand_name,
        title=title,
        topic=topic,
        tone=tone,
        duration_seconds=duration_seconds,
        call_to_action=call_to_action,
    )

    return render_storyboard(
        storyboard=storyboard,
        tone=tone,
        visual_style=visual_style,
        pacing=pacing,
        quality="draft",
        music_enabled=music_enabled,
        music_volume=music_volume,
        voice_enabled=voice_enabled,
        voice_volume=voice_volume,
        voice_style=voice_style,
        voice_rate=voice_rate,
        on_progress=on_progress,
    )
