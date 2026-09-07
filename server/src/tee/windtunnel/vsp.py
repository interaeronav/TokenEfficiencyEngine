"""OpenVSP and VSPAERO at arm's length: TEE writes an AngelScript, `vspscript`
builds the geometry and runs the vortex-lattice sweep, TEE reads the files.

OpenVSP is NASA Open Source Agreement 1.3 and never imported; its bundled
Python API is compiled against one specific Python minor (3.12 in the
Ubuntu package, 3.11 or 3.13 on the Mac) and was measured to fail under any
other, which is why the script route is the primary one. Every API name
below was harvested from the scripts OpenVSP 3.51.3 ships in `scripts/`
(`AddGeom`, `SetParmVal`, `WriteVSPFile`, `ExportFile`, `ComputeDegenGeom`,
`VSPAEROComputeGeometry`, `VSPAEROSweep`) and the two VLM facts were
measured 2026-09-06: the solver needs a `.vspgeom`, which the compute-
geometry analysis writes only with GeomSet = SET_NONE and ThinGeomSet =
SET_ALL; and the `.polar` file names its columns in a header row.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

GENERATED_BY = "generated-by: tee.windtunnel.vsp"


@dataclass
class WingSpec:
    span: float  # full span, m
    root_chord: float
    tip_chord: float | None = None
    sweep_deg: float = 0.0
    dihedral_deg: float = 0.0
    twist_deg: float = 0.0
    airfoil: str = "0012"  # NACA four-digit
    tess_w: int = 33
    tess_u: int = 20

    @property
    def tip(self) -> float:
        return self.root_chord if self.tip_chord is None else self.tip_chord

    @property
    def area(self) -> float:
        return 0.5 * (self.root_chord + self.tip) * self.span

    @property
    def aspect_ratio(self) -> float:
        return self.span * self.span / self.area

    @property
    def mac(self) -> float:
        taper = self.tip / self.root_chord
        return (2.0 / 3.0) * self.root_chord * (1 + taper + taper * taper) / (1 + taper)


def _naca_parts(code: str) -> tuple[float, float, float]:
    if len(code) != 4 or not code.isdigit():
        raise ValueError(f"'{code}' is not a four-digit NACA code")
    return int(code[0]) / 100.0, int(code[1]) / 10.0, int(code[2:]) / 100.0


def wing_script(
    stem: str,
    wing: WingSpec,
    *,
    export_stl: bool = True,
    export_degen: bool = True,
) -> str:
    """Build a single-section wing (planar symmetry on by default) and save
    `<stem>.vsp3` (+ STL, DegenGeom). Chord-normalised NACA camber/thickness
    go onto both section curves."""
    m, p, t = _naca_parts(wing.airfoil)
    lines = [
        f"// {GENERATED_BY}",
        "void main()",
        "{",
        '    string wid = AddGeom( "WING", "" );',
        '    SetGeomName( wid, "WingGeom" );',
        f'    SetParmVal( wid, "Span", "XSec_1", {0.5 * wing.span:.9g} );',
        f'    SetParmVal( wid, "Root_Chord", "XSec_1", {wing.root_chord:.9g} );',
        f'    SetParmVal( wid, "Tip_Chord", "XSec_1", {wing.tip:.9g} );',
        f'    SetParmVal( wid, "Sweep", "XSec_1", {wing.sweep_deg:.9g} );',
        f'    SetParmVal( wid, "Dihedral", "XSec_1", {wing.dihedral_deg:.9g} );',
        f'    SetParmVal( wid, "Twist", "XSec_1", {wing.twist_deg:.9g} );',
        f'    SetParmVal( wid, "ThickChord", "XSecCurve_0", {t:.9g} );',
        f'    SetParmVal( wid, "ThickChord", "XSecCurve_1", {t:.9g} );',
        f'    SetParmVal( wid, "Camber", "XSecCurve_0", {m:.9g} );',
        f'    SetParmVal( wid, "Camber", "XSecCurve_1", {m:.9g} );',
    ]
    if m > 0:
        lines += [
            f'    SetParmVal( wid, "CamberLoc", "XSecCurve_0", {p:.9g} );',
            f'    SetParmVal( wid, "CamberLoc", "XSecCurve_1", {p:.9g} );',
        ]
    lines += [
        f'    SetParmVal( wid, "Tess_W", "Shape", {wing.tess_w} );',
        f'    SetParmVal( wid, "SectTess_U", "XSec_1", {wing.tess_u} );',
        "    Update();",
        '    Print( "TotalSpan=", false );',
        '    Print( GetParmVal( wid, "TotalSpan", "WingGeom" ), true );',
        '    Print( "TotalArea=", false );',
        '    Print( GetParmVal( wid, "TotalArea", "WingGeom" ), true );',
        f'    WriteVSPFile( "{stem}.vsp3", SET_ALL );',
    ]
    if export_stl:
        lines.append(f'    ExportFile( "{stem}.stl", SET_ALL, EXPORT_STL );')
    if export_degen:
        lines.append("    ComputeDegenGeom( SET_ALL, DEGEN_GEOM_CSV_TYPE );")
    lines += ['    Print( "DONE" );', "}"]
    return "\n".join(lines) + "\n"


def sweep_script(
    vsp3: str,
    *,
    alphas: list[float],
    mach: float,
    re_cref: float | None = None,
    ncpu: int = 4,
    wake_iters: int = 3,
) -> str:
    """Open a saved model and run VSPAEROSweep (VLM) over `alphas` at one
    Mach. The results land next to the model as `<stem>.polar/.lod/.history`.
    `alphas` must be evenly spaced (VSPAERO takes start/end/npts)."""
    if not alphas:
        raise ValueError("at least one alpha")
    a0, a1, n = alphas[0], alphas[-1], len(alphas)
    if n > 1:
        step = (a1 - a0) / (n - 1)
        for k, a in enumerate(alphas):
            if abs(a - (a0 + k * step)) > 1e-9:
                raise ValueError("VSPAERO sweeps take evenly spaced alphas (start, end, count)")
    stem = Path(vsp3).stem
    lines = [
        f"// {GENERATED_BY}",
        "void main()",
        "{",
        f'    ReadVSPFile( "{vsp3}" );',
        "    Update();",
        '    string cg = "VSPAEROComputeGeometry";',
        "    SetAnalysisInputDefaults( cg );",
        "    array< int > none_set; none_set.push_back( SET_NONE );",
        "    array< int > all_set; all_set.push_back( SET_ALL );",
        '    SetIntAnalysisInput( cg, "GeomSet", none_set, 0 );',
        '    SetIntAnalysisInput( cg, "ThinGeomSet", all_set, 0 );',
        "    ExecAnalysis( cg );",
        '    string an = "VSPAEROSweep";',
        "    SetAnalysisInputDefaults( an );",
        '    SetIntAnalysisInput( an, "GeomSet", none_set, 0 );',
        '    SetIntAnalysisInput( an, "ThinGeomSet", all_set, 0 );',
        "    array< int > rf; rf.push_back( 1 );",
        '    SetIntAnalysisInput( an, "RefFlag", rf, 0 );',
        '    array< string > wids = FindGeomsWithName( "WingGeom" );',
        '    SetStringAnalysisInput( an, "WingID", wids, 0 );',
        f"    array< double > a0; a0.push_back( {a0:.9g} );",
        f"    array< double > a1; a1.push_back( {a1:.9g} );",
        f"    array< int > an_pts; an_pts.push_back( {n} );",
        '    SetDoubleAnalysisInput( an, "AlphaStart", a0, 0 );',
        '    SetDoubleAnalysisInput( an, "AlphaEnd", a1, 0 );',
        '    SetIntAnalysisInput( an, "AlphaNpts", an_pts, 0 );',
        f"    array< double > m0; m0.push_back( {mach:.9g} );",
        "    array< int > m_pts; m_pts.push_back( 1 );",
        '    SetDoubleAnalysisInput( an, "MachStart", m0, 0 );',
        '    SetIntAnalysisInput( an, "MachNpts", m_pts, 0 );',
    ]
    if re_cref:
        lines += [
            f"    array< double > re; re.push_back( {re_cref:.9g} );",
            '    SetDoubleAnalysisInput( an, "ReCref", re, 0 );',
        ]
    lines += [
        f"    array< int > ncpu; ncpu.push_back( {ncpu} );",
        '    SetIntAnalysisInput( an, "NCPU", ncpu, 0 );',
        f"    array< int > wi; wi.push_back( {wake_iters} );",
        '    SetIntAnalysisInput( an, "WakeNumIter", wi, 0 );',
        "    Update();",
        "    string rid = ExecAnalysis( an );",
        f'    Print( "POLAR={stem}.polar" );',
        '    Print( "DONE" );',
        "}",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Readers: whitespace tables whose header row names the columns
# ---------------------------------------------------------------------------

_POLAR_KEYS = {
    "cl": "CLtot",
    "cd": "CDtot",
    "cdi": "CDi",
    "cdo": "CDo",
    "alpha": "AoA",
    "mach": "Mach",
    "e": "E",
    "l_over_d": "L/D",
}


def read_polar(path: str | Path) -> dict[str, Any]:
    """`.polar`: a banner, then a header row (Beta Mach AoA Re/1e6 CLo CLi
    CLtot CDo CDi CDtot ... L/D E ...), then one row per case."""
    cols: list[str] = []
    rows: list[dict[str, float]] = []
    for line in Path(path).read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        if not cols:
            if parts[0] == "Beta" and "CLtot" in parts:
                cols = parts
            continue
        try:
            vals = [float(v) for v in parts]
        except ValueError:
            continue
        if len(vals) < len(cols):
            continue
        row = dict(zip(cols, vals[: len(cols)], strict=True))
        for canon, name in _POLAR_KEYS.items():
            if name in row:
                row[canon] = row[name]
        rows.append(row)
    if not cols:
        raise ValueError(
            f"{Path(path).name}: no 'Beta ... CLtot ...' header row - not a VSPAERO polar"
        )
    return {"columns": cols, "rows": rows, "source": str(path)}


_RE_LOD_HEADER = re.compile(r"^\s*Wing\s+S\s+Yavg\s+Chord")


def read_lod(path: str | Path) -> dict[str, Any]:
    """`.lod`: per-case blocks of spanwise loads with a header
    (Wing S Yavg Chord V/Vinf Cl Cd Cs ...). Returns the LAST block's rows
    keyed by the header names (the final alpha of the sweep)."""
    blocks: list[dict[str, Any]] = []
    cols: list[str] = []
    rows: list[dict[str, float]] = []
    for line in Path(path).read_text().splitlines():
        if _RE_LOD_HEADER.match(line):
            if cols and rows:
                blocks.append({"columns": cols, "rows": rows})
            cols = line.split()
            rows = []
            continue
        parts = line.split()
        if cols and parts:
            try:
                vals = [float(v) for v in parts]
            except ValueError:
                continue
            if len(vals) >= len(cols):
                rows.append(dict(zip(cols, vals[: len(cols)], strict=True)))
    if cols and rows:
        blocks.append({"columns": cols, "rows": rows})
    return {"blocks": len(blocks), "last": blocks[-1] if blocks else {"columns": [], "rows": []}}


def script_facts(text: str) -> dict[str, float]:
    """TotalSpan / TotalArea printed by the wing script."""
    out: dict[str, float] = {}
    for key in ("TotalSpan", "TotalArea"):
        m = re.search(rf"{key}=\s*([-+0-9.eE]+)", text)
        if m:
            out[key] = float(m.group(1))
    return out


def vsp3_is_model(path: str | Path) -> bool:
    try:
        head = Path(path).read_text(errors="replace")[:4000]
    except OSError:
        return False
    return "<Vsp_Geometry" in head
