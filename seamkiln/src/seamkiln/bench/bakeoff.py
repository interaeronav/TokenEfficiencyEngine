"""A53 P0b: the solver bake-off. The winner picks seamkiln's default backend.

One workload - an n x n sheet released above a sphere, 30 frames, 8
substeps - run on every backend that is present. Compile/JIT time is timed
SEPARATELY and reported, never folded into ms/frame: numba pays it once per
process and a benchmark that hides it flatters the wrong backend.

Usage:
    uv run --project server python -m seamkiln.bench.bakeoff
    uv run --with warp-lang --project server python -m seamkiln.bench.bakeoff
"""

from __future__ import annotations

import argparse
import json
import resource
import sys
import time
from dataclasses import asdict, dataclass

import numpy as np

from seamkiln.solver.backends import blender_cloth, numba_xpbd, torch_xpbd, warp_xpbd
from seamkiln.solver.problem import make_grid

SIZES = (71, 173, 347)  # ~5k, ~30k, ~120k particles
FRAMES = 30
GRID_SIZE = 1.0
RELEASE_HEIGHT = 0.6


@dataclass
class Row:
    backend: str
    device: str
    particles: int
    constraints: int
    ms_per_frame: float | None
    compile_s: float | None
    peak_rss_mb: float
    precision: str
    fingerprint: str | None
    drape_span_m: float | None
    min_radius_m: float | None
    note: str = ""


def _peak_rss_mb() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return usage / (1024 * 1024) if sys.platform == "darwin" else usage / 1024


def _measure(run, problem, *, warmup_frames: int = 1) -> tuple[float, float, np.ndarray]:
    """(compile_seconds, ms_per_frame, positions). The warm-up run absorbs
    JIT compilation and lazy kernel builds; only the second run is timed."""
    start = time.perf_counter()
    run(warmup_frames)
    compile_s = time.perf_counter() - start
    start = time.perf_counter()
    positions = run(FRAMES)
    elapsed = time.perf_counter() - start
    return compile_s, elapsed * 1000.0 / FRAMES, positions


def _drape_stats(problem, positions: np.ndarray) -> tuple[float, float]:
    """(vertical spread, closest approach to the sphere centre).

    A sheet still in free fall is perfectly flat: span ~0. A sheet that has
    landed and draped has span > 0. This is what stops the bake-off from
    timing thirty frames of nothing.
    """
    span = float(positions[:, 1].max() - positions[:, 1].min())
    radius = float(np.linalg.norm(positions - problem.sphere_center, axis=1).min())
    return span, radius


def run_all(sizes=SIZES, only: list[str] | None = None) -> list[Row]:
    rows: list[Row] = []
    want = (lambda name: True) if not only else (lambda name: any(name.startswith(p) for p in only))
    torch_devices = [d for d in ("mps", "cpu") if torch_xpbd.available(d)[0]]

    for n in sizes:
        problem = make_grid(n, size=GRID_SIZE, height=RELEASE_HEIGHT)
        base = dict(particles=problem.n_particles, constraints=problem.n_constraints)

        for device in torch_devices if want("torch") else []:
            fresh = lambda frames, d=device, size=n: torch_xpbd.simulate(  # noqa: E731
                make_grid(size, size=GRID_SIZE, height=RELEASE_HEIGHT), frames, device=d
            )
            compile_s, ms, positions = _measure(fresh, problem)
            span, radius = _drape_stats(problem, positions)
            rows.append(
                Row(
                    backend="torch-xpbd",
                    device=torch_xpbd.available(device)[1],
                    ms_per_frame=ms,
                    compile_s=compile_s,
                    peak_rss_mb=_peak_rss_mb(),
                    precision="float32" if device == "mps" else "float64",
                    fingerprint=problem.fingerprint(positions),
                    drape_span_m=span,
                    min_radius_m=radius,
                    **base,
                )
            )

        if want("numba") and numba_xpbd.available()[0]:
            fresh = lambda frames, size=n: numba_xpbd.simulate_fused(  # noqa: E731
                make_grid(size, size=GRID_SIZE, height=RELEASE_HEIGHT), frames
            )
            compile_s, ms, positions = _measure(fresh, problem)
            span, radius = _drape_stats(problem, positions)
            rows.append(
                Row(
                    backend="numba-xpbd",
                    device=numba_xpbd.available()[1],
                    ms_per_frame=ms,
                    compile_s=compile_s,
                    peak_rss_mb=_peak_rss_mb(),
                    precision="float64",
                    fingerprint=problem.fingerprint(positions),
                    drape_span_m=span,
                    min_radius_m=radius,
                    **base,
                )
            )

        ok, why = warp_xpbd.available() if want("warp") else (False, "skipped")
        if ok:
            fresh = lambda frames, size=n: warp_xpbd.simulate(  # noqa: E731
                make_grid(size, size=GRID_SIZE, height=RELEASE_HEIGHT), frames
            )
            compile_s, ms, positions = _measure(fresh, problem)
            span, radius = _drape_stats(problem, positions)
            rows.append(
                Row(
                    backend="warp-xpbd",
                    device=why,
                    ms_per_frame=ms,
                    compile_s=compile_s,
                    peak_rss_mb=_peak_rss_mb(),
                    precision="float32",
                    fingerprint=problem.fingerprint(positions),
                    drape_span_m=span,
                    min_radius_m=radius,
                    **base,
                )
            )
        else:
            rows.append(
                Row(
                    "warp-xpbd",
                    "absent",
                    ms_per_frame=None,
                    compile_s=None,
                    peak_rss_mb=0.0,
                    precision="-",
                    fingerprint=None,
                    drape_span_m=None,
                    min_radius_m=None,
                    note=why,
                    **base,
                )
            )

        ok, version = blender_cloth.available() if want("blender") else (False, "skipped")
        if ok:
            try:
                report = blender_cloth.bake(
                    problem, FRAMES, n=n, size=GRID_SIZE, height=RELEASE_HEIGHT
                )
                rows.append(
                    Row(
                        backend="blender-cloth",
                        device=version,
                        ms_per_frame=report["seconds"] * 1000.0 / FRAMES,
                        compile_s=None,
                        peak_rss_mb=0.0,  # separate process
                        precision="float32 (implicit mass-spring)",
                        fingerprint=None,  # different algorithm; positions not comparable
                        drape_span_m=None,
                        min_radius_m=None,
                        note=f"status={report['status']} "
                        f"max_error={report['max_error']:.2e} "
                        f"iters={report['avg_iterations']:.1f}",
                        **base,
                    )
                )
            except Exception as exc:
                rows.append(
                    Row(
                        "blender-cloth",
                        version,
                        ms_per_frame=None,
                        compile_s=None,
                        peak_rss_mb=0.0,
                        precision="-",
                        fingerprint=None,
                        drape_span_m=None,
                        min_radius_m=None,
                        note=f"{type(exc).__name__}: {exc}"[:200],
                        **base,
                    )
                )
    return rows


def determinism_check(n: int = 71) -> dict[str, bool]:
    """Law 7: same fixture, same backend, same hash. Twice, in one process."""
    out: dict[str, bool] = {}
    for device in ("mps", "cpu"):
        if not torch_xpbd.available(device)[0]:
            continue
        hashes = {
            make_grid(n).fingerprint(torch_xpbd.simulate(make_grid(n), 10, device=device))
            for _ in range(2)
        }
        out[f"torch-{device}"] = len(hashes) == 1
    if numba_xpbd.available()[0]:
        hashes = {
            make_grid(n).fingerprint(numba_xpbd.simulate_fused(make_grid(n), 10)) for _ in range(2)
        }
        out["numba"] = len(hashes) == 1
    if warp_xpbd.available()[0]:
        hashes = {make_grid(n).fingerprint(warp_xpbd.simulate(make_grid(n), 10)) for _ in range(2)}
        out["warp"] = len(hashes) == 1
    return out


def to_markdown(rows: list[Row]) -> str:
    lines = [
        "| backend | device | particles | ms/frame | compile s | precision "
        "| drape span m | min r m | note |",
        "| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | --- |",
    ]
    for r in rows:
        ms = "-" if r.ms_per_frame is None else f"{r.ms_per_frame:,.1f}"
        cs = "-" if r.compile_s is None else f"{r.compile_s:,.2f}"
        span = "-" if r.drape_span_m is None else f"{r.drape_span_m:.3f}"
        rad = "-" if r.min_radius_m is None else f"{r.min_radius_m:.3f}"
        lines.append(
            f"| {r.backend} | {r.device} | {r.particles:,} | {ms} | {cs} | "
            f"{r.precision} | {span} | {rad} | {r.note} |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="*", default=list(SIZES))
    parser.add_argument("--json", type=str, default="")
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="backend name prefixes to run; default all present",
    )
    args = parser.parse_args()

    rows = run_all(tuple(args.sizes), only=args.only)
    print(to_markdown(rows))
    print("\ndeterminism (same fixture twice, one process):")
    for backend, stable in determinism_check().items():
        print(f"  {backend:12s} {'stable' if stable else 'NOT REPRODUCIBLE'}")
    if args.json:
        from pathlib import Path

        Path(args.json).write_text(json.dumps([asdict(r) for r in rows], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
