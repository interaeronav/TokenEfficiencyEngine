"""Creation lane 0 (A14): procedural materials from measured CC0 data.

The physicallybased.info dataset (CC0-1.0, snapshotted in data/
pbr_materials.json with retrieval date) provides measured albedo/
metalness/roughness/IOR/density - no hallucinated constants. Lane 0 is
the default: zero GPU, zero tokens at rest, values with provenance.
Density rides along for the Phase 11 physics tier.
"""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

from tee.kernel.errors import TeeError

DATASET = "physicallybased.info"
DATASET_LICENSE = "CC0-1.0"
DATASET_AS_OF = "2026-08-22"

_MATERIALS: list[dict[str, Any]] | None = None


def _load() -> list[dict[str, Any]]:
    global _MATERIALS
    if _MATERIALS is None:
        text = (
            resources.files("tee.assets").joinpath("data/pbr_materials.json").read_text()
        )
        _MATERIALS = json.loads(text)
    return _MATERIALS


def list_materials(category: str | None = None) -> list[dict[str, Any]]:
    """Compact rows: name, category, key scalar params."""
    rows = []
    for mat in _load():
        cats = [c.lower() for c in mat.get("category", [])]
        if category and category.lower() not in cats:
            continue
        rows.append(
            {
                "name": mat["name"],
                "category": cats[0] if cats else "",
                "metalness": mat.get("metalness", 0),
                "roughness": mat.get("roughness"),
            }
        )
    return rows


def find_material(query: str) -> dict[str, Any]:
    """Best name/tag match; error names close alternatives (fail loud+cheap)."""
    q = query.lower().strip()
    materials = _load()
    exact = next((m for m in materials if m["name"].lower() == q), None)
    if exact:
        return exact
    scored = []
    for mat in materials:
        text = " ".join(
            [mat["name"].lower(), " ".join(mat.get("tags", [])), " ".join(mat.get("category", []))]
        ).lower()
        words = q.split()
        score = sum(1 for w in words if w in text)
        if score:
            scored.append((score, mat))
    if not scored:
        names = ", ".join(sorted(m["name"] for m in materials)[:10])
        raise TeeError(
            "unknown_material",
            f"No measured material matches '{query}'.",
            fix=f"86 materials available; e.g. {names}… (as_materials lists all).",
        )
    scored.sort(key=lambda pair: -pair[0])
    return scored[0][1]


def material_props(query: str) -> dict[str, Any]:
    """Principled-BSDF-shaped props + provenance, from measured values."""
    mat = find_material(query)
    props: dict[str, Any] = {
        "material": f"tee_{mat['name'].replace(' ', '_').lower()}",
        "base_color": [round(float(c), 4) for c in mat.get("color", [0.8, 0.8, 0.8])[:3]],
        "metallic": float(mat.get("metalness", 0.0)),
        "roughness": float(mat.get("roughness", 0.5)),
    }
    provenance = {
        "kind": "material_provenance",
        "name": mat["name"],
        "dataset": DATASET,
        "license": DATASET_LICENSE,
        "as_of": DATASET_AS_OF,
        "honesty": "measured",
    }
    if mat.get("density") is not None:
        provenance["density_kg_m3"] = mat["density"]
    if mat.get("ior") is not None:
        provenance["ior"] = mat["ior"]
    if mat.get("sources"):
        provenance["sources"] = mat["sources"][:2]
    return {"props": props, "provenance": provenance}


def assign_ops(entity_id: str, query: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """The typed batch op + provenance fact for one assignment."""
    resolved = material_props(query)
    op = {"op": "assign_material", "id": entity_id, "props": resolved["props"]}
    return [op], resolved["provenance"]
