"""Binary point-cloud I/O - the thing this repo could never do (doc 69 1).

Two measured laws are enforced here rather than left to callers (doc 69 3):

1. PLY through trimesh is float32. A cloud sitting on UTM or ECEF
   coordinates loses 250 mm through a PLY round trip. So PLY export is
   ALWAYS origin-shifted and the offset is written into the sidecar.
2. LAS stores int32 ordinates against a float64 offset, and the file size
   does not change with the scale. The conventional 1e-3 spends 0.5 mm of
   the +-2 mm tolerance budget for nothing, so the default here is 1e-4.

E57 is not a Python dependency: CloudCompare already ships its reader.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

from tee.kernel.errors import TeeError

# doc 69 3.2 - 0.05 mm quantisation, +-214 km of addressable span, same bytes.
LAS_SCALE = 1e-4
# doc 69 3.1 - beyond this the float32 mantissa costs more than a millimetre.
PLY_SAFE_ORIGIN_M = 10_000.0
_CC_DEFAULT = "/Applications/CloudCompare.app/Contents/MacOS/CloudCompare"

READABLE = (".ply", ".las", ".laz", ".e57", ".xyz", ".asc", ".pts", ".txt")
WRITABLE = ("ply", "las", "laz", "e57")


def _cloudcompare(cfg: dict[str, Any] | None = None) -> str:
    """The CloudCompare binary, or a refusal naming the install (capture lane pattern)."""
    configured = str((cfg or {}).get("cloudcompare") or "")
    if configured:
        if Path(configured).is_file():
            return configured
        raise TeeError(
            "pc_cloudcompare_missing",
            f"[capture] cloudcompare = {configured} does not exist.",
            fix=f"Fix the path or remove the key to use {_CC_DEFAULT}.",
        )
    for candidate in (_CC_DEFAULT, shutil.which("CloudCompare") or ""):
        if candidate and Path(candidate).is_file():
            return candidate
    raise TeeError(
        "pc_cloudcompare_missing",
        "E57 needs CloudCompare, which is not installed.",
        fix="brew install --cask cloudcompare (2.13.2 probed), or export ply/las instead.",
    )


# -- read ------------------------------------------------------------------


def read(path: Path | str) -> dict[str, Any]:
    """Read a cloud. Returns points (float64 Nx3) plus whatever rode along."""
    path = Path(path)
    if not path.is_file():
        raise TeeError(
            "pc_missing_file", f"No file at {path}.", fix="Check the path to the scan export."
        )
    suffix = path.suffix.lower()
    if suffix == ".ply":
        return _read_ply(path)
    if suffix in (".las", ".laz"):
        return _read_las(path)
    if suffix == ".e57":
        return _read_e57(path)
    if suffix in (".xyz", ".asc", ".pts", ".txt"):
        return _read_text(path)
    raise TeeError(
        "pc_unsupported_format",
        f"'{suffix}' is not a point-cloud format this lane reads.",
        fix=f"One of: {', '.join(READABLE)}.",
    )


def _read_ply(path: Path) -> dict[str, Any]:
    import trimesh

    obj = trimesh.load(path, process=False)
    pts = np.asarray(getattr(obj, "vertices", None), dtype=np.float64)
    if pts.ndim != 2 or pts.shape[1] != 3:
        raise TeeError(
            "pc_bad_ply",
            f"{path.name} carries no Nx3 vertex array.",
            fix="Export a point cloud (not a mesh-less scene) from the scanner app.",
        )
    out: dict[str, Any] = {"points": pts, "format": "ply", "writer": _ply_writer(path)}
    colors = getattr(obj, "colors", None)
    if colors is not None:
        colors = np.asarray(colors)
        if colors.ndim == 2 and colors.shape[0] == len(pts) and colors.shape[1] >= 3:
            out["colors"] = colors[:, :3].astype(np.uint8)
    return out


def _ply_writer(path: Path) -> str | None:
    """Whatever the file says about who wrote it - never assumed (doc 69 3.4)."""
    head = path.read_bytes()[:2048].split(b"end_header")[0]
    for line in head.split(b"\n"):
        if line.startswith((b"comment", b"obj_info")):
            text = line.split(b" ", 1)[-1].decode("utf-8", "replace").strip()
            if text:
                return text[:200]
    return None


def _read_las(path: Path) -> dict[str, Any]:
    import laspy

    las = laspy.read(path)
    pts = np.c_[np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)].astype(np.float64)
    out: dict[str, Any] = {
        "points": pts,
        "format": path.suffix.lower().lstrip("."),
        "point_format": int(las.header.point_format.id),
        "las_version": str(las.header.version),
        "scales": [float(v) for v in las.header.scales],
    }
    try:
        crs = las.header.parse_crs()
        if crs is not None:
            out["srs"] = str(crs.to_string())
    except Exception:  # a malformed VLR must not fail the open
        pass
    dims = set(las.point_format.dimension_names)
    if {"red", "green", "blue"} <= dims:
        rgb = np.c_[las.red, las.green, las.blue]
        if rgb.max(initial=0) > 255:  # 16-bit LAS colour
            rgb = rgb // 257
        out["colors"] = rgb.astype(np.uint8)
    if "intensity" in dims:
        inten = np.asarray(las.intensity, dtype=np.uint16)
        if inten.any():
            out["intensity"] = inten
    return out


def _read_e57(path: Path) -> dict[str, Any]:
    """E57 via CloudCompare, which already ships the reader (doc 69 2)."""
    binary = _cloudcompare()
    tmp = path.with_suffix(".pc-e57.asc")
    cmd = [binary, "-SILENT", "-AUTO_SAVE", "OFF", "-C_EXPORT_FMT", "ASC", "-PREC", "6",
           "-O", str(path), "-SAVE_CLOUDS", "FILE", str(tmp)]  # fmt: skip
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0 or not tmp.is_file():
        tail = ((proc.stdout or "") + (proc.stderr or "")).strip().splitlines()[-2:]
        raise TeeError(
            "pc_e57_read_failed",
            f"CloudCompare could not convert {path.name}: {' | '.join(tail)[:200]}",
            fix="Open the file in CloudCompare to see the cause, or export PLY/LAS instead.",
        )
    try:
        out = _read_text(tmp)
    finally:
        tmp.unlink(missing_ok=True)
    out["format"] = "e57"
    return out


def _read_text(path: Path) -> dict[str, Any]:
    rows = np.loadtxt(path, usecols=(0, 1, 2), ndmin=2)
    if rows.shape[1] != 3:
        raise TeeError(
            "pc_bad_text_cloud",
            f"{path.name} does not start with three numeric columns.",
            fix="Expected XYZ in the first three columns.",
        )
    return {"points": rows.astype(np.float64), "format": path.suffix.lower().lstrip(".")}


# -- write -----------------------------------------------------------------


def write(
    points: np.ndarray,
    out: Path,
    fmt: str,
    *,
    colors: np.ndarray | None = None,
    intensity: np.ndarray | None = None,
) -> dict[str, Any]:
    if fmt not in WRITABLE:
        raise TeeError(
            "pc_unsupported_format",
            f"'{fmt}' is not a format this lane writes.",
            fix=f"One of: {', '.join(WRITABLE)}.",
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "ply":
        return _write_ply(points, out, colors)
    if fmt == "e57":
        return _write_e57(points, out, colors)
    return _write_las(points, out, fmt, colors, intensity)


def _write_ply(points: np.ndarray, out: Path, colors: np.ndarray | None) -> dict[str, Any]:
    """Origin-shifted ALWAYS - trimesh writes float32 (doc 69 3.1)."""
    import trimesh

    offset = points.mean(axis=0)
    shifted = points - offset
    kwargs: dict[str, Any] = {}
    if colors is not None and len(colors) == len(points):
        kwargs["colors"] = colors
    out.write_bytes(trimesh.PointCloud(shifted, **kwargs).export(file_type="ply"))
    residual = float(np.abs(shifted).max())
    return {
        "path": str(out),
        "bytes": out.stat().st_size,
        "origin_offset_m": [round(float(v), 6) for v in offset],
        "precision_note": (
            "PLY vertices are float32; the cloud was origin-shifted so the worst-case "
            f"coordinate error is {residual * 2**-23 * 1000:.4f} mm. Add origin_offset_m "
            "back to recover absolute position."
        ),
    }


def _write_las(
    points: np.ndarray,
    out: Path,
    fmt: str,
    colors: np.ndarray | None,
    intensity: np.ndarray | None,
) -> dict[str, Any]:
    import laspy

    header = laspy.LasHeader(point_format=3, version="1.4")
    header.scales = np.array([LAS_SCALE] * 3)
    header.offsets = points.min(axis=0)
    las = laspy.LasData(header)
    las.x, las.y, las.z = points[:, 0], points[:, 1], points[:, 2]
    if colors is not None and len(colors) == len(points):
        las.red = colors[:, 0].astype(np.uint16) * 257
        las.green = colors[:, 1].astype(np.uint16) * 257
        las.blue = colors[:, 2].astype(np.uint16) * 257
    if intensity is not None and len(intensity) == len(points):
        las.intensity = np.asarray(intensity, dtype=np.uint16)
    las.write(out)
    return {
        "path": str(out),
        "bytes": out.stat().st_size,
        "las_scale_m": LAS_SCALE,
        "precision_note": f"LAS quantisation is {LAS_SCALE * 500:.3f} mm (half a scale unit).",
    }


def _write_e57(points: np.ndarray, out: Path, colors: np.ndarray | None) -> dict[str, Any]:
    binary = _cloudcompare()
    stage = out.with_suffix(".pc-stage.las")
    _write_las(points, stage, "las", colors, None)
    cmd = [binary, "-SILENT", "-AUTO_SAVE", "OFF", "-C_EXPORT_FMT", "E57",
           "-O", str(stage), "-SAVE_CLOUDS", "FILE", str(out)]  # fmt: skip
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    finally:
        stage.unlink(missing_ok=True)
    if proc.returncode != 0 or not out.is_file():
        tail = ((proc.stdout or "") + (proc.stderr or "")).strip().splitlines()[-2:]
        raise TeeError(
            "pc_e57_write_failed",
            f"CloudCompare could not write E57: {' | '.join(tail)[:200]}",
            fix="Export ply or las instead, or convert in the CloudCompare GUI.",
        )
    return {"path": str(out), "bytes": out.stat().st_size}
