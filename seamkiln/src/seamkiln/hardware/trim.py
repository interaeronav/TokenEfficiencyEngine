"""What trim is made of, and what that costs in grams and stiffness.

Every number here is a TRADE figure - a catalogue mass, a handbook density -
not something this project measured, and the tier says so on every card. That
distinction is the same one `fabric.py` makes and for the same reason: a
plausible constant that gets quoted as a measurement is how a spec sheet
starts lying.

The three zipper materials are the three the industry actually sells:

  nylon    a coiled monofilament helix sewn to the tape. The most flexible,
           the lightest, and self-healing - a coil that pops back together.
  plastic  moulded acetal (POM) teeth, injected onto the tape. Stiffer and
           blockier than coil; the "Vislon" style.
  metal    stamped brass or aluminium teeth clamped on. Heaviest by a factor
           of three, stiffest, and the only one that will not self-heal.

Zipper SIZE is the closed chain width in millimetres, which is why a #5 is
about 5 mm across the teeth. Mass scales with the cross-section, so it goes
as the square of the size - a #10 brass chain is four times the metal of a #5.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from seamkiln.pattern.fabric import Tier


@dataclass(frozen=True, slots=True)
class Trim:
    """One hardware material."""

    name: str
    density_kg_m3: float
    # chain + both tapes, grams per metre, at the REFERENCE size 5
    chain_g_per_m: float
    slider_g: float  # one slider body, at size 5
    # How hard the closed chain is to bend, relative to a #5 nylon coil.
    # It is a ratio and not a rigidity in mN.mm because what the solver needs
    # is a compliance, and a ratio is the honest form of a number nobody here
    # put on a bending tester.
    stiffness: float
    teeth_pitch_mm: float
    self_healing: bool
    tier: Tier = Tier.PLAUSIBLE
    source: str = ""

    def at_size(self, size: float) -> Trim:
        """The same material in another zipper size (#3, #5, #8, #10)."""
        scale = (float(size) / 5.0) ** 2
        return replace(
            self,
            chain_g_per_m=self.chain_g_per_m * scale,
            slider_g=self.slider_g * scale,
            stiffness=self.stiffness * scale,
        )

    def chain_kg_per_m(self) -> float:
        return self.chain_g_per_m / 1000.0


ZIPPER_TRIM: dict[str, Trim] = {
    "nylon": Trim(
        name="nylon",
        density_kg_m3=1140.0,
        chain_g_per_m=10.0,
        slider_g=1.4,
        stiffness=1.0,
        teeth_pitch_mm=3.2,
        self_healing=True,
        source="polyamide 6 handbook density; chain mass from trade catalogue ranges",
    ),
    "plastic": Trim(
        name="plastic",
        density_kg_m3=1410.0,
        chain_g_per_m=16.0,
        slider_g=1.6,
        stiffness=2.6,
        teeth_pitch_mm=4.5,
        self_healing=False,
        source="polyoxymethylene handbook density; chain mass from trade catalogue ranges",
    ),
    "metal": Trim(
        name="metal",
        density_kg_m3=8500.0,
        chain_g_per_m=33.0,
        slider_g=3.6,
        stiffness=6.5,
        teeth_pitch_mm=4.2,
        self_healing=False,
        source="brass handbook density; chain mass from trade catalogue ranges",
    ),
}

# Buttons are sold by LIGNE, not millimetres: 1 ligne = 0.635 mm, so the
# 24L on a shirt front is 15.2 mm across. The unit is worth carrying because
# every button supplier quotes it and nobody quotes millimetres.
MM_PER_LIGNE = 0.635


BUTTON_TRIM: dict[str, Trim] = {
    "polyester": Trim(
        name="polyester",
        density_kg_m3=1380.0,
        chain_g_per_m=0.0,
        slider_g=0.0,
        stiffness=2.0,
        teeth_pitch_mm=0.0,
        self_healing=False,
        source="cast polyester resin handbook density; the shirt-button default",
    ),
    "corozo": Trim(
        name="corozo",
        density_kg_m3=1300.0,
        chain_g_per_m=0.0,
        slider_g=0.0,
        stiffness=2.0,
        teeth_pitch_mm=0.0,
        self_healing=False,
        source="tagua nut density, handbook range 1.2-1.4 g/cm3",
    ),
    "horn": Trim(
        name="horn",
        density_kg_m3=1300.0,
        chain_g_per_m=0.0,
        slider_g=0.0,
        stiffness=2.0,
        teeth_pitch_mm=0.0,
        self_healing=False,
        source="keratin density, handbook range 1.25-1.35 g/cm3",
    ),
    "metal": Trim(
        name="metal",
        density_kg_m3=8500.0,
        chain_g_per_m=0.0,
        slider_g=0.0,
        stiffness=6.5,
        teeth_pitch_mm=0.0,
        self_healing=False,
        source="brass handbook density",
    ),
    "shell": Trim(
        name="shell",
        density_kg_m3=2700.0,
        chain_g_per_m=0.0,
        slider_g=0.0,
        stiffness=3.0,
        teeth_pitch_mm=0.0,
        self_healing=False,
        source="nacre/aragonite density, handbook 2.6-2.8 g/cm3",
    ),
}


def zipper_trim(name: str, size: float = 5.0) -> Trim:
    try:
        return ZIPPER_TRIM[name].at_size(size)
    except KeyError:
        raise ValueError(
            f"unknown zipper material {name!r}. Known: {', '.join(sorted(ZIPPER_TRIM))}"
        ) from None


def button_trim(name: str) -> Trim:
    try:
        return BUTTON_TRIM[name]
    except KeyError:
        raise ValueError(
            f"unknown button material {name!r}. Known: {', '.join(sorted(BUTTON_TRIM))}"
        ) from None
