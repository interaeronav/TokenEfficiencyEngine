"""A spec dict -> {verdict, violations, checked}: the `pk_check` backend.

A spec is a closed vocabulary of rules (unknown rule -> `pk_bad_op` listing
every rule, D5's law applied to checks). Every violation is
`{rule, got, limit, fix}` and the fix is literal - "increase min wall to
2 mm at [x, y, z]" - because a verdict without the fix costs the model a
second call (the metric is tokens per completed part task).

Rules and the limit each reads:

  bbox         `[dx, dy, dz]` or `{dims, tol}` - extents on X, Y, Z in the
               model's frame (NOT sorted: a 100x60x10 plate stood on end is
               a different part); tol defaults to 0.01 mm
  volume_mm3   `[lo, hi]` or `{min, max}` band
  mass_g       band, needs a material (argument, or `spec["material"]`) or
               `spec["density_kg_m3"]`; refuses `pk_needs` without one
  holes        `[{dia, count, tol?}]` - cylindrical faces of that radius,
               UNIQUE faces (Law 20). A counterbore seat or a cosmetic
               thread is not a separate hole: the seat is a second, larger
               cylinder and counts under ITS diameter; a thread moves no
               geometry (Law 18) and is never counted.
  min_wall_mm  a number; measured by `checks.wall` (inward ray casting)
  valid        `true` -> `BRepCheck_Analyzer` valid
  watertight   `true` -> valid AND a closed solid (no free edges)
  faces/edges  exact unique counts

Lengths accept unit strings ("2mm", "0.5in") through `partkiln.units`, the
one unit boundary (Law 12).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from partkiln.document import CommandError
from partkiln.units import parse_length

RULES = (
    "bbox",
    "volume_mm3",
    "mass_g",
    "holes",
    "min_wall_mm",
    "valid",
    "watertight",
    "faces",
    "edges",
)
_OPTIONS = ("material", "density_kg_m3", "wall_samples")
_DEFAULT_TOL = 0.01


def _r3(x: float) -> float:
    return round(float(x), 3) + 0.0


def _band(rule: str, limit: Any) -> tuple[float | None, float | None]:
    if isinstance(limit, dict):
        lo, hi = limit.get("min"), limit.get("max")
    elif isinstance(limit, Sequence) and not isinstance(limit, str) and len(limit) == 2:
        lo, hi = limit
    else:
        raise CommandError(
            f"{rule} wants a band [lo, hi] or {{min, max}}, got {limit!r}. "
            f"Fix: write {rule}: [lo, hi].",
            code="pk_bad_op",
        )
    return (None if lo is None else float(lo)), (None if hi is None else float(hi))


class _Measured:
    """Lazily computed measures shared by the rules, each computed once."""

    def __init__(self, shape: Any, material: str | None, density: float | None) -> None:
        self.shape = shape
        self.material = material
        self.density = density
        self._cache: dict[str, Any] = {}

    def mass(self) -> dict[str, Any]:
        if "mass" not in self._cache:
            from partkiln.checks.mass import mass_properties

            self._cache["mass"] = mass_properties(self.shape, self.material, self.density)
        return self._cache["mass"]

    def validity(self) -> dict[str, Any]:
        if "validity" not in self._cache:
            from partkiln.checks.validity import validate

            self._cache["validity"] = validate(self.shape)
        return self._cache["validity"]

    def faces(self) -> list[Any]:
        if "faces" not in self._cache:
            from partkiln.brep import query

            self._cache["faces"] = query.faces(self.shape)
        return self._cache["faces"]

    def wall(self, limit: float, samples: int) -> dict[str, Any]:
        if "wall" not in self._cache:
            from partkiln.checks.wall import check_wall

            self._cache["wall"] = check_wall(self.shape, limit, samples_per_face=samples)
        return self._cache["wall"]


def _rule_bbox(m: _Measured, limit: Any) -> list[dict[str, Any]]:
    tol = _DEFAULT_TOL
    dims = limit
    if isinstance(limit, dict):
        dims = limit.get("dims")
        tol = parse_length(limit.get("tol", _DEFAULT_TOL))
    if not isinstance(dims, Sequence) or isinstance(dims, str) or len(dims) != 3:
        raise CommandError(
            f"bbox wants [dx, dy, dz] or {{dims: [dx, dy, dz], tol}}, got {limit!r}. "
            "Fix: write bbox: [100, 60, 10].",
            code="pk_bad_op",
        )
    want = [parse_length(d) for d in dims]
    got = m.mass()["bbox_mm"]
    out = []
    for axis, w, g in zip("XYZ", want, got, strict=True):
        if abs(w - g) > tol:
            out.append(
                {
                    "rule": "bbox",
                    "axis": axis,
                    "got": g,
                    "limit": _r3(w),
                    "tol": _r3(tol),
                    "fix": f"change the {axis} extent from {g:g} to {w:g} mm (tol {tol:g})",
                }
            )
    return out


def _rule_band(rule: str, m: _Measured, limit: Any) -> list[dict[str, Any]]:
    lo, hi = _band(rule, limit)
    props = m.mass()
    if rule == "mass_g" and "mass_g" not in props:
        raise CommandError(
            "mass_g needs a density: pass material= (a card such as steel_s275) or "
            'spec[\'density_kg_m3\']. Fix: add "material": "steel_s275" to the spec.',
            code="pk_needs",
        )
    got = props[rule]
    unit = "g" if rule == "mass_g" else "mm3"
    if lo is not None and got < lo:
        return [
            {
                "rule": rule,
                "got": got,
                "limit": [lo, hi],
                "fix": f"add {lo - got:g} {unit} (got {got:g}, minimum {lo:g})",
            }
        ]
    if hi is not None and got > hi:
        return [
            {
                "rule": rule,
                "got": got,
                "limit": [lo, hi],
                "fix": f"remove {got - hi:g} {unit} (got {got:g}, maximum {hi:g})",
            }
        ]
    return []


def _rule_holes(m: _Measured, limit: Any) -> list[dict[str, Any]]:
    if isinstance(limit, dict):
        limit = [limit]
    if not isinstance(limit, Sequence) or isinstance(limit, str):
        raise CommandError(
            f"holes wants [{{dia, count}}...], got {limit!r}. "
            "Fix: write holes: [{dia: 10, count: 1}].",
            code="pk_bad_op",
        )
    cylinders = [f for f in m.faces() if f.surface_type == "cylinder" and f.radius is not None]
    out = []
    for row in limit:
        if not isinstance(row, dict) or "dia" not in row:
            raise CommandError(
                f"each holes entry needs dia (and count), got {row!r}. "
                "Fix: write {dia: 10, count: 1}.",
                code="pk_bad_op",
            )
        dia = parse_length(row["dia"])
        tol = parse_length(row.get("tol", _DEFAULT_TOL))
        want = int(row.get("count", 1))
        got = sum(1 for f in cylinders if abs(2.0 * f.radius - dia) <= tol)
        if got != want:
            seen = sorted({_r3(2.0 * f.radius) for f in cylinders})
            out.append(
                {
                    "rule": "holes",
                    "dia": _r3(dia),
                    "got": got,
                    "limit": want,
                    "fix": f"expected {want} cylindrical face(s) of d{dia:g}, found {got}; "
                    f"diameters present: {seen} (seats count under their own diameter, "
                    "cosmetic threads are never counted)",
                }
            )
    return out


def _rule_wall(m: _Measured, limit: Any, samples: int) -> list[dict[str, Any]]:
    want = parse_length(limit)
    return list(m.wall(want, samples)["violations"])


def _rule_valid(m: _Measured, limit: Any, watertight: bool) -> list[dict[str, Any]]:
    if not limit:
        return []
    v = m.validity()
    ok = v["valid"] and (v["closed"] if watertight else True)
    if ok:
        return []
    rule = "watertight" if watertight else "valid"
    what = "; ".join(v["problems"]) or "invalid"
    return [
        {
            "rule": rule,
            "got": False,
            "limit": True,
            "fix": f"{what}: run fix() on an imported body, or rebuild the feature "
            "that produced it",
        }
    ]


def _rule_count(rule: str, m: _Measured, limit: Any) -> list[dict[str, Any]]:
    want = int(limit)
    got = int(m.validity()[rule])
    if got == want:
        return []
    return [
        {
            "rule": rule,
            "got": got,
            "limit": want,
            "fix": f"expected {want} unique {rule}, found {got} (counts are unique sub-shapes)",
        }
    ]


def _as_one_shape(shape_or_parts: Any) -> Any:
    """A single shape, or a compound of several parts checked as one."""
    if isinstance(shape_or_parts, dict):
        shape_or_parts = [shape_or_parts[k] for k in sorted(shape_or_parts)]
    if isinstance(shape_or_parts, list | tuple):
        if not shape_or_parts:
            raise CommandError(
                "check_spec got no parts. Fix: pass a shape or a non-empty list of shapes.",
                code="pk_needs",
            )
        if len(shape_or_parts) == 1:
            return shape_or_parts[0]
        from OCP.BRep import BRep_Builder
        from OCP.TopoDS import TopoDS_Compound

        compound = TopoDS_Compound()
        builder = BRep_Builder()
        builder.MakeCompound(compound)
        for s in shape_or_parts:
            builder.Add(compound, s)
        return compound
    return shape_or_parts


def check_spec(
    shape_or_parts: Any, spec: dict[str, Any], material: str | None = None
) -> dict[str, Any]:
    """Verify `spec` against a shape (or parts, checked as one compound).

    Returns `{verdict: "pass"|"fail", violations: [{rule, got, limit, fix}],
    checked: [rules], material}`. Unknown rules refuse BEFORE any geometry
    is measured, so a typo never costs a wall scan.
    """
    if not isinstance(spec, dict):
        raise CommandError(
            f"spec must be a dict of rules, got {type(spec).__name__}. "
            f"Fix: rules are {', '.join(RULES)}.",
            code="pk_bad_op",
        )
    unknown = sorted(k for k in spec if k not in RULES and k not in _OPTIONS)
    if unknown:
        raise CommandError(
            f"unknown spec rule(s) {', '.join(unknown)}. Fix: use only "
            f"{', '.join(RULES)} (options: {', '.join(_OPTIONS)}).",
            code="pk_bad_op",
        )
    shape = _as_one_shape(shape_or_parts)
    material = material or spec.get("material")
    density = spec.get("density_kg_m3")
    samples = int(spec.get("wall_samples", 5))
    m = _Measured(shape, material, None if density is None else float(density))
    violations: list[dict[str, Any]] = []
    checked: list[str] = []
    for rule in RULES:
        if rule not in spec:
            continue
        limit = spec[rule]
        checked.append(rule)
        if rule == "bbox":
            violations += _rule_bbox(m, limit)
        elif rule in ("volume_mm3", "mass_g"):
            violations += _rule_band(rule, m, limit)
        elif rule == "holes":
            violations += _rule_holes(m, limit)
        elif rule == "min_wall_mm":
            violations += _rule_wall(m, limit, samples)
        elif rule in ("valid", "watertight"):
            violations += _rule_valid(m, limit, rule == "watertight")
        else:
            violations += _rule_count(rule, m, limit)
    return {
        "verdict": "fail" if violations else "pass",
        "violations": violations,
        "checked": checked,
        "material": m.mass()["material"] if "mass" in m._cache else material,
    }


__all__ = ["RULES", "check_spec"]
