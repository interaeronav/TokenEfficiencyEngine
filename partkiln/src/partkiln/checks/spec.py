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
  holes        `[{dia, count, tol?}]` - exactly what a HOLE TABLE would table
               as a hole of that diameter, counted by `brep.holes.hole_walls`,
               which is the ONE predicate `pk_check` and `pk_drawing` share.
               This rule used to be its own second answer, and the two
               disagreed: measured 2026-09-04, a 40 x 20 pocket with r5 corner
               radii and NO HOLES AT ALL passed `holes: [{dia: 10, count: 4}]`
               and failed `count: 0` with "found 4", while the sheet for the
               same part tabled nothing. A sheet and a check that disagree are
               indefensible to whoever is holding both.
               So: a corner radius is NOT a hole (concave, but its wall never
               closes); a bore split across several faces by a seam or a mirror
               join is ONE hole; two coaxial blind holes with METAL between
               them are TWO; and a SLOT's two ends are not holes at all - a
               slot is a slot, and `slots` is the rule that checks it. A
               counterbore seat is a second, larger cylinder and counts under
               ITS diameter; a cosmetic thread moves no geometry (Law 18) and
               is never counted.
  slots        `[{width, length?, count?, tol?}]` - slots, counted from the
               same predicate: two equal-radius concave ends joined by planar
               walls TANGENT to both. `width` is the end diameter, `length`
               the overall cut length (centre distance + one diameter) and is
               OPTIONAL - leave it out to count every slot of that width.
  min_wall_mm  a number; measured by `checks.wall` (inward ray casting). That
               measure is an UPPER bound, so a rule that passes is listed in
               `unproven` with its sample density - it was not disproven,
               which is not the same as proven.
  valid        `true` -> `BRepCheck_Analyzer` valid
  watertight   `true` -> valid AND a closed solid (no free edges)
  faces/edges  exact unique counts

Lengths accept unit strings ("2mm", "0.5in") through `partkiln.units`, the
one unit boundary (Law 12), and a BARE number is the document's unit, not
millimetres: pass `units=` (a unit name, a document, or `None` for
`strict_units`). Every other limit is coerced through `_number`/`_count`, so
a bad spec value refuses with a D8 code instead of escaping as a ValueError.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from partkiln.document import CommandError
from partkiln.units import LENGTH_UNITS, canonical_unit, parse_length

RULES = (
    "bbox",
    "volume_mm3",
    "mass_g",
    "holes",
    "slots",
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


def _number(rule: str, value: Any, what: str = "limit") -> float:
    """A plain number from user input, or a refusal.

    `float("big")` is a ValueError with no fix in it; a spec is user input
    and every refusal owes a D8 code and the fix (D8).
    """
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        raise CommandError(
            f"{rule} wants a number for {what}, got {value!r}. Fix: write a number.",
            code="pk_bad_op",
        )
    try:
        return float(value)
    except ValueError as exc:
        raise CommandError(
            f"{rule} wants a number for {what}, got {value!r}. Fix: write a number "
            "(a length may carry a unit, e.g. '0.5in'; this one may not).",
            code="pk_bad_op",
        ) from exc


def _count(rule: str, value: Any, what: str = "count") -> int:
    """A whole, non-negative count, or a refusal. `int("two")` is a ValueError."""
    number = _number(rule, value, what)
    if number < 0 or number != int(number):
        raise CommandError(
            f"{rule} wants a whole {what} >= 0, got {value!r}. Fix: write an integer.",
            code="pk_bad_op",
        )
    return int(number)


def _default_unit(units: Any) -> str | None:
    """The unit a BARE spec number is in: the document's, or None under
    `strict_units` (Law 12 - a bare number is the document's unit, and
    strict_units refuses it rather than guessing millimetres)."""
    if units is None:
        return None
    if isinstance(units, str):
        canonical_unit(units, "length")  # refuses pk_unit_unknown before any geometry
        return units
    if getattr(units, "strict_units", False):
        return None
    name = getattr(units, "units", None)
    if isinstance(name, str):
        canonical_unit(name, "length")
        return name
    raise CommandError(
        f"units wants a unit name, None, or a document, got {type(units).__name__}. "
        f"Fix: units='mm' (one of {', '.join(LENGTH_UNITS)}), units=None for strict_units, "
        "or pass the document itself.",
        code="pk_bad_op",
    )


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
    return (
        (None if lo is None else _number(rule, lo, "min")),
        (None if hi is None else _number(rule, hi, "max")),
    )


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

    def holes(self) -> list[Any]:
        """Every cylindrical wall of the shape, merged and classified.

        Cached because `holes` and `slots` read the same answer and a spec may
        carry several rows of each: the merge classifies solid points and may
        scan the edges, and measuring it twice would be paying twice for one
        fact.
        """
        if "holes" not in self._cache:
            from partkiln.brep import holes as _holes

            self._cache["holes"] = _holes.hole_walls(self.shape, self.faces())
        return self._cache["holes"]

    def wall(self, limit: float, samples: int) -> dict[str, Any]:
        if "wall" not in self._cache:
            from partkiln.checks.wall import check_wall

            self._cache["wall"] = check_wall(self.shape, limit, samples_per_face=samples)
        return self._cache["wall"]

    def wall_report(self) -> dict[str, Any] | None:
        """The wall measure if one was taken - it carries `proven`, which the
        verdict owes the caller."""
        return self._cache.get("wall")


def _rule_bbox(m: _Measured, limit: Any, unit: str | None) -> list[dict[str, Any]]:
    tol = _DEFAULT_TOL
    dims = limit
    if isinstance(limit, dict):
        dims = limit.get("dims")
        # The DEFAULT tolerance is 0.01 mm whatever the document's unit is;
        # only a tolerance the caller wrote is read in that unit.
        if "tol" in limit:
            tol = parse_length(limit["tol"], unit)
    if not isinstance(dims, Sequence) or isinstance(dims, str) or len(dims) != 3:
        raise CommandError(
            f"bbox wants [dx, dy, dz] or {{dims: [dx, dy, dz], tol}}, got {limit!r}. "
            "Fix: write bbox: [100, 60, 10].",
            code="pk_bad_op",
        )
    want = [parse_length(d, unit) for d in dims]
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


_SEATS_NOTE = " (seats count under their own diameter, cosmetic threads are never counted)"


def _not_counted(m: _Measured, walls: Sequence[Any], dia: float, tol: float) -> str:
    """Which cylinders of this diameter the count passed over, and why.

    A count that is only a number sends the model looking through the whole
    part for four holes that were never there. Every cylinder of the asked-for
    diameter that is not a hole is named here with the reason it is not one,
    because a verdict without the fix costs a second call (D8).
    """
    from partkiln.brep import shapes as _shapes

    def hit(radius: float | None) -> bool:
        return radius is not None and abs(2.0 * radius - dia) <= tol

    cylinders = [f for f in m.faces() if f.surface_type == "cylinder" and hit(f.radius)]
    convex = sum(1 for f in cylinders if not _shapes.is_concave_cylinder(f.shape))
    ends = sum(1 for w in walls if w.kind == "slot" and hit(w.radius))
    partial = sum(1 for w in walls if w.kind == "partial" and hit(w.radius))
    said = []
    if convex:
        said.append(
            f"{convex} convex cylinder(s) of d{dia:g} - a fillet or a boss is not a hole, "
            "a hole's wall is concave"
        )
    if ends:
        said.append(
            f"{ends} slot end(s) of d{dia:g} - a slot is one slot, not two holes; check it "
            "with the slots rule"
        )
    if partial:
        said.append(
            f"{partial} concave wall(s) of d{dia:g} that never close a full turn - a corner "
            "radius or a notch, which belongs to its pocket and not to a hole table"
        )
    return ("" if not said else " NOT counted: " + "; ".join(said) + ".") + _SEATS_NOTE


def _rule_holes(m: _Measured, limit: Any, unit: str | None) -> list[dict[str, Any]]:
    if isinstance(limit, dict):
        limit = [limit]
    if not isinstance(limit, Sequence) or isinstance(limit, str):
        raise CommandError(
            f"holes wants [{{dia, count}}...], got {limit!r}. "
            "Fix: write holes: [{dia: 10, count: 1}].",
            code="pk_bad_op",
        )
    walls = m.holes()
    bores = [w for w in walls if w.kind == "hole"]
    out = []
    for row in limit:
        if not isinstance(row, dict) or "dia" not in row:
            raise CommandError(
                f"each holes entry needs dia (and count), got {row!r}. "
                "Fix: write {dia: 10, count: 1}.",
                code="pk_bad_op",
            )
        dia = parse_length(row["dia"], unit)
        tol = _DEFAULT_TOL if "tol" not in row else parse_length(row["tol"], unit)
        want = _count("holes", row.get("count", 1))
        got = sum(1 for w in bores if abs(2.0 * w.radius - dia) <= tol)
        if got != want:
            seen = sorted({_r3(2.0 * w.radius) for w in bores})
            out.append(
                {
                    "rule": "holes",
                    "dia": _r3(dia),
                    "got": got,
                    "limit": want,
                    "fix": f"expected {want} hole(s) of d{dia:g}, found {got}; hole diameters "
                    f"present: {seen}" + _not_counted(m, walls, dia, tol),
                }
            )
    return out


def _rule_slots(m: _Measured, limit: Any, unit: str | None) -> list[dict[str, Any]]:
    if isinstance(limit, dict):
        limit = [limit]
    if not isinstance(limit, Sequence) or isinstance(limit, str):
        raise CommandError(
            f"slots wants [{{width, length}}...], got {limit!r}. "
            "Fix: write slots: [{width: 8, length: 40, count: 1}].",
            code="pk_bad_op",
        )
    from partkiln.brep import holes as _holes

    sizes = [_holes.slot_size(a, b) for a, b in _holes.slot_ends(m.holes())]
    out = []
    for row in limit:
        if not isinstance(row, dict) or "width" not in row:
            raise CommandError(
                f"each slots entry needs width (length and count are optional), got {row!r}. "
                "Fix: write {width: 8, length: 40, count: 1}.",
                code="pk_bad_op",
            )
        width = parse_length(row["width"], unit)
        length = None if "length" not in row else parse_length(row["length"], unit)
        tol = _DEFAULT_TOL if "tol" not in row else parse_length(row["tol"], unit)
        want = _count("slots", row.get("count", 1))
        got = sum(
            1
            for w, ln in sizes
            if abs(w - width) <= tol and (length is None or abs(ln - length) <= tol)
        )
        if got == want:
            continue
        asked = f"{width:g} wide" + ("" if length is None else f" x {length:g} long")
        seen = sorted({(_r3(w), _r3(ln)) for w, ln in sizes})
        out.append(
            {
                "rule": "slots",
                "width": _r3(width),
                **({} if length is None else {"length": _r3(length)}),
                "got": got,
                "limit": want,
                "fix": f"expected {want} slot(s) {asked}, found {got}; slots present as "
                f"[width, length]: {[list(s) for s in seen]} (a slot is two equal-radius "
                "concave ends joined by planar walls TANGENT to both - two holes with air "
                "between them stay two holes, and a slot's ends are never counted by `holes`)",
            }
        )
    return out


def _rule_wall(m: _Measured, limit: Any, samples: int, unit: str | None) -> list[dict[str, Any]]:
    want = parse_length(limit, unit)
    return list(m.wall(want, samples)["violations"])


def _wall_note(report: dict[str, Any]) -> str:
    """Why a passing wall rule is not a proof, with the density that measured it."""
    n = report.get("samples_per_face")
    return (
        f"min_wall_mm: {report['min_mm']:g} mm is an upper bound, not a proof - "
        f"{n}x{n} UV samples per face plus {report.get('pairs_examined')} face-pair extrema "
        "(checks.wall). Fix: raise wall_samples, or section the suspect region."
    )


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
    want = _count(rule, limit)
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
    shape_or_parts: Any,
    spec: dict[str, Any],
    material: str | None = None,
    units: Any = "mm",
) -> dict[str, Any]:
    """Verify `spec` against a shape (or parts, checked as one compound).

    Returns `{verdict: "pass"|"fail", violations: [{rule, got, limit, fix}],
    checked: [rules], material}`, plus `unproven` (a note per rule whose
    measure is an upper bound, not a proof) when there is one. Unknown rules
    refuse BEFORE any geometry is measured, so a typo never costs a wall scan.

    `units` is the unit a BARE length in the spec is written in (Law 12): a
    unit name, a document (its `units`, or `strict_units` -> refuse a bare
    number), or None for strict. A length written as a string always carries
    its own unit and ignores this.
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
    unit = _default_unit(units)
    shape = _as_one_shape(shape_or_parts)
    material = material or spec.get("material")
    density = spec.get("density_kg_m3")
    samples = _count("wall_samples", spec.get("wall_samples", 5), "sample count")
    m = _Measured(
        shape,
        material,
        None if density is None else _number("density_kg_m3", density),
    )
    violations: list[dict[str, Any]] = []
    checked: list[str] = []
    unproven: list[str] = []
    for rule in RULES:
        if rule not in spec:
            continue
        limit = spec[rule]
        checked.append(rule)
        if rule == "bbox":
            violations += _rule_bbox(m, limit, unit)
        elif rule in ("volume_mm3", "mass_g"):
            violations += _rule_band(rule, m, limit)
        elif rule == "holes":
            violations += _rule_holes(m, limit, unit)
        elif rule == "slots":
            violations += _rule_slots(m, limit, unit)
        elif rule == "min_wall_mm":
            violations += _rule_wall(m, limit, samples, unit)
            report = m.wall_report()
            if report is not None and not report.get("proven", False):
                unproven.append(_wall_note(report))
        elif rule in ("valid", "watertight"):
            violations += _rule_valid(m, limit, rule == "watertight")
        else:
            violations += _rule_count(rule, m, limit)
    return {
        "verdict": "fail" if violations else "pass",
        "violations": violations,
        "checked": checked,
        "material": m.mass()["material"] if "mass" in m._cache else material,
        # Only when there IS one: an always-empty key is tokens for nothing.
        **({"unproven": unproven} if unproven else {}),
    }


__all__ = ["RULES", "check_spec"]
