"""Georeference + align (A42 T3 = A40 V3): CloudCompare ICP registration
and the qgis_process terrain lane.

The datum law, inherited never re-derived: the TARGET (the design model,
sitting on the locked site datum) is truth - registration transforms the
capture INTO that frame and never touches the target. A bad registration
REFUSES with its numbers instead of producing confident nonsense; the
quality gate (max RMS) is explicit and configurable.

Terrain products (contours, hillshade, DEM difference) run headless
through qgis_process; refusals name the missing binary and its install.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

DEFAULT_MAX_RMS_M = 0.05
DEFAULT_TIMEOUT_S = 180.0
_QGIS_DEFAULT = "/Applications/QGIS-final-4_2_1.app/Contents/MacOS/qgis_process"
_CC_DEFAULT = "/Applications/CloudCompare.app/Contents/MacOS/CloudCompare"

_RMS_LINE = re.compile(r"\bRMS: *([0-9.eE+-]+)")
_MATRIX_ROW = re.compile(
    r"^\s*(-?[0-9.eE+-]+)\s+(-?[0-9.eE+-]+)\s+(-?[0-9.eE+-]+)\s+(-?[0-9.eE+-]+)\s*$"
)

TERRAIN_OPS = {
    "contours": ("gdal:contour", "the vector contour lines"),
    "hillshade": ("gdal:hillshade", "the shaded-relief raster"),
    "dem_diff": ("gdal:rastercalculator", "the A-B difference raster"),
}


def _binary(cfg: dict[str, Any], key: str, default: str, install_fix: str) -> str:
    configured = str(cfg.get(key) or "")
    if configured:  # an explicit config that is wrong refuses loudly
        if Path(configured).is_file():
            return configured
        raise TeeError(
            f"capture_{key}_missing",
            f"[capture] {key} = {configured} does not exist.",
            fix=f"Fix the path or remove the key to use {default}.",
        )
    for candidate in (default, shutil.which(Path(default).name) or ""):
        if candidate and Path(candidate).is_file():
            return candidate
    raise TeeError(
        f"capture_{key}_missing",
        f"No {key} binary found (looked at {default} and PATH).",
        fix=install_fix,
    )


def _run(cmd: list[str], timeout_s: float, log_path: Path | None = None) -> str:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        raise TeeError(
            "capture_align_timeout",
            f"{Path(cmd[0]).name} exceeded {timeout_s:.0f} s.",
            fix="Decimate the inputs or raise [capture] align_timeout_s.",
        ) from exc
    output = (proc.stdout or "") + (proc.stderr or "")
    if log_path is not None:
        with_log = log_path.read_text(errors="replace") if log_path.is_file() else ""
        output += "\n" + with_log
    if proc.returncode != 0:
        tail = output.strip().splitlines()[-3:]
        raise TeeError(
            "capture_align_failed",
            f"{Path(cmd[0]).name} exited {proc.returncode}: {' | '.join(tail)[:300]}",
            fix="The log names the cause; check inputs exist and formats match.",
        )
    return output


def register_icp(
    source: Path,
    target: Path,
    *,
    cfg: dict[str, Any],
    work_dir: Path,
    max_rms_m: float | None = None,
    overlap_percent: int | None = None,
    adjust_scale: bool = False,
) -> dict[str, Any]:
    """ICP-register `source` (the capture) onto `target` (design truth).

    CloudCompare's CLI aligns the FIRST loaded entity onto the second -
    verified live against a planted transform before adoption (T3)."""
    for path, role in ((source, "source"), (target, "target")):
        if not Path(path).is_file():
            raise TeeError(
                "capture_align_missing_input",
                f"No {role} at {path}.",
                fix="Point at the reconstruction artifact / design export.",
            )
    binary = _binary(
        cfg, "cloudcompare", _CC_DEFAULT, "brew install --cask cloudcompare (2.13.2 probed)"
    )
    limit = float(
        max_rms_m if max_rms_m is not None else cfg.get("icp_max_rms_m", DEFAULT_MAX_RMS_M)
    )
    work_dir.mkdir(parents=True, exist_ok=True)
    stamp = int(time.time())
    log_path = work_dir / f"icp-{stamp}.log"
    registered_path = work_dir / f"registered-{stamp}.asc"
    cmd = [
        binary, "-SILENT", "-LOG_FILE", str(log_path), "-AUTO_SAVE", "OFF",
        "-C_EXPORT_FMT", "ASC", "-PREC", "6",
        "-O", str(source), "-O", str(target), "-ICP",
    ]  # fmt: skip
    if adjust_scale:
        # video-derived SfM carries arbitrary scale: estimate it (7-DOF ICP)
        # and REPORT it - the honesty band names where scale came from
        cmd += ["-ADJUST_SCALE"]
    if overlap_percent:
        cmd += ["-OVERLAP", str(int(overlap_percent))]
    # save the ALIGNED source cloud - downstream C2M must run on the
    # registered cloud, never the raw one
    cmd += ["-SAVE_CLOUDS", "FILE", str(registered_path)]
    output = _run(cmd, float(cfg.get("align_timeout_s", DEFAULT_TIMEOUT_S)), log_path)
    rms_match = _RMS_LINE.search(output)
    if rms_match is None:
        raise TeeError(
            "capture_bad_registration",
            "CloudCompare reported no final RMS - the alignment did not converge.",
            fix="Check overlap between capture and design; pass overlap_percent.",
        )
    rms = float(rms_match.group(1))
    # CloudCompare writes the transform to a sidecar next to the source;
    # fall back to matrix rows in the log/console for other builds.
    matrix = None
    sidecars = sorted(Path(source).parent.glob(f"{Path(source).stem}_REGISTRATION_MATRIX*.txt"))
    text = sidecars[-1].read_text() if sidecars else output
    rows = [
        [round(float(v), 6) for v in m.groups()]
        for line in text.splitlines()
        if (m := _MATRIX_ROW.match(line))
    ]
    if len(rows) >= 4:
        matrix = rows[-4:]
    if rms > limit:
        raise TeeError(
            "capture_bad_registration",
            f"ICP RMS {rms:.4f} m exceeds the {limit:.3f} m gate - refusing a "
            "confident-looking misregistration.",
            fix="Improve overlap (scale references, more coverage) or raise "
            "[capture] icp_max_rms_m deliberately.",
        )
    result = {
        "rms_m": round(rms, 4),
        "gate_m": limit,
        "matrix": matrix,
        "frame": "target = design truth (locked datum); source transformed, target untouched",
        "log": str(log_path),
    }
    if registered_path.is_file():
        result["registered"] = str(registered_path)
    if adjust_scale:
        scale_match = re.search(r"[Ss]cale: *([0-9.eE+-]+)", output)
        result["scale"] = float(scale_match.group(1)) if scale_match else "estimated (see log)"
        result["scale_note"] = "scale from 7-DOF ICP, not GPS - relative accuracy only"
    return result


def terrain_op(
    op: str,
    dem: Path,
    *,
    cfg: dict[str, Any],
    work_dir: Path,
    dem2: Path | None = None,
    interval_m: float = 1.0,
) -> dict[str, Any]:
    """One headless qgis_process product on a DEM (contours/hillshade/diff)."""
    if op not in TERRAIN_OPS:
        raise TeeError(
            "capture_unknown_terrain_op",
            f"'{op}' is not a terrain op.",
            fix=f"One of: {', '.join(sorted(TERRAIN_OPS))}.",
        )
    if not Path(dem).is_file():
        raise TeeError(
            "capture_align_missing_input", f"No DEM at {dem}.", fix="Point at a raster file."
        )
    binary = _binary(cfg, "qgis_process", _QGIS_DEFAULT, "brew install --cask qgis (4.2.1 probed)")
    algorithm, product = TERRAIN_OPS[op]
    work_dir.mkdir(parents=True, exist_ok=True)
    suffix = ".gpkg" if op == "contours" else ".tif"
    out_path = work_dir / f"{op}-{int(time.time())}{suffix}"
    params: dict[str, Any] = {"INPUT": str(dem), "OUTPUT": str(out_path)}
    if op == "contours":
        params.update({"INTERVAL": interval_m, "FIELD_NAME": "ELEV"})
    if op == "hillshade":
        params.update({"BAND": 1, "Z_FACTOR": 1})
    if op == "dem_diff":
        if dem2 is None or not Path(dem2).is_file():
            raise TeeError(
                "capture_align_missing_input",
                "dem_diff needs dem2 (the surface to subtract).",
                fix="Pass dem2=<the second raster>.",
            )
        params = {
            "INPUT_A": str(dem),
            "BAND_A": 1,
            "INPUT_B": str(dem2),
            "BAND_B": 1,
            "FORMULA": "A-B",
            "OUTPUT": str(out_path),
        }
    cmd = [binary, "run", algorithm, "--json", "--"]
    cmd += [f"{key}={value}" for key, value in params.items()]
    output = _run(cmd, float(cfg.get("align_timeout_s", DEFAULT_TIMEOUT_S)))
    json_start = output.find("{")
    try:
        payload = json.loads(output[json_start:]) if json_start >= 0 else {}
    except json.JSONDecodeError:
        payload = {}
    result_path = str((payload.get("results") or {}).get("OUTPUT") or out_path)
    if not Path(result_path).is_file():
        raise TeeError(
            "capture_align_failed",
            f"{algorithm} reported no output file.",
            fix="Check the DEM's CRS and band; run qgis_process manually to see the log.",
        )
    return {"op": op, "product": product, "path": result_path, "algorithm": algorithm}
