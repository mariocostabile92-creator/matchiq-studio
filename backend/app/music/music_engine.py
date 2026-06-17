import math

import numpy as np
from moviepy import AudioClip


MOOD_NOTES = {
    "cinematic": (196, 247, 294, 392),
    "startup": (220, 277, 330, 440),
    "premium": (174, 220, 261, 349),
    "provocative": (196, 233, 294, 392),
}


def _pluck(time, note, offset, decay=3.4):
    local = np.maximum(0, time - offset)
    active = (time >= offset).astype(float)
    envelope = np.exp(-decay * local) * active
    tone = np.sin(2 * math.pi * note * local) + 0.35 * np.sin(2 * math.pi * note * 2 * local)
    return tone * envelope


def _as_stereo(signal):
    audio = np.asarray(signal, dtype=float)
    if audio.ndim == 0:
        return np.array([float(audio), float(audio)])

    return np.column_stack((audio, audio))


def build_music_bed(tone: str, duration: float, volume: float = 0.08):
    """Create a very subtle placeholder bed.

    This is intentionally restrained: it should sit under the video, not sound
    like a synthetic horror soundtrack. Real licensed/AI music can replace this
    engine later without changing the render pipeline.
    """

    notes = MOOD_NOTES.get(tone, MOOD_NOTES["cinematic"])
    safe_volume = max(0.0, min(0.25, volume))

    def frame_function(t):
        time = np.asarray(t)
        phrase = np.zeros_like(time, dtype=float)

        for step in range(int(duration * 2) + 4):
            note = notes[step % len(notes)]
            phrase += _pluck(time, note, step * 0.5, decay=4.8)

        pad = (
            0.20 * np.sin(2 * math.pi * notes[0] / 2 * time)
            + 0.12 * np.sin(2 * math.pi * notes[1] / 2 * time)
        )
        shimmer = 0.035 * np.sin(2 * math.pi * notes[-1] * 2 * time)
        signal = 0.18 * phrase + pad + shimmer
        fade_in = np.minimum(1.0, time / 1.2)
        fade_out = np.minimum(1.0, np.maximum(0.0, (duration - time) / 1.4))
        return _as_stereo(safe_volume * signal * fade_in * fade_out)

    return AudioClip(frame_function, duration=duration, fps=44100)
