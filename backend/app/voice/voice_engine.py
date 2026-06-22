import asyncio
import re
import shutil
import subprocess
from pathlib import Path


TTS_SCRIPT = r"""
param(
  [Parameter(Mandatory=$true)][string]$Text,
  [Parameter(Mandatory=$true)][string]$OutputPath,
  [int]$Rate = 0,
  [int]$Volume = 100
)

Add-Type -AssemblyName System.Speech
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speaker.Rate = $Rate
$speaker.Volume = $Volume

$italianVoice = $speaker.GetInstalledVoices() |
  Where-Object { $_.VoiceInfo.Culture.Name -eq "it-IT" } |
  Select-Object -First 1

if ($italianVoice) {
  $speaker.SelectVoice($italianVoice.VoiceInfo.Name)
}

$speaker.SetOutputToWaveFile($OutputPath)
$speaker.Speak($Text)
$speaker.Dispose()
"""


VOICE_STYLE_RATES = {
    "calm": -2,
    "studio": -1,
    "energetic": 1,
    "epic": 0,
}

EDGE_VOICES = {
    "calm": "it-IT-ElsaNeural",
    "studio": "it-IT-IsabellaNeural",
    "energetic": "it-IT-DiegoNeural",
    "epic": "it-IT-DiegoNeural",
}


def prepare_voice_script(text: str, style: str = "studio") -> str:
    clean_text = " ".join((text or "").split())
    if not clean_text:
        return ""

    clean_text = re.sub(r"\s*([.!?])\s*", r"\1 ", clean_text)
    clean_text = clean_text.replace("...", ". ")
    clean_text = clean_text.replace("MatchIQ", "Match I Q")

    if style in {"studio", "epic"}:
        clean_text = clean_text.replace(". ", ".  ")
        clean_text = clean_text.replace("? ", "?  ")
        clean_text = clean_text.replace("! ", "!  ")

    return clean_text.strip()


def _windows_tts(clean_text: str, output_path: Path, volume: float, style: str, rate: int | None) -> Path | None:
    if not shutil.which("powershell"):
        return None

    script_path = output_path.parent / "matchiq_tts.ps1"
    script_path.write_text(TTS_SCRIPT, encoding="utf-8")
    safe_volume = int(max(0, min(100, round(max(volume, 0.96) * 100))))
    safe_rate = max(-4, min(3, rate if rate is not None else VOICE_STYLE_RATES.get(style, -1)))
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        "-Text",
        clean_text,
        "-OutputPath",
        str(output_path),
        "-Rate",
        str(safe_rate),
        "-Volume",
        str(safe_volume),
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
    except (subprocess.SubprocessError, OSError):
        return None

    if not output_path.exists() or output_path.stat().st_size == 0:
        return None
    return output_path


async def _edge_tts(clean_text: str, output_path: Path, volume: float, style: str, rate: int | None) -> Path | None:
    try:
        import edge_tts
    except ImportError:
        return None

    voice = EDGE_VOICES.get(style, EDGE_VOICES["studio"])
    edge_path = output_path.with_suffix(".mp3")
    rate_value = rate if rate is not None else VOICE_STYLE_RATES.get(style, -1)
    rate_percent = max(-35, min(28, int(rate_value * 9)))
    volume_percent = max(0, min(60, int((max(volume, 0.98) - 1) * 100)))
    communicate = edge_tts.Communicate(
        clean_text,
        voice=voice,
        rate=f"{rate_percent:+d}%",
        volume=f"{volume_percent:+d}%",
    )
    await communicate.save(str(edge_path))
    if not edge_path.exists() or edge_path.stat().st_size == 0:
        return None
    return edge_path


def synthesize_scene_voice(
    text: str,
    output_path: Path,
    volume: float = 1.0,
    style: str = "studio",
    rate: int | None = None,
) -> Path | None:
    clean_text = prepare_voice_script(text, style=style)
    if not clean_text:
        return None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    windows_path = _windows_tts(clean_text, output_path, volume=volume, style=style, rate=rate)
    if windows_path:
        return windows_path

    try:
        return asyncio.run(_edge_tts(clean_text, output_path, volume=volume, style=style, rate=rate))
    except Exception:
        return None
