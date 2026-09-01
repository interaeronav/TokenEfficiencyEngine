"""A real, sewable sample pattern - the tee block.

Shipped rather than kept in tests, because everything downstream needs
something to chew on: the DXF round-trip, the plotter, the drape kernel and
the benchmarks all want the same four pieces so their numbers compare.

Dimensions are millimetres and roughly a men's medium. It is a block, not a
graded production pattern: the point is that it has every feature the
interchange format has to carry - curves and corners, notches, a grain line,
a fold line, internal lines and a dart - not that it would win a fitting.
"""

from __future__ import annotations

from seamkiln.pattern.geometry import Vertex, cubic, join, line
from seamkiln.pattern.model import (
    EdgeRef,
    InternalLine,
    LineKind,
    Mark,
    MarkKind,
    Panel,
    Pattern,
    Seam,
)

SLEEVE_HEAD_EASE = 219.3 / 214.8  # measured off this block, not a rule of thumb


def _front_outline(half_chest: float, length: float, shoulder: float, neck: float) -> list[Vertex]:
    hem_r = (half_chest, 0.0)
    underarm_r = (half_chest, length * 0.60)
    shoulder_r = (shoulder, length * 0.88)
    neck_r = (neck, length * 0.94)
    neck_l = (-neck, length * 0.94)
    shoulder_l = (-shoulder, length * 0.88)
    underarm_l = (-half_chest, length * 0.60)
    hem_l = (-half_chest, 0.0)
    return join(
        line(hem_l, hem_r),
        line(hem_r, underarm_r),
        # armhole: hollow curve from underarm up to the shoulder tip
        cubic(underarm_r, (half_chest, length * 0.78), (shoulder + 26, length * 0.79), shoulder_r),
        line(shoulder_r, neck_r),
        # front neckline: scooped, deeper than the back
        cubic(neck_r, (neck * 0.6, length * 0.855), (-neck * 0.6, length * 0.855), neck_l),
        line(neck_l, shoulder_l),
        cubic(
            shoulder_l, (-shoulder - 26, length * 0.79), (-half_chest, length * 0.78), underarm_l
        ),
        line(underarm_l, hem_l),
    )


def _back_outline(half_chest: float, length: float, shoulder: float, neck: float) -> list[Vertex]:
    outline = _front_outline(half_chest, length, shoulder, neck)
    # the back neck is high and shallow - swap that one run for a flatter curve
    neck_r = (neck, length * 0.94)
    neck_l = (-neck, length * 0.94)
    flat = cubic(neck_r, (neck * 0.6, length * 0.925), (-neck * 0.6, length * 0.925), neck_l)
    start = next(
        i
        for i, v in enumerate(outline)
        if abs(v.x - neck_r[0]) < 1e-6 and abs(v.y - neck_r[1]) < 1e-6
    )
    end = next(
        i
        for i, v in enumerate(outline)
        if i > start and abs(v.x - neck_l[0]) < 1e-6 and abs(v.y - neck_l[1]) < 1e-6
    )
    return [*outline[:start], *flat, *outline[end + 1 :]]


def _sleeve_outline(cap_width: float, cap_height: float, length: float, cuff: float):
    left = (-cap_width, 0.0)
    right = (cap_width, 0.0)
    return join(
        # the cap: an S-curve over the top, from underarm to underarm
        cubic(
            left,
            (-cap_width * 0.55, cap_height * 1.25),
            (-cap_width * 0.2, cap_height),
            (0.0, cap_height),
        ),
        cubic(
            (0.0, cap_height),
            (cap_width * 0.2, cap_height),
            (cap_width * 0.55, cap_height * 1.25),
            right,
        ),
        line(right, (cuff, -length)),
        line((cuff, -length), (-cuff, -length)),
        line((-cuff, -length), left),
    )


def tee_block(
    *,
    half_chest: float = 260.0,
    length: float = 700.0,
    shoulder: float = 185.0,
    neck: float = 80.0,
) -> Pattern:
    """Front, back and two sleeves, sewn together. Millimetres."""
    front = Panel(
        id="FRONT",
        name="Front",
        outline=_front_outline(half_chest, length, shoulder, neck),
        internals=[
            InternalLine(LineKind.GRAIN, [Vertex(0.0, 60.0), Vertex(0.0, length * 0.8)]),
            InternalLine(LineKind.MIRROR, [Vertex(0.0, 0.0), Vertex(0.0, length * 0.94)]),
        ],
        marks=[
            Mark(MarkKind.NOTCH_SLIT, 0.0, 0.0, depth=6.0),  # centre front at the hem
            Mark(MarkKind.NOTCH_V, half_chest, length * 0.60, depth=6.0),  # right underarm
            Mark(MarkKind.NOTCH_V, -half_chest, length * 0.60, depth=6.0),  # left underarm
        ],
    )
    back = Panel(
        id="BACK",
        name="Back",
        outline=_back_outline(half_chest, length, shoulder, neck),
        internals=[
            InternalLine(LineKind.GRAIN, [Vertex(0.0, 60.0), Vertex(0.0, length * 0.8)]),
        ],
        marks=[
            Mark(MarkKind.NOTCH_SLIT, 0.0, 0.0, depth=6.0),
            Mark(MarkKind.NOTCH_V, half_chest, length * 0.60, depth=6.0),
            Mark(MarkKind.NOTCH_V, -half_chest, length * 0.60, depth=6.0),
            Mark(MarkKind.DRILL, 0.0, length * 0.5, diameter=3.0),
        ],
    )
    sleeves = [
        Panel(
            id=f"SLEEVE_{side}",
            name=f"Sleeve {side.lower()}",
            outline=_sleeve_outline(150.0, 130.0, 220.0, 120.0),
            internals=[
                InternalLine(LineKind.GRAIN, [Vertex(0.0, 100.0), Vertex(0.0, -180.0)]),
            ],
            marks=[Mark(MarkKind.NOTCH_V, 0.0, 130.0, depth=6.0)],  # cap crown
        )
        for side in ("L", "R")
    ]

    pattern = Pattern(name="tee-block", panels=[front, back, *sleeves], units="mm")

    # Edge indices after the outline is normalised counter-clockwise:
    #   body    0 hem | 1 side R | 2 armhole R | 3 shoulder R | 4 neck |
    #           5 shoulder L | 6 armhole L | 7 side L
    #   sleeve  0 cuff | 1 underarm R | 2 cap front-half | 3 cap back-half |
    #           4 underarm L
    #
    # THE BACK PANEL IS MIRRORED WHEN WORN. You look at a back panel from
    # behind, so its pattern-right edge is the body's LEFT. Pairing FRONT#1
    # with BACK#1 therefore sews the front's right side to the back's right-
    # in-pattern, which is the body's left, and wraps the garment round the
    # wearer. Measured: the left sleeve was being sewn to the right half of
    # the back armhole, a point at x = -0.099 paired with one at x = +0.105,
    # and that ONE seam accounted for a 211 mm maximum gap. Mirroring the back
    # indices took the garment's worst seam gap from 211 mm to 48 mm.
    #
    # It also cost a wrong conclusion before it was found: the gap looked like
    # a resolution problem, and it is not - it was identical from 26 mm down
    # to 9 mm particle distance, which is exactly what a topology bug looks
    # like and what a convergence problem does not.
    #
    # The cap halves measure 219.3 mm against a 214.8 mm armhole. That 2.1% is
    # sleeve-head EASE - the fullness a set-in sleeve needs to turn the corner
    # over the shoulder - so it is declared as `gather`, not left to show up as
    # a 4.5 mm drafting error in every report.
    ease = SLEEVE_HEAD_EASE
    pattern.seams = [
        Seam(EdgeRef("FRONT", 1), EdgeRef("BACK", 7), id="side-right"),
        Seam(EdgeRef("FRONT", 7), EdgeRef("BACK", 1), id="side-left"),
        Seam(EdgeRef("FRONT", 3), EdgeRef("BACK", 5), id="shoulder-right"),
        Seam(EdgeRef("FRONT", 5), EdgeRef("BACK", 3), id="shoulder-left"),
        Seam(EdgeRef("SLEEVE_R", 2), EdgeRef("FRONT", 2), gather=ease, id="armhole-right-front"),
        Seam(EdgeRef("SLEEVE_R", 3), EdgeRef("BACK", 6), gather=ease, id="armhole-right-back"),
        Seam(EdgeRef("SLEEVE_L", 2), EdgeRef("FRONT", 6), gather=ease, id="armhole-left-front"),
        Seam(EdgeRef("SLEEVE_L", 3), EdgeRef("BACK", 2), gather=ease, id="armhole-left-back"),
        Seam(EdgeRef("SLEEVE_R", 1), EdgeRef("SLEEVE_R", 4), id="underarm-right"),
        Seam(EdgeRef("SLEEVE_L", 1), EdgeRef("SLEEVE_L", 4), id="underarm-left"),
    ]
    return pattern


def _half_front_outline(
    half_chest: float, length: float, shoulder: float, neck: float, side: float
) -> list[Vertex]:
    """One half of a front, split down the centre. `side` is +1 (wearer's
    right half as drafted) or -1.

    The centre-front edge is a straight line from hem to neck and is edge 3
    once the outline is normalised counter-clockwise. That is the edge a
    zipper or a button placket lands on, and it is straight on purpose: a
    curved opening needs a curved chain, and a chain does not curve.
    """
    hem_cf = (0.0, 0.0)
    hem_out = (side * half_chest, 0.0)
    underarm = (side * half_chest, length * 0.60)
    shoulder_pt = (side * shoulder, length * 0.88)
    neck_pt = (side * neck, length * 0.94)
    neck_cf = (0.0, length * 0.855)
    ring = join(
        line(hem_cf, hem_out),
        line(hem_out, underarm),
        cubic(
            underarm,
            (side * half_chest, length * 0.78),
            (side * (shoulder + 26), length * 0.79),
            shoulder_pt,
        ),
        line(shoulder_pt, neck_pt),
        cubic(neck_pt, (side * neck * 0.6, length * 0.855), neck_cf, neck_cf),
        line(neck_cf, hem_cf),
    )
    return ring


def jacket_block(
    *,
    half_chest: float = 275.0,
    length: float = 700.0,
    shoulder: float = 190.0,
    neck: float = 85.0,
    opening: str = "zipper",
) -> Pattern:
    """A tee block cut down the centre front, so it has an OPENING.

    Everything hardware needs a garment to have, a tee block does not have:
    two edges that face each other and are not sewn. This is the smallest
    pattern that does. `opening` declares what fills it - "zipper" or
    "placket" (buttons) - and either way the centre-front seam is built
    PAIRED but NOT SEWN, which is what makes it an opening rather than a seam.
    """
    if opening not in ("zipper", "placket"):
        raise ValueError(f"opening must be 'zipper' or 'placket', got {opening!r}")
    fronts = [
        Panel(
            id=f"FRONT_{tag}",
            name=f"Front {tag.lower()}",
            outline=_half_front_outline(half_chest, length, shoulder, neck, side),
            internals=[
                InternalLine(
                    LineKind.GRAIN, [Vertex(side * 90.0, 60.0), Vertex(side * 90.0, 520.0)]
                )
            ],
            marks=[Mark(MarkKind.NOTCH_V, side * half_chest, length * 0.60, depth=6.0)],
        )
        for tag, side in (("R", 1.0), ("L", -1.0))
    ]
    back = Panel(
        id="BACK",
        name="Back",
        outline=_back_outline(half_chest, length, shoulder, neck),
        internals=[InternalLine(LineKind.GRAIN, [Vertex(0.0, 60.0), Vertex(0.0, length * 0.8)])],
        marks=[
            Mark(MarkKind.NOTCH_V, half_chest, length * 0.60, depth=6.0),
            Mark(MarkKind.NOTCH_V, -half_chest, length * 0.60, depth=6.0),
        ],
    )
    sleeves = [
        Panel(
            id=f"SLEEVE_{side}",
            name=f"Sleeve {side.lower()}",
            outline=_sleeve_outline(150.0, 130.0, 220.0, 120.0),
            internals=[InternalLine(LineKind.GRAIN, [Vertex(0.0, 100.0), Vertex(0.0, -180.0)])],
            marks=[Mark(MarkKind.NOTCH_V, 0.0, 130.0, depth=6.0)],
        )
        for side in ("L", "R")
    ]
    pattern = Pattern(name=f"jacket-block-{opening}", panels=[*fronts, back, *sleeves], units="mm")

    #   FRONT_R  0 hem | 1 side | 2 armhole | 3 shoulder | 4 neck | 5 CF
    #   FRONT_L  0 neck | 1 shoulder | 2 armhole | 3 side | 4 hem | 5 CF
    #
    # The left half's indices are the right half's REVERSED, and that is not
    # a bug to work around: mirroring a ring reverses its winding, and the
    # outline normaliser turns it back counter-clockwise by walking it the
    # other way. A half-front is the smallest place this shows up, so it is
    # spelled out here rather than discovered again on a real garment.
    #
    #   back     as the tee block: 0 hem | 1 side R | 2 armhole R |
    #            3 shoulder R | 4 neck | 5 shoulder L | 6 armhole L |
    #            7 side L    ... and it is MIRRORED when worn, see above.
    #
    # No sleeve-head ease is declared here, unlike the tee block. This block's
    # armhole measures 219.4 mm against a 219.3 mm cap - they already match,
    # because the wider half-chest lengthened the armhole to meet the same
    # sleeve. Declaring the tee's 2.1% anyway would put a 4.6 mm "mismatch"
    # in every true_up report for a seam that is drafted correctly.
    pattern.seams = [
        Seam(EdgeRef("FRONT_R", 1), EdgeRef("BACK", 7), id="side-right"),
        Seam(EdgeRef("FRONT_L", 3), EdgeRef("BACK", 1), id="side-left"),
        Seam(EdgeRef("FRONT_R", 3), EdgeRef("BACK", 5), id="shoulder-right"),
        Seam(EdgeRef("FRONT_L", 1), EdgeRef("BACK", 3), id="shoulder-left"),
        Seam(EdgeRef("SLEEVE_R", 2), EdgeRef("FRONT_R", 2), id="armhole-right-front"),
        Seam(EdgeRef("SLEEVE_R", 3), EdgeRef("BACK", 6), id="armhole-right-back"),
        Seam(EdgeRef("SLEEVE_L", 2), EdgeRef("FRONT_L", 2), id="armhole-left-front"),
        Seam(EdgeRef("SLEEVE_L", 3), EdgeRef("BACK", 2), id="armhole-left-back"),
        Seam(EdgeRef("SLEEVE_R", 1), EdgeRef("SLEEVE_R", 4), id="underarm-right"),
        Seam(EdgeRef("SLEEVE_L", 1), EdgeRef("SLEEVE_L", 4), id="underarm-left"),
        # The opening. Paired so the two edges know which point faces which,
        # and NOT sewn, which is what `kind` buys.
        Seam(EdgeRef("FRONT_R", 5), EdgeRef("FRONT_L", 5), id="centre-front", kind=opening),
    ]
    return pattern


__all__ = ["SLEEVE_HEAD_EASE", "jacket_block", "tee_block"]
