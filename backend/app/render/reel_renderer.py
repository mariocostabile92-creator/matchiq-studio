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
        original = Image.open(image_path).convert("RGB")
    except OSError:
        return None

    # Keep the full uploaded image visible. The background fills 9:16 with a
    # blurred cover, while the real image is contained in the safe area.
    background = ImageOps.fit(original, (width, height), method=Image.Resampling.LANCZOS, centering=(.5, .5))
    background = background.filter(ImageFilter.GaussianBlur(radius=max(18, width // 28)))
    background = ImageEnhance.Brightness(background).enhance(.58)
    background = ImageEnhance.Color(background).enhance(1.10)

    safe_w = int(width * .92)
    safe_h = int(height * .78)
    foreground = original.copy()
    foreground.thumbnail((safe_w, safe_h), Image.Resampling.LANCZOS)
    foreground = ImageEnhance.Contrast(foreground).enhance(1.08)
    foreground = ImageEnhance.Color(foreground).enhance(1.08)
    foreground = ImageEnhance.Brightness(foreground).enhance(1.04)

    canvas = background.convert("RGBA")
    shadow = Image.new("RGBA", foreground.size, (0, 0, 0, 0))
    shadow_alpha = Image.new("L", foreground.size, 120)
    shadow.putalpha(shadow_alpha.filter(ImageFilter.GaussianBlur(radius=18)))
    x = (width - foreground.width) // 2
    y = int(height * .39 - foreground.height / 2)
    canvas.alpha_composite(shadow, (x, y + 18))
    canvas.alpha_composite(foreground.convert("RGBA"), (x, y))
    return canvas.convert("RGB")

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
    draw.rectangle((0, int(height * .68), width, height), fill=(0, 0, 0, 62))
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


def _effect_preset(scene, visual_style: str) -> str:
    text = f"{visual_style} {scene.title} {scene.visual} {scene.motion}".lower()
    if "sport" in text or "campo" in text or "calcio" in text:
        return "sport"
    if "data" in text or "hud" in text or "codice" in text or "dashboard" in text:
        return "data"
    if "caption" in text or "sottotit" in text:
        return "captions"
    if "neon" in text:
        return "neon"
    if "editorial" in text or "premium" in text:
        return "editorial"
    if "social" in text:
        return "social"
    return "social"


def _draw_dynamic_overlays(frame: Image.Image, scene, t: float, duration: float, visual_style: str, accent, width: int, height: int) -> Image.Image:
    preset = _effect_preset(scene, visual_style)
    progress = max(0.0, min(1.0, t / max(duration, .01)))
    pulse = .5 + .5 * np.sin(progress * np.pi * 4)
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    if preset in {"social", "captions", "neon"}:
        sweep_x = int(width * (-.35 + progress * 1.7))
        draw.polygon(
            [
                (sweep_x, 0),
                (sweep_x + int(width * .22), 0),
                (sweep_x - int(width * .12), height),
                (sweep_x - int(width * .34), height),
            ],
            fill=(*accent, int(16 + 34 * pulse)),
        )

    if preset == "data":
        for row in range(9):
            y = int(height * (.16 + row * .062 + progress * .04))
            alpha = int(35 + 55 * ((row + scene.index) % 3 == 0))
            draw.line((int(width * .08), y, int(width * (.42 + (row % 4) * .12)), y), fill=(*accent, alpha), width=3)
        scan_y = int(height * ((progress * 1.3) % 1))
        draw.rectangle((0, scan_y, width, scan_y + 5), fill=(*accent, 32))

    if preset == "sport":
        y = int(height * (.72 + .03 * np.sin(progress * np.pi * 2)))
        draw.arc((int(width * .18), y - 90, int(width * .82), y + 90), 180, 360, fill=(*accent, 90), width=5)
        draw.line((int(width * .5), int(height * .22), int(width * .5), height), fill=(*accent, 36), width=3)

    if preset == "editorial":
        draw.rectangle((int(width * .06), int(height * .10), int(width * .94), int(height * .105)), fill=(*accent, 120))
        draw.rectangle((int(width * .06), int(height * .88), int(width * .34 + width * .18 * progress), int(height * .886)), fill=(*accent, 150))

    caption = " ".join((scene.voice_over or scene.subtitle or "").split())
    if caption:
        words = caption.split()
        shown = max(1, min(len(words), int(len(words) * min(1, progress * 1.25)) + 1))
        live_caption = " ".join(words[:shown])
        if len(live_caption.split()) > 9:
            live_caption = " ".join(live_caption.split()[-9:])
        font = _get_font(max(24, width // 25))
        lines = _wrap_text(live_caption, font, int(width * .78), width, height)[-2:]
        cap_w = int(width * .86)
        cap_x = int(width * .07)
        cap_h = 58 + len(lines) * int(width * .052)
        cap_y = int(height * (.77 + .018 * (1 - min(1, progress * 5))))
        draw.rounded_rectangle((cap_x, cap_y, cap_x + cap_w, cap_y + cap_h), radius=24, fill=(0, 0, 0, 138), outline=(*accent, int(100 + 80 * pulse)), width=3)
        tx_y = cap_y + 22
        for line in lines:
            draw.text((cap_x + 24, tx_y), line, font=font, fill=(244, 248, 255, 245))
            tx_y += int(width * .052)
        draw.rectangle((cap_x + 22, cap_y + cap_h - 14, cap_x + 22 + int((cap_w - 44) * progress), cap_y + cap_h - 9), fill=(*accent, 210))

    if t < min(.32, duration * .18):
        p = 1 - (t / min(.32, duration * .18))
        draw.rectangle((0, 0, width, height), fill=(255, 255, 255, int(34 * p)))
        wipe = int(width * (1 - p))
        draw.rectangle((0, 0, wipe, height), fill=(*accent, int(24 * p)))

    if t > duration - min(.28, duration * .16):
        p = (t - (duration - min(.28, duration * .16))) / min(.28, duration * .16)
        wipe = int(width * p)
        draw.rectangle((width - wipe, 0, width, height), fill=(0, 0, 0, int(78 * p)))
        draw.rectangle((width - wipe, 0, width - wipe + 8, height), fill=(*accent, int(180 * p)))

    return Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")


def _animate_scene_clip(scene, scene_path: Path, width: int, height: int, pacing: str, visual_style: str, accent):
    duration = scene.duration_seconds
    motion = _motion_kind(scene)
    preset = _effect_preset(scene, visual_style)
    base_zoom = {"social": 1.22, "captions": 1.18, "neon": 1.24, "sport": 1.20, "data": 1.16, "editorial": 1.12}.get(preset, 1.16)
    zoom_level = max(base_zoom, min(1.72, float(_scene_attr(scene, "zoom_level", base_zoom))))
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
        if preset == "social":
            punch = .5 + .5 * np.sin(progress * np.pi * 3)
            return int(max_x * (.50 + .12 * progress + .03 * punch)), int(max_y * (.58 - .24 * progress))
        return int(max_x * (.45 + .18 * progress)), int(max_y * (.60 - .28 * progress))

    def make_frame(t):
        x, y = crop_origin(t)
        frame = source.crop((x, y, x + width, y + height))
        frame = _draw_dynamic_overlays(frame, scene, t, duration, visual_style, accent, width, height)
        return np.array(frame)

    return VideoClip(frame_function=make_frame, duration=duration)

def render_storyboard(storyboard: StoryboardPlan, tone: str, visual_style: str = "auto", pacing: str = "balanced", quality: str = "draft", music_enabled: bool = True, music_volume: float = 0.12, music_mood: str = "cinematic", voice_enabled: bool = True, voice_volume: float = 0.95, voice_style: str = "studio", voice_rate: int = -1, on_progress=None) -> tuple[str, Path]:
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
            on_progress(progress, f"Sto preparando scena {index}: transizioni, testo vivo e sottotitoli animati...")
        scene_path = work_dir / f"scene_{index}.png"
        _draw_scene(storyboard, index, tone, visual_style, scene_path, width, height)
        clips.append(_animate_scene_clip(scene, scene_path, width, height, pacing, visual_style, TONE_BACKGROUNDS.get(tone, TONE_BACKGROUNDS["cinematic"])[2]))
    if on_progress:
        on_progress(82, "Sto esportando il file MP4 in modalita' draft...")
    final = concatenate_videoclips(clips, method="compose")
    total_duration = sum(scene.duration_seconds for scene in storyboard.scenes)
    audio_tracks = []
    audio_clips_to_close = []
    if music_enabled:
        if on_progress:
            on_progress(88, "Sto aggiungendo musica e mix audio...")
        music_audio = build_music_bed(tone=tone, duration=total_duration, volume=min(max(music_volume, 0.10), 0.16), mood=music_mood)
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
                voice_clip = AudioFileClip(str(generated_path)).with_volume_scaled(max(voice_volume, 1.15))
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
