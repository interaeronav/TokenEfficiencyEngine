"""The pattern model: panels, the edges sewing happens along, and seams.

The one design decision worth stating. An **edge** is not stored - it is
*derived* as the run of boundary vertices between two consecutive turn
points. That is how a pattern maker talks ("the side seam", "the armhole"),
it is how ASTM stores a boundary, and it means an edge cannot disagree with
the outline it belongs to. The cost is that edge ids move when corners move,
so `Panel.edge_ids()` is stable exactly as long as the corner count is, and
`Seam` records the corner count it was made against to say so out loud.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from seamkiln.pattern.geometry import (
    Polyline,
    Vertex,
    VertexKind,
    area,
    bounding_box,
    ensure_counter_clockwise,
    perimeter,
    point_at,
    slice_run,
)


class MarkKind(StrEnum):
    NOTCH_SLIT = "notch_slit"
    NOTCH_V = "notch_v"
    NOTCH_CHECK = "notch_check"
    DRILL = "drill"


class LineKind(StrEnum):
    INTERNAL = "internal"  # annotation; not cut
    CUTOUT = "cutout"  # cut inside the outline
    SEW = "sew"  # stitch line
    GRAIN = "grain"
    MIRROR = "mirror"  # fold line
    DART = "dart"
    PLEAT = "pleat"
    STRIPE = "stripe"
    PLAID = "plaid"


@dataclass(frozen=True, slots=True)
class EdgeRef:
    """A whole edge, or the run between two normalised arc-length points.

    `t0`/`t1` are what make segment-to-segment and N:1 seams expressible:
    three panel edges can each claim a different third of one long edge.
    """

    panel: str
    edge: int
    t0: float = 0.0
    t1: float = 1.0

    def __str__(self) -> str:
        span = "" if (self.t0, self.t1) == (0.0, 1.0) else f"[{self.t0:.3f}:{self.t1:.3f}]"
        return f"{self.panel}#{self.edge}{span}"


@dataclass(slots=True)
class Mark:
    """A notch or a drill hole, positioned along an edge or in free space."""

    kind: MarkKind
    x: float
    y: float
    edge: int | None = None
    t: float | None = None
    depth: float = 5.0  # notch depth, mm
    diameter: float = 3.0  # drill diameter, mm


@dataclass(slots=True)
class InternalLine:
    kind: LineKind
    points: Polyline
    closed: bool = False


def _close_implicitly(outline: Polyline) -> Polyline:
    """Drop a trailing vertex that repeats the first.

    An outline is closed implicitly here - the last vertex joins the first,
    it is not repeated. Curve constructors that end where they began (and
    DXF, which stores closed polylines both ways) hand over an explicit
    ring, and the repeat shows up downstream as a zero-length final edge:
    a seam that measures 0.0 mm and matches anything. Normalised once, on
    the way in, so nothing further down has to know.
    """
    while len(outline) > 2:
        first, last = outline[0], outline[-1]
        if abs(first.x - last.x) < 1e-9 and abs(first.y - last.y) < 1e-9:
            outline = outline[:-1]
        else:
            break
    return outline


@dataclass(slots=True)
class Panel:
    """One pattern piece: a closed CCW outline plus everything drawn on it."""

    id: str
    outline: Polyline
    name: str = ""
    internals: list[InternalLine] = field(default_factory=list)
    marks: list[Mark] = field(default_factory=list)
    seam_allowance_mm: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.outline = ensure_counter_clockwise(_close_implicitly(list(self.outline)))
        if not self.name:
            self.name = self.id

    # -- measurement -------------------------------------------------------

    @property
    def area_mm2(self) -> float:
        return area(self.outline)

    @property
    def perimeter_mm(self) -> float:
        return perimeter(self.outline, closed=True)

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return bounding_box(self.outline)

    # -- edges -------------------------------------------------------------

    def corner_indices(self) -> list[int]:
        return [i for i, v in enumerate(self.outline) if v.kind is VertexKind.TURN]

    def edges(self) -> list[Polyline]:
        """Boundary runs between consecutive corners, closing round the end.

        A boundary with no corners at all (a circle) is one edge - the whole
        outline - rather than an error or an empty list.
        """
        corners = self.corner_indices()
        if len(corners) < 2:
            return [[*self.outline, self.outline[0]]]
        runs: list[Polyline] = []
        for k, start in enumerate(corners):
            end = corners[(k + 1) % len(corners)]
            if end > start:
                runs.append(self.outline[start : end + 1])
            else:  # wraps past the end of the list
                runs.append([*self.outline[start:], *self.outline[: end + 1]])
        return runs

    def edge_ids(self) -> list[str]:
        return [f"{self.id}#{k}" for k in range(len(self.edges()))]

    def edge_run(self, ref: EdgeRef) -> Polyline:
        runs = self.edges()
        if not 0 <= ref.edge < len(runs):
            raise IndexError(
                f"{self.id} has {len(runs)} edges (0..{len(runs) - 1}); {ref} asks for {ref.edge}"
            )
        run = runs[ref.edge]
        if (ref.t0, ref.t1) == (0.0, 1.0):
            return run
        return slice_run(run, ref.t0, ref.t1)

    def edge_length(self, ref: EdgeRef) -> float:
        return perimeter(self.edge_run(ref), closed=False)

    def point_on_edge(self, edge: int, t: float) -> tuple[float, float]:
        return point_at(self.edges()[edge], t)


@dataclass(slots=True)
class Seam:
    """Two runs sewn together.

    `gather` is the ratio of `a` length to `b` length that the seam INTENDS -
    1.0 for a plain seam, 1.15 for a sleeve head eased into an armhole, 2.0
    for a gathered ruffle. It is not a fudge factor for a drafting mistake:
    `true_up` measures against it, so an unintended mismatch stays visible.
    """

    a: EdgeRef
    b: EdgeRef
    gather: float = 1.0
    flip: bool = False
    id: str = ""
    kind: str = "plain"

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"{self.a}~{self.b}"
        if self.gather <= 0.0:
            raise ValueError(f"seam {self.id}: gather must be > 0, got {self.gather}")


@dataclass(slots=True)
class GradeRule:
    """Per-point deltas for one size step, in mm. Applied by `grade()`."""

    name: str
    dx: dict[int, float] = field(default_factory=dict)
    dy: dict[int, float] = field(default_factory=dict)


@dataclass(slots=True)
class Pattern:
    name: str = "untitled"
    panels: list[Panel] = field(default_factory=list)
    seams: list[Seam] = field(default_factory=list)
    grade_rules: dict[str, GradeRule] = field(default_factory=dict)
    units: str = "mm"
    provenance: dict[str, Any] = field(default_factory=dict)

    def panel(self, panel_id: str) -> Panel:
        for candidate in self.panels:
            if candidate.id == panel_id:
                return candidate
        known = ", ".join(p.id for p in self.panels) or "(none)"
        raise KeyError(f"no panel {panel_id!r} in {self.name}; have: {known}")

    @property
    def total_area_mm2(self) -> float:
        return sum(p.area_mm2 for p in self.panels)

    def summary(self) -> dict[str, Any]:
        """The compact state a token-efficient caller actually wants.

        Never the vertex list: TEE's first hard rule. Detail is opt-in.
        """
        return {
            "name": self.name,
            "units": self.units,
            "panels": len(self.panels),
            "seams": len(self.seams),
            "area_mm2": round(self.total_area_mm2, 2),
            "pieces": [
                {
                    "id": p.id,
                    "edges": len(p.edges()),
                    "marks": len(p.marks),
                    "internals": len(p.internals),
                    "area_mm2": round(p.area_mm2, 2),
                }
                for p in self.panels
            ],
        }


@dataclass(frozen=True, slots=True)
class SeamCheck:
    seam_id: str
    a_mm: float
    b_mm: float
    expected_b_mm: float
    mismatch_mm: float

    @property
    def ok(self) -> bool:
        return abs(self.mismatch_mm) <= 1.0  # 1 mm: below a pattern-maker's care


def true_up(pattern: Pattern, *, tolerance_mm: float = 1.0) -> list[SeamCheck]:
    """Measure every seam. Reports millimetres, never a boolean.

    "The seams do not match" is not actionable; "back#2 is 7.3 mm longer than
    front#2 expects" is. Rule 6 of the project dogma, applied to drafting.
    """
    checks: list[SeamCheck] = []
    for seam in pattern.seams:
        a_len = pattern.panel(seam.a.panel).edge_length(seam.a)
        b_len = pattern.panel(seam.b.panel).edge_length(seam.b)
        expected = a_len / seam.gather
        checks.append(
            SeamCheck(
                seam_id=seam.id,
                a_mm=round(a_len, 3),
                b_mm=round(b_len, 3),
                expected_b_mm=round(expected, 3),
                mismatch_mm=round(b_len - expected, 3),
            )
        )
    return [c for c in checks if abs(c.mismatch_mm) > tolerance_mm] or checks


def mirror(panel: Panel, *, axis: str = "y", at: float | None = None) -> Panel:
    """Reflect a panel. Winding is restored, so the copy is still CCW."""
    minx, miny, _, _ = panel.bbox
    pivot = at if at is not None else (minx if axis == "y" else miny)

    def flip(x: float, y: float) -> tuple[float, float]:
        return (2 * pivot - x, y) if axis == "y" else (x, 2 * pivot - y)

    return Panel(
        id=f"{panel.id}_mirror",
        name=f"{panel.name} (mirrored)",
        outline=[Vertex(*flip(v.x, v.y), v.kind) for v in panel.outline],
        internals=[
            InternalLine(
                line.kind,
                [Vertex(*flip(v.x, v.y), v.kind) for v in line.points],
                line.closed,
            )
            for line in panel.internals
        ],
        marks=[
            Mark(m.kind, *flip(m.x, m.y), edge=None, t=None, depth=m.depth, diameter=m.diameter)
            for m in panel.marks
        ],
        seam_allowance_mm=panel.seam_allowance_mm,
        meta=dict(panel.meta),
    )


def unfold(panel: Panel, *, axis: str = "y", at: float | None = None) -> Panel:
    """A half-panel drawn against a fold, opened into the whole piece.

    Deliberately does NOT build on `mirror`. Reflection reverses winding and
    `mirror` restores it - right for a mirrored piece, wrong here: walking
    the original forward and then a re-wound copy forward traces a
    figure-eight whose halves cancel, and the shoelace area of a figure-eight
    is exactly 0.0. The reflected half must be walked BACKWARDS so the
    perimeter keeps going the same way round.
    """
    minx, miny, _, _ = panel.bbox
    pivot = at if at is not None else (minx if axis == "y" else miny)

    def flip(x: float, y: float) -> tuple[float, float]:
        return (2 * pivot - x, y) if axis == "y" else (x, 2 * pivot - y)

    def coincident(a: Vertex, b: Vertex) -> bool:
        return abs(a.x - b.x) < 1e-9 and abs(a.y - b.y) < 1e-9

    reflected = [Vertex(*flip(v.x, v.y), v.kind) for v in panel.outline]
    deduped: Polyline = []
    for vertex in [*panel.outline, *reversed(reflected)]:
        if deduped and coincident(deduped[-1], vertex):
            continue
        deduped.append(vertex)

    return Panel(
        id=f"{panel.id}_unfolded",
        name=f"{panel.name} (unfolded)",
        outline=deduped,  # Panel.__post_init__ drops the wrap-around duplicate
        internals=[
            *panel.internals,
            *[
                InternalLine(
                    line.kind,
                    [Vertex(*flip(v.x, v.y), v.kind) for v in line.points],
                    line.closed,
                )
                for line in panel.internals
            ],
        ],
        marks=[
            *panel.marks,
            *[
                Mark(m.kind, *flip(m.x, m.y), depth=m.depth, diameter=m.diameter)
                for m in panel.marks
            ],
        ],
        seam_allowance_mm=panel.seam_allowance_mm,
        meta={**panel.meta, "unfolded_about": axis},
    )


def grade(pattern: Pattern, rule: GradeRule, steps: int = 1) -> Pattern:
    """Apply a grade rule `steps` times. Points not named in the rule stay put."""
    graded: list[Panel] = []
    for panel in pattern.panels:
        moved = [
            Vertex(
                v.x + rule.dx.get(i, 0.0) * steps,
                v.y + rule.dy.get(i, 0.0) * steps,
                v.kind,
            )
            for i, v in enumerate(panel.outline)
        ]
        graded.append(
            Panel(
                id=panel.id,
                name=panel.name,
                outline=moved,
                internals=list(panel.internals),
                marks=list(panel.marks),
                seam_allowance_mm=panel.seam_allowance_mm,
                meta={**panel.meta, "grade": f"{rule.name}+{steps}"},
            )
        )
    return Pattern(
        name=f"{pattern.name} [{rule.name}+{steps}]",
        panels=graded,
        seams=list(pattern.seams),
        grade_rules=dict(pattern.grade_rules),
        units=pattern.units,
        provenance=dict(pattern.provenance),
    )
