import math

import numpy as np
from moviepy import AudioClip


MOOD_PRESETS = {
    "cinematic": {
        "notes": (98, 147, 196, 247),
        "kick": 0.72,
        "pulse": 0.22,
        "pad": 0.16,
        "shimmer": 0.012,
    },
    "startup": {
        "notes": (110, 165, 220, 330),
        "kick": 0.58,
        "pulse": 0.26,
        "pad": 0.13,
        "shimmer": 0.018,
    },
    "premium": {
        "notes": (87, 130, 174, 261),
        "kick": 0.42,
        "pulse": 0.14,
        "pad": 0.20,
        "shimmer": 0.010,
    },
    "provocative": {
        "notes": (98, 146, 196, 294),
        "kick": 0.78,
        "pulse": 0.30,
        "pad": 0.12,
        "shimmer": 0.016,
    },
    "sport": {
        "notes": (110, 165, 220, 440),
        "kick": 0.86,
        "pulse": 0.34,
        "pad": 0.10,
        "shimmer": 0.020,
    },
    "emotional": {
        "notes": (82, 123, 164, 246),
        "kick": 0.26,
        "pulse": 0.10,
        "pad": 0.24,
        "shimmer": 0.008,
    },
}


def _as_stereo(signal):
    audio = np.asarray(signal, dtype=float)
    if audio.ndim == 0:
        return np.array([float(audio), float(audio)])
    return np.column_stack((audio, audio))


def _pluck(time, note, offset, decay=5.2):
    local = np.maximum(0, time - offset)
    active = (time >= offset).astype(float)
    envelope = np.exp(-decay * local) * active
    tone = np.sin(2 * math.pi * note * local) + 0.22 * np.sin(2 * math.pi * note * 2 * local)
    return tone * envelope


def _soft_kick(time, bpm: float, strength: float):
    beat = 60.0 / bpm
    phase = np.mod(time, beat)
    envelope = np.exp(-18 * phase)
    low = np.sin(2 * math.pi * 58 * phase)
    return strength * low * envelope


def _ducking_curve(time, duration: float):
    """Keep music under voice: lower in the center of most scenes."""
    scene_len = max(2.0, duration / 5)
    phase = np.mod(time, scene_len) / scene_len
    # Quieter during likely voice-over window, fuller during transitions.
    return np.where((phase > 0.12) & (phase < 0.78), 0.46, 0.82)


def build_music_bed(tone: str, duration: float, volume: float = 0.06, mood: str | None = None):
    """Create a cleaner placeholder music bed with automatic ducking.

    This still is not licensed music, but it is less invasive, more modern and
    designed to stay behind the voice-over.
    """

    selected = mood or tone or "cinematic"
    preset = MOOD_PRESETS.get(selected, MOOD_PRESETS.get(tone, MOOD_PRESETS["cinematic"]))
    notes = preset["notes"]

    # Never let generated placeholder music dominate the voice.
    safe_volume = max(0.0, min(0.12, volume))
    bpm = 92 if selected in {"premium", "emotional"} else 112 if selected == "sport" else 104

    def frame_function(t):
        time = np.asarray(t)
        phrase = np.zeros_like(time, dtype=float)

        for step in range(int(duration * 1.5) + 6):
            note = notes[step % len(notes)]
            phrase += _pluck(time, note, step * 0.66, decay=5.8)

        pad = (
            preset["pad"] * np.sin(2 * math.pi * notes[0] / 2 * time)
            + (preset["pad"] * 0.55) * np.sin(2 * math.pi * notes[1] / 2 * time)
        )
        pulse = preset["pulse"] * np.sin(2 * math.pi * notes[-1] / 4 * time)
        shimmer = preset["shimmer"] * np.sin(2 * math.pi * notes[-1] * 2 * time)
        kick = _soft_kick(time, bpm=bpm, strength=preset["kick"] * 0.11)

        signal = 0.16 * phrase + pad + pulse + shimmer + kick

        fade_in = np.minimum(1.0, time / 1.0)
        fade_out = np.minimum(1.0, np.maximum(0.0, (duration - time) / 1.2))
        ducking = _ducking_curve(time, duration)

        return _as_stereo(safe_volume * signal * fade_in * fade_out * ducking)

    return AudioClip(frame_function, duration=duration, fps=44100)
