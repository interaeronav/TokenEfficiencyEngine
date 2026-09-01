"""The test room: gravity, wind, temperature, pressure, humidity.

Every one of these is a real lever on how cloth behaves, and every one is
modelled here with its provenance attached, because the difference between
"we simulate temperature" and "we simulate temperature *honestly*" is whether
the number came from somewhere.

  gravity      exact. A vector, so it can point anywhere and be any strength -
               moon gravity, a centrifuge, or sideways.
  air density  exact, from the ideal gas law with a humidity correction.
               p / (R_d T) with the vapour partial pressure removed.
  wind         a drag force per triangle, F = 1/2 rho Cd A |v_rel|^2, applied
               along the surface normal. Real aerodynamics for a thin sheet is
               harder than this; this is the standard cloth-simulation model
               and it is labelled as such.
  temperature  and humidity act through MOISTURE REGAIN - how much water a
  humidity     fibre holds at a given relative humidity. That part is
               measured: the regain figures are published constants and the
               conditioning atmosphere (20 C, 65% RH) is ISO 139. How regain
               changes stiffness is a plausible coupling, flagged as one.

The default is the textile standard atmosphere, so an unconfigured drape is
conditioned the way a laboratory would condition a specimen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

# ISO 139 standard atmosphere for testing textiles.
STANDARD_TEMPERATURE_C = 20.0
STANDARD_HUMIDITY = 0.65
STANDARD_PRESSURE_KPA = 101.325

R_DRY_AIR = 287.058  # J/(kg K)
R_VAPOUR = 461.495  # J/(kg K)
EARTH_G = 9.80665  # m/s^2, the standard value

# Published moisture regain at the standard atmosphere (20 C, 65% RH), as a
# fraction of oven-dry mass. Textbook constants, not measurements of ours.
REGAIN_AT_65: dict[str, float] = {
    "cotton": 0.085,
    "wool": 0.160,
    "silk": 0.110,
    "linen": 0.120,
    "viscose": 0.130,
    "nylon": 0.045,
    "polyester": 0.004,
    "acrylic": 0.020,
    "leather": 0.150,
    "unknown": 0.060,
}

# Gravity elsewhere, for the "change the gravity effect" lever. Values are
# standard surface gravities; naming them beats a bare float nobody can check.
GRAVITY_PRESETS: dict[str, float] = {
    "earth": EARTH_G,
    "moon": 1.625,
    "mars": 3.721,
    "jupiter": 24.79,
    "zero": 0.0,
    "half": EARTH_G / 2.0,
    "double": EARTH_G * 2.0,
}


@dataclass(slots=True)
class Environment:
    """The room the garment is tested in."""

    gravity: float = EARTH_G  # m/s^2, magnitude
    gravity_direction: tuple[float, float, float] = (0.0, -1.0, 0.0)
    wind: tuple[float, float, float] = (0.0, 0.0, 0.0)  # m/s
    wind_gust: float = 0.0  # 0..1, fraction of `wind` that varies over time
    temperature_c: float = STANDARD_TEMPERATURE_C
    humidity: float = STANDARD_HUMIDITY  # relative, 0..1
    pressure_kpa: float = STANDARD_PRESSURE_KPA
    drag_coefficient: float = 1.2  # flat plate normal to flow
    name: str = "standard atmosphere"

    @classmethod
    def preset(cls, gravity: str = "earth", **kwargs: Any) -> Environment:
        if gravity not in GRAVITY_PRESETS:
            raise ValueError(
                f"no gravity preset {gravity!r}; known: {', '.join(GRAVITY_PRESETS)}. "
                "Or pass gravity=<m/s^2> directly."
            )
        return cls(gravity=GRAVITY_PRESETS[gravity], name=f"{gravity} gravity", **kwargs)

    # -- exact physics ------------------------------------------------------

    def gravity_vector(self) -> np.ndarray:
        direction = np.asarray(self.gravity_direction, dtype=np.float64)
        norm = float(np.linalg.norm(direction))
        if norm < 1e-12:
            return np.zeros(3)
        return direction / norm * self.gravity

    def saturation_vapour_pressure_kpa(self) -> float:
        """Tetens' equation over water. Good to ~0.1% between 0 and 50 C."""
        t = self.temperature_c
        return 0.61078 * np.exp(17.27 * t / (t + 237.3))

    def air_density(self) -> float:
        """kg/m^3, from the ideal gas law with the vapour partial pressure
        split out. Moist air is LIGHTER than dry air at the same pressure -
        water is lighter than nitrogen - which surprises people often enough
        to be worth the comment."""
        temperature_k = self.temperature_c + 273.15
        vapour = self.humidity * self.saturation_vapour_pressure_kpa()
        dry = max(self.pressure_kpa - vapour, 0.0)
        return (dry * 1000.0) / (R_DRY_AIR * temperature_k) + (vapour * 1000.0) / (
            R_VAPOUR * temperature_k
        )

    # -- conditioning: the plausible half, flagged --------------------------

    def regain(self, fibre: str) -> float:
        """Moisture regain at THIS humidity, from the published value at 65%.

        Interpolated with a sigmoid in relative humidity, which is the shape a
        real sorption isotherm has; the anchor is measured, the curve between
        anchors is not, and `conditioning()` says so.
        """
        anchor = REGAIN_AT_65.get(fibre.lower(), REGAIN_AT_65["unknown"])
        humidity = min(max(self.humidity, 0.0), 1.0)
        shape = humidity / (0.35 + 0.65 * humidity)  # 0 at 0% RH, 1.0 at 100%
        reference = 0.65 / (0.35 + 0.65 * 0.65)
        return anchor * shape / reference

    def conditioning(self, fibre: str = "cotton") -> dict[str, Any]:
        """How this room changes a fabric's weight and its stiffness."""
        regain = self.regain(fibre)
        # heavier by the water it holds - exact, once regain is known
        mass_factor = 1.0 + regain
        # and softer: natural fibres lose bending rigidity as they take up
        # water, and warm cloth is limper than cold cloth. Both directions are
        # real; these coefficients are chosen, not measured.
        moisture_softening = 1.0 + 2.2 * (regain - REGAIN_AT_65.get(fibre.lower(), 0.06))
        warmth_softening = 1.0 + 0.004 * (self.temperature_c - STANDARD_TEMPERATURE_C)
        return {
            "fibre": fibre,
            "regain": round(regain, 4),
            "mass_factor": round(mass_factor, 4),
            "compliance_factor": round(max(moisture_softening * warmth_softening, 0.2), 4),
            "tier": {
                "regain_at_65": "measured (published constant)",
                "regain_curve": "plausible (sigmoid between anchors)",
                "softening": "plausible (chosen coefficients)",
            },
        }

    def describe(self) -> dict[str, Any]:
        gravity = self.gravity_vector()
        return {
            "name": self.name,
            "gravity_ms2": round(self.gravity, 4),
            "gravity_vector": [round(float(v), 4) for v in gravity],
            "gravity_vs_earth": round(self.gravity / EARTH_G, 3),
            "wind_ms": [round(float(v), 3) for v in self.wind],
            "wind_speed_ms": round(float(np.linalg.norm(self.wind)), 3),
            "wind_gust": self.wind_gust,
            "temperature_c": self.temperature_c,
            "humidity_pct": round(self.humidity * 100.0, 1),
            "pressure_kpa": round(self.pressure_kpa, 3),
            "air_density_kg_m3": round(self.air_density(), 4),
            "standard_atmosphere": bool(
                abs(self.temperature_c - STANDARD_TEMPERATURE_C) < 0.51
                and abs(self.humidity - STANDARD_HUMIDITY) < 0.011
                and abs(self.pressure_kpa - STANDARD_PRESSURE_KPA) < 0.11
            ),
        }


STANDARD = Environment()


@dataclass(slots=True)
class WindField:
    """Wind sampled per substep, so a gust is not a constant.

    Deterministic by construction: the gust is a fixed sum of sinusoids in
    the substep index, not a random draw. A drape that cannot repeat itself
    cannot be benchmarked (law 7), and "it was windy" is not an excuse.
    """

    base: np.ndarray
    gust: float = 0.0

    @classmethod
    def of(cls, environment: Environment) -> WindField:
        return cls(np.asarray(environment.wind, dtype=np.float64), float(environment.wind_gust))

    def at(self, step: int) -> np.ndarray:
        if self.gust <= 0.0:
            return self.base
        phase = step * 0.037
        wobble = (
            0.6 * np.sin(phase) + 0.3 * np.sin(phase * 2.7 + 1.1) + 0.1 * np.sin(phase * 6.1 + 2.4)
        )
        return self.base * (1.0 + self.gust * wobble)

    def samples(self, count: int) -> np.ndarray:
        """The whole schedule up front - the kernel takes an array, not a
        callback, because a Python callback per substep would cost more than
        the wind does."""
        return np.asarray([self.at(step) for step in range(max(count, 1))], dtype=np.float64)
