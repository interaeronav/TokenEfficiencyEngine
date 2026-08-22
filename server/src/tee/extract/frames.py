"""Frame registry and transforms-as-facts (decision A10, docs/research/18).

Every geometric fact carries a `frame` id. Transforms between frames are
first-class records: flat row-major 2D affine params (STAC convention),
method, residual, accuracy_m and tier. Edges form a REP-105-style
single-parent tree anchored at the site ENU hub (`site:<id>:enu`); composing
a chain accumulates every edge's accuracy so conformance can widen its
tolerance honestly. The Blender world is the identity transform of site ENU
(datum at origin, meters, Z-up).

2D (plan/horizontal) for v1; the vertical channel rides on level elevations,
which research 18 ranks as a separate, lower evidence tier for GPS sources.
"""

from __future__ import annotations

import contextlib
import json
import math
import time
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

SITE_FRAME = "site:enu"


def rss(*values: float) -> float:
    return math.sqrt(sum(v * v for v in values))


class FrameRegistry:
    def __init__(self, root: Path):
        self.path = Path(root) / "frames.json"
        self._data: dict[str, Any] = {"frames": {}, "transforms": [], "datum": None}
        self._load()
        if SITE_FRAME not in self._data["frames"]:
            self._data["frames"][SITE_FRAME] = {
                "kind": "site_enu",
                "units": "m",
                "axes": "x-east y-north z-up",
            }

    def _load(self) -> None:
        with contextlib.suppress(FileNotFoundError, json.JSONDecodeError, OSError):
            self._data = json.loads(self.path.read_text())

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=1))
        tmp.replace(self.path)

    # -- frames ------------------------------------------------------------

    def add_frame(self, frame_id: str, kind: str, units: str = "m", axes: str = "") -> None:
        self._data["frames"][frame_id] = {"kind": kind, "units": units, "axes": axes}
        self._save()

    def frames(self) -> dict[str, Any]:
        return dict(self._data["frames"])

    def set_site_datum(self, lat: float, lon: float, h: float = 0.0) -> None:
        """WGS84 anchor of the site ENU frame (GeoPose-Basic compatible)."""
        self._data["datum"] = {"lat": lat, "lon": lon, "h": h}
        self._save()

    def enu_of(self, lat: float, lon: float, h: float = 0.0) -> tuple[float, float, float]:
        datum = self._data.get("datum")
        if datum is None:
            raise TeeError(
                "no_site_datum",
                "No site datum set.",
                fix="Call ex_register with a datum (lat/lon) first.",
            )
        import pymap3d

        east, north, up = pymap3d.geodetic2enu(lat, lon, h, datum["lat"], datum["lon"], datum["h"])
        return float(east), float(north), float(up)

    # -- transforms ---------------------------------------------------------

    def add_transform(
        self,
        from_frame: str,
        to_frame: str,
        params: list[float],
        *,
        method: str,
        accuracy_m: float,
        tier: str,
        residual: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register the ACTIVE edge from_frame -> to_frame (2D affine params
        [a, b, tx, c, d, ty]). One active parent per frame: a new edge for
        the same child replaces the old one (kept in history as inactive)."""
        for frame in (from_frame, to_frame):
            if frame not in self._data["frames"]:
                raise TeeError(
                    "unknown_frame",
                    f"Frame '{frame}' is not registered.",
                    fix=f"Known frames: {', '.join(sorted(self._data['frames']))}.",
                )
        if len(params) != 6 or not all(isinstance(v, (int, float)) for v in params):
            raise TeeError("bad_transform", "params must be 6 numbers [a,b,tx,c,d,ty].")
        record = {
            "id": f"tf{len(self._data['transforms']) + 1}",
            "from": from_frame,
            "to": to_frame,
            "params": [float(v) for v in params],
            "method": method,
            "accuracy_m": float(accuracy_m),
            "tier": tier,
            "residual": residual or {},
            "active": True,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for other in self._data["transforms"]:
            if other["from"] == from_frame and other["active"]:
                other["active"] = False
        self._data["transforms"].append(record)
        self._save()
        return record

    def transforms(self) -> list[dict[str, Any]]:
        return list(self._data["transforms"])

    def chain_to_site(self, frame_id: str) -> tuple[list[list[float]], list[dict[str, Any]]]:
        """Walk active edges child -> parent up to the site frame. Returns
        (3x3 composed matrix as rows, the edge records used)."""
        matrix = _identity()
        used: list[dict[str, Any]] = []
        current = frame_id
        for _ in range(16):
            if current == SITE_FRAME:
                return matrix, used
            edge = next(
                (t for t in self._data["transforms"] if t["from"] == current and t["active"]),
                None,
            )
            if edge is None:
                raise TeeError(
                    "unregistered_frame",
                    f"No active transform chain from '{frame_id}' to the site frame "
                    f"(stuck at '{current}').",
                    fix="Register the missing transform with ex_register.",
                )
            matrix = _matmul(_to_matrix(edge["params"]), matrix)
            used.append(edge)
            current = edge["to"]
        raise TeeError("transform_cycle", f"Transform chain from '{frame_id}' never reaches site.")

    def to_site(self, frame_id: str, points: list[tuple[float, float]]):
        matrix, used = self.chain_to_site(frame_id)
        out = [_apply(matrix, x, y) for x, y in points]
        accuracy = rss(*(e["accuracy_m"] for e in used)) if used else 0.0
        return out, accuracy, used


# -- fitting -----------------------------------------------------------------


def fit_similarity(
    src: list[tuple[float, float]],
    dst: list[tuple[float, float]],
    *,
    fix_scale: float | None = None,
) -> dict[str, Any]:
    """Least-squares 2D similarity fit src -> dst (Umeyama). With
    `fix_scale`, rotation+translation are fitted at the pinned scale and the
    FREE scale is still reported, so callers can flag a units conflict when
    it deviates (>2% rule, research 18)."""
    import numpy as np

    if len(src) != len(dst) or len(src) < 2:
        raise TeeError("bad_fit", "Need >= 2 matched point pairs of equal count.")
    s = np.asarray(src, dtype=float)
    d = np.asarray(dst, dtype=float)
    mu_s, mu_d = s.mean(axis=0), d.mean(axis=0)
    sc, dc = s - mu_s, d - mu_d
    cov = dc.T @ sc / len(s)
    u, sing, vt = np.linalg.svd(cov)
    sign = np.eye(2)
    if np.linalg.det(u @ vt) < 0:
        sign[1, 1] = -1
    rotation = u @ sign @ vt
    var_s = (sc**2).sum() / len(s)
    free_scale = float(np.trace(np.diag(sing) @ sign) / var_s) if var_s > 0 else 1.0
    scale = fix_scale if fix_scale is not None else free_scale
    translation = mu_d - scale * rotation @ mu_s
    transformed = (scale * rotation @ s.T).T + translation
    residuals = np.linalg.norm(transformed - d, axis=1)
    a, b = scale * rotation[0]
    c, e = scale * rotation[1]
    return {
        "params": [
            float(a),
            float(b),
            float(translation[0]),
            float(c),
            float(e),
            float(translation[1]),
        ],
        "free_scale": free_scale,
        "scale": float(scale),
        "rotation_deg": float(math.degrees(math.atan2(rotation[1, 0], rotation[0, 0]))),
        "rmse_m": float(np.sqrt((residuals**2).mean())),
        "max_m": float(residuals.max()),
        "n": len(src),
    }


def scale_conflict(free_scale: float, pinned_scale: float, threshold: float = 0.02) -> bool:
    if pinned_scale == 0:
        return True
    return abs(free_scale - pinned_scale) / abs(pinned_scale) > threshold


# -- 3x3 affine helpers ------------------------------------------------------


def _identity() -> list[list[float]]:
    return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


def _to_matrix(params: list[float]) -> list[list[float]]:
    a, b, tx, c, d, ty = params
    return [[a, b, tx], [c, d, ty], [0.0, 0.0, 1.0]]


def _matmul(m1: list[list[float]], m2: list[list[float]]) -> list[list[float]]:
    return [[sum(m1[i][k] * m2[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def _apply(matrix: list[list[float]], x: float, y: float) -> tuple[float, float]:
    return (
        matrix[0][0] * x + matrix[0][1] * y + matrix[0][2],
        matrix[1][0] * x + matrix[1][1] * y + matrix[1][2],
    )
