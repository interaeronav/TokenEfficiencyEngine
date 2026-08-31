"""A45 P2c — DICOM archives (Orthanc) and volume statistics (MONAI).

Two seams, deliberately different:

* **Orthanc** is reached over **plain HTTP only**, never imported. It is
  GPL-3.0-or-later and its default plugins include AGPL ones; upstream's
  own licensing FAQ blesses "calling Orthanc from a third-party system
  (using REST API or DICOM protocol)" while stating that an in-process
  plugin becomes GPL "by copyleft contamination". TEE therefore never
  writes an Orthanc plugin and never links it. Zero new dependencies: the
  client is `urllib` from the standard library.
* **MONAI** (Apache-2.0) is a normal in-process import, lazy, behind the
  `[medimg]` extra.

**PHI is off by default.** PatientName, PatientBirthDate, PatientID,
AccessionNumber and ReferringPhysicianName are omitted from every list and
summary unless a call explicitly passes `phi=True`. This is both the
largest per-row token saving available and the right default for medical
data: a study list is for finding a study, and identity is rarely what the
question needed.

IDs are returned WHOLE. An abbreviated identifier is not an identifier:
it cannot be passed to the next call, and a compact answer that forces a
re-query is not compact. Orthanc's 44-character UUIDs cost ~12 tokens each
and buy a working handle, which is the right trade.

Token discipline: an archive answer is counts and stable Orthanc IDs, plus
the few DICOM tags that identify a series clinically (Modality,
Description, instance count). Never pixel data, never a full tag dump -
those are explicit second calls against an ID.
"""

from __future__ import annotations

import base64
import contextlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from tee.fleet.probe import have, need, probe_rows
from tee.kernel.errors import TeeError

DEFAULT_URL = "http://127.0.0.1:8042"
TIMEOUT = 30.0
LIST_CAP = 200
DEFAULT_LIMIT = 25

# Identifying tags, withheld unless explicitly requested (see module docstring).
PHI_TAGS = frozenset(
    {
        "PatientName",
        "PatientID",
        "PatientBirthDate",
        "PatientSex",
        "AccessionNumber",
        "ReferringPhysicianName",
        "InstitutionName",
        "OtherPatientIDs",
    }
)

LEVELS = {
    "patients": "Patient",
    "studies": "Study",
    "series": "Series",
    "instances": "Instance",
}

# What a study row is FOR: enough to choose one, nothing more.
STUDY_TAGS = ("StudyDate", "StudyTime", "StudyDescription", "ModalitiesInStudy")
SERIES_TAGS = ("Modality", "SeriesDescription", "SeriesNumber", "BodyPartExamined")


def _cfg(spec: dict[str, Any]) -> tuple[str, str | None, str | None]:
    url = str(spec.get("url") or DEFAULT_URL).rstrip("/")
    return url, spec.get("username"), spec.get("password")


def _call(spec: dict[str, Any], path: str, method: str = "GET", body: Any = None) -> Any:
    """One HTTP call to Orthanc. Read verbs only - see `_GUARD`."""
    url, user, pw = _cfg(spec)
    if method not in ("GET", "POST"):
        raise TeeError(
            "med_forbidden_method",
            f"{method} is not available through TEE.",
            fix="TEE reads a DICOM archive; it does not modify or delete studies.",
        )
    full = f"{url}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(full, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if user is not None:
        token = base64.b64encode(f"{user}:{pw or ''}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            raise TeeError(
                "med_unauthorized",
                f"Orthanc at {url} refused the credentials (401).",
                fix="Pass username/password, or set them in [med] in .tee/config.toml. "
                "Orthanc 1.13+ refuses to start without a declared user.",
            ) from exc
        detail = exc.read()[:200].decode(errors="replace")
        raise TeeError(
            "med_http_error",
            f"Orthanc returned {exc.code} for {path}: {detail}",
            fix="Check the resource id and that the plugin serving it is loaded.",
        ) from exc
    except (urllib.error.URLError, OSError) as exc:
        raise TeeError(
            "med_unreachable",
            f"No Orthanc at {url} ({exc}).",
            fix="Start one: docker run -d -p 8042:8042 -e ORTHANC_PASSWORD=... "
            "-e DICOM_WEB_PLUGIN_ENABLED=true orthancteam/orthanc:latest "
            "(TEE never bundles it - it is GPLv3).",
        ) from exc
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_bytes": len(raw)}


def _strip_phi(tags: dict[str, Any], phi: bool) -> dict[str, Any]:
    if phi:
        return tags
    return {k: v for k, v in tags.items() if k not in PHI_TAGS}


def system(spec: dict[str, Any]) -> dict[str, Any]:
    """Is the archive reachable, and what does it hold?"""
    started = time.monotonic()
    sysinfo = _call(spec, "/system")
    counts = {}
    # Orthanc's level names, spelled out. Deriving them from the plural by
    # slicing produced "Studie" and a 400 - string surgery on a protocol
    # vocabulary is a bug waiting for a plural that is not regular.
    for level, orthanc_level in LEVELS.items():
        got = _call(spec, "/tools/count-resources", "POST", {"Level": orthanc_level, "Query": {}})
        counts[level] = int((got or {}).get("Count", 0))
    return {
        "ok": True,
        "url": _cfg(spec)[0],
        "version": sysinfo.get("Version"),
        "api_version": sysinfo.get("ApiVersion"),
        "counts": counts,
        "plugins": _call(spec, "/plugins"),
        "wall_s": round(time.monotonic() - started, 3),
        "phi": "withheld by default - pass phi=true to include patient identifiers",
    }


def find_studies(spec: dict[str, Any]) -> dict[str, Any]:
    """Search studies. Returns compact rows with stable Orthanc IDs."""
    query = dict(spec.get("query") or {})
    limit = max(1, min(int(spec.get("limit") or DEFAULT_LIMIT), LIST_CAP))
    phi = bool(spec.get("phi"))
    started = time.monotonic()

    total = int(
        (
            _call(spec, "/tools/count-resources", "POST", {"Level": "Study", "Query": query}) or {}
        ).get("Count", 0)
    )
    found = (
        _call(
            spec,
            "/tools/find",
            "POST",
            {
                "Level": "Study",
                "Query": query,
                "Limit": limit,
                "Expand": True,
                "ResponseContent": ["MainDicomTags", "Children", "Parent"],
                "RequestedTags": list(STUDY_TAGS),
            },
        )
        or []
    )
    rows = []
    for st in found:
        tags = dict(st.get("MainDicomTags") or {})
        tags.update(dict(st.get("RequestedTags") or {}))
        patient = dict(st.get("PatientMainDicomTags") or {})
        row: dict[str, Any] = {"id": str(st.get("ID", ""))}
        for k in STUDY_TAGS:
            if tags.get(k):
                row[k] = tags[k]
        row["series"] = len(st.get("Series") or [])
        if phi:
            row.update({k: v for k, v in patient.items() if k in PHI_TAGS})
        rows.append(row)
    out: dict[str, Any] = {
        "ok": True,
        "total": total,
        "returned": len(rows),
        "studies": rows,
        "wall_s": round(time.monotonic() - started, 3),
    }
    if total > len(rows):
        out["more"] = f"{total - len(rows)} more - raise limit (cap {LIST_CAP}) or narrow query"
    if not phi:
        out["phi"] = "patient identifiers withheld - pass phi=true if the task needs them"
    return out


def study_tree(spec: dict[str, Any]) -> dict[str, Any]:
    """One study's series, compactly. Never instance-level, never pixels."""
    sid = str(spec.get("study_id") or "").strip()
    if not sid:
        raise TeeError(
            "med_bad_spec", "study_id is required.", fix="Take one from med_find_studies."
        )
    phi = bool(spec.get("phi"))
    st = _call(spec, f"/studies/{sid}")
    series_rows = []
    for series_id in st.get("Series") or []:
        se = _call(spec, f"/series/{series_id}")
        tags = dict(se.get("MainDicomTags") or {})
        row = {"id": str(series_id), "instances": len(se.get("Instances") or [])}
        for k in SERIES_TAGS:
            if tags.get(k):
                row[k] = tags[k]
        series_rows.append(row)
    tags = _strip_phi(dict(st.get("MainDicomTags") or {}), phi)
    out = {
        "ok": True,
        "study_id": sid,
        "study": tags,
        "series": series_rows,
        "n_series": len(series_rows),
        "n_instances": sum(r["instances"] for r in series_rows),
    }
    if not phi:
        out["phi"] = "withheld"
    return out


def instance_tags(spec: dict[str, Any]) -> dict[str, Any]:
    """The DICOM header of one instance - explicitly, and still without
    pixel data: `simplify` stops at (7fe0,0010) by construction."""
    iid = str(spec.get("instance_id") or "").strip()
    if not iid:
        raise TeeError(
            "med_bad_spec", "instance_id is required.", fix="Take one from med_study_tree."
        )
    phi = bool(spec.get("phi"))
    only = [str(t) for t in (spec.get("tags") or [])]
    tags = _call(spec, f"/instances/{iid}/simplified-tags") or {}
    # PixelData may simply be absent (RTSTRUCT, SR, encapsulated PDF), so
    # this is a .get() - a KeyError here would be a nondeterministic crash
    # depending on which instance the caller happened to pick.
    tags.pop("PixelData", None)
    if only:
        tags = {k: v for k, v in tags.items() if k in only}
    tags = _strip_phi(tags, phi)
    return {
        "ok": True,
        "instance_id": iid,
        "n_tags": len(tags),
        "tags": tags,
        "note": "pixel data is never returned; use the archive's own viewer for images",
    }


# Reader dispatch, done here rather than by MONAI. `LoadImage` is a
# dispatcher, and importing it costs **torch: 505 MB installed and over 60
# seconds on first import** - measured, and it had already timed out a live
# tool call. TEE wanted an array and four scalars. pydicom, nibabel and
# numpy give exactly that for a few MB and a few milliseconds. MONAI is
# still USED when present (it reads formats these do not), it is simply no
# longer required to compute a mean.
def _read_volume(path: str):
    """-> (array, meta). Raises TeeError naming the package that reads it."""
    import numpy as np

    p = Path(path).expanduser()
    suffix = "".join(p.suffixes).lower()

    if suffix.endswith(".npy") or suffix.endswith(".npz"):
        data = np.load(p, allow_pickle=False)
        if hasattr(data, "files"):  # npz
            data = data[data.files[0]]
        return np.asarray(data), {}

    if suffix.endswith(".nii") or suffix.endswith(".nii.gz"):
        nib = need("nibabel", "medimg", what="the NIfTI reader")
        img = nib.load(str(p))
        return np.asarray(img.dataobj), {"pixdim": list(img.header["pixdim"])}

    if suffix.endswith(".dcm") or suffix.endswith(".dicom"):
        pydicom = need("pydicom", "medimg", what="the DICOM reader")
        ds = pydicom.dcmread(str(p))
        if not hasattr(ds, "pixel_array"):
            raise TeeError(
                "med_no_pixels",
                f"{p.name} is a DICOM object with no pixel data "
                f"(Modality {getattr(ds, 'Modality', '?')}).",
                fix="RTSTRUCT, SR and encapsulated PDF carry no image; "
                "use med_instance_tags to read them.",
            )
        arr = np.asarray(ds.pixel_array, dtype=np.float32)
        # Hounsfield units, if the file declares the rescale
        slope = float(getattr(ds, "RescaleSlope", 1) or 1)
        intercept = float(getattr(ds, "RescaleIntercept", 0) or 0)
        if (slope, intercept) != (1.0, 0.0):
            arr = arr * slope + intercept
        meta = {}
        spacing = getattr(ds, "PixelSpacing", None)
        thickness = getattr(ds, "SliceThickness", None)
        if spacing is not None:
            meta["pixdim"] = [1.0, float(spacing[0]), float(spacing[1])] + (
                [float(thickness)] if thickness else []
            )
        return arr, meta

    # Everything else: try MONAI if it happens to be here, then pillow.
    # A failure in either must still end in a message naming the reader,
    # never a bare library traceback.
    if have("monai"):
        try:
            from monai.transforms import LoadImage

            data, meta = LoadImage(image_only=False)(str(p))
            return np.asarray(data), dict(meta or {})
        except Exception:
            pass
    if have("PIL"):
        try:
            from PIL import Image

            return np.asarray(Image.open(p)), {}
        except Exception:
            pass
    raise TeeError(
        "med_unreadable",
        f"No reader here handles '{p.suffix or p.name}'.",
        fix="uv pip install 'tee-engine[medimg]' covers DICOM (.dcm), NIfTI "
        "(.nii/.nii.gz) and numpy (.npy) directly - no torch needed. Other "
        "formats need MONAI, which does pull torch.",
    )


def volume_stats(spec: dict[str, Any]) -> dict[str, Any]:
    """Scalar statistics of a local image volume - shape, range, spacing,
    non-zero fraction. Never the voxel array."""
    need("numpy", "medimg", what="numpy")
    import numpy as np

    path = str(spec.get("path") or "").strip()
    if not path:
        raise TeeError(
            "med_bad_spec",
            "path is required (.dcm, .nii/.nii.gz, .npy, or an image).",
            fix="A local file this machine can read.",
        )
    if not Path(path).expanduser().exists():
        raise TeeError("med_bad_spec", f"No such file: {path}", fix="Check the path.")
    started = time.monotonic()
    try:
        arr, meta = _read_volume(path)
    except TeeError:
        raise
    except Exception as exc:
        raise TeeError(
            "med_unreadable",
            f"Could not read {Path(path).name}: {str(exc)[:180]}",
            fix="Check the file is a valid image or volume.",
        ) from exc

    arr = np.asarray(arr)
    finite = arr[np.isfinite(arr)] if arr.size else arr
    out = {
        "ok": True,
        "path": path,
        "shape": list(arr.shape),
        "dtype": str(arr.dtype),
        "voxels": int(arr.size),
        "min": round(float(finite.min()), 4) if finite.size else None,
        "max": round(float(finite.max()), 4) if finite.size else None,
        "mean": round(float(finite.mean()), 4) if finite.size else None,
        "std": round(float(finite.std()), 4) if finite.size else None,
        "nonzero_fraction": round(float((arr != 0).mean()), 6) if arr.size else None,
        "wall_s": round(time.monotonic() - started, 3),
    }
    spacing = (meta or {}).get("pixdim")
    if spacing is not None:
        # pixdim shape varies by reader; missing spacing is not an error
        with contextlib.suppress(Exception):
            out["spacing"] = [round(float(x), 4) for x in list(spacing)[1:4]]
    return out


def backends(spec: dict[str, Any] | None = None) -> dict[str, Any]:
    rows = probe_rows({"monai": "monai", "numpy": "numpy", "torch": "torch"})
    out: dict[str, Any] = {"libraries": rows}
    try:
        info = system(dict(spec or {}))
        out["orthanc"] = {
            "reachable": True,
            "url": info["url"],
            "version": info["version"],
            "counts": info["counts"],
        }
    except TeeError as exc:
        out["orthanc"] = {"reachable": False, "why": exc.message, "fix": exc.fix}
    if not rows["monai"]["installed"]:
        out["fix"] = "uv pip install 'tee-engine[medimg]'"
    return out
