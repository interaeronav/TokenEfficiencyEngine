"""Blender's own cloth solver, headless - the zero-new-code baseline.

TEE already drives Blender headlessly, and research doc 32 established the
mechanics: `modifiers.new('CLOTH')`, a synchronous `ptcache.bake`, and a
free health report in `solver_result`. Any solver seamkiln writes has to
beat this, or the honest answer is to use the adapter that already exists.

This is a DIFFERENT algorithm from the XPBD backends (Blender's cloth is
implicit mass-spring), so vertex positions will not match. The comparable
quantity is the decision-relevant one: wall clock to drape a sheet of N
particles onto a sphere, and whether it converges at all.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from seamkiln.solver.problem import ClothProblem

_SCRIPT = """
import bpy, json, sys, time
n = int(sys.argv[sys.argv.index("--") + 1])
frames = int(sys.argv[sys.argv.index("--") + 2])
size = float(sys.argv[sys.argv.index("--") + 3])
height = float(sys.argv[sys.argv.index("--") + 4])
radius = float(sys.argv[sys.argv.index("--") + 5])
out = sys.argv[sys.argv.index("--") + 6]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=n - 1, y_subdivisions=n - 1, size=size,
                                location=(0.0, 0.0, height))
cloth_obj = bpy.context.active_object
bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=(0.0, 0.0, 0.0))
sphere = bpy.context.active_object
sphere.modifiers.new("Collision", type="COLLISION")

bpy.context.view_layer.objects.active = cloth_obj
modifier = cloth_obj.modifiers.new("Cloth", type="CLOTH")
settings = modifier.settings
settings.mass = 0.2
settings.quality = 8
cache = modifier.point_cache
cache.frame_start = 1
cache.frame_end = frames
bpy.context.scene.frame_end = frames

start = time.perf_counter()
with bpy.context.temp_override(point_cache=cache):
    bpy.ops.ptcache.bake(bake=True)
elapsed = time.perf_counter() - start

# solver_result is None on the ORIGINAL modifier even after a successful
# bake - it only exists on the evaluated object. Research doc 32 called it
# a "free compact health report" without saying where to read it, and the
# first code that tried (this one) got None.
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = cloth_obj.evaluated_get(depsgraph).modifiers.get("Cloth")
result = getattr(evaluated, "solver_result", None)
report = {
    "seconds": elapsed,
    "frames": frames,
    "vertices": len(cloth_obj.data.vertices),
    "status": sorted(getattr(result, "status", None) or []) or None,
    "max_error": getattr(result, "max_error", None),
    "avg_error": getattr(result, "avg_error", None),
    "avg_iterations": getattr(result, "avg_iterations", None),
}
Path = __import__("pathlib").Path
Path(out).write_text(json.dumps(report))
"""


def available() -> tuple[bool, str]:
    exe = shutil.which("blender")
    if not exe:
        return False, "blender is not on PATH"
    try:
        first = subprocess.run(
            [exe, "--version"], capture_output=True, text=True, timeout=60
        ).stdout.splitlines()[0]
    except Exception as exc:
        return False, f"blender --version failed: {exc}"
    return True, first.strip().lower()


def bake(problem: ClothProblem, frames: int, *, n: int, size: float, height: float) -> dict:
    """Bake `frames` of Blender cloth headlessly; returns its own timing."""
    ok, why = available()
    if not ok:
        raise RuntimeError(why)
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "bake.py"
        script.write_text(_SCRIPT)
        out = Path(tmp) / "report.json"
        proc = subprocess.run(
            [
                shutil.which("blender"),
                "--background",
                "--factory-startup",
                "--python",
                str(script),
                "--",
                str(n),
                str(frames),
                str(size),
                str(height),
                str(problem.sphere_radius),
                str(out),
            ],
            capture_output=True,
            text=True,
            timeout=3600,
        )
        if not out.exists():
            tail = (proc.stderr or proc.stdout or "")[-600:]
            raise RuntimeError(f"blender bake produced no report: {tail}")
        return json.loads(out.read_text())
