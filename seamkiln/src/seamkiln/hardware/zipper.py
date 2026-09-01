"""Zippers: the chain, the slider, and what a closed zipper does to cloth.

You install a zipper the way you sew a seam - by naming two pattern edges -
and the difference is what happens next. A seam is closed everywhere, always.
A zipper is closed only BELOW the slider, and the slider moves. That single
fact is the whole design:

  * the two edges are paired once, at build time, exactly like a seam
  * `engaged()` asks which of those pairs the slider has passed
  * only the engaged pairs become constraints, and they are rebuilt whenever
    the slider moves

The three things a closed zipper does that a seam does not, all of which are
in the constraints and none of which are decoration:

  weight    a #5 brass chain is ~33 g/m against a poplin's 130 g/m^2 - on a
            600 mm front opening that is 20 g of metal hanging on one edge.
  stiffness the closed chain is a ladder truss, not a hinge. It is modelled
            as one: the rungs are the engaged pairs, and cross-braces between
            consecutive rungs stop it shearing into a parallelogram.
  a boundary the open part above the slider is FREE, and free is the point.

Slider layouts, which are the three the trade sells:

  one-way             one slider. Closed below it, open above.
  two-way, head-head  two sliders facing each other; they close toward each
                      other, so pulling them apart opens the MIDDLE. The
                      sleeping-bag-zipped-to-another-sleeping-bag arrangement.
  two-way, bottom-bot two sliders back to back; each closes away from the
                      other, so the OPEN parts are at the two ends. This is
                      what lets a long coat open from the hem while staying
                      closed at the chest.

Head-to-head and bottom-to-bottom are exact complements of each other, which
is the tidiest way to remember which is which - and is asserted in the tests
rather than left as a comment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from seamkiln.drape.garment import GarmentMesh
from seamkiln.hardware.trim import Trim, zipper_trim

# How freely a #5 NYLON COIL's chain bends. Every other material is this over
# its stiffness ratio, so a stiffer chain gets a SMALLER number.
#
# It is a relative softening and not a compliance in m/N - see the note in
# `solve.py`, and note that this cost a wasted sweep: the first four decades
# tried (6e-7 .. 6e-1) were all indistinguishable from rigid, because at those
# values the per-iteration correction is 99.9%+ of full and thousands of
# iterations follow. The range that actually bites is single digits to tens.
#
# Fitted on the jacket block, chain turn angle over a 587 mm front opening,
# with the chain MASS HELD CONSTANT so only stiffness varies:
#     no straighteners     2320 deg   (a free hinge at every tooth)
#     stiffness x1.0       2216 deg   (nylon coil)
#     stiffness x6.5       2012 deg   (brass)
# With the real materials the order is NOT monotone - nylon 2216, plastic
# 2389, metal 2299 - and that is not a defect to hide. A brass chain is 6.5x
# stiffer AND 3.2x heavier than a nylon coil, and on a front opening that
# hangs, the extra sag from the weight partly cancels the extra resistance
# from the stiffness. Both effects are real, both are modelled, and which one
# wins depends on the garment.
_BEND_BASE = 20.0

LAYOUTS = ("one-way", "two-way-head-to-head", "two-way-bottom-to-bottom")

# Standard chain sizes, which are the closed chain width in millimetres.
SIZES = (3.0, 5.0, 8.0, 10.0)


@dataclass(slots=True)
class ZipperSpec:
    """What zipper to fit. Everything the trade lets you order."""

    material: str = "nylon"  # plastic | nylon | metal
    size: float = 5.0  # #3, #5, #8, #10 - the closed chain width in mm
    layout: str = "one-way"
    tape_mm: float = 12.0  # per side, not the total width
    slider_scale: float = 1.0  # a bigger puller-and-body than standard
    weight_scale: float = 1.0  # a thumb on the scale, for a trim you own
    separating: bool = False  # does the bottom stop come apart?

    def __post_init__(self) -> None:
        if self.layout not in LAYOUTS:
            raise ValueError(f"unknown zipper layout {self.layout!r}. Known: {', '.join(LAYOUTS)}")
        if self.size <= 0.0:
            raise ValueError(f"zipper size must be positive, got {self.size}")
        if self.tape_mm <= 0.0:
            raise ValueError(f"tape width must be positive, got {self.tape_mm}")

    @property
    def sliders(self) -> int:
        return 1 if self.layout == "one-way" else 2

    def trim(self) -> Trim:
        return zipper_trim(self.material, self.size)

    def slider_mm(self) -> tuple[float, float]:
        """Body length and width, mm. A #5 slider body is about 20 x 12."""
        return (4.0 * self.size * self.slider_scale, 2.4 * self.size * self.slider_scale)


@dataclass(slots=True)
class Zipper:
    """A fitted zipper: where its chain is, and where its sliders are."""

    id: str
    spec: ZipperSpec
    pairs: np.ndarray  # int32 [n, 2] - left particle, right particle
    t: np.ndarray  # float64 [n] - 0 at the bottom stop, 1 at the top
    length_m: float
    sliders: tuple[float, ...] = (1.0,)
    trim: Trim = field(default=None)  # type: ignore[assignment]

    def __len__(self) -> int:
        return int(self.pairs.shape[0])

    def engaged(self) -> np.ndarray:
        """Which chain pairs are closed, as a boolean mask over `pairs`."""
        return _engaged(self.t, self.spec.layout, self.sliders)

    def open_fraction(self) -> float:
        if not len(self):
            return 0.0
        return float(1.0 - self.engaged().mean())

    def mass_kg(self) -> float:
        chain = self.trim.chain_kg_per_m() * self.length_m
        bodies = self.trim.slider_g / 1000.0 * self.spec.sliders
        return (chain + bodies) * self.spec.weight_scale

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "material": self.spec.material,
            "size": f"#{self.spec.size:g}",
            "layout": self.spec.layout,
            "teeth": round(self.length_m * 1000.0 / self.trim.teeth_pitch_mm),
            "chain_points": len(self),
            "length_mm": round(self.length_m * 1000.0, 1),
            "sliders_at": [round(float(s), 3) for s in self.sliders],
            "engaged": int(self.engaged().sum()),
            "open_percent": round(self.open_fraction() * 100.0, 1),
            "mass_g": round(self.mass_kg() * 1000.0, 2),
            "self_healing": self.trim.self_healing,
        }


def _engaged(t: np.ndarray, layout: str, sliders: tuple[float, ...]) -> np.ndarray:
    if layout == "one-way":
        return t <= sliders[0] + 1e-9
    lo, hi = min(sliders[0], sliders[1]), max(sliders[0], sliders[1])
    if layout == "two-way-head-to-head":
        # closed at both ENDS, open in the middle
        return (t <= lo + 1e-9) | (t >= hi - 1e-9)
    # two-way-bottom-to-bottom: closed in the MIDDLE, open at both ends
    return (t >= lo - 1e-9) & (t <= hi + 1e-9)


def install(
    garment: GarmentMesh,
    points: np.ndarray,
    *,
    seam_id: str,
    spec: ZipperSpec | None = None,
    sliders: tuple[float, ...] | None = None,
) -> Zipper:
    """Fit a zipper to a seam declared `kind="zipper"` on the pattern.

    The pairing is already done - `build_garment` paired the two edges and
    kept them OUT of the sewn set. This turns that pairing into a chain: it
    measures where along the opening each pair sits, and that parameter is
    what a slider position is compared against.
    """
    spec = spec or ZipperSpec()
    if garment.hardware_pairs is None or seam_id not in garment.hardware_spans:
        known = ", ".join(sorted(garment.hardware_spans)) or "none"
        raise ValueError(
            f"no hardware opening called {seam_id!r} on this garment (have: {known}). "
            'A zipper needs its seam declared with kind="zipper" BEFORE the garment '
            "is built - a zipper is a pattern decision, not a drape decision."
        )
    lo, hi = garment.hardware_spans[seam_id]
    pairs = np.ascontiguousarray(garment.hardware_pairs[lo:hi], dtype=np.int32)
    if pairs.shape[0] < 2:
        raise ValueError(
            f"opening {seam_id!r} has {pairs.shape[0]} chain point(s); a zipper needs "
            "at least 2. Mesh the panel finer."
        )

    # Where each pair sits along the opening, 0 at the bottom stop. The chain
    # runs along the MIDLINE between the two edges, because that is where the
    # teeth are once it is closed.
    mid = 0.5 * (points[pairs[:, 0]] + points[pairs[:, 1]])
    steps = np.linalg.norm(np.diff(mid, axis=0), axis=1)
    run = np.concatenate([[0.0], np.cumsum(steps)])
    length = float(run[-1])
    if length <= 0.0:
        raise ValueError(f"opening {seam_id!r} has zero length")
    t = run / length

    # A zipper's t=0 is its BOTTOM STOP, and "bottom" means lower in the
    # world, not lower in the pair index. Getting this backwards puts the
    # slider at the hem when the user asked for it at the collar, and nothing
    # else in the pipeline would notice.
    if mid[-1, 1] < mid[0, 1]:
        order = np.arange(pairs.shape[0])[::-1]
        pairs, t = pairs[order], (1.0 - t[order])

    return Zipper(
        id=seam_id,
        spec=spec,
        pairs=pairs,
        t=np.ascontiguousarray(t, dtype=np.float64),
        length_m=length,
        sliders=_default_sliders(spec) if sliders is None else tuple(float(s) for s in sliders),
        trim=spec.trim(),
    )


def _default_sliders(spec: ZipperSpec) -> tuple[float, ...]:
    """Fully closed, whichever layout it is."""
    if spec.layout == "one-way":
        return (1.0,)
    if spec.layout == "two-way-head-to-head":
        return (0.5, 0.5)  # heads together in the middle: nothing open
    return (0.0, 1.0)  # bottom-to-bottom: both driven out to the ends


def unzip(zipper: Zipper, *, to: float, slider: int = 0) -> Zipper:
    """Drag one slider to `to` (0 = bottom stop, 1 = top) and return the zipper.

    This is the interactive gesture, and it is deliberately just a number: the
    GUI drags the slider mesh, the script calls this, the TEE adapter takes it
    as an argument, and all three go through the same code.
    """
    if not 0.0 <= to <= 1.0:
        raise ValueError(f"slider position must be within 0..1, got {to}")
    if not 0 <= slider < zipper.spec.sliders:
        raise ValueError(
            f"this {zipper.spec.layout} zipper has {zipper.spec.sliders} slider(s); "
            f"there is no slider {slider}"
        )
    moved = list(zipper.sliders)
    moved[slider] = float(to)
    zipper.sliders = tuple(moved)
    return zipper


def apply(garment: GarmentMesh, zipper: Zipper) -> GarmentMesh:
    """Write the CURRENTLY engaged part of the chain into the garment.

    Called again after every slider move. It replaces rather than appends,
    which is the reason attachments are named.
    """
    mask = zipper.engaged()
    engaged = zipper.pairs[mask]
    name = f"zip:{zipper.id}"
    bend_name = f"{name}:bend"
    if engaged.shape[0] == 0:
        garment.detach(name)
        garment.detach(bend_name)
        return garment

    # 1. the rungs: a closed zipper holds its two edges together, at the
    #    chain's own width and not at zero - the teeth have a size.
    gap = zipper.spec.size / 1000.0
    rung_rest = np.full(engaged.shape[0], gap, dtype=np.float64)

    # 2. the ladder. A closed zipper is a truss, not a hinge: the rungs are
    #    the engaged pairs, the stiles run along each tape, and the diagonals
    #    stop it shearing into a parallelogram.
    #
    #    Every rest length here comes from the CLOSED geometry, computed from
    #    the flat pattern - NOT from where the particles happen to be. The
    #    first version measured the braces in the current arrangement, which
    #    is the arrangement with the opening hanging OPEN, so the braces
    #    faithfully held it open: 50 engaged pairs sat at a 204 mm gap while a
    #    single engaged pair closed to 5.0 mm. A constraint that learns its
    #    rest length from a wrong pose preserves the wrong pose.
    rest2d = garment.rest_points_mm / 1000.0
    a, b = engaged[:-1, 0], engaged[:-1, 1]
    a1, b1 = engaged[1:, 0], engaged[1:, 1]
    stile_a = np.linalg.norm(rest2d[a] - rest2d[a1], axis=1)
    stile_b = np.linalg.norm(rest2d[b] - rest2d[b1], axis=1)
    step = 0.5 * (stile_a + stile_b)
    diagonal = np.sqrt(step**2 + gap**2)
    ladder = np.vstack(
        [
            np.stack([a, a1], axis=1),
            np.stack([b, b1], axis=1),
            np.stack([a, b1], axis=1),
            np.stack([b, a1], axis=1),
        ]
    ).astype(np.int32)
    ladder_rest = np.concatenate([stile_a, stile_b, diagonal, diagonal])

    pairs = np.vstack([engaged, ladder]) if ladder.shape[0] else engaged
    rest = np.concatenate([rung_rest, ladder_rest])

    # 3. the weight, spread over the particles the chain is sewn to. Only the
    #    engaged part? No - the tape and teeth are there whether the slider has
    #    passed or not. An unzipped zipper still weighs what it weighs.
    added = np.zeros(garment.n_points, dtype=np.float64)
    per_point = zipper.mass_kg() / max(len(zipper) * 2, 1)
    np.add.at(added, zipper.pairs.reshape(-1), per_point)

    # The ladder itself is rigid. A zipper does not stretch and it does not
    # shear, whatever it is made of - so the material's stiffness does NOT
    # live here, and putting it here does nothing measurable. (It was here
    # first: nylon and brass came out at sinuosity 1.107 and 1.124, because a
    # ladder of distance constraints is already rigid IN PLANE at both
    # compliances and hinges freely out of plane at both.)
    garment.attach(name, pairs, rest, compliance=0.0, added_mass=added, kind="zipper")

    # Where it does live: straighteners spanning i to i+2 along each tape.
    # These resist BENDING, in any direction, which is the whole difference
    # between a nylon coil you can coil round a finger and a brass chain you
    # cannot. A #5 brass chain gets 6.5x the resistance of the nylon coil the
    # ratio is referenced to.
    if engaged.shape[0] >= 3:
        a2, b2 = engaged[2:, 0], engaged[2:, 1]
        straight = np.vstack(
            [np.stack([a[:-1], a2], axis=1), np.stack([b[:-1], b2], axis=1)]
        ).astype(np.int32)
        straight_rest = np.concatenate([stile_a[:-1] + stile_a[1:], stile_b[:-1] + stile_b[1:]])
        garment.attach(
            bend_name,
            straight,
            straight_rest,
            compliance=_BEND_BASE / max(zipper.trim.stiffness, 1e-6),
            kind="zipper-bend",
        )
    else:
        garment.detach(bend_name)
    return garment


def geometry(zipper: Zipper, points: np.ndarray) -> dict[str, np.ndarray]:
    """The parts, as geometry: tape, teeth, slider, puller, stopper.

    Returned as point sets rather than a mesh because that is what every
    consumer needs - the GUI draws them, the exporter instances a box at each,
    and neither wants a triangle soup it has to re-derive positions from.
    """
    left = points[zipper.pairs[:, 0]]
    right = points[zipper.pairs[:, 1]]
    mid = 0.5 * (left + right)
    across = right - left
    norm = np.linalg.norm(across, axis=1, keepdims=True)
    across = across / np.maximum(norm, 1e-12)
    tape = zipper.spec.tape_mm / 1000.0

    # teeth at the material's real pitch, not one per particle
    pitch = zipper.trim.teeth_pitch_mm / 1000.0
    count = max(int(zipper.length_m / pitch), 1)
    at = np.linspace(0.0, 1.0, count)
    teeth = np.stack(
        [np.interp(at, zipper.t, mid[:, k]) for k in range(3)],
        axis=1,
    )
    # a coil is a helix and moulded teeth alternate sides; both read as an
    # alternating offset at this scale, which is what the half-pitch does
    side = np.stack([np.interp(at, zipper.t, across[:, k]) for k in range(3)], axis=1)
    teeth = teeth + side * ((np.arange(count) % 2) - 0.5).reshape(-1, 1) * zipper.spec.size / 1000.0

    def _at(u: float) -> np.ndarray:
        return np.asarray([np.interp(u, zipper.t, mid[:, k]) for k in range(3)])

    return {
        "tape_left": left - across * tape,
        "tape_right": right + across * tape,
        "chain": mid,
        "teeth": teeth,
        "sliders": np.asarray([_at(u) for u in zipper.sliders]),
        # the puller hangs BELOW the slider, which is how you can see at a
        # glance which way up a zipper was fitted
        "pullers": np.asarray(
            [
                _at(u) - np.asarray([0.0, zipper.spec.slider_mm()[0] / 1000.0, 0.0])
                for u in zipper.sliders
            ]
        ),
        "stops": np.asarray([_at(0.0), _at(1.0)]),
    }
