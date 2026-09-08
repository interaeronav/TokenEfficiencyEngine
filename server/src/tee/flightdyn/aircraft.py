"""Write a JSBSim aircraft from a polar and a mass.

The seam this lane exists for: a `wt_sweep` polar is Cl, Cd (and optionally Cm)
over angle of attack, and a JSBSim `<aerodynamics>` axis is a one-dimensional
table over `aero/alpha-rad`. They are the same object in two notations.

Everything here is stdlib and writes text. Units go on the wire in SI, with the
unit always written: JSBSim reads `M`, `M2`, `KG`, `KG*M2` and converts, which
was measured rather than assumed (doc 76 section 2.1) - so the generator never
converts and never has a factor to get wrong.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from tee.kernel.errors import TeeError

#: JSBSim's own limit for a sensible 1-D table, and ours for a reply.
MAX_POLAR_POINTS = 64
GRAVITY = 9.80665


@dataclass(frozen=True)
class Polar:
    """What `wt_sweep` returns, in the units it returns them in."""

    alpha_deg: tuple[float, ...]
    cl: tuple[float, ...]
    cd: tuple[float, ...]
    cm_alpha: float = -0.5  # per radian, about the aero reference point
    cm_q: float = -12.0  # pitch damping, per radian
    cm_de: float = -1.1  # control power, per radian of elevator
    source: str = "given"

    def __post_init__(self) -> None:
        n = len(self.alpha_deg)
        if n < 2:
            raise TeeError(
                "fd_polar_short",
                f"A polar needs at least 2 points; got {n}.",
                fix="Give alpha_deg/cl/cd of equal length, or a wt_sweep case id.",
            )
        if not (n == len(self.cl) == len(self.cd)):
            raise TeeError(
                "fd_polar_ragged",
                f"alpha_deg/cl/cd have lengths {n}/{len(self.cl)}/{len(self.cd)}.",
                fix="All three must be the same length.",
            )
        if n > MAX_POLAR_POINTS:
            raise TeeError(
                "fd_polar_long",
                f"A polar of {n} points exceeds the {MAX_POLAR_POINTS}-point limit.",
                fix=f"Sample the sweep down to {MAX_POLAR_POINTS} points or fewer.",
            )
        if list(self.alpha_deg) != sorted(self.alpha_deg):
            raise TeeError(
                "fd_polar_unsorted",
                "alpha_deg must increase; JSBSim interpolates a sorted table.",
                fix="Sort the sweep by angle of attack before handing it over.",
            )

    def cd_at_cl(self, cl: float) -> float:
        """Drag coefficient at a lift coefficient, by linear interpolation."""
        pairs = sorted(zip(self.cl, self.cd, strict=True))
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        if cl <= xs[0]:
            return ys[0]
        if cl >= xs[-1]:
            return ys[-1]
        for i in range(1, len(xs)):
            if cl <= xs[i]:
                t = (cl - xs[i - 1]) / (xs[i] - xs[i - 1])
                return ys[i - 1] + t * (ys[i] - ys[i - 1])
        return ys[-1]  # pragma: no cover - unreachable


@dataclass(frozen=True)
class Mass:
    """What partkiln knows, or what the caller states. SI throughout."""

    mass_kg: float
    ixx: float
    iyy: float
    izz: float
    cg_m: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def __post_init__(self) -> None:
        bad = [
            n
            for n, v in (
                ("mass_kg", self.mass_kg),
                ("ixx", self.ixx),
                ("iyy", self.iyy),
                ("izz", self.izz),
            )
            if not (v > 0)
        ]
        if bad:
            raise TeeError(
                "fd_mass_nonpositive",
                f"{', '.join(bad)} must be positive; a zero inertia is not an aircraft.",
                fix="Give mass_kg and the three principal inertias in kg m^2.",
            )


@dataclass(frozen=True)
class Geometry:
    """Reference geometry - the same three numbers `wt_case` already carries."""

    wing_area_m2: float
    span_m: float
    chord_m: float

    def __post_init__(self) -> None:
        for n, v in (
            ("wing_area_m2", self.wing_area_m2),
            ("span_m", self.span_m),
            ("chord_m", self.chord_m),
        ):
            if not (v > 0):
                raise TeeError(
                    "fd_geometry_nonpositive",
                    f"{n} must be positive; got {v}.",
                    fix="Give the wing area, span and mean chord in metres.",
                )


@dataclass(frozen=True)
class Design:
    """The condition the thrust is sized for. Not a limit on where it flies."""

    speed_mps: float = 46.3
    altitude_m: float = 1524.0
    thrust_margin: float = 3.0


def _table(pairs: list[tuple[float, float]]) -> str:
    body = "\n".join(f"              {a:11.7f} {v:12.6f}" for a, v in pairs)
    return (
        "          <table>\n"
        '            <independentVar lookup="row">aero/alpha-rad</independentVar>\n'
        f"            <tableData>\n{body}\n            </tableData>\n"
        "          </table>\n"
    )


def _force(name: str, desc: str, extra: str, table: str = "") -> str:
    return (
        f'      <function name="aero/coefficient/{name}">\n'
        f"        <description>{desc}</description>\n"
        "        <product>\n"
        "          <property>aero/qbar-psf</property>\n"
        "          <property>metrics/Sw-sqft</property>\n"
        f"{extra}{table}"
        "        </product>\n"
        "      </function>\n"
    )


def size_thrust_n(polar: Polar, mass: Mass, geom: Geometry, design: Design) -> float:
    """Newtons of maximum thrust: the drag at the design point, times a margin.

    An aircraft that cannot out-thrust its own drag will not trim, and one with
    a hundred times too much (the first draft had 88,507 lbf on an 1,874 lb
    aeroplane) will not trim either. Both failures look like a trim error.
    """
    rho = 1.225 * math.exp(-design.altitude_m / 8500.0)
    q = 0.5 * rho * design.speed_mps**2
    weight_n = mass.mass_kg * GRAVITY
    cl_needed = weight_n / (q * geom.wing_area_m2)
    drag_n = polar.cd_at_cl(cl_needed) * q * geom.wing_area_m2
    return max(drag_n * design.thrust_margin, weight_n * 0.02)


def engine_files(thrust_n: float) -> dict[str, str]:
    """A flat-rated thrust source, and the thruster that passes it through.

    `IdleThrust` and `MilThrust` are NOT optional: a `<turbine_engine>` without
    them segfaults at `run_ic()` rather than reporting a problem (doc 76). Flat
    tables mean thrust is Mach- and altitude-independent, which is honest for a
    lane whose subject is the polar and not the powerplant.
    """
    milthrust_lb = thrust_n * 0.2248089

    def flat(v: str) -> str:
        return (
            "\n   <table>\n"
            '    <independentVar lookup="row">velocities/mach</independentVar>\n'
            '    <independentVar lookup="column">atmosphere/density-altitude</independentVar>\n'
            "    <tableData>\n"
            "              0.0     60000.0\n"
            f"     0.0     {v}     {v}\n"
            f"     1.0     {v}     {v}\n"
            "    </tableData>\n"
            "   </table>"
        )

    return {
        "tee_thrust": (
            '<?xml version="1.0"?>\n'
            '<turbine_engine name="tee_thrust">\n'
            f"  <milthrust> {milthrust_lb:.4f} </milthrust>\n"
            "  <bypassratio> 0.0 </bypassratio><tsfc> 0.8 </tsfc><bleed> 0.0 </bleed>\n"
            "  <idlen1> 30.0 </idlen1><idlen2> 60.0 </idlen2>\n"
            "  <maxn1> 100.0 </maxn1><maxn2> 100.0 </maxn2>\n"
            "  <augmented> 0 </augmented><injected> 0 </injected>\n"
            f'  <function name="IdleThrust">{flat("0.02")}\n  </function>\n'
            f'  <function name="MilThrust">{flat("1.00")}\n  </function>\n'
            "</turbine_engine>\n"
        ),
        "tee_direct": (
            '<?xml version="1.0"?>\n'
            "<!-- Thrust is computed directly by the engine. -->\n"
            '<direct name="tee_direct"></direct>\n'
        ),
    }


def aircraft_xml(name: str, polar: Polar, mass: Mass, geom: Geometry, design: Design) -> str:
    """The six sections JSBSim's schema wants, in the order it wants them."""
    lift = _table([(math.radians(a), c) for a, c in zip(polar.alpha_deg, polar.cl, strict=True)])
    drag = _table([(math.radians(a), c) for a, c in zip(polar.alpha_deg, polar.cd, strict=True)])
    cgx, cgy, cgz = mass.cg_m
    nl = chr(10)
    cbar = "          <property>metrics/cbarw-ft</property>" + nl

    # Built outside the f-string: an f-string expression may not contain a
    # backslash before Python 3.12, and the server targets 3.11.
    pitch = (
        _force(
            "Cmalpha",
            "Static_stability",
            cbar
            + "          <property>aero/alpha-rad</property>"
            + nl
            + f"          <value> {polar.cm_alpha:.6g} </value>"
            + nl,
        )
        + _force(
            "Cmq",
            "Pitch_damping",
            cbar
            + "          <property>aero/ci2vel</property>"
            + nl
            + "          <property>velocities/q-aero-rad_sec</property>"
            + nl
            + f"          <value> {polar.cm_q:.6g} </value>"
            + nl,
        )
        + _force(
            "Cmde",
            "Control_power",
            cbar
            + "          <property>fcs/elevator-pos-rad</property>"
            + nl
            + f"          <value> {polar.cm_de:.6g} </value>"
            + nl,
        )
    )
    return f"""<?xml version="1.0"?>
<fdm_config name="{name}" version="2.0" release="ALPHA">
  <fileheader>
    <description>generated-by TEE flightdyn from a {len(polar.alpha_deg)}-point
      polar ({polar.source})</description>
  </fileheader>
  <metrics>
    <wingarea unit="M2"> {geom.wing_area_m2:.6g} </wingarea>
    <wingspan unit="M"> {geom.span_m:.6g} </wingspan>
    <chord unit="M"> {geom.chord_m:.6g} </chord>
    <location name="AERORP" unit="M"><x> 0 </x><y> 0 </y><z> 0 </z></location>
  </metrics>
  <mass_balance>
    <ixx unit="KG*M2"> {mass.ixx:.6g} </ixx>
    <iyy unit="KG*M2"> {mass.iyy:.6g} </iyy>
    <izz unit="KG*M2"> {mass.izz:.6g} </izz>
    <emptywt unit="KG"> {mass.mass_kg:.6g} </emptywt>
    <location name="CG" unit="M"><x> {cgx:.6g} </x><y> {cgy:.6g} </y><z> {cgz:.6g} </z></location>
  </mass_balance>
  <ground_reactions/>
  <propulsion>
    <engine file="tee_thrust"><feed>0</feed>
      <thruster file="tee_direct">
        <location unit="M"><x> 0 </x><y> 0 </y><z> 0 </z></location>
      </thruster>
    </engine>
    <tank type="FUEL">
      <location unit="M"><x> 0 </x><y> 0 </y><z> 0 </z></location>
      <capacity unit="KG"> {max(mass.mass_kg * 0.1, 1.0):.4g} </capacity>
      <contents unit="KG"> {max(mass.mass_kg * 0.05, 0.5):.4g} </contents>
    </tank>
  </propulsion>
  <flight_control name="minimal">
    <channel name="Pitch">
      <pure_gain name="fcs/elevator-control">
        <input>fcs/elevator-cmd-norm</input>
        <gain>0.35</gain>
        <output>fcs/elevator-pos-rad</output>
      </pure_gain>
    </channel>
  </flight_control>
  <aerodynamics>
    <axis name="LIFT">
{_force("CLalpha", "Lift_from_the_polar", "", lift)}    </axis>
    <axis name="DRAG">
{_force("CDalpha", "Drag_from_the_polar", "", drag)}    </axis>
    <axis name="PITCH">
{pitch}    </axis>
  </aerodynamics>
</fdm_config>
"""


def write(
    root: Path,
    name: str,
    polar: Polar,
    mass: Mass,
    geom: Geometry,
    design: Design | None = None,
) -> dict[str, object]:
    """Write the aircraft and its engine into a JSBSim root. Returns a digest."""
    design = design or Design()
    root = Path(root)
    ac_dir = root / "aircraft" / name
    eng_dir = root / "engine"
    ac_dir.mkdir(parents=True, exist_ok=True)
    eng_dir.mkdir(parents=True, exist_ok=True)

    thrust_n = size_thrust_n(polar, mass, geom, design)
    for stem, text in engine_files(thrust_n).items():
        (eng_dir / f"{stem}.xml").write_text(text)
    xml = aircraft_xml(name, polar, mass, geom, design)
    (ac_dir / f"{name}.xml").write_text(xml)

    return {
        "aircraft": name,
        "path": str(ac_dir / f"{name}.xml"),
        "bytes": len(xml),
        "polar_points": len(polar.alpha_deg),
        "polar_source": polar.source,
        "mass_kg": round(mass.mass_kg, 4),
        "wing_area_m2": round(geom.wing_area_m2, 4),
        "max_thrust_n": round(thrust_n, 2),
        "units": "SI on the wire; JSBSim converts",
    }
