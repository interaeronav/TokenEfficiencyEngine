"""Audio lane (7.4, items 6-8). Claude has no audio input - local
transcription is the ONLY channel for audio content. faster-whisper (MIT)
on CPU; speaker diarization is an optional HF-gated extra that degrades
silently to non-diarized transcription (never fails the ingest).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from tee.extract.video import ffmpeg_exe
from tee.kernel.errors import TeeError

AUDIO_EXTRACTOR = ("audio", "1")
DEFAULT_MODEL = os.environ.get("TEE_WHISPER_MODEL", "tiny")


def resample_wav(path: Path, out: Path) -> Path:
    """Any audio container -> 16 kHz mono WAV for the transcriber."""
    proc = subprocess.run(
        [
            ffmpeg_exe(),
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-y",
            str(out),
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode != 0 or not out.exists():
        raise TeeError("bad_audio", f"ffmpeg resample failed: {proc.stderr[-160:]}")
    return out


def extract_audio(
    path: Path, derived: Path, model_size: str = DEFAULT_MODEL
) -> list[dict[str, Any]]:
    wav = resample_wav(path, derived / "audio16k.wav")
    facts: list[dict[str, Any]] = []
    try:
        from faster_whisper import WhisperModel

        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(wav), vad_filter=True)
        transcript = []
        for segment in segments:
            text = segment.text.strip()
            if not text:
                continue
            transcript.append(
                {
                    "kind": "transcript_segment",
                    "start_s": round(segment.start, 2),
                    "end_s": round(segment.end, 2),
                    "text": text,
                }
            )
        facts.append(
            {
                "kind": "transcript",
                "language": info.language,
                "language_probability": round(float(info.language_probability), 2),
                "segments": len(transcript),
                "model": model_size,
            }
        )
        facts.extend(transcript)
    except Exception as exc:
        facts.append(
            {
                "kind": "note",
                "note": f"transcription unavailable ({type(exc).__name__}: {str(exc)[:120]}); "
                "audio has no other channel into the model - fix the whisper "
                "install or set TEE_WHISPER_MODEL",
            }
        )
    facts.extend(_diarize(wav))
    return facts


def _diarize(wav: Path) -> list[dict[str, Any]]:
    """Optional gated extra: pyannote models require accepted HF terms and a
    user token; anything missing degrades silently (A8)."""
    if not os.environ.get("HF_TOKEN"):
        return []
    try:
        import wave as wave_mod

        import numpy as np
        import torch
        from pyannote.audio import Pipeline  # optional, never a dependency

        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-community-1",
            token=os.environ["HF_TOKEN"],  # pyannote 4.x name (was use_auth_token)
        )
        # Decode with stdlib wave and hand the tensor over: pyannote 4.x file
        # input goes through torchcodec, whose native lib is torch-version
        # locked and absent/broken on many installs. The wav here is always
        # resample_wav's own 16 kHz mono output, so stdlib decoding is safe.
        with wave_mod.open(str(wav)) as w:
            rate = w.getframerate()
            pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        waveform = torch.from_numpy(pcm.astype(np.float32) / 32768.0).unsqueeze(0)
        annotation = pipeline({"waveform": waveform, "sample_rate": rate})
        # 4.x wraps the Annotation in a DiarizeOutput; 3.x returns it bare.
        annotation = getattr(annotation, "speaker_diarization", annotation)
        turns = [
            {
                "kind": "speaker_turn",
                "start_s": round(turn.start, 2),
                "end_s": round(turn.end, 2),
                "speaker": speaker,
            }
            for turn, _, speaker in annotation.itertracks(yield_label=True)
        ]
        return turns[:200]
    except (ImportError, KeyError):
        # the optional extra is absent or ungated (no HF_TOKEN): expected on
        # plain installs - stay silent
        return []
    except Exception as exc:
        # the lane exists but broke: this exact catch once hid three
        # pyannote-4.x API drifts (fixed 4fb7842). Degrade to one visible
        # marker fact instead of vanishing, still never failing the ingest.
        return [
            {
                "kind": "diarization_unavailable",
                "reason": f"{type(exc).__name__}: {exc}"[:120],
            }
        ]


REQUIREMENTS_PROMPT = (
    "Read the transcript segments of this client briefing (ex_facts, kind="
    "'transcript_segment') and store structured requirement facts via "
    "ex_store_facts with extractor='requirements'. Each fact: {kind: "
    "'requirement', tier: 'stated_requirement', topic: <bedrooms|orientation|"
    "budget|material|other>, statement: <short paraphrase>, quote: <verbatim "
    "supporting words>, t: <segment start_s>}. Only requirements actually "
    "stated - no inferences."
)
