"""Verification ladder Tier 0 (A19): static, always-on, milliseconds.

CoM-projection-inside-support-polygon with a stability margin, computed
over cached entity AABBs (contacts analytically, pure Python) - the
ShapeStacks ground truth is exactly this criterion, and analytics beat
learned models when contacts are known. Stacks are checked CUMULATIVELY
per interface: the combined center of mass of everything above each
support must project inside that support region.

Fact wording is honest: "unsupported_com" / "floating" / "penetrating" -
never "unstable structure" and never "structurally sound".

Also here: the SimReady-style readiness gate for Phase 9 imports
(static schema checks with callable fixes - sim-readiness is validated
statically, not by running sims).
"""

from __future__ import annotations

from typing import Any

_CONTACT_TOL = 0.006  # m: interface adjacency tolerance
_MARGIN = 0.02  # stability margin: CoM must be this far inside the edge


def _box(entity) -> dict[str, Any] | None:
    location = entity.summary.get("location")
    dims = entity.summary.get("dimensions") or entity.summary.get("dims_m")
    if not location or not dims:
        return None
    cx, cy, cz = (float(v) for v in location[:3])
    dx, dy, dz = (float(v) for v in dims[:3])
    density = entity.summary.get("physics_density_kg_m3", 1.0)
    mass = dx * dy * dz * float(density)
    return {
        "id": entity.id,
        "lo": [cx - dx / 2, cy - dy / 2, cz],
        "hi": [cx + dx / 2, cy + dy / 2, cz + dz],
        "com": [cx, cy, cz + dz / 2],
        "mass": mass,
    }


def _xy_overlap(a: dict, b: dict) -> tuple[float, float, float, float] | None:
    x0, x1 = max(a["lo"][0], b["lo"][0]), min(a["hi"][0], b["hi"][0])
    y0, y1 = max(a["lo"][1], b["lo"][1]), min(a["hi"][1], b["hi"][1])
    if x1 - x0 <= 0 or y1 - y0 <= 0:
        return None
    return x0, x1, y0, y1


def tier0(app, adapter: str) -> dict[str, Any]:
    """Floating / penetrating / unsupported_com facts over the scene."""
    app.warm(adapter)
    cache = app.caches.get(adapter)
    boxes = []
    for entity in (cache.entities.values() if cache else []):
        box = _box(entity)
        if box:
            boxes.append(box)
    facts: list[dict[str, Any]] = []
    checked = 0

    # supports: which boxes rest on which (interface adjacency + overlap)
    supported_by: dict[str, list[dict]] = {b["id"]: [] for b in boxes}
    for box in boxes:
        for other in boxes:
            if other["id"] == box["id"]:
                continue
            if abs(box["lo"][2] - other["hi"][2]) <= _CONTACT_TOL and _xy_overlap(box, other):
                supported_by[box["id"]].append(other)

    for box in boxes:
        checked += 1
        base = box["lo"][2]
        # at or below grade counts as grounded (ground planes sit at -t)
        on_ground = base <= _CONTACT_TOL
        supporters = supported_by[box["id"]]
        if not on_ground and not supporters:
            facts.append({
                "kind": "floating",
                "id": box["id"],
                "gap_m": round(base, 4),
                "fix": "drop to the ground or onto a support",
            })

    # penetration (beyond contact tolerance in all three axes)
    for i, a in enumerate(boxes):
        for b in boxes[i + 1 :]:
            checked += 1
            overlap = _xy_overlap(a, b)
            z_pen = min(a["hi"][2], b["hi"][2]) - max(a["lo"][2], b["lo"][2])
            if overlap and z_pen > _CONTACT_TOL:
                x0, x1, y0, y1 = overlap
                if (x1 - x0) > _CONTACT_TOL and (y1 - y0) > _CONTACT_TOL:
                    facts.append({
                        "kind": "penetrating",
                        "ids": [a["id"], b["id"]],
                        "depth_m": round(z_pen, 4),
                        "fix": "separate the volumes",
                    })

    # cumulative CoM per support interface (stack criterion)
    boxes_by_id = {b["id"]: b for b in boxes}
    supporter_ids = {
        bid: [s["id"] for s in supporters] for bid, supporters in supported_by.items()
    }
    for support in boxes:
        above = _stack_above(support["id"], boxes_by_id, supporter_ids)
        if not above:
            continue
        checked += 1
        total_mass = sum(b["mass"] for b in above)
        com_x = sum(b["com"][0] * b["mass"] for b in above) / total_mass
        com_y = sum(b["com"][1] * b["mass"] for b in above) / total_mass
        # support region: the interface overlap between the support's top
        # and the boxes directly on it
        direct = [b for b in above if any(s["id"] == support["id"] for s in supported_by[b["id"]])]
        regions = [r for b in direct if (r := _xy_overlap(b, support))]
        if not regions:
            continue
        x0 = min(r[0] for r in regions) + _MARGIN
        x1 = max(r[1] for r in regions) - _MARGIN
        y0 = min(r[2] for r in regions) + _MARGIN
        y1 = max(r[3] for r in regions) - _MARGIN
        if not (x0 <= com_x <= x1 and y0 <= com_y <= y1):
            facts.append({
                "kind": "unsupported_com",
                "id": direct[0]["id"] if len(direct) == 1 else [b["id"] for b in direct],
                "over": support["id"],
                "com_xy": [round(com_x, 3), round(com_y, 3)],
                "support_region": [round(v, 3) for v in (x0, x1, y0, y1)],
                "fix": "center the stack over its support (analytic criterion: "
                "CoM projection outside the support polygon + margin)",
            })

    out: dict[str, Any] = {"checked": checked, "facts": facts}
    if not facts:
        out["summary"] = f"no tier-0 physics conflicts ({checked} checks)"
    return out


def _stack_above(
    support_id: str,
    boxes_by_id: dict[str, dict],
    supporter_ids: dict[str, list[str]],
) -> list[dict]:
    """All boxes whose transitive support chain includes `support_id`."""
    out = []
    for box_id in boxes_by_id:
        if box_id == support_id:
            continue
        seen: set[str] = set()
        stack = list(supporter_ids.get(box_id, []))
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            if node == support_id:
                out.append(boxes_by_id[box_id])
                break
            stack.extend(supporter_ids.get(node, []))
    return out


# -- sim-readiness gate (SimReady-style static checks) ----------------------


def sim_readiness(entity_summary: dict[str, Any]) -> dict[str, Any]:
    """Static requirements with callable fixes - mirror of
    omniverse-asset-validator's severity+location+fix shape."""
    findings = []
    if not entity_summary.get("dimensions") and not entity_summary.get("dims_m"):
        findings.append({
            "requirement": "extents",
            "fix": "measure the asset (glTF probe or DCC read-back) before simulating",
        })
    dims = entity_summary.get("dimensions") or entity_summary.get("dims_m") or []
    if dims and (max(dims) > 50 or min(dims) <= 0):
        findings.append({
            "requirement": "sane_scale",
            "fix": "extents outside 0-50 m - run the four-band scale policy first",
        })
    if not entity_summary.get("physics_density_kg_m3"):
        findings.append({
            "requirement": "physical_material",
            "fix": "assign one with mat_assign (density drives mass = volume x density)",
        })
    if entity_summary.get("collision") in (None, "none"):
        findings.append({
            "requirement": "collision_proxy",
            "fix": "convex default; CoACD decomposition for concave containers "
            "(cached per asset hash)",
        })
    return {
        "ready": not findings,
        "findings": findings,
        "note": "sim-readiness is validated statically (SimReady pattern), "
        "not by running sims",
    }
