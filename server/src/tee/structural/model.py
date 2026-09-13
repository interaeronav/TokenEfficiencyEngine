"""Explicit planar, linear elastic Timoshenko frames. N, mm, MPa, rad, Celsius delta."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from typing import Any


class StructuralError(ValueError):
    pass


def fail(message: str) -> None:
    raise StructuralError(message)


def fingerprint(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def number(value: Any, name: str, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        fail(f"{name} must be a finite number.")
    if abs(value) > 1e30:
        fail(f"{name} exceeds the supported numerical magnitude (1e30).")
    if positive and value <= 0:
        fail(f"{name} must be positive.")
    return float(value)


def keys(value: Any, required: str, optional: str = "") -> None:
    if not isinstance(value, dict):
        fail("Expected an object.")
    missing = set(required.split()) - value.keys()
    unknown = value.keys() - set((required + " " + optional).split())
    if missing or unknown:
        fail(f"Invalid fields: missing={sorted(missing)}, unknown={sorted(unknown)}.")


def source(row: dict) -> None:
    s = row.get("source")
    if not isinstance(s, str) or not s.strip() or len(s) > 1000:
        fail("Every engineering input needs a nonempty source, up to 1000 characters.")


def rows(value: Any, name: str, minimum: int = 1, maximum: int = 300) -> list:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        fail(f"{name} needs {minimum}..{maximum} rows.")
    return value


def indexed(value: Any, name: str, required: str, optional: str = "") -> dict:
    out = {}
    for row in rows(value, name):
        keys(row, "id " + required, optional)
        ident = row["id"]
        if not isinstance(ident, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", ident):
            fail(
                f"{name}: IDs must be 1..64 safe letters/digits/underscore/hyphen, "
                "starting with a letter."
            )
        if ident in out:
            fail(f"{name}: duplicate ID {ident}.")
        out[ident] = row
    return out


def validate(value: dict) -> dict:
    m = copy.deepcopy(value)
    keys(
        m,
        "name units analysis nodes materials sections elements supports cases combinations",
        "bim_source",
    )
    if not isinstance(m["name"], str) or not 1 <= len(m["name"]) <= 160:
        fail("name needs 1..160 characters.")
    if m["units"] != "N-mm-MPa-rad" or m["analysis"] != "linear_static_frame2d":
        fail(
            "Use units=N-mm-MPa-rad and analysis=linear_static_frame2d "
            "(Timoshenko, small displacement)."
        )
    nodes = indexed(m["nodes"], "nodes", "xy_mm")
    if len(nodes) > 200:
        fail("This dense stability gate supports at most 200 nodes.")
    for n in nodes.values():
        xy = rows(n["xy_mm"], "xy_mm", 2, 2)
        for v in xy:
            if abs(number(v, "coordinate")) > 1e8:
                fail("Origin-shift coordinates to within 1e8 mm.")
    materials = indexed(m["materials"], "materials", "E_mpa nu source", "alpha_per_c")
    for mat in materials.values():
        source(mat)
        number(mat["E_mpa"], "E_mpa", True)
        if not -0.99 < number(mat["nu"], "nu") < 0.5:
            fail("Isotropic nu must be between -0.99 and 0.5.")
        if "alpha_per_c" in mat:
            number(mat["alpha_per_c"], "alpha_per_c")
    sections = indexed(
        m["sections"],
        "sections",
        "area_mm2 iz_mm4 shear_area_mm2 source",
        "iy_mm4 torsion_j_mm4 shear_area_z_mm2",
    )
    for sec in sections.values():
        source(sec)
        for k, v in sec.items():
            if k not in ("id", "source"):
                number(v, k, True)
    elements = indexed(m["elements"], "elements", "nodes material section source", "bim_entity")
    used = set()
    for e in elements.values():
        source(e)
        ns = rows(e["nodes"], "element.nodes", 2, 2)
        if any(not isinstance(n, str) or n not in nodes for n in ns):
            fail("Element refers to a missing node.")
        if (
            not isinstance(e["material"], str)
            or e["material"] not in materials
            or not isinstance(e["section"], str)
            or e["section"] not in sections
        ):
            fail("Element refers to a missing material or section.")
        if math.dist(nodes[ns[0]]["xy_mm"], nodes[ns[1]]["xy_mm"]) < 1e-3:
            fail("Member length must be at least 0.001 mm.")
        used.update(ns)
    if used != set(nodes):
        fail("Remove disconnected unused nodes or connect them explicitly.")
    supports = set()
    for s in rows(m["supports"], "supports"):
        keys(s, "node fixed source")
        source(s)
        if not isinstance(s["node"], str) or s["node"] not in nodes or s["node"] in supports:
            fail("Support needs a unique existing node.")
        fixed = rows(s["fixed"], "fixed [ux,uy,rz]", 3, 3)
        if not all(isinstance(v, bool) for v in fixed) or not any(fixed):
            fail("Support fixed needs three booleans with at least one restraint.")
        supports.add(s["node"])
    cases = indexed(m["cases"], "cases", "source nodal", "uniform thermal")
    for c in cases.values():
        source(c)
        for load in rows(c["nodal"], "nodal", 0):
            keys(load, "node fx_n fy_n mz_nmm source")
            source(load)
            if not isinstance(load["node"], str) or load["node"] not in nodes:
                fail("Load refers to a missing node.")
            for k in ("fx_n", "fy_n", "mz_nmm"):
                number(load[k], k)
        for kind, fields in (("uniform", "qx_n_mm qy_n_mm"), ("thermal", "delta_c")):
            for load in rows(c.get(kind, []), kind, 0):
                keys(load, "element source " + fields)
                source(load)
                if not isinstance(load["element"], str) or load["element"] not in elements:
                    fail("Member load refers to a missing element.")
                for k in fields.split():
                    number(load[k], k)
                if (
                    kind == "thermal"
                    and "alpha_per_c" not in materials[elements[load["element"]]["material"]]
                ):
                    fail("Thermal loading requires explicit material alpha_per_c.")
    combos = (
        indexed(m["combinations"], "combinations", "factors source") if m["combinations"] else {}
    )
    for c in combos.values():
        source(c)
        f = c["factors"]
        if not isinstance(f, dict) or not f or not set(f) <= set(cases):
            fail("Combination factors must name existing load cases only.")
        for v in f.values():
            number(v, "factor")
        if c["id"] in cases:
            fail("Case and combination IDs must be distinct.")
    if not isinstance(m["combinations"], list):
        fail("combinations must be a list (empty is allowed).")
    if "bim_source" in m:
        keys(m["bim_source"], "model_id revision document_sha256")
        b = m["bim_source"]
        if not isinstance(b["model_id"], str) or not re.fullmatch(
            r"building_[a-f0-9]{16}", b["model_id"]
        ):
            fail("Invalid BIM model identity.")
        if (
            type(b["revision"]) is not int
            or b["revision"] < 0
            or not isinstance(b["document_sha256"], str)
            or not re.fullmatch(r"[a-f0-9]{64}", b["document_sha256"])
        ):
            fail("Invalid BIM revision/fingerprint.")
    if len(json.dumps(m)) > 500_000:
        fail("Model exceeds 500 kB; split the study.")
    return m
