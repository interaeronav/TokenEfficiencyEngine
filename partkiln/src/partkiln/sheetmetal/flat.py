"""The flat pattern: the sheet-metal model that the fold is DERIVED from (P5b).

Flat-first, by decision 4 of the A66 script: a sheet-metal part is its flat
pattern plus a list of bends, and the folded solid is computed from that
(fold.py), never the other way round. The numbers a press brake needs live
here, in pure Python, with no OCP:

    BA   = A * (pi/180) * (R + K*T)      bend allowance: the arc length of the
                                         neutral axis through the bend
    OSSB = (R + T) * tan(A/2)            outside setback: outside apex to the
                                         tangent point of the outside surface
    BD   = 2*OSSB - BA                   bend deduction
    flat = a + b - 2*OSSB + BA           a two-flange L from OUTSIDE legs a, b

with A the bend angle in degrees, R the INSIDE radius, T the thickness and K
the neutral-axis fraction of T. Formula citation: Wikipedia, "Bending
(metalworking)" (CC BY-SA 4.0), which cites Industrial Press, Machinery's
Handbook (1994) - a FORMULA citation; no table is copied from either. The
pinned fixture (F7: T 2, R 2, K 0.44, 90 deg, outside legs 50 and 30) gives
BA 4.524, BD 3.476 and a flat of 76.524 mm.

K = 0.44 is THIS KERNEL'S CHOICE, inside the typical 0.3-0.5 range. No
standard fixes K: it depends on the material, the tooling and the ratio R/T,
and a shop measures it. A production part passes `k` (or, later, a bend
table); the default is echoed as `assumed` on every sheet so nobody mistakes
it for a measured value. DIN 6935 also prints a "k" - a correction factor in
its own compensation-value formula, a function of r/s - which is a DIFFERENT
quantity from the neutral-axis fraction here and must not be passed as `k`.

Volumes, kept visible on purpose: the bend zone of the FLAT is a strip of
BA * T * L; the same zone FOLDED is an annular sector of
(pi*A/360) * ((R+T)^2 - R^2) * L, which does not contain K at all (F7:
9.425 * 40 = 377.0 mm3 at any K). Their difference is the K-factor's whole
volumetric effect - zero at K = 0.5, where the neutral axis is the
volumetric centre of the sheet - and every sheet reports it with the note
rather than hiding a 0.2 % mass discrepancy.

Coordinates: the flat lies in the XY plane in millimetres; a bend is a line
on it, and the flange that folds lies to the LEFT of the line's direction
(p0 -> p1). The DXF writer puts the outline, the bend centre lines (by
direction) and the holes on the four layers a laser shop expects
(OUTLINE / BEND_UP / BEND_DOWN / HOLES) with `$INSUNITS = 4` (mm); the SVG is
the same drawing for a browser. Both are byte-identical on repeat (Law 7).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from partkiln.document import CommandError

Point2 = tuple[float, float]

DEFAULT_K = 0.44
"""This kernel's default neutral-axis fraction (see the module docstring)."""

K_TYPICAL = (0.3, 0.5)
"""The range a handbook quotes for K; the default sits inside it, declared."""

K_NOTE = (
    f"K = {DEFAULT_K} is partkiln's default inside the typical {K_TYPICAL[0]}-{K_TYPICAL[1]} "
    "range; no standard fixes K - pass k (or a bend table) for a production part"
)

FORMULA_SOURCE = (
    "BA = A*(pi/180)*(R + K*T), OSSB = (R+T)*tan(A/2), BD = 2*OSSB - BA: Wikipedia "
    '"Bending (metalworking)" (CC BY-SA 4.0), citing Industrial Press 1994 - formulas only'
)

DXF_LAYERS = ("OUTLINE", "BEND_UP", "BEND_DOWN", "HOLES")
DXF_INSUNITS_MM = 4
_LAYER_COLOURS = {"OUTLINE": 7, "BEND_UP": 1, "BEND_DOWN": 5, "HOLES": 3}
_DIRECTIONS = ("up", "down")


def r3(x: float) -> float:
    return round(float(x), 3) + 0.0


# --------------------------------------------------------------------------- formulas


def check_bend(angle_deg: float, r_inner: float, t: float, k: float = DEFAULT_K) -> None:
    """Refuse the values the formulas cannot take, naming the fix (D8)."""
    if not 0.0 < angle_deg < 180.0:
        raise CommandError(
            f"bend angle {angle_deg:g} deg is not in (0, 180). A bend is the angle the flange "
            "turns through; 180 deg is a hem, which has no outside setback (tan 90 deg).",
            code="pk_needs",
        )
    if t <= 0.0:
        raise CommandError(f"sheet thickness t must be > 0, got {t:g} mm.", code="pk_needs")
    if r_inner < 0.0:
        raise CommandError(
            f"inside bend radius r must be >= 0, got {r_inner:g} mm.", code="pk_needs"
        )
    if not 0.0 < k < 1.0:
        raise CommandError(
            f"k = {k:g} is not a neutral-axis fraction: 0 < k < 1 (typical "
            f"{K_TYPICAL[0]}-{K_TYPICAL[1]}). DIN 6935's k is a different quantity.",
            code="pk_needs",
        )


def bend_allowance(angle_deg: float, r_inner: float, t: float, k: float = DEFAULT_K) -> float:
    """BA = A*(pi/180)*(R + K*T): F7 -> 4.524 (K 0.44), 4.398 (0.4), 4.712 (0.5)."""
    check_bend(angle_deg, r_inner, t, k)
    return math.radians(angle_deg) * (r_inner + k * t)


def outside_setback(angle_deg: float, r_inner: float, t: float) -> float:
    """OSSB = (R + T)*tan(A/2): the outside apex to the outside tangent point."""
    check_bend(angle_deg, r_inner, t)
    return (r_inner + t) * math.tan(math.radians(angle_deg) / 2.0)


def bend_deduction(angle_deg: float, r_inner: float, t: float, k: float = DEFAULT_K) -> float:
    """BD = 2*OSSB - BA: F7 -> 3.476."""
    return 2.0 * outside_setback(angle_deg, r_inner, t) - bend_allowance(angle_deg, r_inner, t, k)


def bend_zone_volume(angle_deg: float, r_inner: float, t: float, length: float) -> float:
    """The FOLDED bend zone: an annular sector, (pi*A/360)*((R+T)^2 - R^2)*L.

    K does not appear: the sector is geometry, the neutral axis is a
    modelling choice. F7 (90 deg, R 2, T 2, L 40) -> 376.991 mm3 at any K.
    """
    check_bend(angle_deg, r_inner, t)
    return math.pi * angle_deg / 360.0 * ((r_inner + t) ** 2 - r_inner**2) * length


def flat_strip_volume(
    angle_deg: float, r_inner: float, t: float, length: float, k: float = DEFAULT_K
) -> float:
    """The same zone on the FLAT: BA*T*L - the K-dependent half of the difference."""
    return bend_allowance(angle_deg, r_inner, t, k) * t * length


def flat_length(
    outside_legs: Sequence[float],
    angle_deg: float,
    r_inner: float,
    t: float,
    k: float = DEFAULT_K,
) -> float:
    """A two-flange L from its OUTSIDE legs: a + b - 2*OSSB + BA (F7 -> 76.524)."""
    if len(outside_legs) != 2:
        raise CommandError(
            f"flat_length takes the two outside legs of an L, got {len(outside_legs)}.",
            code="pk_needs",
        )
    a, b = (float(v) for v in outside_legs)
    return (
        a
        + b
        - 2.0 * outside_setback(angle_deg, r_inner, t)
        + bend_allowance(angle_deg, r_inner, t, k)
    )


# --------------------------------------------------------------------------- the model


@dataclass(frozen=True)
class Bend:
    """One bend: a line on the flat, an angle, an inside radius, a K and a direction.

    The flange that folds lies to the LEFT of the line's direction p0 -> p1
    (`outboard` is that unit normal); `up` folds it toward +Z (the inside of
    the bend is the sheet's top face, z = t), `down` toward -Z. The bend
    zone is the strip 0 <= (p - p0) . outboard <= BA.
    """

    name: str
    line: tuple[Point2, Point2]
    angle_deg: float
    r_inner: float
    t: float
    k: float = DEFAULT_K
    direction: str = "up"

    def __post_init__(self) -> None:
        check_bend(self.angle_deg, self.r_inner, self.t, self.k)
        if self.direction not in _DIRECTIONS:
            raise CommandError(
                f"bend {self.name}: dir {self.direction!r} is not up or down.", code="pk_needs"
            )
        if self.length < 1e-9:
            raise CommandError(f"bend {self.name}: the bend line has zero length.", code="pk_needs")

    @property
    def ba(self) -> float:
        return bend_allowance(self.angle_deg, self.r_inner, self.t, self.k)

    @property
    def ossb(self) -> float:
        return outside_setback(self.angle_deg, self.r_inner, self.t)

    @property
    def bd(self) -> float:
        return 2.0 * self.ossb - self.ba

    @property
    def length(self) -> float:
        (x0, y0), (x1, y1) = self.line
        return math.hypot(x1 - x0, y1 - y0)

    @property
    def tangent(self) -> Point2:
        (x0, y0), (x1, y1) = self.line
        n = self.length
        return ((x1 - x0) / n, (y1 - y0) / n)

    @property
    def outboard(self) -> Point2:
        dx, dy = self.tangent
        return (-dy, dx)

    @property
    def zone_volume(self) -> float:
        return bend_zone_volume(self.angle_deg, self.r_inner, self.t, self.length)

    @property
    def strip_volume(self) -> float:
        return flat_strip_volume(self.angle_deg, self.r_inner, self.t, self.length, self.k)

    def offset(self, p: Point2) -> float:
        """Signed distance of `p` from the bend line, positive toward the flange."""
        (x0, y0), _ = self.line
        nx, ny = self.outboard
        return (p[0] - x0) * nx + (p[1] - y0) * ny

    def centre_line(self) -> tuple[Point2, Point2]:
        """The line a brake operator marks: the middle of the bend zone."""
        nx, ny = self.outboard
        h = self.ba / 2.0
        (x0, y0), (x1, y1) = self.line
        return ((x0 + h * nx, y0 + h * ny), (x1 + h * nx, y1 + h * ny))

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "angle_deg": r3(self.angle_deg),
            "r_mm": r3(self.r_inner),
            "k": round(self.k, 4),
            "dir": self.direction,
            "ba_mm": r3(self.ba),
            "bd_mm": r3(self.bd),
            "ossb_mm": r3(self.ossb),
            "length_mm": r3(self.length),
            "zone_volume_mm3": r3(self.zone_volume),
            "strip_volume_mm3": r3(self.strip_volume),
        }


@dataclass(frozen=True)
class Hole:
    """A through hole: its centre on the flat, plus where it was asked for."""

    name: str
    centre: Point2
    dia: float
    flange: str = ""
    at: Point2 = (0.0, 0.0)
    source: str = ""

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "name": self.name,
            "dia_mm": r3(self.dia),
            "flat_at": [r3(self.centre[0]), r3(self.centre[1])],
        }
        if self.flange:
            out["flange"] = self.flange
            out["at"] = [r3(self.at[0]), r3(self.at[1])]
        if self.source:
            out["source"] = self.source
        return out


@dataclass(frozen=True)
class Flange:
    """A flange row of the flat: its OUTSIDE length and its flat portion on the layout."""

    name: str
    length: float
    flat_start: float
    flat_end: float
    angle_deg: float | None = None  # the bend INTO this flange; None for the base
    r_inner: float | None = None
    direction: str | None = None

    @property
    def flat_length(self) -> float:
        return self.flat_end - self.flat_start

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "name": self.name,
            "len_mm": r3(self.length),
            "flat_mm": [r3(self.flat_start), r3(self.flat_end)],
            "flat_len_mm": r3(self.flat_length),
        }
        if self.angle_deg is not None:
            out.update({"angle_deg": r3(self.angle_deg), "r_mm": r3(self.r_inner or 0.0)})
            out["dir"] = self.direction
        return out


@dataclass
class Flat:
    """The flat pattern: a closed outline (mm, CCW), its thickness, bends and holes.

    `flanges` and `relief` are set by `from_flanges` (the wire's layout) and
    are what gives a hole a frame to be placed in; a Flat built from a bare
    outline has neither and takes holes in flat coordinates.
    """

    t: float
    outline: list[Point2]
    bends: list[Bend] = field(default_factory=list)
    holes: list[Hole] = field(default_factory=list)
    flanges: list[Flange] = field(default_factory=list)
    relief: dict[str, float] | None = None

    def __post_init__(self) -> None:
        if self.t <= 0.0:
            raise CommandError(f"sheet thickness t must be > 0, got {self.t:g}.", code="pk_needs")
        if len(self.outline) < 3:
            raise CommandError(
                f"a flat outline needs >= 3 points, got {len(self.outline)}.", code="pk_needs"
            )
        self.outline = [(float(x), float(y)) for x, y in self.outline]
        if self.area() <= 0.0:
            raise CommandError(
                "the outline is clockwise or degenerate; list its points counter-clockwise.",
                code="pk_needs",
            )

    # -- construction from the wire's flange chain -------------------------------

    @classmethod
    def from_flanges(
        cls,
        t: float,
        width: float,
        flanges: Sequence[dict[str, Any]],
        k: float = DEFAULT_K,
        relief: dict[str, float] | None = None,
    ) -> Flat:
        """Lay a chain of flanges along +X: f1 is the base (its free end at x = 0),
        each later flange folds off the previous one about a line across the width.

        Each entry is `{len, angle, r, dir}` with `len` the OUTSIDE length
        (apex to apex, or apex to free end); the base carries only `len`. The
        flat portion of a flange is its outside length minus the outside
        setback of every bend it takes part in - the formula the module
        docstring cites, applied per flange - and a flange too short for its
        setbacks refuses by name.
        """
        if t <= 0.0 or width <= 0.0:
            raise CommandError(
                f"sheet t and width must be > 0, got t {t:g}, width {width:g}.", code="pk_needs"
            )
        if not flanges:
            raise CommandError("a sheet needs at least one flange.", code="pk_needs")
        rw, extra = 0.0, 0.0
        if relief:
            rw, extra = float(relief.get("width", 0.0)), float(relief.get("extra", 0.0))
            if rw <= 0.0 or extra < 0.0 or 2.0 * rw >= width:
                raise CommandError(
                    f"relief needs 0 < width < {width / 2:g} (half the sheet width) and "
                    f"extra >= 0, got width {rw:g}, extra {extra:g}.",
                    code="pk_needs",
                )
        specs = [dict(f) for f in flanges]
        n_bends = len(specs) - 1
        setbacks: list[float] = []  # OSSB of bend j (between flange j and j+1)
        allowances: list[float] = []
        for j in range(1, len(specs)):
            spec = specs[j]
            angle = float(spec.get("angle", 90.0))
            r = float(spec.get("r", t))
            check_bend(angle, r, t, k)
            setbacks.append(outside_setback(angle, r, t))
            allowances.append(bend_allowance(angle, r, t, k))
        rows: list[Flange] = []
        bends: list[Bend] = []
        x = 0.0
        for j, spec in enumerate(specs):
            length = float(spec["len"])
            if length <= 0.0:
                raise CommandError(
                    f"flange f{j + 1}: len must be > 0, got {length:g}.", code="pk_needs"
                )
            left = setbacks[j - 1] if j >= 1 else 0.0
            right = setbacks[j] if j < n_bends else 0.0
            flat_len = length - left - right
            if flat_len <= 0.0:
                raise CommandError(
                    f"flange f{j + 1} of {length:g} mm is shorter than its outside setbacks "
                    f"({left:g} + {right:g} mm): lengthen it or reduce the bend radius.",
                    code="pk_needs",
                )
            start = x
            end = x + flat_len
            if j >= 1:
                rows.append(
                    Flange(
                        f"f{j + 1}",
                        length,
                        start,
                        end,
                        float(spec.get("angle", 90.0)),
                        float(spec.get("r", t)),
                        str(spec.get("dir", "up")),
                    )
                )
            else:
                rows.append(Flange("f1", length, start, end))
            x = end
            if j < n_bends:
                nxt = specs[j + 1]
                line = ((x, width - rw), (x, rw))
                bends.append(
                    Bend(
                        f"b{j + 1}",
                        line,
                        float(nxt.get("angle", 90.0)),
                        float(nxt.get("r", t)),
                        t,
                        k,
                        str(nxt.get("dir", "up")),
                    )
                )
                x += allowances[j]
        total = x
        outline = _chain_outline(total, width, bends, rw, extra)
        flat = cls(t, outline, bends, [], rows, dict(relief) if relief else None)
        return flat

    # -- measures ----------------------------------------------------------------

    def extents(self) -> tuple[float, float]:
        xs = [p[0] for p in self.outline]
        ys = [p[1] for p in self.outline]
        return (max(xs) - min(xs), max(ys) - min(ys))

    def bbox(self) -> tuple[float, float, float, float]:
        xs = [p[0] for p in self.outline]
        ys = [p[1] for p in self.outline]
        return (min(xs), min(ys), max(xs), max(ys))

    def area(self) -> float:
        """Shoelace area of the outline (mm2), holes not subtracted."""
        total = 0.0
        pts = self.outline
        for i, (x0, y0) in enumerate(pts):
            x1, y1 = pts[(i + 1) % len(pts)]
            total += x0 * y1 - x1 * y0
        return total / 2.0

    def hole_area(self) -> float:
        return sum(math.pi * (h.dia / 2.0) ** 2 for h in self.holes)

    def flat_volume(self) -> float:
        """The flat plate with its holes: (outline area - holes) * t."""
        return (self.area() - self.hole_area()) * self.t

    def folded_volume(self) -> float:
        """Each flat strip replaced by its annular sector; the holes stay through."""
        return self.flat_volume() + sum(b.zone_volume - b.strip_volume for b in self.bends)

    def volume_delta(self) -> float:
        """folded - flat: the K-factor's whole volumetric effect, kept visible."""
        return self.folded_volume() - self.flat_volume()

    def ba_total(self) -> float:
        return sum(b.ba for b in self.bends)

    def bd_total(self) -> float:
        return sum(b.bd for b in self.bends)

    def volume_note(self) -> str:
        sectors = r3(sum(b.zone_volume for b in self.bends))
        strips = r3(sum(b.strip_volume for b in self.bends))
        return (
            f"folded - flat = {r3(self.volume_delta()):+g} mm3: each bend zone is an annular "
            f"sector ({sectors:g} mm3, K-independent) where the flat has a strip of BA*T*L "
            f"({strips:g} mm3); the difference is the K-factor's whole volumetric effect, "
            "0 at K = 0.5"
        )

    # -- holes --------------------------------------------------------------------

    def flange(self, ref: str | int) -> Flange:
        """A flange by name ('f2') or 1-based index (2); refuses naming the flanges."""
        if not self.flanges:
            raise CommandError(
                "this flat has no flange layout; place holes in flat coordinates (flat_at).",
                code="pk_needs",
            )
        key = f"f{ref}" if isinstance(ref, int) and not isinstance(ref, bool) else str(ref)
        for row in self.flanges:
            if row.name == key:
                return row
        known = ", ".join(r.name for r in self.flanges)
        raise CommandError(f"no flange {ref!r}. Flanges: {known}.", code="pk_ref_unknown")

    def add_hole(
        self,
        dia: float,
        at: Point2,
        flange: str | int | None = None,
        name: str | None = None,
        source: str = "",
    ) -> Hole:
        """A through hole of `dia` at `at`: in a flange's frame (x along the
        flange from where its flat portion begins - the free end of the base,
        the bend tangent of any other - y across the width from y = 0) when
        `flange` is given, else in flat coordinates. Refuses a hole that leaves
        its flange or enters a bend zone, naming the bounds."""
        if dia <= 0.0:
            raise CommandError(f"hole dia must be > 0, got {dia:g}.", code="pk_needs")
        label = name or f"h.{len(self.holes) + 1}"
        if any(h.name == label for h in self.holes):
            raise CommandError(f"hole {label!r} already exists on this sheet.", code="pk_needs")
        x, y = float(at[0]), float(at[1])
        row: Flange | None = None
        if flange is not None:
            row = self.flange(flange)
            centre = (row.flat_start + x, y)
        else:
            centre = (x, y)
        radius = dia / 2.0
        x0, y0, x1, y1 = self.bbox()
        for bend in self.bends:
            d = bend.offset(centre)
            if -radius < d < bend.ba + radius:
                (bx, by), _ = bend.line
                raise CommandError(
                    f"hole {label} (d{dia:g} at flat ({centre[0]:g}, {centre[1]:g})) enters the "
                    f"bend zone of {bend.name} (offset {r3(d):g} of 0..{r3(bend.ba):g} mm from "
                    f"its line at ({bx:g}, {by:g})). Move it at least {r3(radius):g} mm clear "
                    "of the zone.",
                    code="pk_needs",
                )
        if row is not None and not (row.flat_start + radius <= centre[0] <= row.flat_end - radius):
            raise CommandError(
                f"hole {label} (d{dia:g}) at x {x:g} leaves flange {row.name}, whose flat "
                f"portion is {r3(row.flat_length):g} mm long: keep x in "
                f"[{r3(radius):g}, {r3(row.flat_length - radius):g}].",
                code="pk_needs",
            )
        if not (x0 + radius <= centre[0] <= x1 - radius and y0 + radius <= y <= y1 - radius):
            raise CommandError(
                f"hole {label} (d{dia:g}) at flat ({centre[0]:g}, {y:g}) leaves the sheet "
                f"({r3(x0):g}..{r3(x1):g} x {r3(y0):g}..{r3(y1):g} mm).",
                code="pk_needs",
            )
        hole = Hole(label, centre, float(dia), row.name if row else "", (x, y), source)
        self.holes.append(hole)
        return hole

    # -- reports ---------------------------------------------------------------------

    def summary(self) -> dict[str, Any]:
        length, width = self.extents()
        return {
            "t": r3(self.t),
            "flat_mm": [r3(length), r3(width)],
            "area_mm2": r3(self.area() - self.hole_area()),
            "bends": len(self.bends),
            "flanges": len(self.flanges),
            "holes": len(self.holes),
            "ba_total_mm": r3(self.ba_total()),
            "bd_total_mm": r3(self.bd_total()),
            "flat_volume_mm3": r3(self.flat_volume()),
            "folded_volume_mm3": r3(self.folded_volume()),
            "volume_delta_mm3": r3(self.volume_delta()),
        }

    def fingerprint_payload(self) -> list[Any]:
        """Everything the flat IS, rounded to 6 dp - the same bytes in every process."""
        return [
            round(self.t, 6),
            [[round(x, 6), round(y, 6)] for x, y in self.outline],
            [
                [
                    b.name,
                    [[round(c, 6) for c in p] for p in b.line],
                    round(b.angle_deg, 6),
                    round(b.r_inner, 6),
                    round(b.k, 6),
                    b.direction,
                ]
                for b in self.bends
            ],
            [
                [h.name, [round(h.centre[0], 6), round(h.centre[1], 6)], round(h.dia, 6)]
                for h in self.holes
            ],
        ]

    # -- files -------------------------------------------------------------------------

    def write_dxf(self, path: str | Path) -> dict[str, Any]:
        """The flat pattern as DXF R2010: OUTLINE (closed LWPOLYLINE), one LINE per
        bend on BEND_UP or BEND_DOWN at the zone's centre with a TEXT naming it,
        a CIRCLE per hole on HOLES; `$INSUNITS = 4` says millimetres.

        Bytes are identical on repeat (Law 7), and getting there took two
        goes: ezdxf stamps `$TDUPDATE` and a fresh `$VERSIONGUID` on every
        SAVE, and `CREATED_BY_EZDXF` (a DICTIONARYVAR holding
        "<version> @ <ISO timestamp>") at `ezdxf.new()`. Its fixed-metadata
        option covers both, but only if it is set BEFORE the document is
        made - set around `saveas` alone, two consecutive writes still
        differed by one line, 2 720 us apart. So the option wraps the whole
        function and is restored after.
        """
        import ezdxf

        previous = ezdxf.options.write_fixed_meta_data_for_testing
        ezdxf.options.write_fixed_meta_data_for_testing = True
        try:
            return self._write_dxf(ezdxf, path)
        finally:
            ezdxf.options.write_fixed_meta_data_for_testing = previous

    def _write_dxf(self, ezdxf: Any, path: str | Path) -> dict[str, Any]:
        doc = ezdxf.new("R2010", setup=False)
        doc.header["$INSUNITS"] = DXF_INSUNITS_MM
        for layer in DXF_LAYERS:
            doc.layers.add(layer, color=_LAYER_COLOURS[layer])
        msp = doc.modelspace()
        msp.add_lwpolyline(
            [(x, y) for x, y in self.outline], close=True, dxfattribs={"layer": "OUTLINE"}
        )
        counts = dict.fromkeys(DXF_LAYERS, 0)
        counts["OUTLINE"] = 1
        for bend in self.bends:
            layer = "BEND_UP" if bend.direction == "up" else "BEND_DOWN"
            (ax, ay), (bx, by) = bend.centre_line()
            msp.add_line((ax, ay), (bx, by), dxfattribs={"layer": layer})
            label = (
                f"{bend.name} {bend.direction.upper()} {bend.angle_deg:g} deg "
                f"R{bend.r_inner:g} BA{bend.ba:.3f}"
            )
            text = msp.add_text(label, height=max(self.t, 1.0), dxfattribs={"layer": layer})
            text.set_placement(((ax + bx) / 2.0 + 1.0, (ay + by) / 2.0))
            counts[layer] += 1
        for hole in self.holes:
            msp.add_circle(hole.centre, hole.dia / 2.0, dxfattribs={"layer": "HOLES"})
            counts["HOLES"] += 1
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        doc.saveas(str(out))
        return {
            "path": str(out),
            "bytes": out.stat().st_size,
            "format": "dxf",
            "insunits": DXF_INSUNITS_MM,
            "units": "mm",
            "declares_units": True,
            "layers": list(DXF_LAYERS),
            "entities": counts,
        }

    def write_svg(self, path: str | Path) -> dict[str, Any]:
        """The same drawing as SVG, 1 user unit = 1 mm, y up (flipped for the
        browser), one `<g id=LAYER>` per DXF layer so a viewer can toggle them."""
        length, width = self.extents()
        x0, y0, _, _ = self.bbox()

        def fx(x: float) -> str:
            return f"{x - x0:.3f}"

        def fy(y: float) -> str:
            return f"{width - (y - y0):.3f}"

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{length:.3f}mm" '
            f'height="{width:.3f}mm" viewBox="0 0 {length:.3f} {width:.3f}">',
            f"<title>flat pattern {length:.3f} x {width:.3f} mm, t {self.t:g}</title>",
            '<g id="OUTLINE" fill="none" stroke="#000" stroke-width="0.2">',
            '<polygon points="' + " ".join(f"{fx(x)},{fy(y)}" for x, y in self.outline) + '"/>',
            "</g>",
        ]
        for layer, colour, dash in (
            ("BEND_UP", "#c00000", "2 1"),
            ("BEND_DOWN", "#0000c0", "3 1 0.5 1"),
        ):
            lines.append(
                f'<g id="{layer}" fill="none" stroke="{colour}" stroke-width="0.15" '
                f'stroke-dasharray="{dash}">'
            )
            direction = "up" if layer == "BEND_UP" else "down"
            for bend in self.bends:
                if bend.direction != direction:
                    continue
                (ax, ay), (bx, by) = bend.centre_line()
                lines.append(
                    f'<line x1="{fx(ax)}" y1="{fy(ay)}" x2="{fx(bx)}" y2="{fy(by)}">'
                    f"<title>{bend.name} {bend.direction} {bend.angle_deg:g} deg R"
                    f"{bend.r_inner:g} BA {bend.ba:.3f}</title></line>"
                )
            lines.append("</g>")
        lines.append('<g id="HOLES" fill="none" stroke="#008000" stroke-width="0.15">')
        for hole in self.holes:
            lines.append(
                f'<circle cx="{fx(hole.centre[0])}" cy="{fy(hole.centre[1])}" '
                f'r="{hole.dia / 2.0:.3f}"><title>{hole.name} d{hole.dia:g}</title></circle>'
            )
        lines.extend(["</g>", "</svg>", ""])
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines), encoding="utf-8")
        return {
            "path": str(out),
            "bytes": out.stat().st_size,
            "format": "svg",
            "units": "mm",
            "declares_units": True,
            "layers": list(DXF_LAYERS),
        }


def _chain_outline(
    total: float, width: float, bends: Sequence[Bend], rw: float, extra: float
) -> list[Point2]:
    """The rectangle of a flange chain, with a relief notch at each end of every
    bend zone (rw across from the edge, the zone plus `extra` each way along)."""
    if rw <= 0.0:
        return [(0.0, 0.0), (total, 0.0), (total, width), (0.0, width)]
    notches: list[tuple[float, float]] = []
    for bend in bends:
        (bx, _), _ = bend.line
        xa, xb = bx - extra, bx + bend.ba + extra
        if xa < 0.0 or xb > total:
            raise CommandError(
                f"relief at {bend.name} runs from x {r3(xa):g} to {r3(xb):g}, outside the flat "
                f"(0..{r3(total):g}); reduce extra.",
                code="pk_needs",
            )
        if notches and xa <= notches[-1][1]:
            raise CommandError(
                f"relief notches of {bend.name} and the bend before it overlap "
                f"(x {r3(notches[-1][1]):g} vs {r3(xa):g}); reduce extra or lengthen the flange.",
                code="pk_needs",
            )
        notches.append((xa, xb))
    pts: list[Point2] = [(0.0, 0.0)]
    for xa, xb in notches:
        pts.extend([(xa, 0.0), (xa, rw), (xb, rw), (xb, 0.0)])
    pts.extend([(total, 0.0), (total, width)])
    for xa, xb in reversed(notches):
        pts.extend([(xb, width), (xb, width - rw), (xa, width - rw), (xa, width)])
    pts.append((0.0, width))
    return pts


__all__ = [
    "DEFAULT_K",
    "DXF_INSUNITS_MM",
    "DXF_LAYERS",
    "FORMULA_SOURCE",
    "K_NOTE",
    "K_TYPICAL",
    "Bend",
    "Flange",
    "Flat",
    "Hole",
    "Point2",
    "bend_allowance",
    "bend_deduction",
    "bend_zone_volume",
    "check_bend",
    "flat_length",
    "flat_strip_volume",
    "outside_setback",
    "r3",
]
