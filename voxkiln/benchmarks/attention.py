"""Sparse-attention backend A/B (research 45, FlexAttention-MPS tuning).

Two modes:

capture: run ONE real generation with the sparse-attention entry point
wrapped, recording (stage, seqlens, heads, dim, dtype) of every call.
This is the ground truth about what the pipeline actually asks of the
attention backend - never assumed, never imported from upstream numbers.

bench: replay the captured shapes against each backend with random
tensors. Each call is timed with explicit MPS syncs, warmup excluded,
median reported. Per-call ms x captured call counts gives the projected
stage cost; the decisive check remains a full-generation A/B (battery.py
with SPARSE_ATTN_BACKEND set), because attention is not the only thing
that runs.

    uv run python benchmarks/attention.py capture --out /tmp/attn_shapes.json
    uv run python benchmarks/attention.py bench --shapes /tmp/attn_shapes.json \
        --backends sdpa,flex --repeats 7
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CAPTURE_SCRIPT = r"""
import json, sys
from voxkiln.engine import add_vendor_to_path
add_vendor_to_path()
from trellis2.modules.sparse.attention import full_attn as fa

calls = []
real = fa.sparse_scaled_dot_product_attention

def wrapped(*args, **kwargs):
    qkv = kwargs.get("qkv", args[0] if args else None)
    info = {}
    if qkv is not None and hasattr(qkv, "layout"):
        info = {
            "seqlens": [s.stop - s.start for s in qkv.layout],
            "heads": qkv.feats.shape[-2],
            "dim": qkv.feats.shape[-1],
            "dtype": str(qkv.feats.dtype).split(".")[-1],
        }
    calls.append(info)
    return real(*args, **kwargs)

fa.sparse_scaled_dot_product_attention = wrapped

from PIL import Image
import voxkiln.engine as ve

eng = ve.Engine()
image = Image.open(sys.argv[1])
eng.generate(image, seed=42, params={{
    "pipeline_type": "512",
    "texture_size": 1024,
    "target_faces": 500000,
    "repair_level": "fast",
}})

# group consecutive identical signatures into stages
out = []
for c in calls:
    sig = (tuple(c.get("seqlens", [])), c.get("heads"), c.get("dim"))
    if out and (tuple(out[-1]["seqlens"]), out[-1]["heads"], out[-1]["dim"]) == sig:
        out[-1]["count"] += 1
    else:
        out.append({**c, "count": 1})
json.dump(out, open(sys.argv[2], "w"), indent=1)
print(f"captured {{len(calls)}} calls in {{len(out)}} stages", file=sys.stderr)
"""


def bench_shape(shape: dict, backend: str, repeats: int) -> float:
    """Median wall seconds for one call of this shape on this backend."""
    import torch
    from trellis2.modules.sparse import VarLenTensor, config
    from trellis2.modules.sparse.attention.full_attn import (
        sparse_scaled_dot_product_attention,
    )

    seqlens = shape["seqlens"]
    heads, dim = shape["heads"], shape["dim"]
    dtype = getattr(torch, shape.get("dtype", "float16"))
    total = sum(seqlens)
    torch.manual_seed(0)
    feats = torch.randn(total, 3, heads, dim, device="mps", dtype=dtype)
    qkv = VarLenTensor(feats, VarLenTensor.layout_from_seqlen(seqlens))

    config.ATTN = backend
    for _ in range(2):  # warmup: compile + caches
        sparse_scaled_dot_product_attention(qkv)
    torch.mps.synchronize()

    samples = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        sparse_scaled_dot_product_attention(qkv)
        torch.mps.synchronize()
        samples.append(time.perf_counter() - t0)
    return statistics.median(samples)


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    cap = sub.add_parser("capture")
    cap.add_argument("--image", default="eval_images/T.png")
    cap.add_argument("--out", required=True)
    bn = sub.add_parser("bench")
    bn.add_argument("--shapes", required=True)
    bn.add_argument("--backends", default="sdpa,flex")
    bn.add_argument("--repeats", type=int, default=7)
    bn.add_argument("--out", required=True)
    args = ap.parse_args()

    if args.mode == "capture":
        script = CAPTURE_SCRIPT.replace("{{", "{").replace("}}", "}")
        proc = subprocess.run(
            [sys.executable, "-c", script, str(ROOT / args.image), args.out],
            cwd=ROOT,
        )
        return proc.returncode

    # bench
    from voxkiln.engine import add_vendor_to_path

    add_vendor_to_path()
    shapes = json.loads(Path(args.shapes).read_text())
    rows = []
    for shape in shapes:
        row = {
            "seqlens": shape["seqlens"],
            "heads": shape["heads"],
            "dim": shape["dim"],
            "count": shape["count"],
        }
        for backend in args.backends.split(","):
            ms = bench_shape(shape, backend, args.repeats) * 1000
            row[f"{backend}_ms"] = round(ms, 3)
            row[f"{backend}_stage_s"] = round(ms * shape["count"] / 1000, 2)
        rows.append(row)
    Path(args.out).write_text(json.dumps(rows, indent=1) + "\n")
    print(json.dumps(rows, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
