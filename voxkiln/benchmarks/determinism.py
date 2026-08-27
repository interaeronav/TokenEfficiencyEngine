"""Same-seed determinism: N runs of one image at one seed, hashes compared.

Research 48 is explicit that upstream seeds only the global RNG and uses no
deterministic-algorithm flags, so reproducibility must be MEASURED here, not
assumed - and never claimed across devices.

    uv run python benchmarks/determinism.py --image eval_images/T.png \
        --seed 42 --runs 3 --out /tmp/determinism.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--pipeline", default="512")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = []
    for i in range(args.runs):
        run_dir = Path("/tmp/vk_out") / f"det_{args.seed}_{i}"
        run_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable,
            "-m",
            "voxkiln.cli",
            "gen",
            args.image,
            "--seed",
            str(args.seed),
            "--pipeline",
            args.pipeline,
            "--out",
            str(run_dir),
            "--no-cache",
        ]
        started = time.monotonic()
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        wall = round(time.monotonic() - started, 1)
        text = proc.stdout
        start = text.rfind("\n{")
        payload = None
        if start != -1:
            try:
                payload = json.loads(text[start:])
            except ValueError:
                payload = None
        row = {"run": i, "wall_s": wall}
        if not payload or payload.get("state") == "failed":
            row["ok"] = False
            row["error"] = (payload or {}).get("message") or proc.stderr[-300:]
        else:
            report = payload.get("report", payload)
            row["ok"] = True
            row["mesh_hash"] = report.get("mesh_hash")
            row["tris"] = (report.get("stats") or {}).get("tris")
            row["verts"] = (report.get("stats") or {}).get("verts")
            row["glb"] = (report.get("files") or {}).get("glb")
            row["timings_s"] = report.get("timings_s")
        rows.append(row)
        print(json.dumps(row), flush=True)
        Path(args.out).write_text(json.dumps(rows, indent=1) + "\n")

    hashes = {r.get("mesh_hash") for r in rows if r.get("ok")}
    verdict = {
        "runs": len(rows),
        "ok_runs": sum(1 for r in rows if r.get("ok")),
        "distinct_mesh_hashes": len(hashes),
        "deterministic": len(hashes) == 1 and len(rows) == sum(1 for r in rows if r.get("ok")),
    }
    print(json.dumps(verdict))
    Path(args.out).write_text(json.dumps({"runs": rows, "verdict": verdict}, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
