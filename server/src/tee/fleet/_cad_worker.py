"""A46 P1b — CadQuery in its own interpreter, because of what it drags.

Measured in the Claude Desktop extension's venv: installing `cadquery` to
read one number out of a STEP file brought

    vtkmodules  592 MB   a RENDERING toolkit TEE never renders with
    OCP         225 MB   the actual BREP kernel (legitimately needed)
    casadi      159 MB   an assembly solver TEE never assembles with
    llvmlite    129 MB   a JIT (via numba) TEE never triggers
    ----------------
                1.1 GB   for volume, area, bounding box and validity

STEP genuinely needs a BREP kernel, so the capability stays - it moves.
This worker lives in a small dedicated venv and is driven as a subprocess,
the same shape as `_cpsat_worker.py`. TEE's own interpreter goes back to
being something that starts in 0.02 s.

Deliberately imports nothing from `tee`, so the parent can invoke it by
path from any environment.

Contract: JSON on stdin, exactly one JSON object on stdout. Native chatter
is swallowed at the descriptor level so it can never corrupt that.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile


def _measure(path: str) -> dict:
    import cadquery as cq

    suffix = path.lower()
    if suffix.endswith((".step", ".stp")):
        shape = cq.importers.importStep(path)
    elif suffix.endswith(".brep"):
        shape = cq.Workplane(obj=cq.Shape.importBrep(path))
    else:
        return {"error": "unsupported", "message": f"cad worker reads STEP/BREP, not {path}"}

    solid = shape.val()
    bb = solid.BoundingBox()
    return {
        "kind": "solid",
        "volume": float(solid.Volume()),
        "area": float(solid.Area()),
        "bbox": [float(bb.xlen), float(bb.ylen), float(bb.zlen)],
        "valid": bool(solid.isValid()),
        "cadquery": getattr(cq, "__version__", "?"),
    }


def main() -> int:
    try:
        spec = json.loads(sys.stdin.read() or "{}")
    except Exception as exc:
        sys.stdout.write(json.dumps({"error": "bad_json", "message": str(exc)}))
        return 0

    saved = os.dup(1)
    try:
        with tempfile.TemporaryFile(mode="w+b") as tmp:
            os.dup2(tmp.fileno(), 1)
            try:
                result = _measure(str(spec.get("path") or ""))
            finally:
                sys.stdout.flush()
                os.dup2(saved, 1)
    except Exception as exc:
        os.dup2(saved, 1)
        result = {"error": type(exc).__name__, "message": str(exc)[:400]}
    finally:
        os.close(saved)

    sys.stdout.write(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
