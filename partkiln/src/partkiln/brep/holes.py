"""What counts as a HOLE in a solid - ONE answer, for the drawing and the check.

`pk_drawing`'s hole table and `pk_check`'s `holes` rule must never give two
different answers about the same part: a sheet tabling five holes beside a
check that passed a spec of four is indefensible to whoever is holding both.
They were two implementations, and they did disagree. Measured 2026-09-04, a
40 x 20 pocket with r5 corner radii and NO HOLES AT ALL passed
`holes: [{dia: 10, count: 4}]` and failed `count: 0` with "found 4", because
`checks/spec.py` was still counting CONCAVE CYLINDRICAL FACES while the table
had already learned - twice, from two parts - that a concave face is not a
hole. This module is the one predicate both of them call.

A cylindrical face becomes a hole in three steps, and a part paid for each:

1. **The material must lie OUTSIDE it** (`shapes.is_concave_cylinder`). A
   corner fillet is the same surface with the metal on the other side; the W1
   bracket's four r5 fillets tabled as `4x d10` beside its four real M6 holes.
2. **Coaxial equal-radius faces are ONE wall** (`merge_coaxial`) unless there
   is METAL in the gap between them (`material_between`). A bore split by a
   seam or a mirror join is one hole; two blind holes sunk from opposite faces
   of a thick plate are two, and their walls arrive looking the same.
3. **What is left is a hole only if its wall closes** (its summed sweep
   reaches `FULL_TURN_MIN_DEG`) and only if it is not one END of a slot
   (`slot_pairs`). A pocket's corner radius is genuinely concave and sweeps at
   most half a turn; a slot's two ends are a slot, and a drafter dimensions a
   slot as a slot rather than as two holes 32 mm apart.

Everything here is view-independent but for the optional `direction` filter,
which a drawing passes to keep only the faces it sees down their own axis.
This module owns the GEOMETRY of the question; names, table cells and the
`slots` spec rule are the callers' business.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from partkiln.brep import require_ocp

require_ocp()

from OCP.BRepAdaptor import BRepAdaptor_Surface  # noqa: E402
from OCP.BRepClass3d import BRepClass3d_SolidClassifier  # noqa: E402
from OCP.gp import gp_Pnt  # noqa: E402
from OCP.TopAbs import TopAbs_IN  # noqa: E402
from OCP.TopoDS import TopoDS_Face, TopoDS_Shape  # noqa: E402

from partkiln.brep import query, shapes  # noqa: E402

Vec3 = tuple[float, float, float]

SLOT_TOL_MM = 1e-6

# A drilled hole's wall closes on itself; a corner radius does not. A fillet
# tangent to two planar walls that meet at interior angle t sweeps 180 - t
# degrees, so 180 is the ceiling of a corner radius and the sharpest case of
# all - a slot end - is exactly 180. A closed wall is 360, seam included. The
# threshold sits halfway between: no corner radius can ever reach it, while a
# real hole a later feature has clipped by up to a quarter turn (a keyway, a
# hole breaking into a pocket) still counts. It is compared against the SUM
# over the faces of ONE wall, because a hole can reach the inventory as two
# half-cylinders - a mirror-join does exactly that - and two halves of one
# hole are one hole.
FULL_TURN_MIN_DEG = 270.0

#: What a wall turned out to be. `hole` is a hole and nothing else is: `slot`
#: is one END of a slot (the pair is one feature, and `holes` counts none of
#: them), `partial` is a wall that never closes - a corner radius, a notch, an
#: orphaned slot end - which belongs to a feature this module was not handed.
KINDS = ("hole", "slot", "partial")


@dataclass(frozen=True)
class HoleWall:
    """One cylindrical WALL of the solid: every face of one bore, gathered.

    `indices` are into the face list this was measured from, in merge order,
    so the caller can name them; `point` is on the ANALYTIC axis (never the
    centroid - half a cylinder's centroid sits 2r/pi off its own axis);
    `reach` is the union of the faces' extents along that axis.
    """

    indices: tuple[int, ...]
    axis: Vec3
    point: Vec3
    radius: float
    sweep_deg: float
    reach: tuple[float, float]
    thru: bool
    kind: str
    partner: int | None = None

    @property
    def span(self) -> float:
        """How far the wall reaches along its own axis."""
        return self.reach[1] - self.reach[0]

    @property
    def depth(self) -> str:
        """`THRU`, or the span rounded as a drawing writes it (`_depth_text`)."""
        return _depth_text(self.thru, self.span)


def _depth_text(thru: bool, span: float) -> str:
    """How deep the wall goes: `THRU`, or the span rounded to 3 decimals.

    A string and not a number because it is BOTH the table's depth cell and
    the key that decides whether two cylinders are the two ends of one slot
    ("two ends of one cut go equally deep"), and those two answers must not be
    allowed to drift apart by a rounding.
    """
    return "THRU" if thru else f"{round(span, 3) + 0.0:g}"


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(float(x) * float(y) for x, y in zip(a, b, strict=True))


def _delta(p: Vec3, q: Vec3) -> Vec3:
    return (q[0] - p[0], q[1] - p[1], q[2] - p[2])


def _perp(v: Vec3, axis: Vec3) -> Vec3:
    """`v` with its component along `axis` removed."""
    k = _dot(v, axis)
    return (v[0] - k * axis[0], v[1] - k * axis[1], v[2] - k * axis[2])


def cylinder_axis(face: TopoDS_Face) -> Vec3:
    """The face's cylinder axis direction, read from the analytic surface."""
    d = BRepAdaptor_Surface(face).Cylinder().Axis().Direction()
    return (d.X(), d.Y(), d.Z())


def cylinder_axis_point(face: TopoDS_Face) -> Vec3:
    """A point ON the cylinder's axis, read from the analytic surface.

    NOT the face centroid: a slot end is a HALF cylinder whose surface centroid
    sits 2r/pi off its own axis (2.546 mm for the W1 slot's r4 ends), so a slot
    measured centroid-to-centroid would read 34.907 where the model says 40.
    """
    p = BRepAdaptor_Surface(face).Cylinder().Axis().Location()
    return (p.X(), p.Y(), p.Z())


def face_axis_interval(face: Any, axis: Vec3) -> tuple[float, float]:
    """How far along `axis` this face reaches, as `(from, to)`.

    An interval and not a length, because the faces of one wall have to be
    UNIONED: a through hole drilled as two blind holes that meet arrives as
    two faces spanning half the plate each, and the deeper of the two is not
    the hole's depth - their union is.
    """
    x0, y0, z0, x1, y1, z1 = face.bbox
    centre = (0.5 * (x0 + x1), 0.5 * (y0 + y1), 0.5 * (z0 + z1))
    half = 0.5 * abs(_dot((x1 - x0, y1 - y0, z1 - z0), tuple(abs(c) for c in axis)))
    along = _dot(centre, axis)
    return (along - half, along + half)


def body_span(box: Sequence[float], axis: Vec3) -> float:
    """The solid's own extent along `axis` - what makes a wall THRU."""
    return abs(
        _dot(
            (box[3] - box[0], box[4] - box[1], box[5] - box[2]),
            tuple(abs(c) for c in axis),
        )
    )


def material_between(shape: Any, axis: Vec3, point: Vec3, lo: float, hi: float) -> bool:
    """Is there SOLID between two coaxial faces whose reaches stop at `lo` and
    start at `hi`? The midpoint of the gap, on the axis, classified.

    Coaxial and equal-radius is not enough to say "one hole". A clevis is
    drilled through both ears in one pass and IS one hole, its wall arriving as
    two faces with air between them; two blind holes sunk from opposite faces
    of a thick plate are TWO holes with metal between them, and their walls
    arrive looking exactly the same. Measured 2026-09-04: merging them
    regardless printed `1x d10 THRU` for a 30 mm plate holding 20 mm of solid
    between two 5 mm blind holes - a sheet that sends a drill through a wall.
    So the metal is what decides, and one point answers it.
    """
    mid = 0.5 * (lo + hi)
    along = _dot(point, axis)
    p = gp_Pnt(
        point[0] + (mid - along) * axis[0],
        point[1] + (mid - along) * axis[1],
        point[2] + (mid - along) * axis[2],
    )
    cls = BRepClass3d_SolidClassifier(shape, p, 1e-7)
    return bool(cls.State() == TopAbs_IN)


def merge_coaxial(shape: Any, entries: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """The candidate faces gathered into WALLS: one entry per cylinder, not per face.

    A hole does not always reach the inventory as one face. Measured
    2026-09-04: mirroring a half-round notch onto its own plane joins two
    half-cylinders into one d10 bore that the table printed as `2x d10 THRU`
    - one hole counted twice, the same lie as a fillet counted once. Faces
    that share an axis line and a radius are one wall, so their sweeps add
    (180 + 180 = a closed turn) and they count once.

    Coaxial means parallel axes (1e-6 on the direction cosine) whose axis
    points differ by less than `SLOT_TOL_MM` across the axis - the analytic
    axis, never the centroid, because half a cylinder's centroid sits 2r/pi
    off it.
    """
    walls: list[dict[str, Any]] = []
    for entry in entries:
        for wall in walls:
            if abs(wall["radius"] - entry["radius"]) > SLOT_TOL_MM:
                continue
            if abs(_dot(wall["axis"], entry["axis"])) < 1.0 - SLOT_TOL_MM:
                continue
            offset = _perp(_delta(wall["point"], entry["point"]), wall["axis"])
            if math.sqrt(_dot(offset, offset)) > SLOT_TOL_MM:
                continue
            # Coaxial says nothing about which WAY each face's axis points: a
            # hole cut from both sides gives one axis +Z and one -Z, and their
            # reaches only union in one frame. Read the entry's in the wall's.
            lo, hi = entry["reach"]
            if _dot(wall["axis"], entry["axis"]) < 0.0:
                lo, hi = -hi, -lo
            wlo, whi = wall["reach"]
            gap = (whi, lo) if lo > whi else (hi, wlo) if wlo > hi else None
            if (
                gap is not None
                and gap[1] - gap[0] > SLOT_TOL_MM
                and material_between(shape, wall["axis"], wall["point"], *gap)
            ):
                continue  # two holes with metal between them, not one wall
            wall["indices"].append(entry["index"])
            wall["sweep_deg"] += entry["sweep_deg"]
            wall["reach"] = (min(wall["reach"][0], lo), max(wall["reach"][1], hi))
            break
        else:
            walls.append(
                {
                    "indices": [entry["index"]],
                    "axis": entry["axis"],
                    "point": entry["point"],
                    "radius": entry["radius"],
                    "sweep_deg": entry["sweep_deg"],
                    "reach": entry["reach"],
                }
            )
    return walls


def _tangent_walls(
    edges: Sequence[Any], faces: Sequence[Any], wanted: Sequence[int]
) -> dict[int, set[int]]:
    """`{face index -> the planar faces joined to it by a TANGENT edge}`.

    Read straight off the topology. `brep/query` calls an edge tangent when the
    two faces' outward normals agree to 1e-6 at its midpoint, and where a plane
    meets a cylinder along a ruling that IS tangency - so this is the drafting
    definition of a slot wall, not a geometric guess at one.

    One pass over every edge, not one pass per face: an edges-of-face lookup
    scans the whole edge list, and F5's 100-hole plate would pay that a
    hundred times.
    """
    walls: dict[int, set[int]] = {i: set() for i in wanted}
    for edge in edges:
        if edge.convexity != "tangent" or len(edge.adjacent_face_indices) != 2:
            continue
        a, b = edge.adjacent_face_indices
        if a in walls and faces[b].surface_type == "plane":
            walls[a].add(b)
        if b in walls and faces[a].surface_type == "plane":
            walls[b].add(a)
    return walls


def slot_pairs(
    edges: Sequence[Any], faces: Sequence[Any], entries: Sequence[dict[str, Any]]
) -> dict[int, int]:
    """`{position in entries -> position of its partner}` for the ends of a slot.

    `entries` are WALLS as `merge_coaxial` returns them - one per cylinder,
    however many faces it reached the inventory as - so the tangent walls are
    read for every face of each.

    A slot is two equal-radius concave cylinders with parallel axes joined by
    planar walls TANGENT to both. **The tangent wall is the whole test.**
    Sharing a radius proves nothing - a plate's four M6 clearance holes share
    theirs, and merging them would invent a 40 mm slot where the model has two
    holes and air between them - so the wall connection decides, and it is read
    from the topology (`_tangent_walls`) rather than from a distance.

    Two walls are required, not one: a half-round notch on an edge has one, and
    one wall does not close a slot. The pairing must also be unambiguous - a
    cylinder that walls up to two others is a chain, not a slot, and its ends
    stay separate rather than being given a length no drafter asked for.

    The three geometric tolerances, all on numbers OCCT reports analytically:
    equal radii and coincident axes to `SLOT_TOL_MM` (1e-6 mm), and parallel
    axes to 1e-6 on the direction cosine.
    """
    by_face = _tangent_walls(edges, faces, [i for e in entries for i in e["indices"]])
    walls = {i: set().union(*(by_face[k] for k in e["indices"])) for i, e in enumerate(entries)}
    # A cylinder with no tangent wall cannot be a slot end, so a plate of plain
    # drilled holes never enters the pairwise scan at all.
    walled = [i for i, w in walls.items() if w]
    found: list[tuple[int, int]] = []
    for i, a in enumerate(walled):
        for b in walled[i + 1 :]:
            ea, eb = entries[a], entries[b]
            if abs(ea["radius"] - eb["radius"]) > SLOT_TOL_MM:
                continue
            if abs(_dot(ea["axis"], eb["axis"])) < 1.0 - SLOT_TOL_MM:
                continue
            if ea["depth"] != eb["depth"]:
                continue  # two ends of one cut go equally deep
            offset = _perp(_delta(ea["point"], eb["point"]), ea["axis"])
            if math.sqrt(_dot(offset, offset)) <= SLOT_TOL_MM:
                continue  # one wall reached twice; `merge_coaxial` owns that case
            if len(walls[a] & walls[b]) < 2:
                continue
            found.append((a, b))
    degree: dict[int, int] = {}
    for a, b in found:
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1
    partner: dict[int, int] = {}
    for a, b in found:
        if degree[a] == 1 and degree[b] == 1:
            partner[a], partner[b] = b, a
    return partner


def hole_walls(
    shape: TopoDS_Shape,
    faces: Sequence[Any] | None = None,
    edges: Sequence[Any] | None = None,
    direction: Vec3 | None = None,
) -> list[HoleWall]:
    """Every concave cylindrical wall of `shape`, merged and classified.

    The list holds the walls a hole table would consider, each carrying the
    `kind` that decides what it IS - `hole`, one end of a `slot`, or a
    `partial` wall that closes nothing. `holes` counts the first and only the
    first; `slot_ends` reads the second back out as pairs.

    `faces` / `edges` are `brep.query` records to reuse (a drawing already has
    the part's inventory); the edges are only read when there are two walls
    that could pair, so a plate of one hole never pays for the scan. Pass
    `direction` to keep only the walls whose axis is that line of sight - what
    a view can see down - and to measure THRU against the same line.

    Measured 2026-09-04 on F5, the 100-hole plate and the worst case there is:
    23 ms for the whole answer, of which 15 ms is the edge scan the slot
    pairing needs. `hole_table` pays none of that (the inventory carries the
    edges); `check_spec`'s `holes` rule went 5 -> 28 ms, which is what a right
    answer costs on that fixture.
    """
    finfos = list(faces) if faces is not None else query.faces(shape)
    found: list[dict[str, Any]] = []
    for i, face in enumerate(finfos):
        if face.surface_type != "cylinder" or face.radius is None:
            continue
        axis = cylinder_axis(face.shape)
        if direction is not None and abs(_dot(axis, direction)) < 1.0 - 1e-6:
            continue
        if not shapes.is_concave_cylinder(face.shape):
            continue  # a fillet or a boss: same surface, material on the other side
        found.append(
            {
                "index": i,
                "axis": axis,
                # The AXIS, not the centroid: identical for a drilled hole (a
                # full cylinder) and the only right answer for a partial one.
                "point": cylinder_axis_point(face.shape),
                "radius": float(face.radius),
                "sweep_deg": shapes.cylinder_sweep_deg(face.shape),
                "reach": face_axis_interval(face, axis),
            }
        )
    entries = merge_coaxial(shape, found)
    if not entries:
        return []
    box = shapes.bbox(shape)
    along_view = None if direction is None else body_span(box, direction)
    for entry in entries:
        # A view measures every wall against the one line it looks down (and
        # only kept walls parallel to it, so that IS each wall's own axis).
        # With no view, each wall is measured along its own axis instead.
        reference = along_view if along_view is not None else body_span(box, entry["axis"])
        span = entry["reach"][1] - entry["reach"][0]
        entry["thru"] = abs(span - reference) < 1e-6
        entry["depth"] = _depth_text(entry["thru"], span)
    partner: dict[int, int] = {}
    if len(entries) > 1:
        einfos = list(edges) if edges is not None else query.edges(shape, finfos)
        partner = slot_pairs(einfos, finfos, entries)
    walls: list[HoleWall] = []
    for i, entry in enumerate(entries):
        mate = partner.get(i)
        kind = (
            "slot"
            if mate is not None
            else ("hole" if entry["sweep_deg"] >= FULL_TURN_MIN_DEG else "partial")
        )
        walls.append(
            HoleWall(
                indices=tuple(entry["indices"]),
                axis=entry["axis"],
                point=entry["point"],
                radius=entry["radius"],
                sweep_deg=entry["sweep_deg"],
                reach=entry["reach"],
                thru=entry["thru"],
                kind=kind,
                partner=mate,
            )
        )
    return walls


def slot_ends(walls: Sequence[HoleWall]) -> list[tuple[HoleWall, HoleWall]]:
    """Every slot ONCE, as its two end walls in list order."""
    return [
        (wall, walls[wall.partner])
        for i, wall in enumerate(walls)
        if wall.partner is not None and i < wall.partner
    ]


def slot_offset(a: HoleWall, b: HoleWall) -> Vec3:
    """The vector from `a`'s axis to `b`'s, ACROSS the axis they share.

    The slot's long direction and its length in one number, which is what both
    the size and the view angle are read from - so a drawing never measures
    the same slot a second way.
    """
    return _perp(_delta(a.point, b.point), a.axis)


def slot_size(a: HoleWall, b: HoleWall) -> tuple[float, float]:
    """`(width, length)` of the slot those two ends cut, in mm.

    The overall length a shop cuts to: the centre distance between the two
    ANALYTIC axes plus one diameter. Measured across the axis, so a slot in a
    blind pocket reads the same as one cut through.
    """
    delta = slot_offset(a, b)
    radius = 0.5 * (a.radius + b.radius)
    return (2.0 * radius, math.sqrt(_dot(delta, delta)) + 2.0 * radius)


__all__ = [
    "FULL_TURN_MIN_DEG",
    "KINDS",
    "SLOT_TOL_MM",
    "HoleWall",
    "body_span",
    "cylinder_axis",
    "cylinder_axis_point",
    "face_axis_interval",
    "hole_walls",
    "material_between",
    "merge_coaxial",
    "slot_ends",
    "slot_offset",
    "slot_pairs",
    "slot_size",
]
