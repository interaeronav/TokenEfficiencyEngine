"""DJI-spectrum metadata resolver (A42 T2; research 56 owner refinements).

Every capture set answers for itself from its files' metadata — EXIF
Make/Model plus the `drone-dji` XMP block — so the lane never asks which
aircraft flew. The resolver decides three things per set:

- **shutter type -> correction MODE** (constants stay ODM's job at
  reconstruction): mechanical-shutter cameras run with rolling-shutter
  correction OFF because they need none; electronic-shutter models in the
  table run `matched` (ODM's database supplies the readout); unknown codes
  degrade honestly — correction off, stated, with the fly-slow line.
- **positioning class -> honesty band, from the data itself**: the band
  tightens to RTK ONLY when the files carry parseable RtkStd* fields, and
  then to exactly what those std-devs support; otherwise consumer GNSS,
  meters-class absolute.
- **priors**: gimbal attitude and relative altitude ingest as orientation
  and AGL prior facts; multi-camera aircraft split into one set per
  camera code before reconstruction.

Model table sources: electronic rows are the codes ODM's rolling-shutter
database carries constants for (opendm/rollingshutter.py, read live
2026-08-29); mechanical rows are research 56's design of record (Mavic 3
wide class, Phantom 4 Pro class; the Mavic 3E's mechanical shutter also
verified at the DJI Mavic Wikipedia article, read 2026-08-29). ODM lists
readout constants even for some mechanical-shutter cameras (electronic
modes exist on them); per the design of record, mechanical wins: stills
surveys ride the mechanical shutter, correction off.
"""

from __future__ import annotations

import re
import statistics
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

# code (EXIF Model, uppercased) -> (marketing name, shutter type). Electronic
# rows split by whether ODM's RS database carries their readout constant:
# "electronic" = matched constant exists; "electronic-no-constant" = known
# aircraft, no constant -> the honest fallback with the aircraft NAMED
# (first live case: FC7303, the owner's own Mini 2 site video, 2026-08-29).
MODEL_TABLE: dict[str, tuple[str, str]] = {
    # electronic-shutter rows: constants in ODM's RS database
    "FC7203": ("DJI Mavic Mini", "electronic"),
    "FC7303": ("DJI Mini 2", "electronic-no-constant"),
    "FC3682": ("DJI Mini 3", "electronic"),
    "FC3582": ("DJI Mini 3 Pro", "electronic"),
    "FC8482": ("DJI Mini 4 Pro", "electronic"),
    "FC2103": ("DJI Mavic Air", "electronic"),
    "FC3170": ("DJI Mavic Air 2", "electronic"),
    "FC3411": ("DJI Air 2S", "electronic"),
    "FC220": ("DJI Mavic Pro", "electronic"),
    "FC300X": ("DJI Phantom 3 Professional", "electronic"),
    "FC300C": ("DJI Phantom 3 Standard", "electronic"),
    "FC300S": ("DJI Phantom 3 Advanced", "electronic"),
    "FC330": ("DJI Phantom 4", "electronic"),
    "FC350": ("DJI Inspire 1", "electronic"),
    "L1D-20C": ("DJI Mavic 2 Pro", "electronic"),
    # mechanical-shutter rows: research 56 design of record
    "FC6310": ("DJI Phantom 4 Pro", "mechanical"),
    "FC6310S": ("DJI Phantom 4 Pro V2", "mechanical"),
    "FC6310R": ("DJI Phantom 4 RTK", "mechanical"),
    "L2D-20C": ("DJI Mavic 3 (wide)", "mechanical"),
}

FLY_SLOW_NOTE = (
    "unknown camera: rolling-shutter correction off and stated in the report; "
    "fly slow and stop-and-shoot per the capture protocol"
)

_XMP_ATTR = re.compile(rb'drone-dji:(\w+)\s*=\s*"([^"]*)"')
_XMP_ELEM = re.compile(rb"<drone-dji:(\w+)>([^<]*)</drone-dji:\1>")
_PRIOR_KEYS = {
    "GimbalPitchDegree": "gimbal_pitch_deg",
    "GimbalYawDegree": "gimbal_yaw_deg",
    "GimbalRollDegree": "gimbal_roll_deg",
    "RelativeAltitude": "relative_altitude_m",
    "AbsoluteAltitude": "absolute_altitude_m",
}
_RTK_STD_KEYS = ("RtkStdLat", "RtkStdLon", "RtkStdHgt")


def read_metadata(path: Path) -> dict[str, Any]:
    """EXIF Make/Model + the drone-dji XMP attributes of one image file."""
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise TeeError(
            "extract_missing",
            "The capture resolver needs Pillow (the extract extra).",
            fix="Install the server with the 'extract' extra.",
        ) from exc
    path = Path(path)
    if not path.is_file():
        raise TeeError(
            "capture_missing_file", f"No such image: {path}", fix="Pass files that exist."
        )
    with Image.open(path) as img:
        exif = img.getexif()
        make = str(exif.get(271) or "").strip()
        model = str(exif.get(272) or "").strip()
    raw = path.read_bytes()
    xmp: dict[str, str] = {}
    for pattern in (_XMP_ATTR, _XMP_ELEM):
        for key, value in pattern.findall(raw):
            xmp[key.decode()] = value.decode(errors="replace").strip()
    return {"path": str(path), "make": make, "model": model, "xmp": xmp}


def _float(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def _positioning(files: list[dict[str, Any]]) -> dict[str, Any]:
    """RTK is claimed only when the files prove it: parseable RtkStd* fields.

    The band then tightens to exactly what the std-devs support; anything
    else is consumer GNSS, meters-class absolute."""
    stds: list[float] = []
    stamped = 0
    for meta in files:
        vals = [_float(meta["xmp"].get(k)) for k in _RTK_STD_KEYS]
        if all(v is not None and v > 0 for v in vals):
            stamped += 1
            stds.append(max(v for v in vals if v is not None))
    if stamped and stamped == len(files):
        worst_cm = max(stds) * 100.0
        return {
            "positioning": "rtk",
            "band": f"rtk ±{worst_cm:.0f} cm (from RtkStd fields, worst of set)",
        }
    if stamped:
        return {
            "positioning": "gnss",
            "band": "meters-class absolute (RTK fields on only "
            f"{stamped}/{len(files)} files - band not tightened)",
        }
    return {"positioning": "gnss", "band": "meters-class absolute (consumer GNSS)"}


def _priors(files: list[dict[str, Any]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for xmp_key, fact_key in _PRIOR_KEYS.items():
        vals = [v for meta in files if (v := _float(meta["xmp"].get(xmp_key))) is not None]
        if vals:
            out[fact_key] = round(statistics.median(vals), 2)
    return out


def resolve_set(paths: list[Path | str]) -> dict[str, Any]:
    """Split by camera code, then decide correction mode, band and priors per set."""
    if not paths:
        raise TeeError(
            "capture_empty_set", "No files given.", fix="Pass the capture set's image paths."
        )
    by_code: dict[str, list[dict[str, Any]]] = {}
    for p in paths:
        meta = read_metadata(Path(p))
        by_code.setdefault(meta["model"].upper() or "(no-model)", []).append(meta)
    sets = []
    for code, files in sorted(by_code.items()):
        name, shutter = MODEL_TABLE.get(code, (None, None))
        if shutter == "mechanical":
            correction = {"mode": "off", "why": "mechanical shutter needs none"}
        elif shutter == "electronic":
            correction = {"mode": "matched", "why": "readout constant from ODM's database"}
        elif shutter == "electronic-no-constant":
            correction = {
                "mode": "off",
                "why": f"{name}: electronic shutter but no readout constant in "
                "ODM's database - correction off and stated; fly slow, "
                "stop-and-shoot per the capture protocol",
            }
        else:
            correction = {"mode": "off", "why": FLY_SLOW_NOTE}
        entry: dict[str, Any] = {
            "camera_code": code,
            "model": name or "unknown",
            "shutter": shutter or "unknown",
            "correction": correction,
            "files": len(files),
            "priors": _priors(files),
        }
        entry.update(_positioning(files))
        sets.append(entry)
    return {"sets": sets, "split_by_camera": len(sets) > 1}
