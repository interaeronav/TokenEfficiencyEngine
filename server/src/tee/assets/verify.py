"""Render-free verification battery (9.7, A15 R22-R24).

Runs after every apply, entirely from the scene cache + rule tables:
scale sanity vs class envelopes, AABB collision (≤ 5 mm contact
tolerated), support (nothing floats), clearance/circulation when a room
is provided, palette ΔE00 vs the style brief. One compact
violations+fixes report; pixels are a LAST resort - the report says
whether a single budgeted render is even warranted.
"""

from __future__ import annotations

from typing import Any

from tee.assets.color import delta_e2000, srgb_to_lab
from tee.assets.envelopes import envelope_for

_CONTACT_TOLERANCE = 0.005  # 5 mm
_SUPPORT_TOLERANCE = 0.005
_PALETTE_DE_LIMIT = 28.0  # beyond: visibly off-brief


def _aabb(entity) -> tuple[list[float], list[float]] | None:
    location = entity.summary.get("location")
    dims = entity.summary.get("dimensions") or entity.summary.get("dims_m")
    if not location or not dims:
        return None
    half = [float(d) / 2 for d in dims]
    center = [float(v) for v in location]
    # convention: location is the object origin at footprint center, z at base
    lo = [center[0] - half[0], center[1] - half[1], center[2]]
    hi = [center[0] + half[0], center[1] + half[1], center[2] + float(dims[2])]
    return lo, hi


def _overlap_1d(a_lo, a_hi, b_lo, b_hi) -> float:
    return min(a_hi, b_hi) - max(a_lo, b_lo)


def verify_scene(
    app,
    adapter: str,
    *,
    room: dict[str, Any] | None = None,
    region: str = "US",
    style_palette: list[list[float]] | None = None,
) -> dict[str, Any]:
    app.warm(adapter)
    cache = app.caches.get(adapter)
    entities = list(cache.entities.values()) if cache else []
    checked = 0
    violations: list[dict[str, Any]] = []

    boxes: dict[str, tuple[list[float], list[float]]] = {}
    classes: dict[str, str | None] = {}
    for entity in entities:
        box = _aabb(entity)
        if box:
            boxes[entity.id] = box
        classes[entity.id] = entity.summary.get("asset_class") or _guess_class(entity)

    # 1. scale sanity vs envelopes
    for entity in entities:
        cls = classes.get(entity.id)
        env = envelope_for(cls)
        dims = entity.summary.get("dimensions") or entity.summary.get("dims_m")
        if not env or not dims:
            continue
        checked += 1
        lo, hi = env["min"], env["max"]
        bad = [
            i for i in range(3)
            if not (lo[i] * 0.5 <= float(dims[i]) <= hi[i] * 2.0)
        ]
        if bad:
            violations.append(
                {
                    "check": "scale_sanity",
                    "objects": [entity.id],
                    "fix": f"{entity.name} ({cls}) dims {dims} are far outside the "
                    f"class envelope {lo}..{hi} - re-import with target_dims",
                }
            )

    # 2. AABB collision (<= 5 mm contact tolerated)
    ids = list(boxes)
    for i, id_a in enumerate(ids):
        for id_b in ids[i + 1 :]:
            checked += 1
            (a_lo, a_hi), (b_lo, b_hi) = boxes[id_a], boxes[id_b]
            depths = [
                _overlap_1d(a_lo[k], a_hi[k], b_lo[k], b_hi[k]) for k in range(3)
            ]
            if all(d > _CONTACT_TOLERANCE for d in depths):
                worst = min(depths)
                violations.append(
                    {
                        "check": "collision",
                        "objects": [id_a, id_b],
                        "penetration_m": round(worst, 4),
                        "fix": f"separate them by ~{worst:.3f} m",
                    }
                )

    # 3. support: base near z=0 or resting on another box top
    tops = [(id_, boxes[id_][1][2]) for id_ in boxes]
    for entity_id, (lo, hi) in boxes.items():
        checked += 1
        base = lo[2]
        if abs(base) <= _SUPPORT_TOLERANCE:
            continue
        supported = any(
            other != entity_id
            and abs(base - top) <= _SUPPORT_TOLERANCE
            and _overlap_1d(lo[0], hi[0], boxes[other][0][0], boxes[other][1][0]) > 0
            and _overlap_1d(lo[1], hi[1], boxes[other][0][1], boxes[other][1][1]) > 0
            for other, top in tops
        )
        if not supported:
            violations.append(
                {
                    "check": "support",
                    "objects": [entity_id],
                    "fix": f"floats {base:.3f} m above support - drop to z=0 or onto "
                    "a surface",
                }
            )

    # 4. room clearances (reuses the placement rule table)
    if room is not None and boxes:
        from tee.assets.placement import validate_placement

        placements = []
        for entity_id, (lo, hi) in boxes.items():
            placements.append(
                {
                    "name": entity_id,
                    "class": classes.get(entity_id),
                    "dims": [hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]],
                    "location": [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2],
                    "rotation_deg": 0.0,
                    "relax": [],
                }
            )
        report = validate_placement(placements, room, region=region)
        checked += report["checked"]
        for violation in report["violations"]:
            violations.append(
                {
                    "check": violation["rule"],
                    "severity": violation["severity"],
                    "objects": violation["objects"],
                    "fix": violation["fix"],
                }
            )

    # 5. palette vs brief
    if style_palette:
        brief = [tuple(v) for v in style_palette]
        for entity in entities:
            rgb = entity.summary.get("base_color")
            if not rgb:
                continue
            checked += 1
            lab = srgb_to_lab(tuple(rgb[:3]))
            distance = min(delta_e2000(lab, b) for b in brief)
            if distance > _PALETTE_DE_LIMIT:
                violations.append(
                    {
                        "check": "palette",
                        "objects": [entity.id],
                        "delta_e": round(distance, 1),
                        "fix": f"{entity.name} color is ΔE {distance:.0f} off the "
                        "style brief - pick a brief-palette material",
                    }
                )

    out: dict[str, Any] = {"checked": checked, "violations": violations}
    if not violations:
        out["summary"] = f"no geometric conflicts detected ({checked} checks)"
    # single-render gate (P3): pixels only after a geometric pass AND for a
    # genuinely visual question
    out["render_warranted"] = not violations and bool(style_palette)
    out["render_policy"] = (
        "at most ONE budgeted render (~768x512 via tee_capture max_kb<=32) "
        "and only for a visual question geometry cannot answer"
    )
    return out


def _guess_class(entity) -> str | None:
    """Fallback class from the entity/asset name (import stores asset_key)."""
    name = (entity.summary.get("asset_key") or entity.name or "").lower()
    for cls in (
        "sofa", "chair", "table", "bed", "wardrobe", "door", "window",
        "toilet", "sink", "bathtub", "refrigerator", "stove", "rug",
    ):
        if cls in name:
            return cls
    return None
