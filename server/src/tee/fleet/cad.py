"""A45 P2e — parametric CAD: OpenSCAD (subprocess) and CadQuery (in-process).

Two tools for two different jobs:

* **OpenSCAD** builds a solid from its own modelling language and exports
  it. GPL-2.0-or-later, so it is driven as a SUBPROCESS through its
  documented command line - never linked, never imported. (`pythonscad`
  and upstream's ENABLE_PYTHON build do expose a CPython binding; TEE uses
  neither, deliberately.)
* **CadQuery** (Apache-2.0) is imported in-process to MEASURE geometry -
  volume, area, bounding box, validity - of a file that already exists.

**`-D` is never exposed, and that is a security decision.** OpenSCAD's
`-D` does not set a scalar: it *prepends arbitrary statements* to the
script. A caller-supplied `-D` is code execution on the owner's machine
wearing the costume of a parameter. Parameterisation goes through
OpenSCAD's own customizer JSON (`-p`), with values type-checked here and
never interpolated into source text.

Token discipline: a build answers with facets, volume, bounding box and
the output path - never geometry. A mesh is a file reference; that is the
whole point of writing it to disk.
"""

from __future__ import annotations

import json
import math
import re
import shutil
import struct
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from tee.fleet.probe import have, need, probe_rows
from tee.kernel.errors import TeeError

FORMATS = ("stl", "binstl", "asciistl", "3mf", "off", "amf", "dxf", "svg", "csg")
DEFAULT_FORMAT = "binstl"
BUILD_TIMEOUT = 300.0
MAX_SOURCE = 200_000

# OpenSCAD reports the CGAL cell complex on stderr; these are the only
# numbers worth carrying into an answer.
_FACETS = re.compile(r"Facets:\s*(\d+)")
_VOLUMES = re.compile(r"Volumes:\s*(\d+)")


def openscad_bin() -> str | None:
    return shutil.which("openscad")


def _require_openscad() -> str:
    exe = openscad_bin()
    if exe is None:
        raise TeeError(
            "cad_no_openscad",
            "OpenSCAD is not on PATH.",
            fix="brew install --cask openscad  (GPL-2.0-or-later; TEE runs it "
            "as a separate program and never links it).",
        )
    return exe


def _params_file(params: dict[str, Any], tmp: Path) -> Path | None:
    """OpenSCAD customizer JSON. The ONLY parameter path TEE offers.

    Values are validated to scalars here. `-D` is not exposed at all: it
    prepends statements to the script, so `-D 'x=1; system("rm -rf /")'`
    is not a parameter, it is an injection point.
    """
    if not params:
        return None
    clean: dict[str, Any] = {}
    for k, v in params.items():
        key = str(k)
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise TeeError(
                "cad_bad_param",
                f"parameter name '{key}' is not a plain identifier.",
                fix="Names must match [A-Za-z_][A-Za-z0-9_]* - no expressions.",
            )
        if (
            isinstance(v, bool)
            or isinstance(v, (int, float))
            or isinstance(v, str)
            or (isinstance(v, list) and all(isinstance(x, (int, float)) for x in v))
        ):
            clean[key] = v
        else:
            raise TeeError(
                "cad_bad_param",
                f"parameter '{key}' must be a number, string, bool or list of numbers.",
                fix="Complex values would have to be interpolated into source, "
                "which TEE does not do.",
            )
    path = tmp / "params.json"
    path.write_text(json.dumps({"parameterSets": {"tee": clean}, "fileFormatVersion": "1"}))
    return path


def scad_build(spec: dict[str, Any]) -> dict[str, Any]:
    """Build a solid from OpenSCAD source and export it."""
    exe = _require_openscad()
    source = spec.get("source")
    src_path = spec.get("path")
    if not source and not src_path:
        raise TeeError(
            "cad_bad_spec",
            "Supply `source` (OpenSCAD text) or `path` (a .scad file).",
            fix='e.g. source: "cube([10,10,10]);"',
        )
    if source and len(str(source)) > MAX_SOURCE:
        raise TeeError(
            "cad_bad_spec",
            f"source is {len(str(source))} chars; the cap is {MAX_SOURCE}.",
            fix="Put a large model in a .scad file and pass `path`.",
        )
    fmt = str(spec.get("format") or DEFAULT_FORMAT).lower()
    if fmt not in FORMATS:
        raise TeeError(
            "cad_bad_format",
            f"'{fmt}' is not an export format.",
            fix=f"Use one of: {', '.join(FORMATS)}.",
        )
    out = spec.get("out")
    started = time.monotonic()

    with tempfile.TemporaryDirectory(prefix="tee-scad-") as td:
        tmp = Path(td)
        if source:
            scad = tmp / "model.scad"
            scad.write_text(str(source))
        else:
            scad = Path(str(src_path)).expanduser()
            if not scad.is_file():
                raise TeeError("cad_bad_spec", f"No such file: {scad}", fix="Check the path.")
        suffix = "stl" if fmt in ("binstl", "asciistl") else fmt
        target = Path(str(out)).expanduser() if out else tmp / f"model.{suffix}"
        target.parent.mkdir(parents=True, exist_ok=True)

        argv = [exe, "-o", str(target), "--export-format", fmt]
        pfile = _params_file(dict(spec.get("params") or {}), tmp)
        if pfile is not None:
            argv += ["-p", str(pfile), "-P", "tee"]
        argv.append(str(scad))

        try:
            proc = subprocess.run(argv, capture_output=True, text=True, timeout=BUILD_TIMEOUT)
        except subprocess.TimeoutExpired as exc:
            raise TeeError(
                "cad_timeout",
                f"OpenSCAD did not finish within {BUILD_TIMEOUT:.0f}s.",
                fix="Reduce $fn, simplify the model, or export a coarser format.",
            ) from exc

        stderr = (proc.stderr or "").strip()
        if proc.returncode != 0 or not target.exists():
            raise TeeError(
                "cad_build_failed",
                f"OpenSCAD exited {proc.returncode}.",
                fix=_first_error(stderr) or "See the model's own syntax.",
            )
        size = target.stat().st_size
        kept = None
        if out:
            kept = str(target)
        else:
            # no destination asked for: keep the bytes out of the answer, but
            # do not silently delete the only copy either
            keep = Path(tempfile.gettempdir()) / f"tee-scad-{int(time.time())}.{suffix}"
            keep.write_bytes(target.read_bytes())
            kept = str(keep)

    wall = round(time.monotonic() - started, 3)
    result: dict[str, Any] = {
        "ok": True,
        "format": fmt,
        "path": kept,
        "bytes": size,
        "wall_s": wall,
    }
    facets = _FACETS.search(stderr)
    if facets:
        result["facets"] = int(facets.group(1))
    volumes = _VOLUMES.search(stderr)
    if volumes:
        result["volumes"] = int(volumes.group(1))
    warnings = [ln for ln in stderr.splitlines() if "WARNING" in ln.upper()][:3]
    if warnings:
        result["warnings"] = warnings
    return result


def _first_error(stderr: str) -> str | None:
    for line in stderr.splitlines():
        if "ERROR" in line.upper():
            return line.strip()[:220]
    return stderr.splitlines()[-1][:220] if stderr else None


def measure(spec: dict[str, Any]) -> dict[str, Any]:
    """Scalar geometry facts about an existing solid, via CadQuery."""
    need("cadquery", "cad", what="CadQuery")
    import cadquery as cq

    path = Path(str(spec.get("path") or "")).expanduser()
    if not str(path) or not path.is_file():
        raise TeeError(
            "cad_bad_spec",
            f"No such file: {path}",
            fix="Give a STEP, BREP or STL produced by cad_scad_build or any CAD tool.",
        )
    started = time.monotonic()
    suffix = path.suffix.lower()
    try:
        if suffix in (".step", ".stp"):
            shape = cq.importers.importStep(str(path))
        elif suffix in (".stl",):
            shape = cq.Workplane(obj=cq.Shape.importBrep(str(path))) if False else None
            if shape is None:
                # CadQuery has no first-class STL importer; measure the mesh
                return _measure_stl(path, started)
        else:
            raise TeeError(
                "cad_unsupported",
                f"'{suffix}' is not a format cad_measure reads.",
                fix="Use STEP (.step/.stp) for solids, or STL for a mesh.",
            )
    except TeeError:
        raise
    except Exception as exc:
        raise TeeError(
            "cad_unreadable",
            f"Could not read {path.name}: {str(exc)[:180]}",
            fix="Check the file is a valid solid model.",
        ) from exc

    solid = shape.val()
    bb = solid.BoundingBox()
    return {
        "ok": True,
        "path": str(path),
        "kind": "solid",
        "volume": round(float(solid.Volume()), 6),
        "area": round(float(solid.Area()), 6),
        "bbox": [round(bb.xlen, 6), round(bb.ylen, 6), round(bb.zlen, 6)],
        "valid": bool(solid.isValid()),
        "wall_s": round(time.monotonic() - started, 3),
    }


def _measure_stl(path: Path, started: float) -> dict[str, Any]:
    """Real geometry from a binary STL, with no dependency at all.

    Volume by the signed-tetrahedron sum (each triangle with the origin),
    which is exact for a closed surface and is how every mesh tool does it.
    Reporting only a triangle count would have been the lazy answer: the
    question a caller actually has about a solid is how big it is.
    """
    data = path.read_bytes()
    if len(data) < 84 or data[:5].lower().startswith(b"solid"):
        return {
            "ok": True,
            "path": str(path),
            "kind": "mesh",
            "bytes": len(data),
            "wall_s": round(time.monotonic() - started, 3),
            "note": "ASCII STL - re-export as binary STL for measurement.",
        }
    n = int.from_bytes(data[80:84], "little")
    expect = 84 + n * 50
    if len(data) < expect:
        raise TeeError(
            "cad_unreadable",
            f"STL claims {n} triangles but the file is {len(data)} bytes (expected {expect}).",
            fix="The file looks truncated; re-export it.",
        )
    vol2 = 0.0
    area2 = 0.0
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    off = 84
    for _ in range(n):
        vs = struct.unpack_from("<9f", data, off + 12)
        a, b, c = vs[0:3], vs[3:6], vs[6:9]
        # signed volume of the tetrahedron (origin, a, b, c), x6
        vol2 += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        )
        # triangle area via the cross product magnitude
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        cx, cy, cz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        area2 += math.sqrt(cx * cx + cy * cy + cz * cz)
        for p in (a, b, c):
            for i in range(3):
                lo[i] = min(lo[i], p[i])
                hi[i] = max(hi[i], p[i])
        off += 50
    return {
        "ok": True,
        "path": str(path),
        "kind": "mesh",
        "triangles": n,
        "volume": round(abs(vol2) / 6.0, 6),
        "area": round(area2 / 2.0, 6),
        "bbox": [round(hi[i] - lo[i], 6) for i in range(3)],
        "bytes": len(data),
        "wall_s": round(time.monotonic() - started, 3),
        "note": "volume by signed-tetrahedron sum; exact for a closed mesh, "
        "meaningless for an open one",
    }


def probe() -> dict[str, Any]:
    exe = openscad_bin()
    version = None
    if exe:
        try:
            out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=20)
            version = ((out.stdout or "") + (out.stderr or "")).strip().splitlines()[0]
        except Exception:
            version = "present"
    rows = probe_rows({"cadquery": "cadquery"})
    return {
        "openscad": {
            "installed": exe is not None,
            "path": exe,
            "version": version,
            "fix": None if exe else "brew install --cask openscad",
        },
        "cadquery": rows["cadquery"]
        | ({} if have("cadquery") else {"fix": "uv pip install 'tee-engine[cad]'"}),
        "formats": list(FORMATS),
        "note": "OpenSCAD runs as a separate program (GPL-2.0-or-later); "
        "-D is deliberately not exposed - use `params`.",
    }
