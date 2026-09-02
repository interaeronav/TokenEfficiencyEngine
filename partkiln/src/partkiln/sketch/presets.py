"""Profile presets: one word in the batch, a fully constrained sketch out.

`{rect: [100, 60]}` is what a model writes; four points, four lines, two
horizontals, two verticals, two dimensions and a fixed corner is what the
solver needs. The expansion is deterministic - the tags are derived from the
preset tag (`r.p0`, `r.0`, `r.w`), so the model can name `r.w` in a later
`set` without ever seeing a coordinate.

Every preset is `anchored` by default: its reference point is fixed at
`at`, and the report says `dof 0`. `anchored: false` leaves it free for the
constraints a designer adds (the P1 acceptance rectangle is exactly that).
Values arrive as numbers in mm/deg or as strings ("W", "3/8in"); the two
callables passed in convert them, so the units and parameter rules live in
the document and nowhere else.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from partkiln.document import CommandError
from partkiln.sketch.model import Arc, Circle, Entity, Line, Point

PRESETS = ("rect", "circle", "slot", "polygon", "poly")

Parser = Callable[[Any], float]


@dataclass(slots=True)
class Expansion:
    """What a preset adds to a sketch, in order. Constraints are
    (kind, refs, tag); dims are (kind, refs, value, tag, axis, expr)."""

    entities: list[Entity] = field(default_factory=list)
    constraints: list[tuple[str, tuple[str, ...], str]] = field(default_factory=list)
    dims: list[tuple[str, tuple[str, ...], float, str, str | None, str | None]] = field(
        default_factory=list
    )
    assumed: dict[str, Any] = field(default_factory=dict)
    tag: str = ""
    anchor: str = ""  # the point `anchored` fixes


def preset_kind(spec: dict[str, Any]) -> str:
    kinds = [k for k in PRESETS if k in spec]
    if len(kinds) != 1:
        raise CommandError(
            f"a profile names exactly one preset; got {sorted(spec) or 'nothing'}. "
            f"Presets: {', '.join(PRESETS)}.",
            code="pk_bad_op",
        )
    return kinds[0]


def _pair(spec: dict[str, Any], key: str, what: str) -> tuple[Any, Any]:
    raw = spec.get(key)
    if not isinstance(raw, list | tuple) or len(raw) != 2:
        raise CommandError(f"{key} needs {what}, e.g. {key}: [100, 60].", code="pk_needs")
    return raw[0], raw[1]


def _expr(raw: Any) -> str | None:
    return raw if isinstance(raw, str) else None


def expand(
    spec: dict[str, Any],
    *,
    length: Parser,
    angle: Parser,
    existing: set[str] = frozenset(),  # type: ignore[assignment]
) -> Expansion:
    """Expand one preset spec. `length`/`angle` turn a raw value into mm/deg."""
    kind = preset_kind(spec)
    tag = str(spec.get("tag") or kind)
    if tag in existing:
        n = 2
        while f"{tag}{n}" in existing:
            n += 1
        tag = f"{tag}{n}"
    out = Expansion(tag=tag)
    at_raw = spec.get("at")
    if at_raw is None:
        ax, ay = 0.0, 0.0
        out.assumed["at"] = [0, 0]
    else:
        if not isinstance(at_raw, list | tuple) or len(at_raw) != 2:
            raise CommandError("at needs [x, y].", code="pk_needs")
        ax, ay = length(at_raw[0]), length(at_raw[1])
    anchored = bool(spec.get("anchored", True))
    if "anchored" not in spec:
        out.assumed["anchored"] = True

    if kind == "rect":
        _rect(out, spec, ax, ay, length)
    elif kind == "circle":
        _circle(out, spec, ax, ay, length)
    elif kind == "slot":
        _slot(out, spec, ax, ay, length, angle)
    elif kind == "polygon":
        _polygon(out, spec, ax, ay, length)
    else:
        _poly(out, spec, length, anchored)
    if anchored and out.anchor:
        out.constraints.append(("fix", (out.anchor,), f"{tag}.fix"))
    return out


def _rect(out: Expansion, spec: dict[str, Any], ax: float, ay: float, length: Parser) -> None:
    w_raw, h_raw = _pair(spec, "rect", "[width, height]")
    w, h = length(w_raw), length(h_raw)
    if w <= 0 or h <= 0:
        raise CommandError(f"rect needs positive sides, got [{w:g}, {h:g}] mm.", code="pk_needs")
    t = out.tag
    corners = [(ax, ay), (ax + w, ay), (ax + w, ay + h), (ax, ay + h)]
    for k, (x, y) in enumerate(corners):
        out.entities.append(Point(f"{t}.p{k}", x, y))
    for k in range(4):
        out.entities.append(Line(f"{t}.{k}", f"{t}.p{k}", f"{t}.p{(k + 1) % 4}"))
    out.constraints += [
        ("horizontal", (f"{t}.0",), f"{t}.h0"),
        ("vertical", (f"{t}.1",), f"{t}.v1"),
        ("horizontal", (f"{t}.2",), f"{t}.h2"),
        ("vertical", (f"{t}.3",), f"{t}.v3"),
    ]
    out.dims += [
        ("len", (f"{t}.0",), w, f"{t}.w", None, _expr(w_raw)),
        ("len", (f"{t}.1",), h, f"{t}.h", None, _expr(h_raw)),
    ]
    out.anchor = f"{t}.p0"


def _circle(out: Expansion, spec: dict[str, Any], ax: float, ay: float, length: Parser) -> None:
    d_raw = spec["circle"]
    d = length(d_raw)
    if d <= 0:
        raise CommandError(f"circle needs a positive diameter, got {d:g} mm.", code="pk_needs")
    t = out.tag
    out.entities.append(Point(f"{t}.c", ax, ay))
    out.entities.append(Circle(t, f"{t}.c", d / 2.0))
    out.dims.append(("dia", (t,), d, f"{t}.d", None, _expr(d_raw)))
    out.anchor = f"{t}.c"


def _slot(
    out: Expansion, spec: dict[str, Any], ax: float, ay: float, length: Parser, angle: Parser
) -> None:
    len_raw, w_raw = _pair(spec, "slot", "[length, width]")
    total, w = length(len_raw), length(w_raw)
    if w <= 0 or total <= w:
        raise CommandError(
            f"slot needs length > width > 0, got length {total:g} mm, width {w:g} mm.",
            code="pk_needs",
        )
    if "angle" in spec:
        theta = angle(spec["angle"])
    else:
        theta = 0.0
        out.assumed["angle"] = 0
    t = out.tag
    cc = total - w  # centre to centre
    r = w / 2.0
    h = cc / 2.0
    ct, st = math.cos(math.radians(theta)), math.sin(math.radians(theta))

    def local(x: float, y: float) -> tuple[float, float]:
        return (ax + x * ct - y * st, ay + x * st + y * ct)

    c0, c1 = local(-h, 0.0), local(h, 0.0)
    p0, p1, p2, p3 = local(-h, r), local(h, r), local(h, -r), local(-h, -r)
    for name, (x, y) in (("c0", c0), ("c1", c1), ("p0", p0), ("p1", p1), ("p2", p2), ("p3", p3)):
        out.entities.append(Point(f"{t}.{name}", x, y))
    out.entities += [
        Line(f"{t}.0", f"{t}.p0", f"{t}.p1"),
        Arc(f"{t}.a1", f"{t}.c1", f"{t}.p2", f"{t}.p1", ccw=True),
        Line(f"{t}.1", f"{t}.p2", f"{t}.p3"),
        Arc(f"{t}.a0", f"{t}.c0", f"{t}.p0", f"{t}.p3", ccw=True),
    ]
    out.constraints += [
        ("tangent", (f"{t}.0", f"{t}.a0"), f"{t}.t0"),
        ("tangent", (f"{t}.0", f"{t}.a1"), f"{t}.t1"),
        ("tangent", (f"{t}.1", f"{t}.a1"), f"{t}.t2"),
        ("tangent", (f"{t}.1", f"{t}.a0"), f"{t}.t3"),
        ("equal", (f"{t}.a0", f"{t}.a1"), f"{t}.eq"),
    ]
    out.dims += [
        ("dist", (f"{t}.c0", f"{t}.c1"), cc, f"{t}.cc", None, None),
        ("dia", (f"{t}.a0",), w, f"{t}.w", None, _expr(w_raw)),
    ]
    if theta % 180.0 == 0.0:
        out.constraints.append(("horizontal", (f"{t}.c0", f"{t}.c1"), f"{t}.dir"))
    elif theta % 180.0 == 90.0:
        out.constraints.append(("vertical", (f"{t}.c0", f"{t}.c1"), f"{t}.dir"))
    else:
        # An arbitrary angle is pinned by the centre offsets along X and Y;
        # the centre distance above is then the third, redundant, row - so
        # it is replaced by the two projections.
        out.dims.pop(0)
        out.dims += [
            ("dist", (f"{t}.c0", f"{t}.c1"), abs(cc * ct), f"{t}.dx", "X", None),
            ("dist", (f"{t}.c0", f"{t}.c1"), abs(cc * st), f"{t}.dy", "Y", None),
        ]
    out.anchor = f"{t}.c0"


def _polygon(out: Expansion, spec: dict[str, Any], ax: float, ay: float, length: Parser) -> None:
    n_raw = spec["polygon"]
    try:
        n = int(n_raw)
    except (TypeError, ValueError):
        n = 0
    if n < 3 or n != n_raw:
        raise CommandError(
            f"polygon needs an integer side count >= 3, got {n_raw!r}.", code="pk_needs"
        )
    if "d" not in spec:
        raise CommandError(
            "polygon needs d, the circumscribed (vertex) circle diameter.", code="pk_needs"
        )
    d = length(spec["d"])
    if d <= 0:
        raise CommandError(f"polygon needs a positive d, got {d:g} mm.", code="pk_needs")
    t = out.tag
    R = d / 2.0
    out.entities.append(Point(f"{t}.c", ax, ay))
    out.entities.append(Circle(f"{t}.cc", f"{t}.c", R, construction=True))
    for k in range(n):
        phi = math.radians(-90.0 - 180.0 / n + k * 360.0 / n)
        out.entities.append(Point(f"{t}.p{k}", ax + R * math.cos(phi), ay + R * math.sin(phi)))
    for k in range(n):
        out.entities.append(Line(f"{t}.{k}", f"{t}.p{k}", f"{t}.p{(k + 1) % n}"))
    out.dims.append(("dia", (f"{t}.cc",), d, f"{t}.d", None, _expr(spec["d"])))
    for k in range(n):
        out.constraints.append(("coincident", (f"{t}.p{k}", f"{t}.cc"), f"{t}.on{k}"))
    for k in range(1, n):
        out.constraints.append(("equal", (f"{t}.0", f"{t}.{k}"), f"{t}.eq{k}"))
    out.constraints.append(("horizontal", (f"{t}.0",), f"{t}.h0"))
    out.anchor = f"{t}.c"


def _poly(out: Expansion, spec: dict[str, Any], length: Parser, anchored: bool) -> None:
    raw = spec["poly"]
    if not isinstance(raw, list | tuple) or len(raw) < 2:
        raise CommandError("poly needs at least two [x, y] points.", code="pk_needs")
    closed = bool(spec.get("closed", True))
    if "closed" not in spec:
        out.assumed["closed"] = True
    if closed and len(raw) < 3:
        raise CommandError("a closed poly needs at least three points.", code="pk_needs")
    t = out.tag
    tags = spec.get("tags")
    if tags is not None and (not isinstance(tags, list | tuple) or len(tags) != len(raw)):
        raise CommandError(
            f"poly tags must name every point: {len(raw)} points, {len(tags or [])} tags.",
            code="pk_needs",
        )
    names = [str(x) for x in tags] if tags else [f"{t}.p{k}" for k in range(len(raw))]
    for name, xy in zip(names, raw, strict=True):
        if not isinstance(xy, list | tuple) or len(xy) != 2:
            raise CommandError(f"poly point {name}: needs [x, y], got {xy!r}.", code="pk_needs")
        out.entities.append(Point(name, length(xy[0]), length(xy[1])))
    count = len(raw) if closed else len(raw) - 1
    for k in range(count):
        out.entities.append(Line(f"{t}.{k}", names[k], names[(k + 1) % len(raw)]))
    if anchored:
        # A poly IS its coordinates: anchoring fixes every vertex, so a
        # traced outline reports dof 0 and stays where it was drawn.
        for k, name in enumerate(names):
            out.constraints.append(("fix", (name,), f"{t}.fix{k}"))
    out.anchor = ""
