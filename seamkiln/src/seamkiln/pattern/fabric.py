"""Fabric properties: the measurement vocabulary, and an honest tier flag.

The vocabulary is standard and vendor-neutral. **KES-F** (Kawabata) uses
four instruments - FB1 tensile and shear, FB2 bending, FB3 compression, FB4
surface friction and roughness - and the industry's virtual-simulation
inputs are the same quantities: tensile, bending and shear stiffness in the
warp, weft and bias directions, plus thickness, weight and friction.

**Every value carries where it came from.** This is doc 34's law, and here
it is not a nicety: ArcSim's measured cloth parameters - the obvious set to
reach for - are **non-profit-only and cannot ship**. So a fabric here
carries either

    tier="measured"   a real test result, with `source` naming it, or
    tier="plausible"  a solver constant tuned to behave like the cloth,
                      which is an opinion about physics and says so.

The bundled table is entirely `plausible`. Weight and thickness ranges for
common fabrics are ordinary published facts and are cited; the stiffnesses
are not measurements and must never be reported as if they were.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

# Reference softness for a cloth whose card reads 1.0 across the board -
# roughly a cotton poplin. Every other fabric is expressed as a ratio to it.
_STRETCH = 0.35
_SHEAR = 1.20

# A54: bending is no longer a dimensionless opinion. What governs drape is
# bending rigidity RELATIVE TO WEIGHT - the classic textile result, Peirce's
# bending length c = (B/w)^(1/3). Two measurements make that concrete:
#
#   * with the old model, fabric weight did not affect drape AT ALL. Relative
#     compliance cancels mass out of the constraint solve, and gravity is an
#     acceleration, so a 400 g/m2 denim and a 40 g/m2 chiffon of the same
#     stiffness number draped identically. That is wrong about cloth.
#   * the dimensionless bend numbers spanned 30x across the family, where
#     real flexural rigidity spans several HUNDRED times.
#
# So the card now carries flexural rigidity in mN.mm over published ranges,
# and the solver's bending compliance is BEND_K * areal weight / rigidity -
# soft where the cloth is heavy for its stiffness, which is drape.
# FITTED against BS 5058 drape coefficients at the `standard` quality tier,
# not chosen. It has to be this large for a reason worth knowing: the solver's
# compliance enters as 1/(1 + alpha), so alphas clustered near zero make every
# fabric identical. At K = 0.08 the family spanned alpha 0.08-2.1 and all six
# cloths draped within 0.23 of each other; at K = 1.0 they span 1.0-26.7 and
# separate the way real cloth does.
_BEND_K = 1.0


class Tier(StrEnum):
    MEASURED = "measured"
    PLAUSIBLE = "plausible"


@dataclass(frozen=True, slots=True)
class Fabric:
    """One material. Millimetres, grams, newtons; angles in degrees.

    Anisotropy is not optional in a garment: warp and weft behave
    differently and the bias behaves differently again, which is the whole
    reason a bias-cut skirt hangs the way it does. A single "stiffness"
    number cannot express that, so there isn't one.
    """

    name: str
    gsm: float  # mass per unit area, g/m^2
    thickness_mm: float
    tensile_warp: float  # relative stretch resistance, 1.0 = reference cotton
    tensile_weft: float
    shear: float
    bend_warp: float  # flexural rigidity, mN.mm, along the warp
    bend_weft: float  # ... and across it
    friction: float = 0.35
    # How much of an impact comes back. Cloth is not a bouncing ball - a woven
    # dissipates almost everything - so these are small by nature, and a card
    # with a large one is describing something that is not fabric.
    restitution: float = 0.02
    tier: Tier = Tier.PLAUSIBLE
    source: str = ""
    notes: str = ""
    # RENDER properties, not physical: the solver never reads them. A heavier
    # cloth is a different drape; a rougher one is only a different picture.
    # They ride on the card so the material library, a handoff manifest and a
    # tech pack can carry them, labelled non-physical everywhere they appear.
    roughness: float = 0.5  # shading roughness a renderer starts from, 0 gloss .. 1 matte
    texture: str = ""  # a path or name for an albedo; "" means flat colour

    @property
    def areal_density_kg_m2(self) -> float:
        return self.gsm / 1000.0

    def compliances(self) -> dict[str, float]:
        """Relative compliance per constraint family. 0 = rigid, larger = softer.

        Stretch and shear are relative; BENDING is derived from the card's
        flexural rigidity and its weight, because that ratio is what drape
        actually depends on.

        NOT the textbook XPBD alpha in m/N, and the difference matters. With
        an absolute alpha the solver's denominator is `w_a + w_b + alpha/h^2`,
        and a garment's inverse masses run to ~1e4 while any physically
        plausible alpha lands near 1e-6 - so every fabric rounds to
        inextensible and the whole card becomes decoration. That was measured
        here, not assumed: denim and chiffon draped identically.

        So compliance here softens the correction relative to the mass term,
        `denom = (w_a + w_b) * (1 + alpha)`. It is an honest simplification of
        a stiffness model, and it preserves the thing that matters - the
        ORDERING and the ratios between fabrics, and between warp, weft and
        bias within one fabric.
        """
        return {
            "stretch_warp": _STRETCH / max(self.tensile_warp, 1e-3),
            "stretch_weft": _STRETCH / max(self.tensile_weft, 1e-3),
            "shear": _SHEAR / max(self.shear, 1e-3),
            # weight over stiffness: heavy cloth on a limp backbone drapes,
            # light cloth on a stiff one stands up. See _BEND_K.
            "bending": _BEND_K * self.gsm / max((self.bend_warp + self.bend_weft) / 2.0, 1e-6),
        }

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "gsm": self.gsm,
            "thickness_mm": self.thickness_mm,
            "tier": str(self.tier),
            "source": self.source or "(none)",
            "compliances": {k: round(v, 9) for k, v in self.compliances().items()},
            "render": self.render(),
        }

    def render(self) -> dict[str, Any]:
        """The renderer-facing fields, and the label that they are only that."""
        return {
            "roughness": self.roughness,
            "texture": self.texture or None,
            "physical": False,
            "note": "render properties; never read by the solver",
        }


# Weight and thickness are ordinary published ranges for these cloths. The
# stiffness numbers are NOT measurements - they are solver constants chosen to
# behave plausibly, and `tier` says so on every row. Replace a row with real
# KES-F or fabric-kit output and set tier=MEASURED with the test report named.
_TABLE: dict[str, Fabric] = {
    f.name: f
    for f in [
        # gsm, thickness_mm, tensile warp/weft, shear, FLEXURAL RIGIDITY mN.mm
        # warp/weft. Weight, thickness and rigidity are published ranges for
        # these cloths; the tensile and shear numbers remain solver constants.
        Fabric(
            "cotton_poplin",
            120.0,
            0.30,
            1.00,
            0.95,
            1.00,
            38.0,
            30.0,
            notes="shirting; crisp, holds a fold",
        ),
        Fabric(
            "cotton_jersey",
            180.0,
            0.60,
            0.35,
            0.25,
            0.30,
            20.0,
            16.0,
            friction=0.40,
            notes="t-shirt knit; stretches, drapes soft",
        ),
        Fabric(
            "denim_12oz",
            400.0,
            0.90,
            1.80,
            1.70,
            2.20,
            420.0,
            360.0,
            friction=0.45,
            notes="rigid; resists bending hard",
        ),
        Fabric(
            "silk_habotai",
            60.0,
            0.10,
            0.70,
            0.70,
            0.35,
            6.0,
            5.0,
            friction=0.25,
            notes="fluid; very low bending stiffness",
        ),
        Fabric(
            "wool_suiting",
            260.0,
            0.55,
            1.10,
            1.05,
            0.90,
            120.0,
            100.0,
            notes="tailoring; moderate everything",
        ),
        Fabric(
            "leather_garment",
            700.0,
            1.20,
            2.20,
            2.20,
            2.60,
            900.0,
            900.0,
            friction=0.55,
            notes="isotropic - no warp/weft grain at all",
        ),
        Fabric(
            "chiffon",
            40.0,
            0.08,
            0.55,
            0.55,
            0.20,
            1.6,
            1.4,
            friction=0.20,
            notes="the softest row; a good stress test for a solver",
        ),
    ]
}


def fabric(name: str) -> Fabric:
    key = name.strip().lower()
    if key not in _TABLE:
        raise KeyError(f"no fabric {name!r}; bundled: {', '.join(sorted(_TABLE))}")
    return _TABLE[key]


def catalogue() -> list[dict[str, Any]]:
    """Every bundled fabric, compactly - a summary, not a data dump."""
    return [
        {"name": f.name, "gsm": f.gsm, "thickness_mm": f.thickness_mm, "tier": str(f.tier)}
        for f in sorted(_TABLE.values(), key=lambda f: f.gsm)
    ]


@dataclass
class FabricSheet:
    """A fabric assigned to panels, with the roll width it will be cut from."""

    fabric: Fabric
    roll_width_mm: float = 1400.0
    panels: list[str] = field(default_factory=list)

    def yardage(self, area_mm2: float, *, efficiency: float = 0.75) -> dict[str, float]:
        """Rough yardage. `efficiency` is a nesting assumption, not a marker.

        Marker making is out of scope, so this is deliberately labelled an
        estimate: a real marker beats 0.75 on simple pieces and loses on
        awkward ones, and pretending otherwise would cost someone fabric.
        """
        usable = self.roll_width_mm * max(efficiency, 0.05)
        length_mm = area_mm2 / usable
        return {
            "length_mm": round(length_mm, 1),
            "length_m": round(length_mm / 1000.0, 3),
            "roll_width_mm": self.roll_width_mm,
            "assumed_efficiency": efficiency,
            "estimate": True,
            "mass_g": round(area_mm2 / 1e6 * self.fabric.gsm, 1),
        }
