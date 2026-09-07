"""ParaView at arm's length: scripts TEE writes for `pvpython`, numbers and
pictures TEE reads back. No `vtk` or `paraview` import ever happens in this
process (docs 46/68: VTK is permissive but 600 MB of weight the kernel does
not need); `pvpython` is BSD-3 and comes with the ParaView install.

Measured 2026-09-06 on the apt build (5.11.2): rendering without a display
segfaults even with --force-offscreen-rendering, `xvfb-run -a pvpython`
renders, and `PlotOverLine` -> CSV works with no display at all. The runner
therefore samples render-free and renders under xvfb when there is no
DISPLAY and xvfb-run exists; official binaries (EGL/OSMesa on Linux, the
Mac app) take the plain --force-offscreen-rendering path.
"""

from __future__ import annotations

import csv
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

GENERATED_BY = "generated-by: tee.windtunnel.paraview"

VIEWS = ("pressure", "velocity", "cp", "mesh", "residuals")


def _reader_lines(source: Path) -> list[str]:
    """Open an OpenFOAM case (.foam stub) or an SU2 volume file (.vtu).

    The block's contract, which `state.py` depends on: it leaves `src` bound to
    the reader and `ts` bound to its time steps. The `.vtu` branch defined only
    the first, and `wt_open` on an SU2 case died with `NameError: ts` (measured
    2026-09-07 on the shipped code, doc 73 §2.10) - a single `.vtu` has no time
    steps, so the honest value is an empty list rather than no name at all.
    """
    s = str(source)
    if s.endswith(".foam"):
        return [
            f"src = OpenFOAMReader(FileName={s!r})",
            "src.MeshRegions = ['internalMesh']",
            "src.CellArrays = ['p', 'U', 'k', 'omega', 'nut']",
            "src.UpdatePipelineInformation()",
            "ts = src.TimestepValues",
            "last = ts[-1] if hasattr(ts, '__len__') and len(ts) else 0.0",
            "src.UpdatePipeline(last)",
        ]
    if s.endswith(".vtu"):
        return [
            f"src = XMLUnstructuredGridReader(FileName=[{s!r}])",
            "src.UpdatePipeline()",
            "ts = list(getattr(src, 'TimestepValues', []) or [])",
        ]
    raise TeeError(
        "wt_field_missing",
        f"{source.name} is neither a .foam stub nor a .vtu volume file.",
        fix="Point pvpython at the case's .foam stub (OpenFOAM) or flow.vtu (SU2).",
    )


def line_script(
    source: Path,
    p1: tuple[float, float, float],
    p2: tuple[float, float, float],
    n: int,
    out_csv: Path,
) -> str:
    lines = [f"# {GENERATED_BY}", "from paraview.simple import *"]
    lines += _reader_lines(source)
    lines += [
        "pol = PlotOverLine(Input=src)",
        f"pol.Point1 = {list(p1)!r}",
        f"pol.Point2 = {list(p2)!r}",
        f"pol.Resolution = {max(int(n) - 1, 1)}",
        f"SaveData({str(out_csv)!r}, proxy=pol)",
        "print('OK')",
    ]
    return "\n".join(lines) + "\n"


def slice_stats_script(
    source: Path,
    origin: tuple[float, float, float],
    normal: tuple[float, float, float],
    field: str,
    out_csv: Path,
) -> str:
    lines = [f"# {GENERATED_BY}", "from paraview.simple import *"]
    lines += _reader_lines(source)
    lines += [
        "sl = Slice(Input=src)",
        "sl.SliceType = 'Plane'",
        f"sl.SliceType.Origin = {list(origin)!r}",
        f"sl.SliceType.Normal = {list(normal)!r}",
        "sl.UpdatePipeline()",
        "cd = CellDatatoPointData(Input=sl)",
        "cd.UpdatePipeline()",
        f"SaveData({str(out_csv)!r}, proxy=cd, PointDataArrays=[{field!r}])",
        "print('OK')",
    ]
    return "\n".join(lines) + "\n"


def render_script(
    source: Path,
    view: str,
    out_png: Path,
    *,
    size: tuple[int, int] = (1200, 800),
    plane_normal: str = "z",
) -> str:
    if view not in VIEWS:
        raise TeeError(
            "wt_bad_view", f"'{view}' is not a view preset.", fix=f"One of: {', '.join(VIEWS)}."
        )
    lines = [f"# {GENERATED_BY}", "from paraview.simple import *"]
    lines += _reader_lines(source)
    field = {"pressure": "p", "velocity": "U", "cp": "p", "mesh": None, "residuals": None}[view]
    lines += [
        "rv = GetActiveViewOrCreate('RenderView')",
        f"rv.ViewSize = [{size[0]}, {size[1]}]",
        "rv.OrientationAxesVisibility = 0",
        "sl = Slice(Input=src)",
        "sl.SliceType = 'Plane'",
        "b = src.GetDataInformation().GetBounds()",
        "sl.SliceType.Origin = [(b[0]+b[1])/2, (b[2]+b[3])/2, (b[4]+b[5])/2]",
        f"sl.SliceType.Normal = {dict(x=[1, 0, 0], y=[0, 1, 0], z=[0, 0, 1])[plane_normal]!r}",
        "d = Show(sl, rv)",
    ]
    if view == "mesh":
        lines += ["d.SetRepresentationType('Surface With Edges')", "ColorBy(d, None)"]
    elif field:
        lines += [
            f"ColorBy(d, ('CELLS', {field!r}))",
            f"lut = GetColorTransferFunction({field!r})",
            "d.RescaleTransferFunctionToDataRange(True, False)",
            "d.SetScalarBarVisibility(rv, True)",
            f"rng = src.CellData[{field!r}].GetRange() if {field!r} in src.CellData.keys() "
            "else (0, 0)",
            "print('RANGE', rng[0], rng[1])",
        ]
    lines += [
        f"rv.InteractionMode = '2D' if {plane_normal!r} == 'z' else '3D'",
        "rv.ResetCamera()",
        "Render(rv)",
        f"SaveScreenshot({str(out_png)!r}, rv, ImageResolution=[{size[0]}, {size[1]}])",
        "print('OK')",
    ]
    return "\n".join(lines) + "\n"


def argv_for(pvpython: str, script: Path, *, render: bool) -> list[str]:
    """The argv that works here: xvfb-run when rendering with no DISPLAY on
    Linux and xvfb-run exists; otherwise plain pvpython (with
    --force-offscreen-rendering for a render)."""
    if render and platform.system() != "Darwin" and not os.environ.get("DISPLAY"):
        xvfb = shutil.which("xvfb-run")
        if xvfb:
            return [xvfb, "-a", pvpython, str(script)]
        return [pvpython, "--force-offscreen-rendering", str(script)]
    if render:
        return [pvpython, "--force-offscreen-rendering", str(script)]
    return [pvpython, str(script)]


def run_script(
    pvpython: str, script_text: str, workdir: Path, *, render: bool, timeout_s: float = 180.0
) -> str:
    workdir.mkdir(parents=True, exist_ok=True)
    script = workdir / "pv_script.py"
    script.write_text(script_text)
    argv = argv_for(pvpython, script, render=render)
    try:
        res = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout_s, cwd=str(workdir)
        )
    except subprocess.TimeoutExpired as exc:
        raise TeeError(
            "wt_probe_failed",
            f"pvpython exceeded {timeout_s:.0f} s.",
            fix="Smaller case, or raise timeout_s.",
        ) from exc
    text = res.stdout + res.stderr
    if res.returncode != 0 or "OK" not in res.stdout:
        tail = " ".join(x.strip() for x in text.strip().splitlines()[-4:])[:400]
        code = "wt_render_failed" if render else "wt_probe_failed"
        fix = (
            "pvpython cannot render here: on Linux install xvfb (`apt-get install xvfb`) "
            "or use ParaView's "
            "EGL/OSMesa binary; set [windtunnel] pvpython = <path> to choose the binary."
            if render
            else "Check the field name and that the case has a written time directory."
        )
        raise TeeError(code, f"pvpython failed ({' '.join(argv[:2])}): {tail}", fix=fix)
    return res.stdout


def read_csv_columns(path: Path) -> dict[str, list[float]]:
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = [h.strip().strip('"') for h in next(reader)]
        cols: dict[str, list[float]] = {h: [] for h in header}
        for raw in reader:
            for h, v in zip(header, raw, strict=False):
                try:
                    cols[h].append(float(v))
                except ValueError:
                    cols[h].append(float("nan"))
    return cols


def stats(values: list[float]) -> dict[str, float]:
    vals = sorted(v for v in values if v == v)  # drop NaN
    if not vals:
        return {"n": 0}
    n = len(vals)

    def pct(p: float) -> float:
        k = min(max(round(p * (n - 1)), 0), n - 1)
        return vals[k]

    def sig(v: float) -> float:
        return float(f"{v:.6g}")

    return {
        "n": n,
        "min": sig(vals[0]),
        "max": sig(vals[-1]),
        "mean": sig(sum(vals) / n),
        "p05": sig(pct(0.05)),
        "p95": sig(pct(0.95)),
    }


def foam_stub(case_dir: Path, name: str = "case.foam") -> Path:
    """ParaView's OpenFOAM reader wants an (empty) file with the .foam suffix
    in the case directory."""
    stub = case_dir / name
    if not stub.exists():
        stub.write_text("")
    return stub


def csv_sample(
    cols: dict[str, list[float]], field: str, limit: int = 64, *, components: bool = False
) -> dict[str, Any]:
    """Pick the field (a vector field arrives as field:0/1/2 columns) and
    thin to at most `limit` samples along arc_length. A vector comes back
    as its magnitude; the components cost three more arrays and are opt-in."""
    keys = [k for k in cols if k == field or k.startswith(field + ":")]
    if not keys:
        raise TeeError(
            "wt_field_missing",
            f"'{field}' is not in the sampled data ({', '.join(list(cols)[:12])}).",
            fix="Use one of the listed field names.",
        )
    n = len(cols[keys[0]])
    step = max(1, -(-n // limit))
    idx = list(range(0, n, step))[:limit]
    out: dict[str, Any] = {"n_total": n, "n": len(idx)}
    # a point outside the mesh (inside the body) carries vtkValidPointMask 0
    # and a zero value: it is no sample at all, so it becomes NaN (null on
    # the wire) and stays out of the statistics
    mask = cols.get("vtkValidPointMask")
    nan = float("nan")

    def val(k: str, i: int) -> float:
        if mask is not None and i < len(mask) and mask[i] == 0:
            return nan
        return cols[k][i]

    def sig(v: float) -> float:
        return float(f"{v:.6g}") if v == v else v

    def mag(i: int) -> float:
        return sum(val(k, i) ** 2 for k in keys) ** 0.5

    if "arc_length" in cols:
        out["s"] = [sig(cols["arc_length"][i]) for i in idx]
    if len(keys) == 1 or components:
        for k in keys:
            out[k] = [sig(val(k, i)) for i in idx]
    if len(keys) > 1:  # magnitude of a vector
        out[field + "_mag"] = [sig(mag(i)) for i in idx]
    out["stats"] = stats(
        [val(keys[0], i) for i in range(n)] if len(keys) == 1 else [mag(i) for i in range(n)]
    )
    if mask is not None:
        out["outside_mesh"] = sum(1 for i in idx if i < len(mask) and mask[i] == 0)
    return out
