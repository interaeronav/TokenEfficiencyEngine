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
    bend_warp: float
    bend_weft: float
    friction: float = 0.35
    tier: Tier = Tier.PLAUSIBLE
    source: str = ""
    notes: str = ""

    @property
    def areal_density_kg_m2(self) -> float:
        return self.gsm / 1000.0

    def compliances(self) -> dict[str, float]:
        """XPBD compliance (inverse stiffness) per constraint family.

        The mapping from a fabric card to solver constants is the place where
        a number stops being a measurement, so it is one function, named, and
        the tier travels with the result.
        """
        return {
            "structural": 0.0 if self.tensile_warp >= 1.0 else 1e-6 / max(self.tensile_warp, 1e-3),
            "shear": 5e-6 / max(self.shear, 1e-3),
            "bending": 2e-5 / max((self.bend_warp + self.bend_weft) / 2, 1e-3),
        }

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "gsm": self.gsm,
            "thickness_mm": self.thickness_mm,
            "tier": str(self.tier),
            "source": self.source or "(none)",
            "compliances": {k: round(v, 9) for k, v in self.compliances().items()},
        }


# Weight and thickness are ordinary published ranges for these cloths. The
# stiffness numbers are NOT measurements - they are solver constants chosen to
# behave plausibly, and `tier` says so on every row. Replace a row with real
# KES-F or fabric-kit output and set tier=MEASURED with the test report named.
_TABLE: dict[str, Fabric] = {
    f.name: f
    for f in [
        Fabric(
            "cotton_poplin",
            120.0,
            0.30,
            1.00,
            0.95,
            1.00,
            1.00,
            1.05,
            notes="shirting; crisp, holds a fold",
        ),
        Fabric(
            "cotton_jersey",
            180.0,
            0.60,
            0.35,
            0.25,
            0.30,
            0.45,
            0.40,
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
            3.00,
            3.20,
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
            0.20,
            0.20,
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
            1.40,
            1.45,
            notes="tailoring; moderate everything",
        ),
        Fabric(
            "leather_garment",
            700.0,
            1.20,
            2.20,
            2.20,
            2.60,
            3.50,
            3.50,
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
            0.10,
            0.10,
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
