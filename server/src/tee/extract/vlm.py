"""VLM extraction passes (7.5) - the only tokens this module ever spends.

Channel decision A9: MCP sampling is dead, so the DEFAULT driver is in-band:
`ex_prepare` hands the host model file paths (it reads media with its own
tools), a schema fragment and storing instructions; the host writes back via
`ex_store_facts`. The OPTIONAL ApiDriver runs off-session extraction as an
async job when ANTHROPIC_API_KEY is configured. One interface, two drivers,
same fact store.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from tee.extract.images import STANDARD_EDGE_CAP, image_tokens, size_for_budget
from tee.extract.plan import SCHEMA_ID

IN_BAND_EXTRACTOR_VERSION = "in-band-1"
TILE_MAX_TOKENS = 4784  # high-res tier cap; also fine on standard tier
TILE_MAX_SIDE = 2000  # hard client-side cap per research 14

_PLAN_SCHEMA_HINT = {
    "schema": SCHEMA_ID,
    "frame": "<frame id from ex_facts kind=page>",
    "units": "m",
    "scale": {"method": "vlm", "confidence": 0.5},
    "levels": [{"index": 0, "elevation_z": 0.0, "ceiling_height": None}],
    "walls": [
        {"id": "w1", "level": 0, "a": [0, 0], "b": [4.2, 0], "thickness": 0.2, "height": None}
    ],
    "openings": [
        {"id": "o1", "wall": "w1", "t": 0.5, "width": 0.9, "kind": "door", "sill": 0, "head": 2.1}
    ],
    "rooms": [
        {"id": "r1", "level": 0, "name": "Bedroom 2", "polygon": [[0, 0], [4, 0], [4, 3], [0, 3]]}
    ],
    "roof": None,
}

_GUIDANCE = {
    "document": (
        "Read the sheet image(s) yourself (paths below). TRANSCRIBE, don't "
        "measure: dimension strings, level markers (FIN. FLR., T.O. PLATE, "
        "RIDGE), pitch triangles (n/12), room labels - VLM text reading is "
        "~0.95 accurate but symbol counting/pixel measuring is 0.40-0.55, so "
        "geometry comes from the deterministic facts already extracted. "
        "Cross-check every dimension you read against the kind='dimension' "
        "facts; store a plan fact only for sheets the deterministic lane "
        "could not parse."
    ),
    "image": (
        "Look at the contact sheet first (one bounded image), then request "
        "specific crops via tee_media if needed. Store facts about "
        "materials, colors (hex), window/door positions relative to named "
        "walls, and site features. Never estimate dimensions from photos - "
        "dimensions come from drawings."
    ),
    "video": (
        "Use the keyframe facts and contact sheet; fetch single frames by "
        "timestamp via tee_media only when a keyframe is insufficient. "
        "Store room-identification facts: {kind:'room_sighting', room, "
        "pts_time, keyframe}."
    ),
    "audio": (
        "Read the transcript segments (kind='transcript_segment') and store "
        "requirement facts: {kind:'requirement', tier:'stated_requirement', "
        "topic:<bedrooms|orientation|budget|material|other>, statement, "
        "quote, t}. Only requirements actually stated."
    ),
}


def prepare_instructions(source: dict[str, Any], derived_root: Path) -> dict[str, Any]:
    """The in-band extraction packet: what to read, what to store, and the
    schema. Text-only - the host model reads media with its own tools."""
    media_type = source["media_type"]
    packet: dict[str, Any] = {
        "source": source["hash"][:8],
        "media_type": media_type,
        "paths": source["paths"][:3],
        "store_with": {
            "tool": "ex_store_facts",
            "extractor": f"vlm-{media_type}",
        },
        "guidance": _GUIDANCE.get(media_type, "Store compact facts about this source."),
    }
    if media_type == "document":
        packet["plan_schema_example"] = _PLAN_SCHEMA_HINT
    sheets = sorted(derived_root.glob("**/sheet*.jpg")) + sorted(derived_root.glob("**/k*.jpg"))
    if sheets:
        packet["prepared_images"] = [str(p) for p in sheets[:12]]
    return packet


def tile_plan(width: int, height: int) -> list[dict[str, int]]:
    """Tile grid for a coordinate-bearing image: every tile within both the
    token cap and the hard side cap, expressed in source pixels."""
    cols = max(1, -(-width // TILE_MAX_SIDE))
    rows = max(1, -(-height // TILE_MAX_SIDE))
    # widen the grid until each rendered tile fits the token budget
    while True:
        tile_w, tile_h = -(-width // cols), -(-height // rows)
        rendered = size_for_budget(tile_w, tile_h, TILE_MAX_TOKENS)
        if image_tokens(*rendered) <= TILE_MAX_TOKENS and max(rendered) <= min(
            TILE_MAX_SIDE, STANDARD_EDGE_CAP
        ):
            break
        if tile_w >= tile_h:
            cols += 1
        else:
            rows += 1
    tiles = []
    for r in range(rows):
        for c in range(cols):
            tiles.append(
                {
                    "index": r * cols + c,
                    "x": c * (width // cols),
                    "y": r * (height // rows),
                    "w": width // cols,
                    "h": height // rows,
                }
            )
    return tiles


class ApiDriver:
    """Optional off-session extraction with a server-owned API key. Absent a
    key (or the sdk), everything silently degrades to the in-band driver."""

    def __init__(self) -> None:
        self.model = os.environ.get("TEE_EXTRACT_MODEL", "claude-opus-5")

    @staticmethod
    def available() -> bool:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return False
        try:
            import anthropic  # noqa: F401

            return True
        except ImportError:
            return False

    def extract_document_page(self, image_path: Path, schema_hint: dict) -> dict[str, Any]:
        import base64

        import anthropic

        client = anthropic.Anthropic()
        data = base64.standard_b64encode(image_path.read_bytes()).decode()
        response = client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": data,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "Extract this architectural sheet into JSON matching "
                                "this example schema exactly (no prose):\n"
                                + json.dumps(schema_hint)
                            ),
                        },
                    ],
                }
            ],
        )
        text = "".join(b.text for b in response.content if b.type == "text")
        return json.loads(text[text.index("{") : text.rindex("}") + 1])
