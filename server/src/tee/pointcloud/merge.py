"""Merging several scans into one cloud, by handing registration to `capture_*`.

There is no second ICP here on purpose. `capture/align.py` already drives
CloudCompare, already refuses an RMS over its gate, and already carries the
7-DOF degeneracy guard that A42 T6 paid for. This module's whole job is to get
points to that function in a frame it can handle, and to apply the answer back
to float64 arrays instead of re-reading a text dump.

Both clouds are shifted by the TARGET's centroid before they are written out,
so the transform comes back in a frame this module named rather than one
CloudCompare chose. A site cloud in UTM would otherwise be re-centred by
CloudCompare's own global shift, and the matrix would be silently unusable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from tee.kernel.errors import TeeError
from tee.pointcloud import io

OVERLAP_TOL_M = 0.05


def register_onto(
    source: np.ndarray,
    target: np.ndarray,
    *,
    cfg: dict[str, Any],
    work_dir: Path,
    max_rms_m: float | None = None,
    overlap_percent: int | None = None,
) -> dict[str, Any]:
    """Rigidly align `source` onto `target`; return the moved points and the fit."""
    from tee.capture.align import register_icp

    origin = target.mean(axis=0)
    work_dir.mkdir(parents=True, exist_ok=True)
    source_path = work_dir / "merge-source.las"
    target_path = work_dir / "merge-target.las"
    io.write(source - origin, source_path, "las")
    io.write(target - origin, target_path, "las")

    fit = register_icp(
        source_path,
        target_path,
        cfg=cfg,
        work_dir=work_dir,
        max_rms_m=max_rms_m,
        overlap_percent=overlap_percent,
        adjust_scale=False,
    )
    matrix = fit.get("matrix")
    if matrix and len(matrix) == 4:
        transform = np.asarray(matrix, dtype=np.float64)
        moved = (source - origin) @ transform[:3, :3].T + transform[:3, 3] + origin
    elif fit.get("registered"):
        # older CloudCompare builds write no matrix sidecar; the aligned cloud
        # itself is still authoritative, and it is in the shifted frame
        moved = io.read(Path(fit["registered"]))["points"] + origin
        if len(moved) != len(source):
            raise TeeError(
                "pc_merge_lost_points",
                f"The aligned cloud has {len(moved)} points, the source had {len(source)}.",
                fix="Decimate before merging, or upgrade CloudCompare so it writes a matrix.",
            )
    else:
        raise TeeError(
            "pc_merge_no_transform",
            "CloudCompare returned neither a transform nor an aligned cloud.",
            fix=f"Read the log at {fit.get('log')}; the ICP may have been cancelled.",
        )
    return {"points": moved, "rms_m": fit.get("rms_m"), "gate_m": fit.get("gate_m")}


def overlap(moved: np.ndarray, target: np.ndarray, tol_m: float = OVERLAP_TOL_M) -> dict[str, Any]:
    """A second opinion on the fit, computed here rather than taken on trust.

    CloudCompare's RMS is over the correspondences IT chose. This is over every
    source point: how much of the scan actually landed on the other one, and how
    far off it is where it did. A high RMS with 4% overlap is two scans of
    different rooms; a low RMS with 60% overlap is a merge worth keeping.
    """
    from scipy.spatial import cKDTree

    distances, _ = cKDTree(target).query(moved, workers=-1)
    near = distances <= tol_m
    return {
        "overlap": round(float(near.mean()), 3),
        "overlap_rms_mm": round(float(np.sqrt((distances[near] ** 2).mean()) * 1000), 1)
        if near.any()
        else None,
        "tol_mm": round(tol_m * 1000, 1),
    }
