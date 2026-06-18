from pathlib import Path
from uuid import uuid4
import math

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from moviepy import AudioFileClip, CompositeAudioClip, VideoClip, concatenate_videoclips

from backend.app.core.config import RENDERS_DIR, UPLOADS_DIR
from backend.app.core.config import FRONTEND_DIR
from backend.app.music.music_engine import build_music_bed
from backend.app.voice.voice_engine import synthesize_scene_voice
from backend.app.video.storyboard import StoryboardPlan


DRAFT_WIDTH = 720
DRAFT_HEIGHT = 1280
FINAL_WIDTH = 1080
FINAL_HEIGHT = 1920

TONE_BACKGROUNDS = {
    "cinematic": ((7, 10, 24), (12, 36, 76), (83, 140, 255)),
    "provocative": ((20, 8, 14), (86, 18, 32), (255, 91, 91)),
    "premium": ((8, 9, 12), (34, 31, 24), (238, 206, 134)),
    "startup": ((4, 18, 15), (13, 72, 52), (63, 207, 142)),
}

BRAND_ICON_PATH = FRONTEND_DIR / "assets" / "brand" / "matchiq-app-icon.png"
_BRAND_ICON_CACHE = {}


def _get_font(size: int):
    for font_path in ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"]:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size=size)

    return ImageFont.load_default()


def _wrap_text(text: str, font, max_width: int, width: int, height: int):
    words = text.split()
    lines = []
    current = ""
    draw = ImageDraw.Draw(Image.new("RGB", (width, height)))

    for word in words:
        test_line = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test_line
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def _scene_attr(scene, name: str, default):
    return getattr(scene, name, default)


def _resolve_visual_style(visual_style: str, scene_index: int) -> str:
    if visual_style and visual_style != "auto":
        return visual_style

    styles = ["cinematic", "data", "sport", "editorial"]
    return styles[(scene_index - 1) % len(styles)]


def _draw_style_layer(draw, style: str, scene_index: int, accent, width: int, height: int):
    soft = tuple(min(255, int(value * 1.15)) for value in accent)
    dim = tuple(max(0, int(value * .28)) for value in accent)

    if style == "data":
        for x in range(0, width, max(48, width // 12)):
            draw.line((x, 0, x, height), fill=dim, width=1)
        for y in range(0, height, max(48, height // 18)):
            draw.line((0, y, width, y), fill=dim, width=1)
        for index in range(3):
            y = int(height * (.18 + index * .12))
            draw.rounded_rectangle(
                (int(width * .08), y, int(width * .38), y + int(height * .055)),
                radius=10,
                outline=soft if index == 0 else dim,
                width=2,
            )
        return

    if style == "sport":
        horizon = int(height * .34)
        draw.line((int(width * .08), horizon, int(width * .92), horizon), fill=dim, width=3)
        for index in range(5):
            x = int(width * (.16 + index * .17))
            draw.line((x, horizon - 90, int(width * .5), int(height * .72)), fill=dim, width=2)
        draw.ellipse((int(width * .32), horizon - 90, int(width * .68), horizon + 90), outline=soft, width=3)
        return

    if style == "editorial":
        stripe_x = int(width * (.08 if scene_index % 2 else .72))
        draw.rectangle((stripe_x, 0, stripe_x + int(width * .10), height), fill=tuple(max(0, int(v * .35)) for v in accent))
        draw.text(
            (int(width * .08), int(height * .16)),
            f"0{scene_index}",
            font=_get_font(max(78, width // 5)),
            fill=dim,
        )
        return

    beam_width = int(width * .24)
    start_x = int(width * (.12 + (scene_index % 3) * .18))
    draw.polygon(
        [
            (start_x, 0),
            (start_x + beam_width, 0),
            (start_x + int(width * .42), height),
            (start_x - int(width * .04), height),
        ],
        fill=tuple(max(0, int(v * .20)) for v in accent),
    )


def _load_scene_image(image_url: str | None, width: int, height: int) -> Image.Image | None:
    if not image_url or not image_url.startswith("/uploads/"):
        return None

    filename = Path(image_url).name
    image_path = UPLOADS_DIR / filename
    if not image_path.exists():
        return None

    try:
        image = Image.open(image_path).convert("RGB")
    except OSError:
        return None

    image = ImageOps.fit(image, (width, height), method=Image.Resampling.LANCZOS, centering=(.5, .5))
    image = ImageEnhance.Contrast(image).enhance(1.08)
    image = ImageEnhance.Color(image).enhance(1.02)
    return ImageEnhance.Brightness(image).enhance(.88)


def _apply_photo_overlay(img: Image.Image, accent, width: int, height: int) -> Image.Image:
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for y in range(height):
        ratio = y / height
        alpha = int(14 + 118 * ratio)
        draw.line((0, y, width, y), fill=(0, 0, 0, alpha))

    draw.rectangle((0, 0, width, int(height * .14)), fill=(0, 0, 0, 62))
    draw.rectangle((0, int(height * .78), width, height), fill=(0, 0, 0, 102))
    draw.line((int(width * .08), int(height * .16), int(width * .92), int(height * .16)), fill=(*accent, 190), width=3)
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def _apply_cinematic_grade(img: Image.Image, scene, accent, width: int, height: int) -> Image.Image:
    color_grade = _scene_attr(scene, "color_grade", "sport_tech_dark")
    glow = _scene_attr(scene, "glow", "medium")
    grain = _scene_attr(scene, "grain", "subtle")
    vignette = _scene_attr(scene, "vignette", "medium")

    contrast = 1.08 if color_grade != "soft" else 1.02
    saturation = 1.04 if "sport" in color_grade or "dark" in color_grade else 1.0
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Color(img).enhance(saturation)

    if glow in {"medium", "strong"}:
        glow_layer = img.filter(ImageFilter.GaussianBlur(radius=10 if glow == "medium" else 16))
        alpha = 0.10 if glow == "medium" else 0.16
        img = Image.blend(img, glow_layer, alpha)

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    if vignette in {"medium", "strong"}:
        max_radius = math.sqrt((width / 2) ** 2 + (height / 2) ** 2)
        center_x, center_y = width / 2, height / 2
        strength = 120 if vignette == "medium" else 165
        for y in range(0, height, 3):
            for x in range(0, width, 3):
                dist = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                alpha = int(max(0, (dist / max_radius - .42)) * strength)
                if alpha > 0:
                    draw.rectangle((x, y, x + 3, y + 3), fill=(0, 0, 0, min(130, alpha)))

    if grain in {"subtle", "medium"}:
        rng = np.random.default_rng(seed=scene.index * 17)
        noise_alpha = 10 if grain == "subtle" else 18
        noise = rng.integers(0, 255, (height, width), dtype=np.uint8)
        noise_img = Image.fromarray(noise, "L").convert("RGBA")
        noise_img.putalpha(noise_alpha)
        overlay = Image.alpha_composite(overlay, noise_img)

    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def _draw_particles(draw, scene, accent, width: int, height: int):
    particles = _scene_attr(scene, "particles", "light")
    if particles == "none":
        return

    count = 18 if particles == "light" else 36
    rng = np.random.default_rng(seed=scene.index * 31)
    for _ in range(count):
        x = int(rng.uniform(width * .05, width * .95))
        y = int(rng.uniform(height * .12, height * .72))
        r = int(rng.uniform(1, 3 if particles == "light" else 5))
        alpha_color = tuple(min(255, int(v * rng.uniform(.55, 1.2))) for v in accent)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=alpha_color)


def _draw_scene(
    storyboard: StoryboardPlan,
    scene_index: int,
    tone: str,
    visual_style: str,
    output_path: Path,
    width: int,
    height: int,
):
    scene = storyboard.scenes[scene_index - 1]
    style = _resolve_visual_style(visual_style, scene_index)
    top, bottom, accent = TONE_BACKGROUNDS.get(tone, TONE_BACKGROUNDS["cinematic"])
    media_image = _load_scene_image(scene.image_url, width, height)
    img = media_image or Image.new("RGB", (width, height), top)
    if media_image:
        img = _apply_photo_overlay(img, accent, width, height)
    draw = ImageDraw.Draw(img)

    if not media_image:
        for y in range(height):
            ratio = y / height
            color = tuple(int(top[channel] + (bottom[channel] - top[channel]) * ratio) for channel in range(3))
            draw.line((0, y, width, y), fill=color)

        center_x = width // 2
        center_y = int(height * .48)
        for radius in range(int(width * .54), 0, -12):
            alpha = radius / (width * .54)
            color = tuple(int(value * alpha) for value in accent)
            draw.ellipse(
                (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
                outline=color,
                width=2,
            )

    _draw_style_layer(draw, style, scene_index, accent, width, height)
    if not media_image:
        _draw_scene_motif(img, draw, scene, accent, width, height)

    _draw_particles(draw, scene, accent, width, height)

    brand_font = _get_font(max(24, width // 24))
    title_font = _get_font(max(42, width // 12))
    small_font = _get_font(max(18, width // 34))
    body_font = _get_font(max(20, width // 30))

    margin = int(width * .065)
    draw.text((margin, margin), storyboard.brand_name.upper(), font=brand_font, fill=(255, 255, 255))
    draw.text((margin, margin + 48), scene.title.upper(), font=small_font, fill=accent)

    _draw_scene_text(draw, scene, title_font, body_font, accent, width, height, style, scene_index)

    meta = f"{scene.camera} | {scene.motion}"
    meta_lines = _wrap_text(meta, body_font, int(width * .82), width, height)[:2]
    meta_y = int(height * .77)
    for line in meta_lines:
        draw.text((margin, meta_y), line, font=body_font, fill=(210, 220, 235))
        meta_y += int(width * .045)

    draw.text((margin, height - margin - 34), f"{scene.index}/{len(storyboard.scenes)}", font=small_font, fill=accent)
    draw.text((margin, height - margin), "CREATED WITH MatchIQ Studio", font=small_font, fill=(220, 230, 245))

    img = _apply_cinematic_grade(img, scene, accent, width, height)
    img.save(output_path)


def _draw_scene_text(
    draw,
    scene,
    title_font,
    body_font,
    accent,
    width: int,
    height: int,
    style: str,
    scene_index: int,
):
    kind = _motion_kind(scene)
    subtitle_position = _scene_attr(scene, "subtitle_position", "center")
    text_animation = _scene_attr(scene, "text_animation", "word_reveal")
    emphasis_words = [word.upper() for word in _scene_attr(scene, "text_emphasis", [])]

    if style == "editorial":
        x = int(width * (.16 if scene_index % 2 else .10))
        y = int(height * .46)
        max_width = int(width * .68)
        align = "left"
    elif style == "data":
        x = int(width * .11)
        y = int(height * .52)
        max_width = int(width * .72)
        align = "left"
    elif kind == "pan":
        x = int(width * .10)
        y = int(height * .58)
        max_width = int(width * .70)
        align = "left"
    elif kind == "scan":
        x = int(width * .12)
        y = int(height * .54)
        max_width = int(width * .76)
        align = "left"
    elif kind == "reveal":
        x = int(width * .12)
        y = int(height * .51)
        max_width = int(width * .76)
        align = "center"
    else:
        x = int(width * .12)
        y = int(height * .41)
        max_width = int(width * .76)
        align = "center"

    if subtitle_position == "lower":
        y = int(height * .60)
    elif subtitle_position == "upper":
        y = int(height * .34)

    lines = _wrap_text(scene.subtitle.upper(), title_font, max_width, width, height)[:4]
    line_height = int(width * .105)
    start_y = y - (len(lines) * line_height) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        line_width = bbox[2] - bbox[0]
        draw_x = x if align == "left" else (width - line_width) // 2

        if text_animation in {"word_reveal", "kinetic"} and emphasis_words:
            current_x = draw_x
            for token in line.split(" "):
                clean = token.strip(".,!?;:").upper()
                fill = accent if clean in emphasis_words else (255, 255, 255)
                draw.text((current_x, start_y), token, font=title_font, fill=fill)
                token_w = draw.textbbox((0, 0), f"{token} ", font=title_font)[2]
                current_x += token_w
        else:
            draw.text((draw_x, start_y), line, font=title_font, fill=(255, 255, 255))

        start_y += line_height

    voice = (scene.voice_over or scene.subtitle).strip()
    if not voice:
        return

    caption_font = body_font
    caption_lines = _wrap_text(voice, caption_font, int(width * .78), width, height)[:2]
    cap_x = int(width * .10)
    cap_y = int(height * .835)
    cap_h = 46 + len(caption_lines) * int(width * .045)
    cap_w = int(width * .80)

    draw.rounded_rectangle(
        (cap_x, cap_y, cap_x + cap_w, cap_y + cap_h),
        radius=18,
        fill=(0, 0, 0),
        outline=tuple(min(255, int(value * 1.15)) for value in accent),
        width=2,
    )
    draw.text((cap_x + 20, cap_y + 13), "VOICE / SUBTITLE", font=_get_font(max(14, width // 45)), fill=accent)

    text_y = cap_y + 38
    for line in caption_lines:
        draw.text((cap_x + 20, text_y), line, font=caption_font, fill=(230, 238, 250))
        text_y += int(width * .045)


def _draw_scene_motif(img, draw, scene, accent, width: int, height: int):
    text = f"{scene.title} {scene.visual} {scene.subtitle}".lower()
    soft = tuple(min(255, int(value * 1.25)) for value in accent)
    dim = tuple(max(0, int(value * .45)) for value in accent)

    if "pc" in text or "computer" in text or "monitor" in text:
        screen = (int(width * .19), int(height * .22), int(width * .81), int(height * .43))
        draw.rounded_rectangle(screen, radius=18, outline=soft, width=4, fill=(6, 12, 18))
        draw.rectangle((int(width * .46), int(height * .43), int(width * .54), int(height * .49)), fill=dim)
        draw.rounded_rectangle((int(width * .34), int(height * .49), int(width * .66), int(height * .515)), radius=10, fill=soft)
        for index in range(5):
            y = int(height * .255) + index * int(height * .027)
            draw.line((int(width * .25), y, int(width * (.52 + index * .035)), y), fill=dim, width=3)
        return

    if "campo" in text or "calcio" in text or "stadio" in text:
        y = int(height * .35)
        draw.line((int(width * .14), y, int(width * .86), y), fill=soft, width=4)
        draw.arc((int(width * .28), y - 110, int(width * .72), y + 110), 0, 180, fill=dim, width=4)
        draw.line((int(width * .5), y - 130, int(width * .5), y + 130), fill=dim, width=3)
        for offset in range(0, 220, 42):
            draw.line((int(width * .16), y + offset, int(width * .84), y + offset), fill=dim, width=1)
        return

    if "codice" in text or "code" in text or "dashboard" in text or "dati" in text:
        panel = (int(width * .16), int(height * .2), int(width * .84), int(height * .47))
        draw.rounded_rectangle(panel, radius=18, outline=dim, width=3, fill=(5, 10, 16))
        for index in range(8):
            y = int(height * .235) + index * int(height * .027)
            x2 = int(width * (.44 + (index % 4) * .09))
            draw.line((int(width * .22), y, x2, y), fill=soft if index % 3 == 0 else dim, width=3)
        return

    if "logo" in text or "reveal" in text:
        box = (int(width * .33), int(height * .23), int(width * .67), int(height * .42))
        draw.rounded_rectangle(box, radius=28, outline=soft, width=5, fill=(7, 12, 18))
        if BRAND_ICON_PATH.exists():
            icon = _get_brand_icon(width)
            x = int(width * .5 - icon.width / 2)
            y = int(height * .325 - icon.height / 2)
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            overlay.alpha_composite(icon, (x, y))
            composed = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            img.paste(composed)
        else:
            draw.text((int(width * .42), int(height * .295)), "IQ", font=_get_font(max(36, width // 10)), fill=soft)
        draw.line((int(width * .25), int(height * .47), int(width * .75), int(height * .47)), fill=dim, width=4)
        return

    if "cta" in text or "call" in text or "final" in text:
        button = (int(width * .25), int(height * .31), int(width * .75), int(height * .40))
        draw.rounded_rectangle(button, radius=24, fill=soft)
        draw.line((int(width * .36), int(height * .45), int(width * .64), int(height * .45)), fill=dim, width=4)


def _get_brand_icon(width: int):
    target_size = int(width * .24)
    if target_size not in _BRAND_ICON_CACHE:
        icon = Image.open(BRAND_ICON_PATH).convert("RGBA")
        icon.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
        _BRAND_ICON_CACHE[target_size] = icon

    return _BRAND_ICON_CACHE[target_size]


def _motion_kind(scene) -> str:
    text = f"{scene.title} {scene.camera} {scene.motion} {scene.visual} {_scene_attr(scene, 'transition', '')}".lower()

    if "laterale" in text or "campo" in text or "carrellata" in text or "pan" in text:
        return "pan"

    if "logo" in text or "reveal" in text:
        return "reveal"

    if "codice" in text or "glitch" in text or "scan" in text:
        return "scan"

    return "push"


def _ease(progress: float) -> float:
    progress = max(0.0, min(1.0, progress))
    return progress * progress * (3 - 2 * progress)


def _pacing_factor(pacing: str) -> float:
    return {
        "slow": .72,
        "balanced": 1.0,
        "fast": 1.35,
    }.get(pacing, 1.0)


def _motion_speed_factor(scene) -> float:
    speed = _scene_attr(scene, "motion_speed", "medium")
    return {
        "slow": .72,
        "medium": 1.0,
        "fast": 1.32,
        "impact": 1.55,
    }.get(speed, 1.0)


def _animate_scene_clip(scene, scene_path: Path, width: int, height: int, pacing: str):
    duration = scene.duration_seconds
    motion = _motion_kind(scene)
    zoom_level = float(_scene_attr(scene, "zoom_level", 1.08))
    zoom_level = max(1.02, min(1.6, zoom_level))
    overscan = max(zoom_level, 1.08)
    source = Image.open(scene_path).convert("RGB")
    zoomed_width = int(width * overscan)
    zoomed_height = int(height * overscan)
    source = source.resize((zoomed_width, zoomed_height), Image.Resampling.LANCZOS)
    max_x = zoomed_width - width
    max_y = zoomed_height - height
    speed_factor = _motion_speed_factor(scene)

    def crop_origin(t):
        progress = _ease(min(1.0, (t / duration) * _pacing_factor(pacing) * speed_factor))
        if motion == "pan":
            return int(max_x * (.06 + .88 * progress)), int(max_y * (.46 + .08 * progress))
        if motion == "scan":
            return int(max_x * (.42 + .16 * progress)), int(max_y * (.05 + .90 * progress))
        if motion == "reveal":
            return int(max_x * (.50 + .20 * progress)), int(max_y * (.62 - .34 * progress))
        return int(max_x * (.46 + .12 * progress)), int(max_y * (.58 - .22 * progress))

    def make_frame(t):
        x, y = crop_origin(t)
        frame = source.crop((x, y, x + width, y + height))

        transition = _scene_attr(scene, "transition", "cinematic_cut")
        if transition in {"flash_fade", "light_sweep"} and t < min(.22, duration * .18):
            intensity = 1 - (t / min(.22, duration * .18))
            white = Image.new("RGB", (width, height), (255, 255, 255))
            frame = Image.blend(frame, white, intensity * .22)

        if _scene_attr(scene, "blur_style", "cinematic_depth") == "motion_blur" and t < duration * .18:
            frame = frame.filter(ImageFilter.GaussianBlur(radius=1.1))

        return np.array(frame)

    return VideoClip(frame_function=make_frame, duration=duration)


def render_storyboard(
    storyboard: StoryboardPlan,
    tone: str,
    visual_style: str = "auto",
    pacing: str = "balanced",
    quality: str = "draft",
    music_enabled: bool = False,
    music_volume: float = 0.08,
    voice_enabled: bool = True,
    voice_volume: float = 0.95,
    voice_style: str = "studio",
    voice_rate: int = -1,
    on_progress=None,
) -> tuple[str, Path]:
    width, height = (DRAFT_WIDTH, DRAFT_HEIGHT) if quality == "draft" else (FINAL_WIDTH, FINAL_HEIGHT)
    fps = 18 if quality == "draft" else 24
    preset = "ultrafast" if quality == "draft" else "medium"

    reel_id = uuid4().hex[:10]
    work_dir = RENDERS_DIR / reel_id
    work_dir.mkdir(parents=True, exist_ok=True)

    clips = []
    for index, scene in enumerate(storyboard.scenes, start=1):
        if on_progress:
            progress = 18 + int((index - 1) / len(storyboard.scenes) * 58)
            on_progress(progress, f"Sto preparando scena {index}: motion, glow e typography...")

        scene_path = work_dir / f"scene_{index}.png"
        _draw_scene(storyboard, index, tone, visual_style, scene_path, width, height)
        clips.append(_animate_scene_clip(scene, scene_path, width, height, pacing))

    if on_progress:
        on_progress(82, "Sto esportando il file MP4 in modalita' draft...")

    final = concatenate_videoclips(clips, method="compose")
    total_duration = sum(scene.duration_seconds for scene in storyboard.scenes)

    audio_tracks = []
    audio_clips_to_close = []

    if music_enabled:
        if on_progress:
            on_progress(88, "Sto aggiungendo musica e mix audio...")
        music_audio = build_music_bed(tone=tone, duration=total_duration, volume=music_volume)
        audio_tracks.append(music_audio)
        audio_clips_to_close.append(music_audio)

    if voice_enabled:
        if on_progress:
            on_progress(90, "Sto generando voice-over con pause cinematiche...")

        offset = 0.0
        for index, scene in enumerate(storyboard.scenes, start=1):
            voice_path = work_dir / f"voice_{index}.wav"
            generated_path = synthesize_scene_voice(
                scene.voice_over or scene.subtitle,
                voice_path,
                voice_volume,
                style=voice_style,
                rate=voice_rate,
            )

            pause_before = float(_scene_attr(scene, "voice_pause_before", 0.08))
            pause_after = float(_scene_attr(scene, "voice_pause_after", 0.15))

            if generated_path:
                voice_clip = AudioFileClip(str(generated_path)).with_volume_scaled(voice_volume)
                max_voice_duration = max(.4, scene.duration_seconds - pause_before - pause_after)
                if voice_clip.duration > max_voice_duration:
                    voice_clip = voice_clip.subclipped(0, max_voice_duration)
                voice_clip = voice_clip.with_start(offset + pause_before)
                audio_tracks.append(voice_clip)
                audio_clips_to_close.append(voice_clip)

            offset += scene.duration_seconds

    if audio_tracks:
        mixed_audio = CompositeAudioClip(audio_tracks).with_duration(total_duration)
        final = final.with_audio(mixed_audio)
        audio_clips_to_close.append(mixed_audio)

    filename = f"matchiq_studio_reel_{reel_id}.mp4"
    output_path = RENDERS_DIR / filename
    final.write_videofile(
        str(output_path),
        fps=fps,
        codec="libx264",
        audio=bool(audio_tracks),
        audio_codec="aac" if audio_tracks else None,
        preset=preset,
        threads=4,
        logger=None,
    )
    final.close()

    for audio_clip in audio_clips_to_close:
        audio_clip.close()

    for clip in clips:
        clip.close()

    return filename, output_path
