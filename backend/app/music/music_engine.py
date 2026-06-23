import math

import numpy as np
from moviepy import AudioClip


MOOD_PRESETS = {
    "cinematic": {"root": 55, "third": 65.41, "fifth": 82.41, "top": 196, "bpm": 92, "drive": .55, "pad": .42},
    "premium": {"root": 49, "third": 61.74, "fifth": 73.42, "top": 146.83, "bpm": 84, "drive": .32, "pad": .54},
    "startup": {"root": 65.41, "third": 82.41, "fifth": 98, "top": 220, "bpm": 104, "drive": .48, "pad": .38},
    "sport": {"root": 55, "third": 82.41, "fifth": 110, "top": 220, "bpm": 116, "drive": .70, "pad": .30},
    "emotional": {"root": 43.65, "third": 55, "fifth": 65.41, "top": 164.81, "bpm": 78, "drive": .22, "pad": .58},
    "provocative": {"root": 55, "third": 69.3, "fifth": 82.41, "top": 196, "bpm": 108, "drive": .64, "pad": .35},
    "cinematic_lift": {"root": 55, "third": 65.41, "fifth": 82.41, "top": 196, "bpm": 96, "drive": .46, "pad": .50},
    "sport_hype": {"root": 55, "third": 82.41, "fifth": 110, "top": 246.94, "bpm": 124, "drive": .78, "pad": .26},
    "club_energy": {"root": 65.41, "third": 82.41, "fifth": 98, "top": 261.63, "bpm": 118, "drive": .66, "pad": .30},
    "luxury_minimal": {"root": 49, "third": 61.74, "fifth": 73.42, "top": 146.83, "bpm": 82, "drive": .24, "pad": .62},
    "deep_focus": {"root": 43.65, "third": 55, "fifth": 65.41, "top": 130.81, "bpm": 74, "drive": .18, "pad": .70},
    "bright_launch": {"root": 65.41, "third": 82.41, "fifth": 98, "top": 220, "bpm": 108, "drive": .52, "pad": .36},
}


def _as_stereo(signal, pan=0.0):
    audio = np.asarray(signal, dtype=float)
    pan_value = np.asarray(pan, dtype=float)
    left_gain = 1 - np.maximum(0, pan_value) * .25
    right_gain = 1 + np.minimum(0, pan_value) * .25
    if audio.ndim == 0:
        return np.array([float(audio * left_gain), float(audio * right_gain)])
    return np.column_stack((audio * left_gain, audio * right_gain))


def _sine(time, freq, amount=1.0):
    return amount * np.sin(2 * math.pi * freq * time)


def _soft_clip(signal):
    return np.tanh(signal * 1.35) * .82


def _beat_envelope(time, bpm, width=.11):
    beat = 60.0 / bpm
    phase = np.mod(time, beat)
    return np.exp(-phase / width)


def _sidechain_curve(time, duration):
    scene_len = max(2.0, duration / 5)
    phase = np.mod(time, scene_len) / scene_len
    return np.where((phase > .18) & (phase < .76), .58, .96)


def build_music_bed(tone: str, duration: float, volume: float = 0.12, mood: str | None = None):
    selected = (mood or tone or "cinematic").lower()
    preset = MOOD_PRESETS.get(selected, MOOD_PRESETS.get(tone, MOOD_PRESETS["cinematic"]))
    bpm = preset["bpm"]
    safe_volume = max(0.0, min(0.26, volume))

    def frame_function(t):
        time = np.asarray(t, dtype=float)
        fade_in = np.minimum(1.0, time / 1.3)
        fade_out = np.minimum(1.0, np.maximum(0.0, (duration - time) / 1.6))
        duck = _sidechain_curve(time, duration)

        root = preset["root"]
        third = preset["third"]
        fifth = preset["fifth"]
        top = preset["top"]

        warm_pad = (
            _sine(time, root, .48)
            + _sine(time, third, .22)
            + _sine(time, fifth, .20)
            + _sine(time, root / 2, .28)
        ) * preset["pad"]

        slow_filter = .72 + .28 * np.sin(2 * math.pi * time / 7.5)
        warm_pad *= slow_filter

        beat = _beat_envelope(time, bpm, width=.075)
        sub = np.sin(2 * math.pi * 46 * np.mod(time, 60 / bpm)) * beat * preset["drive"] * .18

        hat_phase = np.mod(time, (60 / bpm) / 2)
        soft_hat = np.exp(-hat_phase / .025) * .018 * np.sin(2 * math.pi * 8200 * hat_phase)

        arp = np.zeros_like(time)
        step_len = (60 / bpm) / 2
        notes = [root * 2, third * 2, fifth * 2, top]
        for i, note in enumerate(notes):
            local = np.maximum(0, time - i * step_len)
            phase = np.mod(local, step_len * len(notes))
            active = phase < step_len
            env = np.exp(-np.mod(phase, step_len) / .18) * active
            arp += np.sin(2 * math.pi * note * np.mod(phase, step_len)) * env * .045

        riser = .018 * np.sin(2 * math.pi * (180 + 40 * np.sin(time * .22)) * time)
        signal = warm_pad + sub + soft_hat + arp + riser
        signal = _soft_clip(signal) * fade_in * fade_out * duck * safe_volume
        return _as_stereo(signal, pan=.08 * np.sin(time / 3))

    return AudioClip(frame_function, duration=duration, fps=44100)
