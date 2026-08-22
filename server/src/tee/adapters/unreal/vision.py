"""Viewport capture and text-first scene checks (principle P4).

Epic's `CaptureViewport` returns a base64 PNG at whatever size the level
viewport happens to be, with no resolution parameter. Returned raw that is a
token catastrophe, so TEE re-encodes to JPEG and shrinks until the payload
fits an explicit byte budget - the same contract the Blender adapter honours.

The capture also carries text metadata (camera pose, labelled actors) which
is free evidence and usually answers the question without the image at all.
"""

from __future__ import annotations

import base64
import io
from typing import Any

from tee.kernel.errors import TeeError

# Rungs tried in order until one fits the budget.
_RUNGS = ((1024, 60), (800, 55), (640, 50), (480, 45), (320, 40))


def encode_within_budget(png_b64: str, max_bytes: int) -> tuple[bytes, dict[str, Any]]:
    """PNG(base64) -> JPEG bytes no larger than `max_bytes`."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise TeeError(
            "pillow_missing",
            "Viewport capture needs Pillow to fit an image into the byte budget.",
            fix="Install the extract extra (uv sync --extra extract), or use "
            "ue_scene_checks, which answers most questions in text.",
        ) from exc

    try:
        raw = base64.b64decode(png_b64)
        image = Image.open(io.BytesIO(raw))
        image.load()
    except Exception as exc:  # any decode failure collapses to one clear error
        raise TeeError(
            "capture_decode_failed",
            f"The editor returned an image TEE could not decode ({exc}).",
            fix="Check the viewport is visible and not mid-level-load.",
        ) from exc

    original = image.size
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    for width, quality in _RUNGS:
        candidate = image
        if image.width > width:
            height = max(1, round(image.height * width / image.width))
            candidate = image.resize((width, height), Image.LANCZOS)
        buffer = io.BytesIO()
        candidate.save(buffer, format="JPEG", quality=quality, optimize=True)
        data = buffer.getvalue()
        if len(data) <= max_bytes:
            return data, {
                "source_px": list(original),
                "sent_px": list(candidate.size),
                "bytes": len(data),
                "quality": quality,
            }
    raise TeeError(
        "capture_over_budget",
        f"Smallest render is {len(data)} bytes; budget is {max_bytes}.",
        fix="Raise max_kb, or use ue_scene_checks / tee_scene_summary - text "
        "state is the default evidence.",
    )


def summarize_capture(payload: dict[str, Any]) -> dict[str, Any]:
    """The free text half of a capture: pose and what is actually on screen."""
    out: dict[str, Any] = {}
    for key in ("cameraLocation", "cameraRotation", "cameraFOV"):
        if key in payload:
            out[key] = payload[key]
    labelled = payload.get("labeledActors")
    if isinstance(labelled, list):
        out["labeled_actors"] = labelled[:40]
        out["labeled_actor_count"] = len(labelled)
    return out
