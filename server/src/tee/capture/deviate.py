"""The deviation engine (A42 T4 = A40 V4): C2M -> budgeted as-built facts.

TEE reports; the OWNER decides. Every report ends in the decision menu
(accept-as-built / keep-design / flag-for-site) and nothing here mutates
a scene, a drawing, or anything beyond its own work dir. Facts carry
sign, extent and the capture's honesty band; severities are
plaus_check-style, and deltas below the band's floor count as
measurement noise, never as findings.

The fact lines are deterministic. When the router is available they may
be phrased by the local engine under the extractive-numbers verifier
(every number survives verbatim or the result is discarded) - the lane
never waits on a model and a router escalation simply means the
deterministic lines stand.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from tee.capture.align import _binary, _run
from tee.kernel.budget import estimate_tokens
from tee.kernel.errors import TeeError

_CC_DEFAULT = "/Applications/CloudCompare.app/Contents/MacOS/CloudCompare"
DEFAULT_BUDGET_TOKENS = 300
DEFAULT_CELL_M = 0.25
DEFAULT_NOISE_FLOOR_M = 0.005
DEFAULT_WARN_M = 0.010
DEFAULT_HIGH_M = 0.030
MENU = ("accept-as-built", "keep-design", "flag-for-site")


def _c2m_cloud(source: Path, design: Path, cfg: dict[str, Any], work_dir: Path) -> Path:
    binary = _binary(cfg, "cloudcompare", _CC_DEFAULT, "brew install --cask cloudcompare")
    work_dir.mkdir(parents=True, exist_ok=True)
    log_path = work_dir / f"c2m-{int(time.time())}.log"
    out_path = work_dir / f"c2m-{int(time.time())}.asc"
    cmd = [
        binary, "-SILENT", "-LOG_FILE", str(log_path),
        "-C_EXPORT_FMT", "ASC", "-PREC", "6",
        "-O", str(source), "-O", str(design),
        "-C2M_DIST", "-SAVE_CLOUDS", "FILE", str(out_path),
    ]  # fmt: skip
    _run(cmd, float(cfg.get("align_timeout_s", 180.0)), log_path)
    if not out_path.is_file():
        raise TeeError(
            "capture_deviation_failed",
            "C2M produced no distance cloud.",
            fix=f"See {log_path}; check the design mesh loads (OBJ/PLY).",
        )
    return out_path


def _parse_distances(path: Path) -> list[tuple[float, float, float, float]]:
    """ASC rows -> (x, y, z, signed distance); the C2M SF is the last column."""
    points = []
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            x, y, z, dist = float(parts[0]), float(parts[1]), float(parts[2]), float(parts[-1])
        except ValueError:
            continue
        points.append((x, y, z, dist))
    if not points:
        raise TeeError(
            "capture_deviation_failed",
            f"No parseable points in {path.name}.",
            fix="The exported cloud is empty - check the inputs overlap.",
        )
    return points


def _cluster(
    points: list[tuple[float, float, float, float]], floor_m: float, cell_m: float
) -> list[dict[str, Any]]:
    """Grid-bin the above-floor points, merge 8-neighbour cells, one row per
    contiguous deviation region."""
    cells: dict[tuple[int, int], list[tuple[float, float, float, float]]] = {}
    for x, y, z, dist in points:
        if abs(dist) < floor_m:
            continue
        cells.setdefault((int(x // cell_m), int(y // cell_m)), []).append((x, y, z, dist))
    parent: dict[tuple[int, int], tuple[int, int]] = {c: c for c in cells}

    def find(c):
        while parent[c] != c:
            parent[c] = parent[parent[c]]
            c = parent[c]
        return c

    for cx, cy in list(cells):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                neighbour = (cx + dx, cy + dy)
                if neighbour in cells:
                    parent[find((cx, cy))] = find(neighbour)
    groups: dict[tuple[int, int], list[tuple[float, float, float, float]]] = {}
    for cell, pts in cells.items():
        groups.setdefault(find(cell), []).extend(pts)
    clusters = []
    for pts in groups.values():
        dists = [p[3] for p in pts]
        mean = sum(dists) / len(dists)
        peak = max(dists, key=abs)
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        clusters.append(
            {
                "points": len(pts),
                "mean_m": round(mean, 4),
                "max_m": round(peak, 4),
                "extent_m": [round(max(xs) - min(xs), 2), round(max(ys) - min(ys), 2)],
                "centroid": [round(sum(xs) / len(xs), 2), round(sum(ys) / len(ys), 2)],
            }
        )
    clusters.sort(key=lambda c: abs(c["mean_m"]) * c["points"], reverse=True)
    return clusters


def _name(cluster: dict[str, Any], elements: list[dict[str, Any]] | None) -> str:
    cx, cy = cluster["centroid"]
    for element in elements or []:
        lo, hi = element.get("min") or [], element.get("max") or []
        if len(lo) >= 2 and len(hi) >= 2 and lo[0] <= cx <= hi[0] and lo[1] <= cy <= hi[1]:
            return str(element.get("name") or "element")
    return f"region@({cx:.1f},{cy:.1f})"


def _severity(mean_abs_m: float, warn_m: float, high_m: float) -> str:
    if mean_abs_m >= high_m:
        return "high"
    return "warn" if mean_abs_m >= warn_m else "info"


def deviation_report(
    source: Path,
    design: Path,
    *,
    cfg: dict[str, Any],
    work_dir: Path,
    band: str,
    elements: list[dict[str, Any]] | None = None,
    budget_tokens: int = DEFAULT_BUDGET_TOKENS,
    phrase=None,
) -> dict[str, Any]:
    """The lane's product: compact, budgeted deviation facts + the menu.

    `phrase` (optional) is a callable(list[str]) -> list[str] | None - the
    routed phrasing hook; None or a failed verification leaves the
    deterministic lines standing."""
    for path, role in ((source, "capture"), (design, "design")):
        if not Path(path).is_file():
            raise TeeError(
                "capture_align_missing_input", f"No {role} at {path}.", fix="Check the path."
            )
    floor = float(cfg.get("noise_floor_m", DEFAULT_NOISE_FLOOR_M))
    warn = float(cfg.get("sev_warn_m", DEFAULT_WARN_M))
    high = float(cfg.get("sev_high_m", DEFAULT_HIGH_M))
    cloud = _c2m_cloud(Path(source), Path(design), cfg, work_dir)
    points = _parse_distances(cloud)
    clusters = _cluster(points, floor, float(cfg.get("cluster_cell_m", DEFAULT_CELL_M)))
    within = len(points) - sum(c["points"] for c in clusters)
    for index, cluster in enumerate(clusters):
        cluster["id"] = f"d{index + 1}"
        cluster["name"] = _name(cluster, elements)
        cluster["severity"] = _severity(abs(cluster["mean_m"]), warn, high)
        mm, peak = cluster["mean_m"] * 1000, cluster["max_m"] * 1000
        ex = cluster["extent_m"]
        cluster["fact"] = (
            f"{cluster['name']}: {mm:+.0f} mm (peak {peak:+.0f} mm) over "
            f"{ex[0]:.1f}x{ex[1]:.1f} m [{cluster['severity']}]"
        )
    lines = [c["fact"] for c in clusters[:6]]
    phrasing = "deterministic"
    if phrase is not None and lines:
        try:
            better = phrase(lines)
        except Exception:  # the lane NEVER waits on or fails with a model
            better = None
        if better and len(better) == len(lines):
            lines = better
            phrasing = "routed"
    report = {
        "points": len(points),
        "within_band_pct": round(100.0 * within / len(points), 1),
        "band": band,
        "noise_floor_mm": floor * 1000,
        "deviations": lines,
        "ids": [c["id"] for c in clusters[:6]],
        "more": max(0, len(clusters) - 6),
        "phrasing": phrasing,
        "menu": list(MENU),
        "note": "TEE reports; the owner decides - nothing is applied from here",
    }
    while estimate_tokens(str(report)) > budget_tokens and len(report["deviations"]) > 1:
        report["deviations"] = report["deviations"][:-1]
        report["ids"] = report["ids"][:-1]
        report["more"] += 1
    report["_clusters"] = clusters  # full rows for the drill-down caller
    return report
