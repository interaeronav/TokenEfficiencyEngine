"""A47 — senses a model can borrow when it has none of its own.

The owner ran DeepSeek locally as the HOST model, in opencode, driving TEE
over MCP, and asked it about an image. TEE answered that machine vision was
not a feature it offered. **That was true**, and it was true for an
architectural reason: decision A9 makes the default extraction channel
in-band - `ex_prepare` hands the host file paths because "it reads media
with its own tools" - which assumed the host was Claude. `tee_media` and
`tee_capture` return pixels. To a seeing host that is the efficient answer;
to a blind one it is a payload it cannot read.

Meanwhile `kernel/local_vlm.py` is a working local vision client, and
`extract/vlm.py` holds a `LocalVlmDriver` that `ex_prepare` even advertises
as "available (free, on-machine)" - while no code path has ever called it.
This module is the steering wheel that driver never had.

**Three rules, and the third is the point.**

1. Never silent. Every answer names the provider that produced it, and the
   swap cost if one was paid. A description arriving as if the asking model
   had seen the image is the failure this feature exists to prevent, not a
   convenience it offers.
2. Refuse rather than improvise. No provider - a TeeError with the exact
   fix. Never a plausible guess about pixels nobody looked at.
3. A description is not sight. The model reasoning over this answer never
   saw the image; it is reading a summary another model wrote, with that
   model's choices about what mattered. Every payload says so.

The token case is the quiet one: a 4K site frame costs the local provider
2,065 input tokens and hands back a 63-token answer - 33x, and the 2,065
are spent on a model that bills nothing.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

# Re-encoded to JPEG before sending: the VL server takes what browsers take,
# and HEIC (the owner's iPhone format) is not on that list.
_RECODE = frozenset({".heic", ".heif", ".hif", ".heics", ".avif"})
_DIRECT = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
           ".webp": "image/webp", ".gif": "image/gif", ".bmp": "image/bmp"}  # fmt: skip

ANSWER_TOKENS_DEFAULT = 300
ANSWER_TOKENS_CAP = 1200

# Above this, the provider was cold and the host's model was evicted to make
# room. Measured 2026-08-31: warm vision calls land at 0.8-4.0 s, a cold
# start (which kills the 84 GB session model first) at 7.5-10 s.
COLD_START_S = 6.0

NOT_SIGHT = (
    "A description, not the image. The model reading this never saw the "
    "pixels - it is reading a summary another model wrote, including that "
    "model's choices about what was worth mentioning."
)


def _cache_path(state_dir: Path) -> Path:
    return Path(state_dir) / "senses-cache.json"


def _cache_key(payload: bytes, question: str, context: str, model: str) -> str:
    """Exact content hash, deliberately NOT a perceptual hash.

    `extract/images.py` has phash dedupe and it would be the wrong tool
    here: two frames a hamming-5 apart are 'the same photo' for grouping and
    emphatically not the same photo for 'what does this label say'. Serving
    a cached reading of a NEARLY identical card is precisely the confident
    wrong answer this module exists to prevent.
    """
    h = hashlib.sha256()
    h.update(payload)
    h.update(b"\x00")
    h.update(question.encode())
    h.update(b"\x00")
    h.update(context.encode())
    h.update(b"\x00")
    h.update(model.encode())
    return h.hexdigest()


def _load_cache(state_dir: Path | None) -> dict[str, Any]:
    if not state_dir:
        return {}
    p = _cache_path(state_dir)
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_cache(state_dir: Path | None, cache: dict[str, Any]) -> None:
    if not state_dir:
        return
    try:
        p = _cache_path(state_dir)
        p.parent.mkdir(parents=True, exist_ok=True)
        # Bounded: the newest 200 answers. A cache that grows without limit
        # in a state dir nobody prunes is a slow leak, not a feature.
        if len(cache) > 200:
            for k in list(cache)[: len(cache) - 200]:
                cache.pop(k, None)
        p.write_text(json.dumps(cache))
    except OSError:
        pass  # a read-only state dir must not fail the answer


def _image_payload(path: Path) -> tuple[bytes, str]:
    """(bytes, media_type) the vision server will accept."""
    suffix = path.suffix.lower()
    if suffix in _RECODE:
        # v0.11.0's door: HEIC opens here or nowhere.
        import io

        from tee.kernel.imaging import open_image

        with open_image(path) as img:
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality=88)
        return buf.getvalue(), "image/jpeg"
    if suffix in _DIRECT:
        return path.read_bytes(), _DIRECT[suffix]
    raise TeeError(
        "sense_unsupported_media",
        f"{path.name} is not an image type the vision provider reads.",
        fix=f"Supported: {', '.join(sorted(set(_DIRECT) | _RECODE))}.",
    )


def describe(spec: dict[str, Any], *, state_dir: Path | None = None) -> dict[str, Any]:
    """Borrow an eye: one question about one image, answered as text."""
    from tee.kernel import local_vlm
    from tee.kernel.machine import ENGINES

    raw = str(spec.get("path") or "").strip()
    if not raw:
        raise TeeError(
            "sense_no_path", "sense_describe needs an image path.", fix='Pass {"path": "..."}.'
        )
    path = Path(raw).expanduser()
    if not path.is_file():
        raise TeeError(
            "sense_missing_file", f"No such image: {path}", fix="Pass a path that exists."
        )
    question = str(spec.get("question") or "Describe this image in two sentences.").strip()
    context = str(spec.get("context") or "").strip()
    budget = max(32, min(int(spec.get("max_tokens") or ANSWER_TOKENS_DEFAULT), ANSWER_TOKENS_CAP))
    model = local_vlm.DEFAULT_MODEL

    payload, media_type = _image_payload(path)
    key = _cache_key(payload, question, context, model)
    cache = _load_cache(state_dir)
    hit = cache.get(key)

    # Context in front of the question: measured to work - given "the
    # drawings say gable G3 is solid plastered", the provider answered the
    # DELTA against that spec rather than captioning the wall.
    asked = f"Context: {context}\n\nQuestion: {question}" if context else question

    if hit:
        answer, wall, cached = hit["answer"], 0.0, True
    else:
        started = time.monotonic()
        answer = local_vlm.describe(
            payload, asked, model=model, media_type=media_type, max_tokens=budget
        ).strip()
        wall = time.monotonic() - started
        cached = False
        cache[key] = {"answer": answer}
        _save_cache(state_dir, cache)

    qvl = ENGINES.get("qvl", {})
    out: dict[str, Any] = {
        "ok": True,
        "answer": answer,
        "sense": "vision",
        "provided_by": f"{model} (local, {qvl.get('footprint_gb', '?')} GB)",
        "cached": cached,
        "cost": {
            "answer_tokens_max": budget,
            "wall_s": round(wall, 2),
            "off_machine_calls": 0,
            "usd": 0.0,
        },
        "note": NOT_SIGHT,
    }
    evicts = qvl.get("evicts") or []
    if not cached and wall >= COLD_START_S and evicts:
        out["swap_note"] = (
            f"the vision provider was cold, which evicts {', '.join(evicts)} on "
            f"this machine - the next text turn pays ~{qvl.get('cost', {}).get('swap_s', '?')}s "
            "to reload it. Ask all image questions together to pay this once."
        )
    return out


def transcribe(spec: dict[str, Any], *, state_dir: Path | None = None) -> dict[str, Any]:
    """Borrow an ear: speech in an audio or video file, answered as text."""
    from tee.kernel.machine import ENGINES

    raw = str(spec.get("path") or "").strip()
    if not raw:
        raise TeeError(
            "sense_no_path", "sense_transcribe needs an audio path.", fix='Pass {"path": "..."}.'
        )
    path = Path(raw).expanduser()
    if not path.is_file():
        raise TeeError(
            "sense_missing_file", f"No such file: {path}", fix="Pass a path that exists."
        )
    size = str(spec.get("model_size") or "base").lower()
    if size not in ("tiny", "base", "small", "medium", "large-v3"):
        raise TeeError(
            "sense_bad_model",
            f"'{size}' is not a whisper size.",
            fix="Use tiny, base, small, medium or large-v3. base is the "
            "measured default (0.62 s on a spoken fixture).",
        )
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise TeeError(
            "sense_audio_unavailable",
            "Transcription needs faster-whisper, which is not installed.",
            fix="uv pip install 'tee-engine[extract]'",
        ) from exc

    key = _cache_key(path.read_bytes(), "transcribe", size, "faster-whisper")
    cache = _load_cache(state_dir)
    hit = cache.get(key)
    if hit:
        text = hit["answer"]
        segments = hit.get("segments", [])
        lang = hit.get("lang")
        wall, cached = 0.0, True
    else:
        started = time.monotonic()
        model = WhisperModel(size, device="cpu", compute_type="int8")
        segs, info = model.transcribe(str(path))
        collected = [
            {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
            for s in segs
        ]
        text = " ".join(s["text"] for s in collected).strip()
        wall = time.monotonic() - started
        lang = info.language
        segments, cached = collected, False
        cache[key] = {"answer": text, "segments": collected, "lang": lang}
        _save_cache(state_dir, cache)

    wh = ENGINES.get("whisper", {})
    out: dict[str, Any] = {
        "ok": True,
        "answer": text or "(no speech detected)",
        "sense": "audio",
        "language": lang,
        "provided_by": f"faster-whisper {size} (local, {wh.get('footprint_gb', '?')} GB)",
        "cached": cached,
        "cost": {"wall_s": round(wall, 2), "off_machine_calls": 0, "usd": 0.0},
        "note": "A transcript, not the audio. Speech only - tone, speaker "
        "identity and non-speech sound are not captured.",
    }
    if spec.get("segments"):
        out["segments"] = segments
    return out


def register_sense_tools(app, project_root: str | Path) -> None:
    """Register sense_* as virtual tools (the surface stays 17)."""
    from tee.kernel.registry import VirtualTool

    state = Path(project_root) / ".tee"

    def sense_describe(args: dict[str, Any]) -> dict[str, Any]:
        return describe(args, state_dir=state)

    def sense_transcribe(args: dict[str, Any]) -> dict[str, Any]:
        return transcribe(args, state_dir=state)

    app.registry.register(
        VirtualTool(
            name="sense_describe",
            description=(
                "Machine VISION for a model that has none: ask one question "
                "about one image file and get TEXT back. Runs on this "
                "machine's local vision model - free, nothing leaves the "
                "machine. Use this instead of tee_media/tee_capture if you "
                "cannot read images yourself. Pass `context` (what the "
                "drawings say, what you expect) and the answer addresses "
                "that rather than merely captioning."
            ),
            schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Image file to look at."},
                    "question": {"type": "string"},
                    "context": {
                        "type": "string",
                        "description": "What you already know; the answer will address it.",
                    },
                    "max_tokens": {"type": "integer"},
                },
                "required": ["path"],
            },
            handler=sense_describe,
            tags=[
                "sense",
                "vision",
                "image",
                "photo",
                "describe",
                "look",
                "see",
                "machine vision",
                "caption",
                "ocr",
                "read image",
            ],  # fmt: skip
            examples=[
                {
                    "path": "site/frame_012.jpg",
                    "context": "The drawings say gable G3 is solid plastered brick.",
                    "question": "Does the gable match the spec? What differs?",
                }
            ],
        )
    )

    app.registry.register(
        VirtualTool(
            name="sense_transcribe",
            description=(
                "HEARING for a model that has none: speech in an audio or "
                "video file, returned as text. Runs locally on "
                "faster-whisper - free, nothing leaves the machine. "
                "segments=true adds timestamps."
            ),
            schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "model_size": {
                        "type": "string",
                        "enum": ["tiny", "base", "small", "medium", "large-v3"],
                    },
                    "segments": {"type": "boolean"},
                },
                "required": ["path"],
            },
            handler=sense_transcribe,
            tags=[
                "sense",
                "audio",
                "transcribe",
                "speech",
                "listen",
                "hear",
                "sound",
                "voice",
                "recording",
                "subtitle",
            ],  # fmt: skip
            examples=[{"path": "site/walkthrough.m4a", "model_size": "base"}],
        )
    )
