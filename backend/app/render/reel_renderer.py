from pathlib import Path
from uuid import uuid4

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from moviepy import AudioFileClip, CompositeAudioClip, VideoClip, VideoFileClip, concatenate_videoclips

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
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".m4v"}
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


def _enhance_uploaded_image(img: Image.Image) -> Image.Image:
    img = ImageEnhance.Contrast(img).enhance(1.08)
    img = ImageEnhance.Color(img).enhance(1.08)
    return ImageEnhance.Brightness(img).enhance(1.03)


def _rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def _paste_shadowed(canvas: Image.Image, foreground: Image.Image, x: int, y: int, radius: int = 28):
    shadow = Image.new("RGBA", foreground.size, (0, 0, 0, 0))
    shadow.putalpha(Image.new("L", foreground.size, 145).filter(ImageFilter.GaussianBlur(radius=22)))
    canvas.alpha_composite(shadow, (x, y + 18))
    if radius > 0:
        fg = foreground.convert("RGBA")
        fg.putalpha(_rounded_mask(foreground.size, radius))
        canvas.alpha_composite(fg, (x, y))
    else:
        canvas.alpha_composite(foreground.convert("RGBA"), (x, y))


def _uploaded_media_path(media_url: str | None) -> Path | None:
    if not media_url or not media_url.startswith("/uploads/"):
        return None
    path = UPLOADS_DIR / Path(media_url).name
    return path if path.exists() else None


def _is_video_media(media_url: str | None) -> bool:
    path = _uploaded_media_path(media_url)
    return bool(path and path.suffix.lower() in VIDEO_EXTENSIONS)


def _compose_uploaded_visual(original: Image.Image, width: int, height: int, layout: str = "auto") -> Image.Image:
    layout = (layout or "auto").lower().strip()
    if layout == "auto":
        ratio = original.width / max(1, original.height)
        layout = "full" if .48 <= ratio <= .70 else "poster"

    background = ImageOps.fit(original, (width, height), method=Image.Resampling.LANCZOS, centering=(.5, .5))
    background = background.filter(ImageFilter.GaussianBlur(radius=max(20, width // 25)))
    background = ImageEnhance.Brightness(background).enhance(.50)
    background = ImageEnhance.Color(background).enhance(1.12)
    canvas = background.convert("RGBA")

    if layout == "full":
        full = ImageOps.fit(original, (width, height), method=Image.Resampling.LANCZOS, centering=(.5, .5))
        full = _enhance_uploaded_image(full)
        return Image.blend(canvas.convert("RGB"), full, .92)

    if layout == "split":
        media_h = int(height * .58)
        media = ImageOps.fit(original, (width, media_h), method=Image.Resampling.LANCZOS, centering=(.5, .5))
        media = _enhance_uploaded_image(media)
        canvas.alpha_composite(media.convert("RGBA"), (0, 0))
        panel = Image.new("RGBA", (width, height - media_h + 80), (3, 8, 17, 218))
        canvas.alpha_composite(panel, (0, media_h - 80))
        return canvas.convert("RGB")

    if layout == "quote":
        dark = Image.new("RGBA", (width, height), (4, 8, 17, 242))
        canvas = Image.blend(canvas, dark, .74)
        safe_w, safe_h = int(width * .78), int(height * .34)
        card = original.copy()
        card.thumbnail((safe_w, safe_h), Image.Resampling.LANCZOS)
        card = ImageEnhance.Brightness(_enhance_uploaded_image(card)).enhance(.82)
        _paste_shadowed(canvas, card, (width - card.width) // 2, int(height * .12), radius=24)
        return canvas.convert("RGB")

    if layout == "player":
        safe_w, safe_h = int(width * .88), int(height * .52)
        card = original.copy()
        card.thumbnail((safe_w, safe_h), Image.Resampling.LANCZOS)
        card = _enhance_uploaded_image(card)
        x = (width - card.width) // 2
        y = int(height * .13)
        frame = Image.new("RGBA", (card.width + 28, card.height + 28), (255, 255, 255, 0))
        fdraw = ImageDraw.Draw(frame)
        fdraw.rounded_rectangle((0, 0, frame.width - 1, frame.height - 1), radius=34, fill=(255, 255, 255, 20), outline=(255, 255, 255, 62), width=2)
        canvas.alpha_composite(frame, (x - 14, y - 14))
        _paste_shadowed(canvas, card, x, y, radius=26)
        hud = ImageDraw.Draw(canvas)
        hud.ellipse((int(width * .78), int(height * .075), int(width * .80), int(height * .087)), fill=(255, 68, 68, 235))
        hud.text((int(width * .81), int(height * .065)), "REC", font=_get_font(max(16, width // 38)), fill=(255, 255, 255, 225))
        return canvas.convert("RGB")

    safe_w = int(width * .92)
    safe_h = int(height * .70)
    foreground = original.copy()
    foreground.thumbnail((safe_w, safe_h), Image.Resampling.LANCZOS)
    foreground = _enhance_uploaded_image(foreground)
    x = (width - foreground.width) // 2
    y = int(height * .38 - foreground.height / 2)
    _paste_shadowed(canvas, foreground, x, y, radius=26)
    lower = Image.new("RGBA", (width, int(height * .34)), (0, 0, 0, 104))
    canvas.alpha_composite(lower, (0, int(height * .66)))
    return canvas.convert("RGB")


def _load_scene_image(image_url: str | None, width: int, height: int, layout: str = "auto") -> Image.Image | None:
    image_path = _uploaded_media_path(image_url)
    if not image_path or image_path.suffix.lower() in VIDEO_EXTENSIONS:
        return None
    try:
        original = Image.open(image_path).convert("RGB")
    except OSError:
        return None
    return _compose_uploaded_visual(original, width, height, layout)

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
        alpha = int(4 + 46 * ratio)
        draw.line((0, y, width, y), fill=(0, 0, 0, alpha))
    draw.rectangle((0, 0, width, int(height * .12)), fill=(0, 0, 0, 20))
    draw.rectangle((0, int(height * .74), width, height), fill=(0, 0, 0, 78))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def _draw_fast_visual_motif(draw, scene, accent, width: int, height: int):
    text = f"{scene.title} {scene.visual} {scene.subtitle}".lower()
    soft = tuple(min(255, int(v * 1.05)) for v in accent)
    if "campo" in text or "calcio" in text or "stadio" in text:
        horizon = int(height * .42)
        draw.rectangle((0, horizon, width, height), fill=(5, 22, 15))
        glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.ellipse((int(width * .10), int(height * .18), int(width * .90), int(height * .78)), fill=(*accent, 24))
        draw.bitmap((0, 0), glow.split()[-1], fill=soft)
        return
    if "codice" in text or "dashboard" in text or "dati" in text or "code" in text:
        for index in range(5):
            x = int(width * (.12 + index * .16))
            y = int(height * (.32 + (index % 2) * .12))
            draw.rounded_rectangle((x, y, x + int(width * .11), y + int(height * .075)), radius=18, fill=(255, 255, 255, 16), outline=(*accent, 38), width=2)
        return
    for radius in range(int(width * .68), int(width * .16), -34):
        alpha = max(16, int(70 * radius / (width * .68)))
        draw.ellipse((width // 2 - radius, int(height * .38) - radius, width // 2 + radius, int(height * .38) + radius), outline=(*accent, alpha), width=2)

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
    base_size = int(width * (.135 if scene_index == 1 else .118))
    font_size = max(42, base_size)
    font = _get_font(font_size)
    lines = _wrap_text(text, font, max_width, width, height)[:3]
    measure = ImageDraw.Draw(Image.new("RGB", (width, height)))
    while font_size > 34 and any((measure.textbbox((0, 0), line, font=font)[2] - measure.textbbox((0, 0), line, font=font)[0]) > max_width for line in lines):
        font_size -= 4
        font = _get_font(font_size)
        lines = _wrap_text(text, font, max_width, width, height)[:3]
    line_height = int(base_size * 1.02)
    block_h = len(lines) * line_height
    layout = _scene_attr(scene, "visual_layout", "auto")
    has_media = bool(_scene_attr(scene, "image_url", ""))
    if has_media and layout in {"split", "poster", "player"}:
        anchor = .73
    elif has_media and layout == "quote":
        anchor = .58
    elif has_media:
        anchor = .48
    else:
        anchor = .43 if scene_index == 1 else .48
    y = int(height * anchor) - block_h // 2
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
    # The live subtitle layer handles spoken text during motion.


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
    media_image = _load_scene_image(scene.image_url, width, height, _scene_attr(scene, "visual_layout", "auto"))
    img = media_image or _background_gradient(width, height, top, bottom)
    if media_image:
        img = _apply_photo_overlay(img, accent, width, height)
    img = img.convert("RGBA")
    draw = ImageDraw.Draw(img)
    if not media_image:
        _draw_fast_visual_motif(draw, scene, accent, width, height)
    if not media_image:
        _draw_particles(draw, scene, accent, width, height)
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
    has_media = bool(_scene_attr(scene, "image_url", ""))

    if not has_media and preset in {"social", "captions", "neon"}:
        glow_x = int(width * (.18 + .64 * progress))
        draw.ellipse((glow_x - int(width * .34), int(height * .12), glow_x + int(width * .34), int(height * .72)), fill=(*accent, int(10 + 20 * pulse)))

    if not has_media and preset == "sport":
        draw.ellipse((int(width * .08), int(height * .18), int(width * .92), int(height * .82)), outline=(*accent, 42), width=4)

    if not has_media and preset == "data":
        for index in range(4):
            x = int(width * (.12 + index * .19))
            y = int(height * (.24 + .04 * np.sin(progress * np.pi * 2 + index)))
            draw.rounded_rectangle((x, y, x + int(width * .13), y + int(height * .08)), radius=20, fill=(255, 255, 255, 14), outline=(*accent, 42), width=2)

    caption = " ".join((scene.voice_over or scene.subtitle or "").split())
    if caption:
        words = caption.split()
        shown = max(1, min(len(words), int(len(words) * min(1, progress * 1.35)) + 1))
        live_caption = " ".join(words[:shown])
        if len(live_caption.split()) > 8:
            live_caption = " ".join(live_caption.split()[-8:])
        font = _get_font(max(30, width // 20) if has_media else max(34, width // 18))
        lines = _wrap_text(live_caption.upper(), font, int(width * (.86 if has_media else .82)), width, height)[-2:]
        gradient = Image.new("RGBA", (width, int(height * .28)), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(gradient)
        for yy in range(gradient.height):
            alpha = int(170 * (yy / max(1, gradient.height - 1)))
            gdraw.line((0, yy, width, yy), fill=(0, 0, 0, alpha))
        overlay.alpha_composite(gradient, (0, height - gradient.height))
        line_h = int(width * .074)
        block_h = len(lines) * line_h
        tx_y = int(height * .80) - block_h // 2 + int(10 * (1 - min(1, progress * 5)))
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tx_x = (width - (bbox[2] - bbox[0])) // 2
            for dx, dy in [(-2, 3), (2, 3), (0, 5)]:
                draw.text((tx_x + dx, tx_y + dy), line, font=font, fill=(0, 0, 0, 210))
            draw.text((tx_x, tx_y), line, font=font, fill=(248, 251, 255, 245))
            tx_y += line_h
        progress_w = int(width * (.34 if has_media else .42) * min(1, progress * 1.08))
        bar_x = (width - int(width * (.34 if has_media else .42))) // 2
        bar_y = int(height * .89)
        draw.rounded_rectangle((bar_x, bar_y, bar_x + progress_w, bar_y + 5), radius=3, fill=(*accent, 210))

    if t < min(.26, duration * .15):
        p = 1 - (t / min(.26, duration * .15))
        draw.rectangle((0, 0, width, height), fill=(255, 255, 255, int(24 * p)))

    if t > duration - min(.24, duration * .14):
        p = (t - (duration - min(.24, duration * .14))) / min(.24, duration * .14)
        draw.rectangle((0, 0, width, height), fill=(0, 0, 0, int(52 * p)))

    return Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")

def _draw_text_brand_grade(img: Image.Image, scene, scene_index: int, accent, width: int, height: int) -> Image.Image:
    draw = ImageDraw.Draw(img)
    _draw_reel_text(draw, scene, scene_index, accent, width, height)
    icon = _get_brand_asset(width, full=False)
    if icon:
        img.alpha_composite(icon, (int(width * .83), int(height * .89)))
    return _apply_cinematic_grade(img.convert("RGB"), scene, width, height)


def _animate_uploaded_video_clip(scene, width: int, height: int, pacing: str, visual_style: str, accent, scene_index: int):
    path = _uploaded_media_path(scene.image_url)
    source = VideoFileClip(str(path))
    duration = scene.duration_seconds
    source_duration = max(.2, float(source.duration or duration))
    speed_factor = _motion_speed_factor(scene)

    def make_frame(t):
        progress = _ease(min(1.0, (t / max(duration, .01)) * _pacing_factor(pacing) * speed_factor))
        frame_time = min(source_duration - .05, (t * (1.0 + progress * .08)) % source_duration)
        frame = Image.fromarray(source.get_frame(frame_time)).convert("RGB")
        layout = _scene_attr(scene, "visual_layout", "full")
        img = _compose_uploaded_visual(frame, width, height, "full" if layout == "auto" else layout).convert("RGBA")
        img = _apply_photo_overlay(img, accent, width, height).convert("RGBA")
        img = _draw_text_brand_grade(img, scene, scene_index, accent, width, height)
        img = _draw_dynamic_overlays(img, scene, t, duration, visual_style, accent, width, height)
        return np.array(img)

    clip = VideoClip(frame_function=make_frame, duration=duration)
    clip._matchiq_source_clip = source
    return clip


def _animate_scene_clip(scene, scene_path: Path, width: int, height: int, pacing: str, visual_style: str, accent):
    duration = scene.duration_seconds
    motion = _motion_kind(scene)
    preset = _effect_preset(scene, visual_style)
    base_zoom = {"social": 1.10, "captions": 1.08, "neon": 1.12, "sport": 1.10, "data": 1.08, "editorial": 1.06}.get(preset, 1.08)
    requested_zoom = float(_scene_attr(scene, "zoom_level", base_zoom))
    zoom_level = max(base_zoom, min(1.22, requested_zoom))
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
            return int(max_x * (.34 + .32 * progress)), int(max_y * (.48 + .04 * progress))
        if motion == "scan":
            return int(max_x * (.45 + .10 * progress)), int(max_y * (.32 + .36 * progress))
        if motion == "reveal":
            return int(max_x * (.48 + .08 * progress)), int(max_y * (.56 - .16 * progress))
        if preset == "social":
            punch = .5 + .5 * np.sin(progress * np.pi * 3)
            return int(max_x * (.48 + .06 * progress + .015 * punch)), int(max_y * (.54 - .10 * progress))
        return int(max_x * (.46 + .08 * progress)), int(max_y * (.54 - .12 * progress))

    def make_frame(t):
        x, y = crop_origin(t)
        frame = source.crop((x, y, x + width, y + height))
        frame = _draw_dynamic_overlays(frame, scene, t, duration, visual_style, accent, width, height)
        return np.array(frame)

    return VideoClip(frame_function=make_frame, duration=duration)

def render_storyboard(storyboard: StoryboardPlan, tone: str, visual_style: str = "auto", pacing: str = "balanced", quality: str = "draft", music_enabled: bool = True, music_volume: float = 0.12, music_mood: str = "cinematic", voice_enabled: bool = True, voice_volume: float = 0.95, voice_style: str = "studio", voice_rate: int = -1, on_progress=None) -> tuple[str, Path]:
    is_draft = quality == "draft"
    width, height = (DRAFT_WIDTH, DRAFT_HEIGHT) if is_draft else (FINAL_WIDTH, FINAL_HEIGHT)
    fps = 20 if is_draft else 30
    preset = "ultrafast" if is_draft else "medium"
    video_bitrate = "2800k" if is_draft else "9500k"
    audio_bitrate = "128k" if is_draft else "192k"
    reel_id = uuid4().hex[:10]
    work_dir = RENDERS_DIR / reel_id
    work_dir.mkdir(parents=True, exist_ok=True)
    clips = []
    for index, scene in enumerate(storyboard.scenes, start=1):
        if on_progress:
            progress = 18 + int((index - 1) / len(storyboard.scenes) * 58)
            on_progress(progress, f"Sto preparando scena {index}: transizioni, testo vivo e sottotitoli animati...")
        scene_path = work_dir / f"scene_{index}.png"
        accent = TONE_BACKGROUNDS.get(tone, TONE_BACKGROUNDS["cinematic"])[2]
        if _is_video_media(scene.image_url):
            clips.append(_animate_uploaded_video_clip(scene, width, height, pacing, visual_style, accent, index))
        else:
            _draw_scene(storyboard, index, tone, visual_style, scene_path, width, height)
            clips.append(_animate_scene_clip(scene, scene_path, width, height, pacing, visual_style, accent))
    if on_progress:
        mode_label = "anteprima veloce" if is_draft else "qualita Pro 1080p"
        on_progress(82, f"Sto esportando il file MP4 in {mode_label}...")
    final = concatenate_videoclips(clips, method="compose")
    total_duration = sum(scene.duration_seconds for scene in storyboard.scenes)
    audio_tracks = []
    audio_clips_to_close = []
    if music_enabled:
        if on_progress:
            on_progress(88, "Sto aggiungendo musica e mix audio...")
        music_audio = build_music_bed(tone=tone, duration=total_duration, volume=min(max(music_volume, 0.08), 0.24), mood=music_mood)
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
    final.write_videofile(str(output_path), fps=fps, codec="libx264", audio=bool(audio_tracks), audio_codec="aac" if audio_tracks else None, audio_bitrate=audio_bitrate if audio_tracks else None, bitrate=video_bitrate, preset=preset, threads=4, logger=None)
    final.close()
    for audio_clip in audio_clips_to_close:
        audio_clip.close()
    for clip in clips:
        source_clip = getattr(clip, "_matchiq_source_clip", None)
        clip.close()
        if source_clip:
            source_clip.close()
    return filename, output_path
