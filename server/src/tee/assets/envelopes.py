"""Semantic-class dimension envelopes + the four-band scale policy (A15).

Bands, in order (research 25 R1-R4):
  1. accept       - measured dims fit the class envelope (or the target)
  2. fix          - a silent power-of-ten or inch-factor correction brings
                    them into the envelope; applied and RECORDED as a fact
                    (unit-boundary bugs are the #1 import failure)
  3. snap         - within ±10% of the target/catalogue dims; snapped
  4. reject       - one line naming measured vs expected

Scaling is uniform-only unless the asset (or class) declares stretch_axes;
non-uniform is forbidden outright for rigid classes (doors, windows,
appliances, sanitary, seating, humans, plants).
"""

from __future__ import annotations

import json
import math
from importlib import resources
from typing import Any

_UNIT_FACTORS = (
    (0.001, "mm->m"),
    (0.01, "cm->m"),
    (0.1, "dm->m"),
    (10.0, "x10"),
    (100.0, "m->cm authored"),
    (1000.0, "m->mm authored"),
    (0.0254, "inches->m"),
    (39.3701, "m->inches authored"),
)

_SNAP_TOLERANCE = 0.10
_ACCEPT_SLACK = 1.02  # envelopes are bands, not gauges


def load_envelopes() -> dict[str, Any]:
    text = (
        resources.files("tee.assets").joinpath("data/envelopes.json").read_text()
    )
    data = json.loads(text)
    data.pop("_meta", None)
    return data


_ENVELOPES: dict[str, Any] | None = None


def envelope_for(asset_class: str | None) -> dict[str, Any] | None:
    global _ENVELOPES
    if _ENVELOPES is None:
        _ENVELOPES = load_envelopes()
    if not asset_class:
        return None
    return _ENVELOPES.get(asset_class.lower())


def _fits(dims: list[float], env: dict[str, Any]) -> bool:
    lo, hi = env["min"], env["max"]
    return all(
        lo[i] / _ACCEPT_SLACK <= dims[i] <= hi[i] * _ACCEPT_SLACK for i in range(3)
    )


def _matches_target(dims: list[float], target: list[float], tol: float) -> bool:
    pairs = [(d, t) for d, t in zip(dims, target, strict=False) if t]
    return bool(pairs) and all(abs(d - t) <= tol * t for d, t in pairs)


def scale_policy(
    measured: list[float],
    *,
    asset_class: str | None = None,
    target: list[float] | None = None,
) -> dict[str, Any]:
    """Rule on measured dims [x, y, z] in meters. Returns
    {band, scale (uniform factor), dims (after scale), note, fact?}."""
    measured = [float(v) for v in measured[:3]]
    env = envelope_for(asset_class)
    if not any(v > 0 for v in measured):
        return {
            "band": "reject",
            "scale": 1.0,
            "dims": measured,
            "note": "asset has zero extents - not importable",
        }

    def result(band: str, scale: float, note: str, fact: dict | None = None):
        out: dict[str, Any] = {
            "band": band,
            "scale": round(scale, 6),
            "dims": [round(v * scale, 4) for v in measured],
            "note": note,
        }
        if fact:
            out["fact"] = fact
        return out

    # band 1: accept as-is
    if target is not None and _matches_target(measured, target, 0.02):
        return result("accept", 1.0, "matches target dims within 2%")
    if target is None and env is not None and _fits(measured, env):
        return result("accept", 1.0, f"within the {asset_class} envelope")

    # band 2: silent unit-factor fix, recorded
    for factor, label in _UNIT_FACTORS:
        fixed = [v * factor for v in measured]
        ok = (
            _matches_target(fixed, target, _SNAP_TOLERANCE)
            if target is not None
            else env is not None and _fits(fixed, env)
        )
        if ok:
            fact = {
                "kind": "scale_fix",
                "factor": factor,
                "reason": label,
                "measured": [round(v, 4) for v in measured],
            }
            return result(
                "fix", factor, f"unit correction {label} (x{factor:g}), recorded", fact
            )

    # band 3: snap within ±10% of the target (or the class typical size).
    # Uniform scale = geometric mean of the constrained-axis ratios; every
    # constrained axis must land within ±10% of its reference afterwards
    # (a zero/None target axis means unconstrained, e.g. door thickness).
    reference = target if target is not None else (env or {}).get("typical")
    if reference:
        ratios = [
            reference[i] / measured[i]
            for i in range(min(3, len(reference)))
            if reference[i] and measured[i] > 0
        ]
        if ratios:
            scale = math.prod(ratios) ** (1 / len(ratios))
            fits_after = all(
                abs(measured[i] * scale - reference[i]) <= _SNAP_TOLERANCE * reference[i]
                for i in range(min(3, len(reference)))
                if reference[i] and measured[i] > 0
            )
            if abs(1 - scale) <= _SNAP_TOLERANCE and fits_after:
                fact = {
                    "kind": "scale_snap",
                    "factor": round(scale, 4),
                    "target": [round(v, 4) for v in reference],
                    "measured": [round(v, 4) for v in measured],
                }
                return result(
                    "snap", scale, f"snapped x{scale:.3f} to catalogue dims", fact
                )

    # band 4: reject, one line
    expected = (
        f"target {[round(v, 2) for v in target]}"
        if target is not None
        else (
            f"{asset_class} envelope {env['min']}..{env['max']}"
            if env
            else "no envelope or target to judge against"
        )
    )
    return result(
        "reject",
        1.0,
        f"measured {[round(v, 2) for v in measured]} m does not fit {expected} "
        "and no unit factor or ±10% snap explains it",
    )


def non_uniform_allowed(asset_class: str | None, axis: str) -> bool:
    env = envelope_for(asset_class)
    if env is None:
        return False
    if env.get("rigid"):
        return False
    return axis in env.get("stretch_axes", [])
