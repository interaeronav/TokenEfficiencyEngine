"""The fold: the folded solid DERIVED from the flat, and the sheet entity (P5b).

Flat-first (A66 decision 4): `flat.py` owns the model, this module owns the
consequence. Nothing here is a second source of truth - the folded solid is
built by taking the flat apart along its own bend lines and putting it back
with a cylindrical bend where each strip was:

    flange piece   the flat plate clipped to that flange's flat span, moved
                   rigidly into place
    bend piece     an annular sector, inside radius R, thickness T, swept
                   through A about the bend axis - the strip of width BA is
                   REPLACED, never bent
    holes          one cylinder per hole, cut through BOTH bodies after the
                   same rigid motion, so a hole is in the same place on the
                   flat and on the part

so `flat` and `folded` are two views of one parametric object and a change to
either is a change to the command that made it.

**The volume difference is real and stays visible.** The bend zone of the
folded part is an annular sector,

    (pi*A/360) * ((R+T)^2 - R^2) * L

which contains NO K at all - it is geometry, while K is a modelling choice
about where the neutral fibre sits. F7 (A 90, R 2, T 2, L 40) is
9.4248 * 40 = 376.991 mm3 at K 0.4, 0.44 and 0.5 alike, and a test asserts
that equality. The same zone on the flat is a strip of BA*T*L, and BA does
contain K. Their difference is the K-factor's whole volumetric effect (zero
at K = 0.5, where the neutral fibre is the volumetric middle of the sheet);
W3 reports folded - flat = +18.850 mm3 on a 9 652 mm3 part. Reporting the
difference with its note beats hiding a 0.2 % mass error.

**The fold arithmetic**, per bend, in the (u, z) plane of that bend - u the
outboard distance from the bend line on the flat, z through the thickness:

    z_in   = t (dir up) | 0 (dir down)        the INSIDE surface of the bend
    z_axis = z_in + s*R,  s = +1 up, -1 down  the bend axis
    phi    = s*A                              the turn, CCW in (u, z)

and the outboard flange's rigid motion is "slide back by BA, then rotate by
phi about the axis": the slide is what makes arc length come out right, since
the neutral fibre of radius R + K*T sweeps exactly BA through the sector. That
is the ONE place K enters the geometry, and it is why an L of outside legs a
and b lands at a + b - 2*OSSB + BA on the flat.

`dir` is read in each FLANGE's own frame, not the world's - "up" means the
flange folds toward that flange's own top face. Measured on a 30/80/30 chain
of 90 deg bends, t 2 r 2: up then up gives a U (both legs the same side,
folded bbox [30, 50, 80]), up then down gives a Z ([58, 50, 80]).

Bends must be parallel to the Y axis with the flange outboard toward +X - the
chain `Flat.from_flanges` (and so `create sheet`) lays out. A hand-built Flat
with a slanted bend line is refused by name rather than folded wrongly.

Measured (this Mac, OCP 7.9.3): W3 folds in 15 ms; its folded solid is one
valid solid of 10 faces / 24 edges whose exact `BRepGProp` volume equals the
arithmetic above to the last printed digit, and whose bounding box equals
`folded_extents` exactly - which is what makes the analytic answer safe to
report while the kernel is still warming.

OCP is imported inside functions only: `import partkiln.sheetmetal.fold`
costs nothing, and `Sheet.summary()` - including `folded_bbox_mm` - is pure
arithmetic that answers with no B-rep kernel installed at all.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

from partkiln.document import CommandError
from partkiln.sheetmetal.flat import DEFAULT_K, Bend, Flat, Hole, r3

_MARGIN_MM = 1.0
"""How far a clipping slab / a hole tool overshoots the sheet (mm)."""


# --------------------------------------------------------------------------- 2D placement


@dataclass(frozen=True)
class Place:
    """A rigid motion of the (x, z) plane: `origin + x*ex + z*ez`.

    Only two axes move. Every bend line is parallel to Y and every bend axis
    with it, so y is carried through untouched - which is also why one 3x4
    `gp_Trsf` per flange is enough for OCCT.
    """

    origin: tuple[float, float] = (0.0, 0.0)
    ex: tuple[float, float] = (1.0, 0.0)
    ez: tuple[float, float] = (0.0, 1.0)

    def __call__(self, x: float, z: float) -> tuple[float, float]:
        return (
            self.origin[0] + x * self.ex[0] + z * self.ez[0],
            self.origin[1] + x * self.ex[1] + z * self.ez[1],
        )

    def then(self, inner: Place) -> Place:
        """`self` after `inner`: the composition that applies `inner` first."""
        return Place(
            origin=self(*inner.origin),
            ex=(
                inner.ex[0] * self.ex[0] + inner.ex[1] * self.ez[0],
                inner.ex[0] * self.ex[1] + inner.ex[1] * self.ez[1],
            ),
            ez=(
                inner.ez[0] * self.ex[0] + inner.ez[1] * self.ez[0],
                inner.ez[0] * self.ex[1] + inner.ez[1] * self.ez[1],
            ),
        )

    def is_identity(self) -> bool:
        return (
            abs(self.origin[0]) < 1e-12
            and abs(self.origin[1]) < 1e-12
            and abs(self.ex[0] - 1.0) < 1e-12
            and abs(self.ex[1]) < 1e-12
            and abs(self.ez[0]) < 1e-12
            and abs(self.ez[1] - 1.0) < 1e-12
        )


def bend_axis_z(bend: Bend) -> float:
    """The bend axis height: `t + R` folding up, `-R` folding down."""
    s = 1.0 if bend.direction == "up" else -1.0
    return inside_z(bend) + s * bend.r_inner


def inside_z(bend: Bend) -> float:
    """The INSIDE surface of the bend: the top face folding up, the bottom down."""
    return bend.t if bend.direction == "up" else 0.0


def fold_place(bend: Bend, line_u: float) -> Place:
    """The rigid motion the flange OUTBOARD of `bend` takes, in the flat's frame.

    `line_u` is the bend line's own x on the flat. Slide back by BA (arc
    length is what the flat spends on the bend), then turn by phi = s*A about
    the axis - see the module docstring for why that order is the whole
    K-factor.
    """
    s = 1.0 if bend.direction == "up" else -1.0
    phi = math.radians(s * bend.angle_deg)
    cos, sin = math.cos(phi), math.sin(phi)
    z_axis = bend_axis_z(bend)
    # The pre-translation puts the flange's near edge on the axis' own u.
    du, dz = -bend.ba - line_u, -z_axis
    return Place(
        origin=(line_u + du * cos - dz * sin, z_axis + du * sin + dz * cos),
        ex=(cos, sin),
        ez=(-sin, cos),
    )


# --------------------------------------------------------------------------- the chain


@dataclass(frozen=True)
class Segment:
    """One piece of the folded body: a flange span or a bend, and where it goes."""

    kind: str  # "flange" | "bend"
    name: str
    place: Place
    u0: float = 0.0  # flange only: its flat span
    u1: float = 0.0
    bend: Bend | None = None
    line_u: float = 0.0


def chain(flat: Flat) -> list[Segment]:
    """Walk the flat's flange/bend chain, accumulating each piece's placement.

    Refuses a layout this fold cannot honour - a slanted or reversed bend
    line, or bends with no flange rows to sit between - naming `create sheet`
    as the fix rather than folding something that is nearly right.
    """
    if not flat.bends:
        u0, _, u1, _ = flat.bbox()
        return [Segment("flange", flat.flanges[0].name if flat.flanges else "f1", Place(), u0, u1)]
    if len(flat.flanges) != len(flat.bends) + 1:
        raise CommandError(
            f"this flat has {len(flat.bends)} bend(s) but {len(flat.flanges)} flange row(s); the "
            "fold needs one more flange than bends. Build it with create sheet (or "
            "Flat.from_flanges), which lays the chain out.",
            code="pk_needs",
        )
    for bend in flat.bends:
        tx, ty = bend.tangent
        if abs(tx) > 1e-9 or ty > -1 + 1e-9:
            raise CommandError(
                f"bend {bend.name}: the fold only folds a chain whose bend lines run across the "
                f"sheet (tangent (0, -1), flange toward +x), and this one runs ({tx:g}, {ty:g}). "
                "Build the sheet with create sheet, which lays that chain out.",
                code="pk_needs",
            )
    segments: list[Segment] = []
    place = Place()
    for index, row in enumerate(flat.flanges):
        segments.append(Segment("flange", row.name, place, row.flat_start, row.flat_end))
        if index < len(flat.bends):
            bend = flat.bends[index]
            line_u = row.flat_end
            segments.append(Segment("bend", bend.name, place, bend=bend, line_u=line_u))
            place = place.then(fold_place(bend, line_u))
    return segments


def place_of(flat: Flat, hole: Hole, segments: list[Segment]) -> Place:
    """Where a hole's flange went. A hole in a bend zone cannot exist (`add_hole`
    refuses it), so a hole outside every flange span is a built-by-hand Flat."""
    for segment in segments:
        if segment.kind != "flange":
            continue
        if segment.u0 - 1e-9 <= hole.centre[0] <= segment.u1 + 1e-9:
            return segment.place
    spans = ", ".join(
        f"{s.name} {r3(s.u0):g}..{r3(s.u1):g}" for s in segments if s.kind == "flange"
    )
    raise CommandError(
        f"hole {hole.name} at flat x {hole.centre[0]:g} is on no flange (spans: {spans}); a hole "
        "must sit on a flange, clear of every bend zone.",
        code="pk_ref_unknown",
    )


# --------------------------------------------------------------------------- extents (no OCP)


def _arc_points(
    centre: tuple[float, float], radii: tuple[float, ...], a0: float, a1: float
) -> list[tuple[float, float]]:
    """Every point an arc's bounding box can touch: the two ends, plus each
    quarter-turn direction the sweep actually crosses (that is where a circle
    reaches its extreme x or z), at both radii."""
    lo, hi = (a0, a1) if a0 <= a1 else (a1, a0)
    angles = [a0, a1]
    k = math.ceil(lo / (math.pi / 2.0))
    while k * (math.pi / 2.0) <= hi + 1e-12:
        angles.append(k * (math.pi / 2.0))
        k += 1
    return [
        (centre[0] + r * math.cos(a), centre[1] + r * math.sin(a)) for a in angles for r in radii
    ]


def folded_points(flat: Flat) -> list[tuple[float, float]]:
    """Every (x, z) the folded body's bounding box can touch. Pure arithmetic:
    the analytic answer is the one `Sheet.summary()` reports whether or not a
    B-rep kernel is installed, and a `-m brep` test checks it against OCCT."""
    points: list[tuple[float, float]] = []
    for segment in chain(flat):
        bend = segment.bend
        if segment.kind == "flange" or bend is None:
            points.extend(
                segment.place(u, z) for u in (segment.u0, segment.u1) for z in (0.0, flat.t)
            )
            continue
        s = 1.0 if bend.direction == "up" else -1.0
        centre = segment.place(segment.line_u, bend_axis_z(bend))
        start = segment.place(
            segment.line_u, bend_axis_z(bend) - s * bend.r_inner
        )  # the theta = 0 point at radius R
        a0 = math.atan2(start[1] - centre[1], start[0] - centre[0])
        a1 = a0 + s * math.radians(bend.angle_deg)
        points.extend(_arc_points(centre, (bend.r_inner, bend.r_inner + bend.t), a0, a1))
    return points


def folded_extents(flat: Flat) -> tuple[float, float, float]:
    """The folded bounding box as (dx, dy, dz) mm. W3 -> [60, 50, 40]."""
    points = folded_points(flat)
    xs = [p[0] for p in points]
    zs = [p[1] for p in points]
    _, y0, _, y1 = flat.bbox()
    return (max(xs) - min(xs), y1 - y0, max(zs) - min(zs))


# --------------------------------------------------------------------------- the solids


def _trsf(place: Place) -> Any:
    """One `gp_Trsf` from a `Place`; y maps to y. `SetValues` refuses a matrix
    that is not a rotation, so a sign error here is caught by OCCT, not by eye."""
    from OCP.gp import gp_Trsf

    trsf = gp_Trsf()
    trsf.SetValues(
        place.ex[0],
        0.0,
        place.ez[0],
        place.origin[0],
        0.0,
        1.0,
        0.0,
        0.0,
        place.ex[1],
        0.0,
        place.ez[1],
        place.origin[1],
    )
    return trsf


def _moved(shape: Any, place: Place) -> Any:
    if place.is_identity():
        return shape
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform

    return BRepBuilderAPI_Transform(shape, _trsf(place), True).Shape()


def plate(flat: Flat) -> Any:
    """The flat outline extruded by t, holes NOT cut - the stock every piece is cut from."""
    from partkiln.brep import shapes

    face = shapes.make_face_from_points([(x, y, 0.0) for x, y in flat.outline])
    return shapes.prism(face, (0.0, 0.0, flat.t)).shape


def _hole_tools(flat: Flat, segments: list[Segment] | None) -> list[Any]:
    """One through cylinder per hole, in flat coordinates or moved with its flange."""
    from partkiln.brep import shapes

    tools: list[Any] = []
    for hole in flat.holes:
        tool = shapes.cylinder(
            hole.dia / 2.0,
            flat.t + 2.0 * _MARGIN_MM,
            at=(hole.centre[0], hole.centre[1], -_MARGIN_MM),
            direction=(0.0, 0.0, 1.0),
        )
        tools.append(tool if segments is None else _moved(tool, place_of(flat, hole, segments)))
    return tools


def _cut_holes(body: Any, flat: Flat, tools: list[Any], what: str) -> Any:
    from partkiln.brep import shapes

    if not tools:
        return body
    result = shapes.cut(body, tools)
    if not result.is_done:
        raise CommandError(
            f"cutting {len(tools)} hole(s) out of the {what} body failed. Check that every hole "
            "is inside the outline and clear of the bend zones.",
            code="pk_op_failed",
        )
    if result.no_effect:
        raise CommandError(
            f"the {len(tools)} hole(s) removed nothing from the {what} body (Law 11: a boolean "
            "that changes no topology is a failed boolean). Check the hole positions.",
            code="pk_no_effect",
        )
    return result.shape


def flat_solid(flat: Flat) -> Any:
    """The flat pattern as a solid: the outline extruded by t, holes through."""
    return _cut_holes(plate(flat), flat, _hole_tools(flat, None), "flat")


def _slab(flat: Flat, u0: float, u1: float, pad_lo: float, pad_hi: float) -> Any:
    """An axis-aligned box that clips the plate to one flange's flat span.

    The chain's two OUTER ends are padded past the outline: a boolean whose
    tool face lands exactly on the argument's own face is the fragile case,
    and the ends have no bend to meet there anyway. The INNER ends are not
    padded - they are the tangent planes the sectors are built against, and
    the two must coincide to the last bit for the fuse to weld them.
    """
    from partkiln.brep import shapes

    _, y0, _, y1 = flat.bbox()
    m = _MARGIN_MM
    return shapes.box(
        (u1 + pad_hi) - (u0 - pad_lo),
        (y1 - y0) + 2.0 * m,
        flat.t + 2.0 * m,
        at=(u0 - pad_lo, y0 - m, -m),
    )


def _sector(flat: Flat, segment: Segment) -> Any:
    """The bend zone as an annular sector: a rectangle from R to R+T across the
    bend line, revolved through A about the bend axis.

    Its volume is `(pi*A/360)*((R+T)^2 - R^2)*L` and has no K in it (see the
    module docstring); the flat's strip of BA*T*L is what it replaces.
    """
    from partkiln.brep import shapes

    bend = segment.bend
    if bend is None:
        raise CommandError(
            f"segment {segment.name!r} is a bend with no bend on it - build the sheet with "
            "create sheet (or Flat.from_flanges), which lays the chain out.",
            code="pk_internal",
        )
    s = 1.0 if bend.direction == "up" else -1.0
    (px, py), _ = bend.line
    z_in = inside_z(bend)
    z_axis = bend_axis_z(bend)
    tx, ty = bend.tangent
    length = bend.length
    inner = (px, py, z_in)
    outer = (px, py, z_in - s * bend.t)
    face = shapes.make_face_from_points(
        [
            inner,
            outer,
            (px + tx * length, py + ty * length, outer[2]),
            (px + tx * length, py + ty * length, inner[2]),
        ]
    )
    revolution = shapes.revolve(face, (px, py, z_axis), (s * tx, s * ty, 0.0), bend.angle_deg)
    if not revolution.is_done:
        raise CommandError(
            f"bend {bend.name}: the {bend.angle_deg:g} deg sector of R{bend.r_inner:g} x "
            f"T{bend.t:g} over {r3(length):g} mm would not build. Check r and t.",
            code="pk_op_failed",
        )
    return _moved(revolution.shape, segment.place)


def folded_solid(flat: Flat) -> Any:
    """The folded part: every flange moved into place, every bend zone replaced
    by its annular sector, fused, unified, and the holes cut through."""
    from partkiln.brep import shapes

    segments = chain(flat)
    stock = plate(flat)
    last = len(segments) - 1
    pieces: list[Any] = []
    for index, segment in enumerate(segments):
        if segment.kind == "flange":
            pad_lo = _MARGIN_MM if index == 0 else 0.0
            pad_hi = _MARGIN_MM if index == last else 0.0
            piece = shapes.common(stock, _slab(flat, segment.u0, segment.u1, pad_lo, pad_hi))
            if piece.empty:
                raise CommandError(
                    f"flange {segment.name} clips to nothing between x {r3(segment.u0):g} and "
                    f"{r3(segment.u1):g}. Lengthen it, or reduce the bend radius.",
                    code="pk_op_failed",
                )
            pieces.append(_moved(piece.shape, segment.place))
        else:
            pieces.append(_sector(flat, segment))
    if len(pieces) == 1:
        body = pieces[0]
    else:
        welded = shapes.fuse(pieces)
        if not welded.is_done or welded.empty:
            raise CommandError(
                f"the {len(pieces)} folded pieces did not fuse into one body. Check that every "
                "flange is longer than its outside setbacks.",
                code="pk_op_failed",
            )
        body, _ = shapes.unify(welded.shape)
    return _cut_holes(body, flat, _hole_tools(flat, segments), "folded")


# --------------------------------------------------------------------------- the entity


@dataclass
class Sheet:
    """A sheet-metal part: one flat, its bends, and the folded body they imply.

    The entity `create sheet` puts in `document.sheets`. `summary()` is the
    D7 row - scalars only, no geometry (hard rule 1) - and every number in it
    is arithmetic from `flat.py`, so it answers with no OCP installed;
    `solid()` is the opt-in B-rep and the only part that needs the kernel.
    """

    name: str
    flat: Flat
    material: str | None = None
    k: float = DEFAULT_K
    notes: list[str] = field(default_factory=list)

    # -- numbers -------------------------------------------------------------

    def folded_bbox(self) -> tuple[float, float, float]:
        return folded_extents(self.flat)

    def mass_g(self) -> float | None:
        """Mass of the FOLDED part (the flat and the folded differ by the bend
        zones, and the part you weigh is the folded one)."""
        if not self.material:
            return None
        from partkiln import materials

        return materials.mass_g(self.material, self.flat.folded_volume())

    def fingerprint(self) -> str:
        """16 hex over everything the sheet IS, rounded first (Law 7)."""
        payload = [self.name, self.material, round(self.k, 6), self.flat.fingerprint_payload()]
        return sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16]

    def summary(self) -> dict[str, Any]:
        """The D7 sheet row: scalars, and the volume note that explains the delta."""
        flat = self.flat
        length, width = flat.extents()
        bbox = self.folded_bbox()
        out: dict[str, Any] = {
            "id": f"sheet:{self.name}",
            "kind": "sheet",
            "t": r3(flat.t),
            "k": round(self.k, 4),
            "bends": len(flat.bends),
            "flanges": len(flat.flanges),
            "holes": len(flat.holes),
            "flat_mm": [r3(length), r3(width)],
            "folded_bbox_mm": [r3(v) for v in bbox],
            "ba_total_mm": r3(flat.ba_total()),
            "bd_total_mm": r3(flat.bd_total()),
            "flat_volume_mm3": r3(flat.flat_volume()),
            "folded_volume_mm3": r3(flat.folded_volume()),
            "volume_delta_mm3": r3(flat.volume_delta()),
            "material": self.material,
            "mass_g": self.mass_g(),
            "fingerprint": self.fingerprint(),
        }
        return out

    def detail(self, entity_id: str) -> dict[str, Any] | None:
        """`Document.detail`'s hook: the full report for this sheet's own id,
        and None for anything else (the document asks every container item)."""
        if str(entity_id) in (f"sheet:{self.name}", self.name):
            return self.report()
        return None

    def report(self) -> dict[str, Any]:
        """`tee_entity_detail`: the row plus the per-bend and per-hole rows."""
        return {
            **self.summary(),
            "bend_rows": [b.as_dict() for b in self.flat.bends],
            "flange_rows": [f.as_dict() for f in self.flat.flanges],
            "hole_rows": [h.as_dict() for h in self.flat.holes],
            "notes": [*self.notes, self.flat.volume_note()],
        }

    # -- geometry (opt-in, needs the kernel) ----------------------------------

    def solid(self, kind: str = "folded") -> Any:
        """The B-rep body: `folded` (the part) or `flat` (the blank)."""
        if kind == "folded":
            return folded_solid(self.flat)
        if kind == "flat":
            return flat_solid(self.flat)
        raise CommandError(
            f"a sheet has a 'folded' body and a 'flat' body, not {kind!r}.", code="pk_bad_op"
        )


__all__ = [
    "Place",
    "Segment",
    "Sheet",
    "bend_axis_z",
    "chain",
    "flat_solid",
    "fold_place",
    "folded_extents",
    "folded_points",
    "folded_solid",
    "inside_z",
    "place_of",
    "plate",
]
