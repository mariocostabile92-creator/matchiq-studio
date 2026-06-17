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
}


def synthesize_scene_voice(
    text: str,
    output_path: Path,
    volume: float = 0.95,
    style: str = "studio",
    rate: int | None = None,
) -> Path | None:
    clean_text = " ".join((text or "").split())
    if not clean_text:
        return None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    script_path = output_path.parent / "matchiq_tts.ps1"
    script_path.write_text(TTS_SCRIPT, encoding="utf-8")

    safe_volume = int(max(0, min(100, round(volume * 100))))
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
