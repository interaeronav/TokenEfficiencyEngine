"""Stock-vs-ours battery (research 48).

One row per input x pipeline x seed x arm. Each generation runs in a FRESH
SUBPROCESS: the arm is selected by an environment variable the vendored VAEs
read once, and a cold process is also the only honest way to sample peak
memory and keep one run's allocator state out of the next one's timing.

Geometry metrics come from the exported GLB - the artifact that ships - via
voxkiln.metrics, not from the raw decode mesh.

    uv run python benchmarks/battery.py --images eval_images/T.png \
        --seeds 42 --pipelines 512 --arms ours,stock --out /tmp/rows.json
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def one_run(image: Path, seed: int, pipeline: str, arm: str, out_dir: Path) -> dict:
    """Generate once in a cold process; return the row."""
    run_dir = out_dir / f"{arm}_{image.stem[:12]}_{pipeline}_{seed}"
    env = dict(os.environ)
    env["VOXKILN_STOCK"] = "1" if arm == "stock" else "0"
    cmd = [
        sys.executable,
        "-m",
        "voxkiln.cli",
        "gen",
        str(image),
        "--seed",
        str(seed),
        "--pipeline",
        pipeline,
        "--out",
        str(run_dir),
        "--no-cache",
    ]
    started = time.monotonic()
    proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    wall = time.monotonic() - started
    # ru_maxrss of the reaped child, in bytes on macOS
    peak_gb = round(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 2**30, 2)

    row = {
        "image": image.name,
        "pipeline": pipeline,
        "seed": seed,
        "arm": arm,
        "wall_s": round(wall, 1),
        "peak_rss_gb_cumulative": peak_gb,
    }
    payload = _last_json(proc.stdout)
    if payload is None or payload.get("state") == "failed":
        row["ok"] = False
        row["error"] = (payload or {}).get("message") or proc.stderr.strip()[-300:]
        return row
    row["ok"] = True
    report = payload.get("report", payload)
    stats = report.get("stats", {})
    row.update(
        {
            "mesh_hash": report.get("mesh_hash"),
            "tris": stats.get("tris"),
            "verts": stats.get("verts"),
            "watertight": stats.get("watertight"),
            "boundary_loops": stats.get("boundary_loops"),
            "nonmanifold_edges": stats.get("nonmanifold_edges"),
            "degenerate_faces": stats.get("degenerate_faces"),
            "components": stats.get("components"),
            "uv_overlap": stats.get("uv_overlap"),
            "texel_density_cv": stats.get("texel_density_cv"),
            "accepted": (report.get("verdict") or {}).get("accepted"),
            "timings_s": report.get("timings_s"),
            "glb": (report.get("files") or {}).get("glb"),
        }
    )
    return row


def _last_json(text: str) -> dict | None:
    """The CLI prints progress then one JSON document."""
    start = text.rfind("\n{")
    if start == -1:
        start = text.find("{")
    if start == -1:
        return None
    try:
        return json.loads(text[start:])
    except ValueError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True, help="comma-separated paths")
    ap.add_argument("--seeds", default="0,42,1234")
    ap.add_argument("--pipelines", default="512")
    ap.add_argument("--arms", default="ours,stock")
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--cooldown",
        type=float,
        default=0.0,
        help="seconds to idle between runs (thermal protocol)",
    )
    args = ap.parse_args()

    images = [Path(p) for p in args.images.split(",")]
    seeds = [int(s) for s in args.seeds.split(",")]
    pipelines = args.pipelines.split(",")
    arms = args.arms.split(",")
    out_path = Path(args.out)
    out_dir = out_path.parent / "glb"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    total = len(images) * len(seeds) * len(pipelines) * len(arms)
    n = 0
    for image in images:
        for pipeline in pipelines:
            for seed in seeds:
                for arm in arms:
                    n += 1
                    print(f"[{n}/{total}] {arm} {image.name} {pipeline} seed={seed}", flush=True)
                    row = one_run(image, seed, pipeline, arm, out_dir)
                    print(
                        "   ",
                        json.dumps({k: row[k] for k in ("ok", "wall_s") if k in row}),
                        flush=True,
                    )
                    rows.append(row)
                    out_path.write_text(json.dumps(rows, indent=1) + "\n")
                    if args.cooldown:
                        time.sleep(args.cooldown)
    print(f"wrote {len(rows)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
