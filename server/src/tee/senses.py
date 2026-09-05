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

# Any machine's own facts land here from [senses] in .tee/config.toml; the
# code carries NO owner-specific value. `machine.ENGINES` keeps this
# machine's measured rows as the documented example, and config overrides
# them wholesale for other users:
#
#   [senses]
#   vision_url   = "http://127.0.0.1:4000/v1"   # any OpenAI-style endpoint
#   vision_model = "claude-qwen-vl"
#   vision_footprint_gb = 17.0
#   vision_evicts = ["dsflash"]     # models this machine must park first
#   vision_swap_s = 10.0            # what that costs, if measured
_CFG: dict[str, Any] = {}


def configure(senses_cfg: dict[str, Any] | None) -> None:
    """Called at registration with [senses] from the project config."""
    _CFG.clear()
    _CFG.update(senses_cfg or {})


def _vision_facts() -> tuple[str | None, str | None, dict[str, Any]]:
    """(url, model, engine-row facts) - config first, ENGINES as fallback."""
    from tee.kernel.machine import ENGINES

    row = dict(ENGINES.get("qvl") or {})
    if "vision_footprint_gb" in _CFG:
        row["footprint_gb"] = _CFG["vision_footprint_gb"]
    if "vision_evicts" in _CFG:
        row["evicts"] = list(_CFG["vision_evicts"])
        row.setdefault("cost", {})
    if "vision_swap_s" in _CFG:
        row.setdefault("cost", {})["swap_s"] = _CFG["vision_swap_s"]
    return _CFG.get("vision_url"), _CFG.get("vision_model"), row


# Re-encoded to JPEG before sending: the VL server takes what browsers take,
# and HEIC (the owner's iPhone format) is not on that list.
_RECODE = frozenset({".heic", ".heif", ".hif", ".heics", ".avif"})
_DIRECT = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
           ".webp": "image/webp", ".gif": "image/gif", ".bmp": "image/bmp"}  # fmt: skip

ANSWER_TOKENS_DEFAULT = 300
ANSWER_TOKENS_CAP = 1200

# A48 P0.2 killed a magic number. `COLD_START_S = 6.0` tried to infer an
# eviction from the vision call's own latency, and measuring the real
# sequence through this module showed the inference was backwards:
#
#   text 10.75s | vision 3.03s | vision 0.85s | text 10.34s | text 0.79s
#
# The eviction is not paid by the vision call. It is paid by the NEXT TEXT
# TURN, when the host's own model reloads - 10.34 s against 0.79 s warm.
# The vision call was 3.03 s and would never have crossed a 6 s threshold,
# so the warning that exists to disclose this cost never fired once.
#
# So stop guessing from a stopwatch. Whether a modality switch costs
# anything is a property of the CONFIGURATION - `evicts` on the provider
# row - and of whether the provider was actually called. A cached answer
# touches no provider and evicts nothing.

NOT_SIGHT = (
    "A description, not the image. The model reading this never saw the "
    "pixels - it is reading a summary another model wrote, including that "
    "model's choices about what was worth mentioning."
)


def _eviction_note(qvl: dict[str, Any]) -> str | None:
    """What using the eye costs the host, when the config says it costs
    something. Silent on machines whose provider coexists with the host -
    most of them - because there is nothing to disclose."""
    evicts = qvl.get("evicts") or []
    if not evicts:
        return None
    swap = (qvl.get("cost") or {}).get("swap_s")
    cost = f"~{swap}s" if swap else "a reload"
    return (
        f"using the eye parks {', '.join(evicts)} on this machine, so your "
        f"NEXT TEXT TURN pays {cost} to bring it back - not this call, which "
        "is why the delay arrives later than you expect. Ask every image "
        "question together to pay it once."
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
    url, cfg_model, qvl = _vision_facts()
    model = cfg_model or local_vlm.DEFAULT_MODEL

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
        kwargs: dict[str, Any] = {"model": model, "media_type": media_type,
                                  "max_tokens": budget}  # fmt: skip
        if url:
            kwargs["url"] = url
        answer = local_vlm.describe(payload, asked, **kwargs).strip()
        wall = time.monotonic() - started
        cached = False
        cache[key] = {"answer": answer}
        _save_cache(state_dir, cache)

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
    if not cached:
        note = _eviction_note(qvl)
        if note:
            out["swap_note"] = note
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


def _one_viewport(adapters: dict[str, Any]) -> str:
    """The lane a viewport question means when none was named (A68): the
    one connected lane that renders - never the first alphabetically. Two
    that could answer is a question back, not a guess."""
    able = []
    for name, adapter in adapters.items():
        vocab = getattr(adapter, "vocab", None)
        try:
            renders = vocab().renders if callable(vocab) else True
        except Exception:
            renders = True
        if renders:
            able.append(name)
    if len(able) == 1:
        return able[0]
    if not able:
        raise TeeError(
            "sense_no_adapter",
            "No connected lane renders a viewport.",
            fix=f"Connected: {', '.join(sorted(adapters))}. Start Blender or Unreal with the "
            "TEE bridge, then pass adapter=<lane>.",
        )
    raise TeeError(
        "sense_adapter_required",
        f"{len(able)} connected lanes have a viewport: {', '.join(able)}.",
        fix="Pass adapter=<lane>.",
    )


def viewport(spec: dict[str, Any], *, adapters: dict[str, Any]) -> dict[str, Any]:
    """Look at what a DCC is actually showing, and answer in text.

    Unreal has had this since 3.7 as `ue_look`. Blender never got it: its
    adapter honours the same `capture(view, max_bytes)` contract and returns
    raw JPEG bytes, which a host that cannot read images has no use for. So
    a blind model driving Blender through TEE was flying instruments-only -
    it could mutate the scene and never see the result.

    The image goes to the LOCAL model and never enters the host's context,
    which has a pleasant consequence: the byte budget can be GENEROUS.
    Bigger capture, better answer, identical host cost.
    """
    from tee.kernel import local_vlm

    name = str(spec.get("adapter") or "").strip().lower()
    if not adapters:
        raise TeeError(
            "sense_no_adapter",
            "No DCC is connected, so there is no viewport to look at.",
            fix="Start Blender or Unreal with the TEE bridge and reconnect.",
        )
    if name and name not in adapters:
        raise TeeError(
            "sense_unknown_adapter",
            f"No adapter named '{name}'.",
            fix=f"Connected: {', '.join(sorted(adapters))}.",
        )
    if not name:
        name = _one_viewport(adapters)
    adapter = adapters[name]

    question = str(spec.get("question") or "").strip()
    if not question:
        question = "Describe what is visible in this viewport in two sentences."
    # 96 KB by default, matching ue_look: the host never sees these bytes.
    max_kb = max(8, min(int(spec.get("max_kb") or 96), 512))
    view = str(spec.get("view") or "camera")

    started = time.monotonic()
    try:
        data = adapter.capture(view, max_kb * 1024)
    except TeeError:
        raise
    except Exception as exc:
        raise TeeError(
            "sense_capture_failed",
            f"{name} could not produce a viewport image: {str(exc)[:160]}",
            fix="Check the DCC is responsive and a camera exists in the scene.",
        ) from exc
    url, cfg_model, qvl = _vision_facts()
    kwargs: dict[str, Any] = {"media_type": "image/jpeg",
                              "max_tokens": int(spec.get("max_tokens") or 300)}  # fmt: skip
    if url:
        kwargs["url"] = url
    if cfg_model:
        kwargs["model"] = cfg_model
    answer = local_vlm.describe(data, question, **kwargs).strip()
    wall = time.monotonic() - started

    out: dict[str, Any] = {
        "ok": True,
        "answer": answer,
        "sense": "vision",
        "adapter": name,
        "view": view,
        "provided_by": f"{cfg_model or local_vlm.DEFAULT_MODEL} "
        f"(local, {qvl.get('footprint_gb', '?')} GB)",
        "cost": {
            "capture_kb": round(len(data) / 1024, 1),
            "host_tokens_for_the_image": 0,
            "wall_s": round(wall, 2),
            "off_machine_calls": 0,
        },
        "note": "A description of the viewport, not the viewport. The image "
        "was read by a local model and never entered your context - which is "
        "why the capture budget can be generous.",
    }
    note = _eviction_note(qvl)
    if note:
        out["swap_note"] = note
    return out


def camera(spec: dict[str, Any], *, adapters: dict[str, Any]) -> dict[str, Any]:
    """The ACTIVE camera: aim, then look.

    `sense_viewport` answers about whatever the scene camera already shows.
    This one lets a blind model direct its own eye - name an object, pick an
    angle, and TEE positions a TEMPORARY camera (the scene is left exactly
    as found, the same restore contract the capture path has always had),
    renders within budget, and answers in text.

    Blender only: Unreal's `ue_look` already carries its own camera
    metadata, and aiming the editor viewport there is a different contract.
    """
    from tee.kernel import local_vlm

    # A68: the served Blender by what it can do, not by its name
    blender = adapters.get("blender") or next(
        (a for a in adapters.values() if hasattr(a, "capture_look")), None
    )
    if blender is None:
        raise TeeError(
            "sense_no_adapter",
            "sense_camera aims a Blender camera and no Blender is connected.",
            fix="Start Blender with the TEE bridge. For Unreal use ue_look.",
        )
    if not hasattr(blender, "capture_look"):
        raise TeeError(
            "sense_no_adapter",
            "This Blender adapter predates the aimed camera.",
            fix="Reconnect with the current TEE build.",
        )
    question = str(spec.get("question") or "Describe what is visible.").strip()
    context = str(spec.get("context") or "").strip()
    if context:
        question = f"Context: {context}\n\nQuestion: {question}"
    target = str(spec.get("target") or "").strip()
    azimuth = float(spec.get("azimuth_deg") or 45.0)
    elevation = float(spec.get("elevation_deg") or 20.0)
    # 1.0 = the solved fit (A51 P2). Below 1 moves in, above 1 pulls back;
    # the old 1.05 floor existed because `distance` used to multiply the raw
    # bounding radius and anything under 1 put the camera inside the subject.
    distance = max(0.2, float(spec.get("distance") or 1.0))
    max_kb = max(8, min(int(spec.get("max_kb") or 96), 512))

    started = time.monotonic()
    try:
        data = blender.capture_look(
            max_kb * 1024,
            target=target,
            azimuth_deg=azimuth,
            elevation_deg=elevation,
            distance=distance,
        )
    except TeeError:
        raise
    except Exception as exc:
        raise TeeError(
            "sense_capture_failed",
            f"Blender could not render the aimed view: {str(exc)[:160]}",
            fix="Check the target object exists (tee_scene_summary lists names).",
        ) from exc

    url, cfg_model, qvl = _vision_facts()
    kwargs: dict[str, Any] = {
        "media_type": "image/jpeg",
        "max_tokens": int(spec.get("max_tokens") or 300),
    }
    if url:
        kwargs["url"] = url
    if cfg_model:
        kwargs["model"] = cfg_model
    answer = local_vlm.describe(data, question, **kwargs).strip()
    wall = time.monotonic() - started

    out: dict[str, Any] = {
        "ok": True,
        "answer": answer,
        "sense": "vision",
        "aimed_at": target or "(whole scene)",
        "azimuth_deg": azimuth,
        "elevation_deg": elevation,
        "provided_by": f"{cfg_model or local_vlm.DEFAULT_MODEL} "
        f"(local, {qvl.get('footprint_gb', '?')} GB)",
        "cost": {
            "capture_kb": round(len(data) / 1024, 1),
            "host_tokens_for_the_image": 0,
            "wall_s": round(wall, 2),
            "off_machine_calls": 0,
        },
        "note": "Rendered from a temporary camera that no longer exists; "
        "the scene was left exactly as found. A description, not the image.",
    }
    note = _eviction_note(qvl)
    if note:
        out["swap_note"] = note
    return out


FRAME_VERDICTS = ("too far", "good", "too close", "cropped")
FRAME_MAX_RETRIES = 2

_FRAME_QUESTION = (
    "Judge only the FRAMING of this render, not its content or quality. "
    "Reply on ONE line in exactly this form and nothing else:\n"
    "FILL=<integer percent of the image the main subject occupies> "
    "CROPPED=<yes|no> VERDICT=<too far|good|too close>"
)


def _parse_frame_verdict(answer: str) -> dict[str, Any]:
    """Read the model's grade, and admit when it did not answer the form.

    A model asked for a rigid form will sometimes write prose anyway. That
    is not a crash and it is not a pass - it is an unusable grade, and the
    loop has to be able to tell the difference or it will 'converge' on
    noise.
    """
    import re

    text = " ".join(answer.split())
    fill = re.search(r"FILL\s*=\s*(\d{1,3})", text, re.I)
    cropped = re.search(r"CROPPED\s*=\s*(yes|no)", text, re.I)
    verdict = re.search(r"VERDICT\s*=\s*(too far|good|too close|cropped)", text, re.I)
    parsed: dict[str, Any] = {"raw": answer.strip()[:160]}
    if fill:
        parsed["fill_percent"] = max(0, min(int(fill.group(1)), 100))
    if cropped:
        parsed["cropped"] = cropped.group(1).lower() == "yes"
    if verdict:
        parsed["verdict"] = verdict.group(1).lower()
    parsed["usable"] = "verdict" in parsed or "fill_percent" in parsed
    return parsed


def _next_distance(current: float, grade: dict[str, Any]) -> float | None:
    """Where to move the camera, or None if it is already right.

    Deliberately coarse. The model is grading a picture, not solving optics,
    so its advice is a direction rather than a measurement - a big confident
    step lands closer than a fussy one derived from a number it estimated
    by eye.
    """
    verdict = grade.get("verdict")
    if grade.get("cropped"):
        return round(current * 1.35, 3)
    if verdict == "good":
        return None
    if verdict == "too far":
        fill = grade.get("fill_percent")
        # If it gave a number, aim at ~55% fill; otherwise step in a third.
        factor = max(0.45, min((fill / 55.0) ** 0.5, 0.9)) if fill else 0.67
        return round(current * factor, 3)
    if verdict == "too close":
        return round(current * 1.4, 3)
    return None


def frame(spec: dict[str, Any], *, adapters: dict[str, Any], state_dir: Path | None = None):
    """Render, let the local model grade the framing, re-aim, repeat.

    A51 P3. `sense_camera` aims by arithmetic and returns whatever it gets;
    nothing checks that the subject actually landed well. This closes the
    loop with the only instrument that can judge a rendered scene - the
    vision model. A pixel heuristic cannot: measuring "fraction of frame
    filled" by brightness reported 100% at every distance during research,
    because it was measuring the backdrop.

    The model's verdict is ADVICE, not truth (the A47 law: a description is
    a summary another model wrote). So the loop is bounded, every attempt is
    reported with its grade, and a run that does not converge returns its
    best attempt SAYING it did not converge. It never loops silently and it
    never reports the last frame as though it were the right one.
    """
    from tee.kernel.machine import ENGINES

    name = str(spec.get("adapter") or "").strip().lower()
    if not adapters:
        raise TeeError(
            "sense_no_adapter",
            "No DCC is connected, so there is nothing to frame.",
            fix="Start Blender or Unreal with the TEE bridge and reconnect.",
        )
    if name and name not in adapters:
        raise TeeError(
            "sense_unknown_adapter",
            f"No adapter named '{name}'.",
            fix=f"Connected: {', '.join(sorted(adapters))}.",
        )
    name = name or _one_viewport(adapters)
    adapter = adapters[name]
    if not hasattr(adapter, "capture_look"):
        raise TeeError(
            "sense_no_aiming",
            f"The {name} adapter cannot aim a camera.",
            fix="Aimed framing needs capture_look; Godot renders nothing "
            "headlessly at all (use run_scene output instead).",
        )

    distance = max(0.2, float(spec.get("distance") or 1.0))
    azimuth = float(spec.get("azimuth_deg") or 45.0)
    elevation = float(spec.get("elevation_deg") or 20.0)
    max_kb = max(8, min(int(spec.get("max_kb") or 96), 512))
    retries = max(0, min(int(spec.get("max_retries") or FRAME_MAX_RETRIES), 4))

    attempts: list[dict[str, Any]] = []
    best: tuple[bytes, dict[str, Any], float] | None = None
    for attempt in range(retries + 1):
        data = adapter.capture_look(
            max_kb * 1024, azimuth_deg=azimuth, elevation_deg=elevation, distance=distance
        )
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as handle:
            handle.write(data)
            shot = Path(handle.name)
        try:
            graded = describe(
                {"path": str(shot), "question": _FRAME_QUESTION, "max_tokens": 60},
                state_dir=state_dir,
            )
        finally:
            shot.unlink(missing_ok=True)
        grade = _parse_frame_verdict(graded["answer"])
        attempts.append(
            {
                "distance": distance,
                **{k: v for k, v in grade.items() if k != "raw"},
                "grade": grade["raw"],
            }
        )
        if best is None or (grade.get("verdict") == "good" and not grade.get("cropped")):
            best = (data, grade, distance)
        if grade.get("verdict") == "good" and not grade.get("cropped"):
            break
        if not grade["usable"]:
            break  # an ungradeable answer is not a signal to move the camera
        nxt = _next_distance(distance, grade)
        if nxt is None or attempt == retries:
            break
        distance = max(0.2, min(nxt, 8.0))

    data, grade, chosen = best  # type: ignore[misc]
    converged = grade.get("verdict") == "good" and not grade.get("cropped")
    qvl = ENGINES.get("qvl", {})
    out: dict[str, Any] = {
        "ok": True,
        "image_bytes": len(data),
        "adapter": name,
        "distance": chosen,
        "azimuth_deg": azimuth,
        "elevation_deg": elevation,
        "converged": converged,
        "attempts": attempts,
        "graded_by": f"{__import__('tee.kernel.local_vlm', fromlist=['x']).DEFAULT_MODEL} (local)",
        "note": "The framing was graded by a local vision model, whose "
        "verdict is advice rather than measurement. Every attempt is listed "
        "with the grade it received.",
    }
    if not converged:
        out["warning"] = (
            f"did not converge in {len(attempts)} attempt(s) - this is the "
            "best of them, not a framing the grader called good. Try a "
            "different azimuth/elevation, or set distance by hand."
        )
    note = _eviction_note(qvl)
    if note:
        out["swap_note"] = note
    return out


def register_sense_tools(app, project_root: str | Path) -> None:
    """Register sense_* as virtual tools (the surface stays 17). Reads
    [senses] from the project config so another user's endpoint, model and
    eviction facts come from THEIR machine, not this one's."""
    from tee.kernel.registry import VirtualTool

    configure(getattr(getattr(app, "config", None), "senses", None))
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
            ],
            examples=[
                {
                    "path": "site/frame_012.jpg",
                    "context": "The drawings say gable G3 is solid plastered brick.",
                    "question": "Does the gable match the spec? What differs?",
                }
            ],
        )
    )

    def sense_frame(args: dict[str, Any]) -> dict[str, Any]:
        return frame(args, adapters=app.adapters, state_dir=state)

    app.registry.register(
        VirtualTool(
            name="sense_frame",
            description=(
                "Frame a subject WELL: renders an aimed view, has the local "
                "vision model grade the framing, moves the camera and "
                "retries. Returns the grade for every attempt and says "
                "plainly when it did not converge. Use when you want a "
                "usable shot rather than whatever the first guess produced. "
                "The image never enters your context - only the grades."
            ),
            schema={
                "type": "object",
                "properties": {
                    "adapter": {"type": "string"},
                    "azimuth_deg": {"type": "number"},
                    "elevation_deg": {"type": "number"},
                    "distance": {
                        "type": "number",
                        "description": "1.0 fits the subject; lower moves in. Starting point only.",
                    },
                    "max_retries": {"type": "integer", "description": "Default 2, cap 4."},
                    "max_kb": {"type": "integer"},
                },
            },
            handler=sense_frame,
            tags=[
                "sense",
                "frame",
                "framing",
                "camera",
                "compose",
                "shot",
                "aim",
                "zoom",
                "fit",
                "vision",
                "render",
                "well framed",
            ],
            examples=[{"azimuth_deg": 35, "elevation_deg": 20}],
        )
    )

    def sense_viewport(args: dict[str, Any]) -> dict[str, Any]:
        return viewport(args, adapters=app.adapters)

    def sense_camera(args: dict[str, Any]) -> dict[str, Any]:
        return camera(args, adapters=app.adapters)

    app.registry.register(
        VirtualTool(
            name="sense_camera",
            description=(
                "ACTIVE camera for a model that cannot see: aim at a named "
                "object (or the whole scene) from an angle you choose, and "
                "get a TEXT answer about what the render shows. Blender "
                "only; the temporary camera is removed and the scene left "
                "exactly as found. azimuth_deg 0 looks from +X, 90 from +Y; "
                "elevation_deg tilts up."
            ),
            schema={
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "target": {
                        "type": "string",
                        "description": "Object name from tee_scene_summary; empty = whole scene.",
                    },
                    "context": {
                        "type": "string",
                        "description": "What you already know (e.g. what the target is); "
                        "the answer addresses it.",
                    },
                    "azimuth_deg": {"type": "number"},
                    "elevation_deg": {"type": "number"},
                    "distance": {
                        "type": "number",
                        "description": "Multiple of the target's size, default 2.2.",
                    },
                    "max_kb": {"type": "integer"},
                    "max_tokens": {"type": "integer"},
                },
            },
            handler=sense_camera,
            tags=[
                "sense",
                "vision",
                "camera",
                "aim",
                "look at",
                "angle",
                "orbit",
                "inspect",
                "blender",
                "frame",
                "point",
            ],
            examples=[
                {
                    "target": "arm-pad-L",
                    "azimuth_deg": 180,
                    "elevation_deg": 10,
                    "question": "Is the arm pad orange and undamaged?",
                }
            ],
        )
    )

    app.registry.register(
        VirtualTool(
            name="sense_viewport",
            description=(
                "SEE the scene you are building: captures the connected "
                "DCC's viewport (Blender or Unreal) and answers a question "
                "about it in TEXT. Use this when you cannot read images but "
                "need to check what your edits actually did. The capture "
                "goes to a local model and never enters your context, so it "
                "costs you nothing in image tokens."
            ),
            schema={
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "adapter": {"type": "string", "description": "blender | unreal"},
                    "view": {"type": "string", "description": "camera (default) or a named view."},
                    "max_kb": {"type": "integer", "description": "Capture budget, default 96."},
                    "max_tokens": {"type": "integer"},
                },
            },
            handler=sense_viewport,
            tags=[
                "sense",
                "vision",
                "viewport",
                "scene",
                "look",
                "see",
                "blender",
                "unreal",
                "render",
                "check",
                "camera",
                "screenshot",
            ],
            examples=[{"question": "Is the chair back mesh visible and orange?"}],
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
            ],
            examples=[{"path": "site/walkthrough.m4a", "model_size": "base"}],
        )
    )
