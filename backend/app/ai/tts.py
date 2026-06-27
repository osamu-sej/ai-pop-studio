"""Local text-to-speech for podcast audio.

All options run on-device with no API:
- **piper**: high-quality neural voices (needs a downloaded .onnx voice).
- **pyttsx3**: uses the OS speech engine (espeak / SAPI / NSSpeech), offline.
- **none**: no audio — the podcast transcript is still produced.

If neither engine is installed the feature degrades to "script only", which is
still useful (read it, or paste into any TTS later).
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import wave
from pathlib import Path

from ..config import get_settings


class BaseTTS:
    name = "none"

    def available(self) -> bool:
        return False

    def synthesize(self, segments: list[dict], out_path: Path) -> bool:
        return False


class Pyttsx3TTS(BaseTTS):
    name = "pyttsx3"

    def available(self) -> bool:
        return importlib.util.find_spec("pyttsx3") is not None

    def synthesize(self, segments: list[dict], out_path: Path) -> bool:
        import pyttsx3  # optional

        engine = pyttsx3.init()
        voices = engine.getProperty("voices") or []
        # Map up to two distinct speakers onto two different system voices.
        speakers = list(dict.fromkeys(s["speaker"] for s in segments))
        voice_for = {}
        for i, sp in enumerate(speakers):
            if voices:
                voice_for[sp] = voices[i % len(voices)].id

        tmp_dir = out_path.parent / (out_path.stem + "_parts")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        parts: list[Path] = []
        for i, seg in enumerate(segments):
            if seg["speaker"] in voice_for:
                engine.setProperty("voice", voice_for[seg["speaker"]])
            part = tmp_dir / f"{i:04d}.wav"
            engine.save_to_file(seg["text"], str(part))
            engine.runAndWait()
            if part.exists():
                parts.append(part)
        if not parts:
            return False
        _concat_wavs(parts, out_path)
        for p in parts:
            p.unlink(missing_ok=True)
        tmp_dir.rmdir()
        return out_path.exists()


class PiperTTS(BaseTTS):
    name = "piper"

    def available(self) -> bool:
        s = get_settings()
        return bool(shutil.which("piper")) and bool(s.piper_model_path) and Path(s.piper_model_path).exists()

    def synthesize(self, segments: list[dict], out_path: Path) -> bool:
        s = get_settings()
        tmp_dir = out_path.parent / (out_path.stem + "_parts")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        parts: list[Path] = []
        for i, seg in enumerate(segments):
            part = tmp_dir / f"{i:04d}.wav"
            try:
                subprocess.run(
                    ["piper", "--model", s.piper_model_path, "--output_file", str(part)],
                    input=seg["text"].encode("utf-8"), check=True, capture_output=True,
                )
            except Exception:
                continue
            if part.exists():
                parts.append(part)
        if not parts:
            return False
        _concat_wavs(parts, out_path)
        for p in parts:
            p.unlink(missing_ok=True)
        tmp_dir.rmdir()
        return out_path.exists()


def _concat_wavs(parts: list[Path], out_path: Path) -> None:
    with wave.open(str(parts[0]), "rb") as w0:
        params = w0.getparams()
    with wave.open(str(out_path), "wb") as out:
        out.setparams(params)
        for p in parts:
            with wave.open(str(p), "rb") as w:
                out.writeframes(w.readframes(w.getnframes()))


def build_tts() -> BaseTTS:
    from . import runtime

    provider = str(runtime.value("tts_provider") or "auto").lower()
    if provider == "pyttsx3":
        return Pyttsx3TTS()
    if provider == "piper":
        return PiperTTS()
    if provider == "none":
        return BaseTTS()
    for tts in (PiperTTS(), Pyttsx3TTS()):  # auto
        if tts.available():
            return tts
    return BaseTTS()


def get_tts() -> BaseTTS:
    return build_tts()
