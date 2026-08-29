#!/usr/bin/env python3
"""C2M probe fixture: a 2 m design plane (OBJ) + a capture cloud displaced
+38 mm along Z. CloudCompare's cloud-to-mesh distance must report a mean of
~38 mm with near-zero spread — the planted truth the T0 probe checks.

Run:  python3 c2m_fixture.py <out_dir>
Probe (once CloudCompare is installed):
  CloudCompare -SILENT -O <out>/capture_plus38mm.xyz -O <out>/design_plane.obj -C2M_DIST
"""
import os
import sys

out = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(out, exist_ok=True)

with open(os.path.join(out, "design_plane.obj"), "w") as f:
    f.write("v -1 -1 0\nv 1 -1 0\nv 1 1 0\nv -1 1 0\nf 1 2 3\nf 1 3 4\n")

n = 50
with open(os.path.join(out, "capture_plus38mm.xyz"), "w") as f:
    for i in range(n):
        for j in range(n):
            x = -0.98 + 1.96 * i / (n - 1)
            y = -0.98 + 1.96 * j / (n - 1)
            f.write(f"{x:.4f} {y:.4f} 0.0380\n")

print(f"wrote design_plane.obj + capture_plus38mm.xyz ({n * n} pts) -> {out}")
