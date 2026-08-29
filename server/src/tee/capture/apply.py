"""Apply lanes (A42 T5 = A40 V5): owner-approved deviations flow to the
DCC lanes — checkpointed, diffed, read back.

The menu's law: `capture_apply` runs ONLY on the owner's explicit
decision. keep-design and flag-for-site are decisions too — they are
RECORDED and apply nothing. accept-as-built translates one deviation
into lane-specific mutations through the EXISTING machinery (the
checkpointed batch path), so every apply arrives with its checkpoint id
and its diff, and the read-back proves what the scene now says. Every
decision lands in `.tee/capture/decisions.jsonl` — the trip's paper
trail.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

DECISIONS = ("accept-as-built", "keep-design", "flag-for-site")
AXES = {"x": 0, "y": 1, "z": 2}
# (location prop key, meters -> adapter-native factor, unit label):
# FreeCAD places via 'at' in millimeters; UE actors in centimeters (uu).
LANE_UNITS = {"freecad": ("at", 1000.0, "mm"), "unreal": ("location", 100.0, "uu")}


def record_decision(work_dir: Path, entry: dict[str, Any]) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)
    path = work_dir / "decisions.jsonl"
    line = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), **entry}
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, separators=(",", ":")) + "\n")
    return path


def apply_scene_offset(
    app,
    adapter_name: str,
    entity_id: str,
    delta_m: float,
    axis: str = "z",
) -> dict[str, Any]:
    """The scene-lane apply: move the named entity by the accepted
    deviation along one axis, through the checkpointed batch path."""
    if axis not in AXES:
        raise TeeError(
            "capture_apply_bad_axis", f"'{axis}' is not an axis.", fix="One of: x, y, z."
        )
    cache = app.cache(adapter_name)
    entity = cache.get(entity_id)
    if entity is None:
        raise TeeError(
            "unknown_entity",
            f"No entity '{entity_id}' in the {adapter_name} scene cache.",
            fix="List ids with tee_scene_summary; refresh=true if stale.",
        )
    prop, factor, unit = LANE_UNITS.get(adapter_name, ("location", 1.0, "m"))
    location = list(entity.summary.get("location") or [0.0, 0.0, 0.0])
    while len(location) < 3:
        location.append(0.0)
    location[AXES[axis]] = round(float(location[AXES[axis]]) + float(delta_m) * factor, 6)
    result = app.run_batch(
        adapter_name,
        [{"op": "set", "id": entity_id, "props": {prop: location}}],
        label=f"apply-deviation:{entity_id}",
    )
    readback = cache.get(entity_id)
    return {
        "adapter": adapter_name,
        "entity": entity_id,
        "checkpoint": result.get("checkpoint"),
        "moved_m": {axis: round(float(delta_m), 4)},
        "location": (readback.summary.get("location") if readback else None),
        "units": unit,
        "revision": result.get("revision"),
    }


def staged_lane(lane: str) -> TeeError:
    """The lanes whose live leg needs its application running - loud,
    named, never silently skipped."""
    needs = {
        "fabrication": "the FreeCAD GUI bridge (launch FreeCAD; the A37 lane "
        "regenerates TechDraw sheets from the corrected model)",
        "unreal": "the OkongoSim editor (the house import lane and the "
        "terrain path live in /Users/john/OkongoSim/tools)",
    }
    return TeeError(
        "capture_apply_staged",
        f"The {lane} apply leg needs {needs.get(lane, 'its application')} live.",
        fix="Launch it and re-run; the scene lane (blender) applies today.",
    )
