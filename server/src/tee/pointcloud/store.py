"""The point-cloud workspace: clouds on disk, digests in the response.

One directory per project at `<project>/.tee/pointcloud`, mirroring
`ExtractStore`'s shape. A cloud is `<cloud_id>.npy` (float64 Nx3, always -
see doc 69 3.1 on why float32 is not safe as an interchange precision) plus
a JSON sidecar holding provenance, the applied transform chain and the
control baselines.

Every operation that changes geometry mints a NEW cloud_id and records its
parent, so any step is reversible and the lineage is auditable without
re-reading a single point.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

import numpy as np

from tee.kernel.errors import TeeError

# The response caps that justify this module's existence (acceptance A8).
MAX_ARRAY = 64
MAX_STRING = 2_048


class CloudStore:
    def __init__(self, project_root: Path | str):
        self.root = Path(project_root) / ".tee" / "pointcloud"

    # -- paths -------------------------------------------------------------

    def _points_path(self, cloud_id: str) -> Path:
        return self.root / f"{cloud_id}.npy"

    def _meta_path(self, cloud_id: str) -> Path:
        return self.root / f"{cloud_id}.json"

    def out_dir(self) -> Path:
        d = self.root / "out"
        d.mkdir(parents=True, exist_ok=True)
        return d

    # -- lifecycle ---------------------------------------------------------

    def mint(
        self,
        points: np.ndarray,
        *,
        parent: str | None = None,
        op: str = "open",
        extra: dict[str, Any] | None = None,
        colors: np.ndarray | None = None,
        intensity: np.ndarray | None = None,
    ) -> str:
        """Write a cloud and its sidecar; return the new cloud_id."""
        pts = np.ascontiguousarray(np.asarray(points, dtype=np.float64))
        if pts.ndim != 2 or pts.shape[1] != 3:
            raise TeeError(
                "pc_bad_points",
                f"Points must be an Nx3 array, got shape {pts.shape}.",
                fix="Pass XYZ triples.",
            )
        if len(pts) == 0:
            raise TeeError(
                "pc_empty_cloud",
                "The operation left no points.",
                fix="Widen the crop / slice, or check the input units.",
            )
        cloud_id = f"pc_{uuid.uuid4().hex[:10]}"
        self.root.mkdir(parents=True, exist_ok=True)
        np.save(self._points_path(cloud_id), pts)

        chain: list[dict[str, Any]] = []
        controls: list[dict[str, Any]] = []
        if parent:
            pm = self.meta(parent)
            chain = list(pm.get("chain") or [])
            controls = list(pm.get("controls") or [])
        chain.append({"op": op, "at": int(time.time()), **(extra or {})})

        meta: dict[str, Any] = {
            "cloud_id": cloud_id,
            "parent": parent,
            "count": len(pts),
            "chain": chain,
            "controls": controls,
        }
        if colors is not None:
            np.save(self.root / f"{cloud_id}.rgb.npy", np.asarray(colors, dtype=np.uint8))
            meta["has_colour"] = True
        elif parent and self.attr_path(parent, "rgb").is_file():
            # attributes ride along a geometry-only transform unchanged
            meta["has_colour"] = True
            meta["attrs_from"] = parent
        if intensity is not None:
            np.save(self.root / f"{cloud_id}.int.npy", np.asarray(intensity, dtype=np.uint16))
            meta["has_intensity"] = True
        elif parent and self.attr_path(parent, "int").is_file():
            meta["has_intensity"] = True
            meta["attrs_from"] = parent
        self._meta_path(cloud_id).write_text(json.dumps(meta, indent=2))
        return cloud_id

    def attr_path(self, cloud_id: str, kind: str) -> Path:
        """Where an attribute array lives, following one attrs_from hop."""
        direct = self.root / f"{cloud_id}.{kind}.npy"
        if direct.is_file():
            return direct
        meta = self._meta_path(cloud_id)
        if meta.is_file():
            src = json.loads(meta.read_text()).get("attrs_from")
            if src:
                return self.root / f"{src}.{kind}.npy"
        return direct

    def points(self, cloud_id: str) -> np.ndarray:
        path = self._points_path(cloud_id)
        if not path.is_file():
            raise TeeError(
                "pc_unknown_cloud",
                f"No cloud '{cloud_id}' in this workspace.",
                fix="Open one with pc_open; ids come back from every pc_* call.",
            )
        return np.load(path)

    def attr(self, cloud_id: str, kind: str) -> np.ndarray | None:
        path = self.attr_path(cloud_id, kind)
        return np.load(path) if path.is_file() else None

    def meta(self, cloud_id: str) -> dict[str, Any]:
        path = self._meta_path(cloud_id)
        if not path.is_file():
            raise TeeError(
                "pc_unknown_cloud",
                f"No cloud '{cloud_id}' in this workspace.",
                fix="Open one with pc_open; ids come back from every pc_* call.",
            )
        return json.loads(path.read_text())

    def update_meta(self, cloud_id: str, **fields: Any) -> dict[str, Any]:
        meta = self.meta(cloud_id)
        meta.update(fields)
        self._meta_path(cloud_id).write_text(json.dumps(meta, indent=2))
        return meta


def digest(points: np.ndarray) -> dict[str, Any]:
    """The numbers a model may see about a cloud. Never the points."""
    lo = points.min(axis=0)
    hi = points.max(axis=0)
    return {
        "count": len(points),
        "bbox_m": [round(float(v), 4) for v in (*lo, *hi)],
        "size_m": [round(float(v), 4) for v in (hi - lo)],
        "centroid_m": [round(float(v), 4) for v in points.mean(axis=0)],
    }


def spacing(points: np.ndarray, sample: int = 20_000, seed: int = 0) -> float:
    """Median nearest-neighbour distance in metres, from a bounded sample."""
    from scipy.spatial import cKDTree

    rng = np.random.default_rng(seed)
    idx = rng.choice(len(points), sample, replace=False) if len(points) > sample else slice(None)
    sub = points[idx]
    if len(sub) < 2:
        return 0.0
    d, _ = cKDTree(sub).query(sub, k=2, workers=-1)
    return float(np.median(d[:, 1]))
