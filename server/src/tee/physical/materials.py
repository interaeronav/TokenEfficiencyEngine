"""Three-tier material facts (A20): render / physics / engineering,
honesty-labeled per value, on a CC0/standards backbone.

Render values come from the Phase 9 physicallybased.info snapshot
(measured); physics and engineering values from materials_eng.json
(EN-standard cited). `mat_assign` wires every applicable tier at once
and returns the facts it applied - including the Bullet friction
caveat (Bullet multiplies pair coefficients: bodies get sqrt(mu)) and
the computed mass (volume x density).
"""

from __future__ import annotations

import json
import math
from functools import cache
from importlib import resources
from typing import Any

from tee.kernel.errors import TeeError


@cache
def _eng() -> dict[str, Any]:
    text = (
        resources.files("tee.physical").joinpath("data/materials_eng.json").read_text()
    )
    return json.loads(text)


def banned_sources() -> list[str]:
    return _eng()["_meta"]["banned_bulk_sources"]


def find(query: str) -> tuple[str, dict[str, Any]]:
    materials = _eng()["materials"]
    q = query.lower().strip()
    for key, mat in materials.items():
        if q == key or q in (a.lower() for a in mat.get("aliases", [])):
            return key, mat
    for key, mat in materials.items():
        if q in key or any(q in a.lower() for a in mat.get("aliases", [])):
            return key, mat
    raise TeeError(
        "unknown_material",
        f"No engineering material matches '{query}'.",
        fix=f"Known: {', '.join(sorted(materials))} (aliases accepted); "
        "render-only materials live in as_materials.",
    )


def facts(query: str) -> dict[str, Any]:
    """All tiers for one material, every value with source + honesty."""
    key, mat = find(query)
    out: dict[str, Any] = {"material": key}
    out["physics"] = mat.get("physics", {})
    if mat.get("engineering"):
        out["engineering"] = mat["engineering"]
    render_ref = mat.get("render_ref")
    if render_ref:
        try:
            from tee.assets.materials import material_props

            resolved = material_props(render_ref)
            out["render"] = {**resolved["props"], "provenance": resolved["provenance"]}
        except Exception:
            out["render_ref"] = render_ref
    out["engine_caveats"] = _eng()["_meta"]["engine_caveats"]
    return out


def _density_value(mat: dict[str, Any]) -> tuple[float, str]:
    density = mat["physics"]["density"]
    value = density["value"]
    if isinstance(value, list):
        mid = (value[0] + value[1]) / 2
        return mid, f"midpoint of {value} ({density['honesty']})"
    return float(value), density["honesty"]


def assign_ops(
    entity_id: str, query: str, *, volume_m3: float | None = None
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Typed ops + the fact payload for one assignment. Render tier rides
    the assign_material op; physics tier travels as props (adapters that
    support rigid bodies consume them; others carry them as facts)."""
    key, mat = find(query)
    density, density_note = _density_value(mat)
    pair_friction = float(mat["physics"]["friction"]["value"])
    body_friction = round(math.sqrt(pair_friction), 4)
    props: dict[str, Any] = {
        "material": f"tee_{key}",
        "physics_density_kg_m3": density,
        "physics_friction_body": body_friction,
        "physics_restitution": mat["physics"]["restitution"]["value"],
    }
    render = None
    if mat.get("render_ref"):
        try:
            from tee.assets.materials import material_props

            render = material_props(mat["render_ref"])
            props.update({
                "base_color": render["props"]["base_color"],
                "metallic": render["props"]["metallic"],
                "roughness": render["props"]["roughness"],
            })
        except Exception:
            render = None
    ops = [{"op": "assign_material", "id": entity_id, "props": props}]
    fact: dict[str, Any] = {
        "kind": "material_fact",
        "material": key,
        "density_kg_m3": density,
        "density_note": density_note,
        "friction_pair": pair_friction,
        "friction_body_sqrt": body_friction,
        "friction_note": "Bullet multiplies pair coefficients - bodies carry sqrt(mu)",
        "sources": {
            tier: {name: leaf.get("source") for name, leaf in mat.get(tier, {}).items()}
            for tier in ("physics", "engineering")
            if mat.get(tier)
        },
        "honesty": {
            tier: {name: leaf.get("honesty") for name, leaf in mat.get(tier, {}).items()}
            for tier in ("physics", "engineering")
            if mat.get(tier)
        },
    }
    if render:
        fact["render_honesty"] = render["provenance"]["honesty"]
    if volume_m3 is not None:
        fact["mass_kg"] = round(volume_m3 * density, 2)
    return ops, fact
