"""76-evidence: how far a TEE-GENERATED aircraft gets.

Doc 74 proved JSBSim flies a BUNDLED aircraft. The A75 lane's premise is the
other thing: that a `wt_sweep` polar plus mass properties can be written as an
aircraft file that flies. This is how far that got, honestly — including one
finding that kills the process.

Nothing is read from a bundled aircraft: the polar below is synthetic but
shaped exactly like a `wt_sweep` reply, and the engine and thruster are written
here too.

    python bridge.py             # SI units on the wire
    python bridge.py --imperial  # the same aircraft, converted by us
"""

from __future__ import annotations

import math
import subprocess
import sys
import tempfile
from pathlib import Path

import jsbsim
import numpy as np

SI = "--imperial" not in sys.argv
M2_FT2, M_FT, KGM2_SLUGFT2, KG_LB = 10.763910, 3.2808399, 0.7375621, 2.2046226

# --- the "wt_sweep" reply ---------------------------------------------------
ALPHA_DEG = [-6.0, -3.0, 0.0, 3.0, 6.0, 9.0, 12.0, 15.0]
CL = [-0.38, -0.06, 0.26, 0.58, 0.89, 1.18, 1.40, 1.32]
CD = [0.0181, 0.0132, 0.0121, 0.0148, 0.0213, 0.0316, 0.0470, 0.0721]
CM_ALPHA, CM_DE = -0.55, -1.10
# --- the "partkiln" mass properties ----------------------------------------
MASS_KG, IXX, IYY, IZZ = 850.0, 1_290.0, 1_820.0, 2_670.0
S_M2, B_M, C_M = 16.2, 10.9, 1.49


def _tab(pairs):
    body = "\n".join(f"              {a:9.6f} {v:11.6f}" for a, v in pairs)
    return ('          <table>\n'
            '            <independentVar lookup="row">aero/alpha-rad</independentVar>\n'
            f"            <tableData>\n{body}\n            </tableData>\n"
            "          </table>\n")


def _axis(name, fname, desc, table=None, extra=()):
    inner = "".join(f"          <{k}>{v}</{k}>\n" for k, v in extra)
    return (f'    <axis name="{name}">\n'
            f'      <function name="aero/coefficient/{fname}">\n'
            f"        <description>{desc}</description>\n        <product>\n"
            "          <property>aero/qbar-psf</property>\n"
            "          <property>metrics/Sw-sqft</property>\n"
            f"{inner}{table or ''}        </product>\n      </function>\n    </axis>\n")


def aircraft_xml(*, engine: bool = True) -> str:
    """The six sections JSBSim's schema wants, in its own order."""
    U = (lambda si, imp: si if SI else imp)
    area, span, chord = (S_M2, B_M, C_M) if SI else (S_M2 * M2_FT2, B_M * M_FT, C_M * M_FT)
    ix, iy, iz = (IXX, IYY, IZZ) if SI else (IXX * KGM2_SLUGFT2, IYY * KGM2_SLUGFT2, IZZ * KGM2_SLUGFT2)
    wt = MASS_KG if SI else MASS_KG * KG_LB
    ul, ua, ui = U("M", "FT"), U("M2", "FT2"), U("KG*M2", "SLUG*FT2")

    prop = ('  <propulsion>\n    <engine file="tee_motor">\n'
            '      <thruster file="tee_prop">'
            '<location unit="M"><x> 0 </x><y> 0 </y><z> 0 </z></location></thruster>\n'
            "    </engine>\n  </propulsion>\n") if engine else "  <propulsion/>\n"
    pitch = (
        _axis("PITCH", "Cmalpha", "Static_stability",
              extra=(("property", "metrics/cbarw-ft"), ("property", "aero/alpha-rad"),
                     ("value", f" {CM_ALPHA} "))).rstrip("\n")[: -len("    </axis>")]
        + _axis("", "Cmde", "Control_power",
                extra=(("property", "metrics/cbarw-ft"),
                       ("property", "fcs/elevator-pos-rad"), ("value", f" {CM_DE} ")))
        .replace('    <axis name="">\n', ""))
    return f"""<?xml version="1.0"?>
<fdm_config name="tee_generated" version="2.0" release="ALPHA">
  <fileheader><description>generated-by TEE docs/research/76-evidence/bridge.py</description></fileheader>
  <metrics>
    <wingarea unit="{ua}"> {area:g} </wingarea>
    <wingspan unit="{ul}"> {span:g} </wingspan>
    <chord unit="{ul}"> {chord:g} </chord>
    <location name="AERORP" unit="{ul}"><x> 0 </x><y> 0 </y><z> 0 </z></location>
  </metrics>
  <mass_balance>
    <ixx unit="{ui}"> {ix:g} </ixx>
    <iyy unit="{ui}"> {iy:g} </iyy>
    <izz unit="{ui}"> {iz:g} </izz>
    <emptywt unit="{U('KG', 'LBS')}"> {wt:g} </emptywt>
    <location name="CG" unit="{ul}"><x> 0 </x><y> 0 </y><z> 0 </z></location>
  </mass_balance>
  <ground_reactions/>
{prop}  <flight_control name="minimal">
    <channel name="Pitch"><pure_gain name="fcs/elevator-control">
      <input>fcs/elevator-cmd-norm</input><gain>0.35</gain>
      <output>fcs/elevator-pos-rad</output></pure_gain></channel>
  </flight_control>
  <aerodynamics>
{_axis("LIFT", "CLalpha", "Lift_from_the_polar", _tab([(math.radians(a), c) for a, c in zip(ALPHA_DEG, CL)]))}{_axis("DRAG", "CDalpha", "Drag_from_the_polar", _tab([(math.radians(a), c) for a, c in zip(ALPHA_DEG, CD)]))}{pitch}  </aerodynamics>
</fdm_config>
"""


def write_root(*, engine: bool) -> Path:
    root = Path(tempfile.mkdtemp(prefix="tee-fd-"))
    (root / "aircraft" / "tee_generated").mkdir(parents=True)
    (root / "engine").mkdir()
    # TEE writes its own engine and thruster: nothing bundled is referenced.
    (root / "engine" / "tee_motor.xml").write_text(
        '<?xml version="1.0"?>\n<electric_engine name="tee_motor">'
        "<power unit=\"WATTS\"> 120000 </power></electric_engine>\n")
    (root / "engine" / "tee_prop.xml").write_text(
        '<?xml version="1.0"?>\n<direct name="tee_prop"/>\n')
    (root / "aircraft" / "tee_generated" / "tee_generated.xml").write_text(
        aircraft_xml(engine=engine))
    return root


CHILD = """
import sys, jsbsim
sys.path.insert(0, {here!r})
from bridge import write_root
root = write_root(engine={engine})
f = jsbsim.FGFDMExec(str(root)); f.set_debug_level(0); f.load_model("tee_generated")
f.set_property_value("ic/h-sl-ft", 5000); f.set_property_value("ic/vc-kts", 90); f.run_ic()
lin = jsbsim.FGLinearization(f)
print("SURVIVED", len(lin.x_names))
"""


def main() -> None:
    here = str(Path(__file__).resolve().parent)
    print(f"units          {'SI on the wire' if SI else 'imperial (converted by TEE)'}")

    root = write_root(engine=True)
    xml = (root / "aircraft" / "tee_generated" / "tee_generated.xml").read_text()
    print(f"aircraft       {len(xml)} bytes, engine + thruster written beside it")

    fdm = jsbsim.FGFDMExec(str(root))
    fdm.set_debug_level(0)
    print(f"load_model     {fdm.load_model('tee_generated')}")
    print(f"  Sw   {fdm.get_property_value('metrics/Sw-sqft'):10.4f} ft2   expected {S_M2 * M2_FT2:10.4f}")
    print(f"  cbar {fdm.get_property_value('metrics/cbarw-ft'):10.4f} ft    expected {C_M * M_FT:10.4f}")
    print(f"  wt   {fdm.get_property_value('inertia/empty-weight-lbs'):10.4f} lb    expected {MASS_KG * KG_LB:10.4f}")
    print(f"  iyy  {fdm.get_property_value('inertia/iyy-slugs_ft2'):10.4f}       <- 0.0 BEFORE run_ic, always")

    fdm.set_property_value("ic/h-sl-ft", 5000)
    fdm.set_property_value("ic/vc-kts", 90)
    print(f"run_ic         {fdm.run_ic()}")
    print(f"  iyy  {fdm.get_property_value('inertia/iyy-slugs_ft2'):10.4f} slug-ft2  expected {IYY * KGM2_SLUGFT2:10.4f}  [after run_ic]")
    print(f"  engines {fdm.get_propulsion().get_num_engines()}")

    fdm.set_property_value("propulsion/set-running", -1)
    try:
        fdm.do_trim(0)
        print(f"do_trim(0)     ok   alpha {fdm.get_property_value('aero/alpha-deg'):.3f} deg")
    except jsbsim.TrimFailureError as exc:
        print(f"do_trim(0)     OPEN — {exc}")
        print("               the pitch axis is not yet trimmable; this is A75 P3's")
        print("               acceptance criterion and is deliberately NOT claimed here.")

    # The finding worth the whole file: linearising an engineless aircraft
    # does not raise. It kills the process.
    print("\nFGLinearization vs propulsion (each in a FRESH interpreter):")
    for engine in (True, False):
        r = subprocess.run([sys.executable, "-c", CHILD.format(here=here, engine=engine)],
                           capture_output=True, text=True)
        out = [l for l in r.stdout.splitlines() if "SURVIVED" in l]
        verdict = out[0] if out else f"DIED rc={r.returncode}" + (
            " (SIGSEGV)" if r.returncode == -11 or r.returncode == 139 else "")
        print(f"  <propulsion> with {'one engine ' if engine else 'NO engine  '} -> {verdict}")


if __name__ == "__main__":       # NOT optional: CHILD imports this module
    main()
