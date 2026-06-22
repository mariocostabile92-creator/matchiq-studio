from pathlib import Path
from uuid import uuid4

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
    "cinematic": ((5, 8, 18), (8, 22, 48), (120, 255, 63)),
    "provocative": ((18, 5, 10), (76, 12, 26), (255, 91, 91)),
    "premium": ((6, 7, 10), (30, 27, 21), (238, 206, 134)),
    "startup": ((3, 14, 12), (10, 58, 42), (120, 255, 63)),
}

BRAND_ICON_PATH = FRONTEND_DIR / "assets" / "brand" / "matchiq-app-icon.png"
BRAND_FULL_LOGO_PATH = FRONTEND_DIR / "assets" / "brand" / "matchiq-studio-primary.png"
_BRAND_ICON_CACHE = {}
_BRAND_FULL_CACHE = {}


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


def _smart_reel_text(scene, scene_index: int) -> str:
    text = (scene.subtitle or scene.voice_over or scene.title or "").strip()
    text = " ".join(text.split())
    if scene_index == 1:
        parts = [part.strip() for part in text.replace("?", ".").replace("!", ".").split(".") if part.strip()]
        if parts:
            text = parts[0]
    words = text.split()
    max_words = 7 if scene_index <= 2 else 9
    if len(words) > max_words:
        text = " ".join(words[:max_words]).rstrip(".,;:") + "."
    return text.upper()


def _load_scene_image(image_url: str | None, width: int, height: int) -> Image.Image | None:
    if not image_url or not image_url.startswith("/uploads/"):
        return None
    image_path = UPLOADS_DIR / Path(image_url).name
    if not image_path.exists():
        return None
    try:
        image = Image.open(image_path).convert("RGB")
    except OSError:
        return None
    image = ImageOps.fit(image, (width, height), method=Image.Resampling.LANCZOS, centering=(.5, .5))
    image = ImageEnhance.Contrast(image).enhance(1.10)
    image = ImageEnhance.Color(image).enhance(1.08)
    return ImageEnhance.Brightness(image).enhance(1.03)


def _background_gradient(width: int, height: int, top, bottom):
    img = Image.new("RGB", (width, height), top)
    draw = ImageDraw.Draw(img)
    for y in range(height):
        ratio = y / height
        color = tuple(int(top[channel] + (bottom[channel] - top[channel]) * ratio) for channel in range(3))
        draw.line((0, y, width, y), fill=color)
    return img


def _apply_photo_overlay(img: Image.Image, accent, width: int, height: int) -> Image.Image:
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(height):
        ratio = y / height
        alpha = int(8 + 72 * ratio)
        draw.line((0, y, width, y), fill=(0, 0, 0, alpha))
    draw.rectangle((0, 0, width, int(height * .20)), fill=(0, 0, 0, 42))
    draw.rectangle((0, int(height * .68), width, height), fill=(0, 0, 0, 92))
    draw.line((int(width * .08), int(height * .16), int(width * .92), int(height * .16)), fill=(*accent, 210), width=4)
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def _draw_fast_visual_motif(draw, scene, accent, width: int, height: int):
    text = f"{scene.title} {scene.visual} {scene.subtitle}".lower()
    soft = tuple(min(255, int(v * 1.2)) for v in accent)
    dim = tuple(max(0, int(v * .38)) for v in accent)
    if "campo" in text or "calcio" in text or "stadio" in text:
        horizon = int(height * .36)
        draw.rectangle((0, horizon, width, height), fill=(5, 24, 16))
        for offset in range(0, height - horizon, 75):
            draw.line((int(width * .08), horizon + offset, int(width * .92), horizon + offset), fill=dim, width=2)
        draw.line((int(width * .50), horizon, int(width * .50), height), fill=soft, width=4)
        draw.ellipse((int(width * .30), horizon - 100, int(width * .70), horizon + 100), outline=soft, width=5)
        return
    if "codice" in text or "dashboard" in text or "dati" in text or "code" in text:
        for index in range(10):
            y = int(height * .18) + index * int(height * .055)
            x1 = int(width * .12)
            x2 = int(width * (.42 + (index % 4) * .12))
            draw.line((x1, y, x2, y), fill=soft if index % 3 == 0 else dim, width=5)
        for index in range(4):
            x = int(width * (.12 + index * .19))
            draw.rounded_rectangle((x, int(height * .55), x + int(width * .13), int(height * .64)), radius=18, outline=dim, width=3)
        return
    for radius in range(int(width * .72), int(width * .14), -26):
        alpha = radius / (width * .72)
        color = tuple(int(v * alpha) for v in accent)
        draw.ellipse((width // 2 - radius, int(height * .36) - radius, width // 2 + radius, int(height * .36) + radius), outline=color, width=3)


def _draw_particles(draw, scene, accent, width: int, height: int):
    particles = _scene_attr(scene, "particles", "light")
    if particles == "none":
        return
    count = 24 if particles == "light" else 42
    rng = np.random.default_rng(seed=scene.index * 31)
    for _ in range(count):
        x = int(rng.uniform(width * .05, width * .95))
        y = int(rng.uniform(height * .08, height * .70))
        r = int(rng.uniform(1, 5))
        color = tuple(min(255, int(v * rng.uniform(.65, 1.2))) for v in accent)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=color)


def _get_brand_asset(width: int, full: bool = False):
    path = BRAND_FULL_LOGO_PATH if full else BRAND_ICON_PATH
    cache = _BRAND_FULL_CACHE if full else _BRAND_ICON_CACHE
    target_width = int(width * (.36 if full else .12))
    if not path.exists():
        return None
    if target_width not in cache:
        img = Image.open(path).convert("RGBA")
        ratio = target_width / img.width
        img = img.resize((target_width, max(1, int(img.height * ratio))), Image.Resampling.LANCZOS)
        cache[target_width] = img
    return cache[target_width]


def _draw_reel_text(draw, scene, scene_index: int, accent, width: int, height: int):
    text = _smart_reel_text(scene, scene_index)
    max_width = int(width * .84)
    base_size = int(width * (.155 if scene_index == 1 else .135))
    font = _get_font(max(48, base_size))
    lines = _wrap_text(text, font, max_width, width, height)[:3]
    line_height = int(base_size * 1.02)
    block_h = len(lines) * line_height
    y = int(height * (.43 if scene_index == 1 else .48)) - block_h // 2
    emphasis_words = [word.upper() for word in _scene_attr(scene, "text_emphasis", [])]
    if not emphasis_words and lines and lines[0].split():
        emphasis_words = [lines[0].split()[0].strip(".,!?;:")]
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (width - line_w) // 2
        for dx, dy in [(-3, 3), (3, 3), (0, 4)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0))
        current_x = x
        for token in line.split(" "):
            clean = token.strip(".,!?;:").upper()
            fill = accent if clean in emphasis_words else (255, 255, 255)
            draw.text((current_x, y), token, font=font, fill=fill)
            token_w = draw.textbbox((0, 0), f"{token} ", font=font)[2]
            current_x += token_w
        y += line_height
    voice = (scene.voice_over or scene.subtitle or "").strip()
    if voice:
        caption_font = _get_font(max(22, width // 28))
        caption = " ".join(voice.split())
        if len(caption.split()) > 12:
            caption = " ".join(caption.split()[:12]).rstrip(".,;:") + "."
        cap_lines = _wrap_text(caption, caption_font, int(width * .80), width, height)[:2]
        cap_x = int(width * .08)
        cap_y = int(height * .79)
        cap_w = int(width * .84)
        cap_h = 52 + len(cap_lines) * int(width * .052)
        draw.rounded_rectangle((cap_x, cap_y, cap_x + cap_w, cap_y + cap_h), radius=24, fill=(0, 0, 0), outline=tuple(min(255, int(v * 1.18)) for v in accent), width=3)
        text_y = cap_y + 22
        for line in cap_lines:
            draw.text((cap_x + 24, text_y), line, font=caption_font, fill=(235, 242, 252))
            text_y += int(width * .052)


def _apply_cinematic_grade(img: Image.Image, scene, width: int, height: int) -> Image.Image:
    glow = _scene_attr(scene, "glow", "medium")
    grain = _scene_attr(scene, "grain", "subtle")
    img = ImageEnhance.Contrast(img).enhance(1.09)
    img = ImageEnhance.Color(img).enhance(1.08)
    if glow in {"medium", "strong"}:
        glow_layer = img.filter(ImageFilter.GaussianBlur(radius=12 if glow == "medium" else 18))
        img = Image.blend(img, glow_layer, .06 if glow == "medium" else .10)
    if grain in {"subtle", "medium"}:
        rng = np.random.default_rng(seed=scene.index * 17)
        noise_alpha = 5 if grain == "subtle" else 10
        noise = rng.integers(0, 255, (height, width), dtype=np.uint8)
        noise_img = Image.fromarray(noise, "L").convert("RGBA")
        noise_img.putalpha(noise_alpha)
        img = Image.alpha_composite(img.convert("RGBA"), noise_img).convert("RGB")
    return img


def _draw_scene(storyboard: StoryboardPlan, scene_index: int, tone: str, visual_style: str, output_path: Path, width: int, height: int):
    scene = storyboard.scenes[scene_index - 1]
    top, bottom, accent = TONE_BACKGROUNDS.get(tone, TONE_BACKGROUNDS["cinematic"])
    media_image = _load_scene_image(scene.image_url, width, height)
    img = media_image or _background_gradient(width, height, top, bottom)
    if media_image:
        img = _apply_photo_overlay(img, accent, width, height)
    img = img.convert("RGBA")
    draw = ImageDraw.Draw(img)
    if not media_image:
        _draw_fast_visual_motif(draw, scene, accent, width, height)
    _draw_particles(draw, scene, accent, width, height)
    small_font = _get_font(max(18, width // 34))
    margin = int(width * .065)
    draw.rounded_rectangle((margin, margin, margin + int(width*.24), margin + 42), radius=21, fill=(0,0,0,160), outline=(*accent, 190), width=2)
    draw.text((margin + 16, margin + 12), f"SCENA {scene.index}", font=small_font, fill=accent)
    _draw_reel_text(draw, scene, scene_index, accent, width, height)
    icon = _get_brand_asset(width, full=(scene_index == len(storyboard.scenes)))
    if icon:
        x = int(width * .5 - icon.width / 2) if scene_index == len(storyboard.scenes) else int(width*.83)
        y = int(height * .68) if scene_index == len(storyboard.scenes) else int(height*.89)
        img.alpha_composite(icon, (x, y))
    img = _apply_cinematic_grade(img.convert("RGB"), scene, width, height)
    img.save(output_path)


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
    return {"slow": .72, "balanced": 1.0, "fast": 1.42}.get(pacing, 1.0)


def _motion_speed_factor(scene) -> float:
    return {"slow": .72, "medium": 1.0, "fast": 1.38, "impact": 1.62}.get(_scene_attr(scene, "motion_speed", "medium"), 1.0)


def _animate_scene_clip(scene, scene_path: Path, width: int, height: int, pacing: str):
    duration = scene.duration_seconds
    motion = _motion_kind(scene)
    zoom_level = max(1.08, min(1.72, float(_scene_attr(scene, "zoom_level", 1.16))))
    source = Image.open(scene_path).convert("RGB")
    zoomed_width = int(width * zoom_level)
    zoomed_height = int(height * zoom_level)
    source = source.resize((zoomed_width, zoomed_height), Image.Resampling.LANCZOS)
    max_x = zoomed_width - width
    max_y = zoomed_height - height
    speed_factor = _motion_speed_factor(scene)

    def crop_origin(t):
        progress = _ease(min(1.0, (t / duration) * _pacing_factor(pacing) * speed_factor))
        if motion == "pan":
            return int(max_x * (.05 + .90 * progress)), int(max_y * (.48 + .06 * progress))
        if motion == "scan":
            return int(max_x * (.44 + .12 * progress)), int(max_y * (.08 + .84 * progress))
        if motion == "reveal":
            return int(max_x * (.50 + .14 * progress)), int(max_y * (.62 - .30 * progress))
        return int(max_x * (.45 + .18 * progress)), int(max_y * (.60 - .28 * progress))

    def make_frame(t):
        x, y = crop_origin(t)
        frame = source.crop((x, y, x + width, y + height))
        start_window = min(.28, duration * .20)
        end_window = min(.22, duration * .16)
        if t < start_window:
            p = 1 - (t / start_window)
            white = Image.new("RGB", (width, height), (255, 255, 255))
            frame = Image.blend(frame, white, p * .16)
        if t > duration - end_window:
            p = (t - (duration - end_window)) / end_window
            black = Image.new("RGB", (width, height), (0, 0, 0))
            frame = Image.blend(frame, black, p * .14)
        return np.array(frame)
    return VideoClip(frame_function=make_frame, duration=duration)


def render_storyboard(storyboard: StoryboardPlan, tone: str, visual_style: str = "auto", pacing: str = "balanced", quality: str = "draft", music_enabled: bool = False, music_volume: float = 0.05, music_mood: str = "cinematic", voice_enabled: bool = True, voice_volume: float = 0.95, voice_style: str = "studio", voice_rate: int = -1, on_progress=None) -> tuple[str, Path]:
    width, height = (DRAFT_WIDTH, DRAFT_HEIGHT) if quality == "draft" else (FINAL_WIDTH, FINAL_HEIGHT)
    fps = 20 if quality == "draft" else 24
    preset = "ultrafast" if quality == "draft" else "medium"
    reel_id = uuid4().hex[:10]
    work_dir = RENDERS_DIR / reel_id
    work_dir.mkdir(parents=True, exist_ok=True)
    clips = []
    for index, scene in enumerate(storyboard.scenes, start=1):
        if on_progress:
            progress = 18 + int((index - 1) / len(storyboard.scenes) * 58)
            on_progress(progress, f"Sto preparando scena {index}: testo gigante, motion e visual...")
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
        music_audio = build_music_bed(tone=tone, duration=total_duration, volume=min(music_volume, 0.045), mood=music_mood)
        audio_tracks.append(music_audio)
        audio_clips_to_close.append(music_audio)
    if voice_enabled:
        if on_progress:
            on_progress(90, "Sto generando voice-over con pause cinematiche...")
        offset = 0.0
        for index, scene in enumerate(storyboard.scenes, start=1):
            voice_path = work_dir / f"voice_{index}.wav"
            generated_path = synthesize_scene_voice(scene.voice_over or scene.subtitle, voice_path, max(voice_volume, 0.98), style=voice_style, rate=voice_rate)
            pause_before = float(_scene_attr(scene, "voice_pause_before", 0.08))
            pause_after = float(_scene_attr(scene, "voice_pause_after", 0.15))
            if generated_path:
                voice_clip = AudioFileClip(str(generated_path)).with_volume_scaled(max(voice_volume, 1.0))
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
    final.write_videofile(str(output_path), fps=fps, codec="libx264", audio=bool(audio_tracks), audio_codec="aac" if audio_tracks else None, preset=preset, threads=4, logger=None)
    final.close()
    for audio_clip in audio_clips_to_close:
        audio_clip.close()
    for clip in clips:
        clip.close()
    return filename, output_path
