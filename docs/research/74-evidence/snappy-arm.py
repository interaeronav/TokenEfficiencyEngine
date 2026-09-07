"""A74 P0 probe: cfMesh (cartesianMesh) against snappyHexMesh on ONE geometry.

The question HELYX raises and this answers with numbers: is the mesher already
inside the OpenFOAM the lane drives better at the thing snappy is weakest at -
boundary layers - and what would it cost the lane to offer it.

Prints, never asserts. Both arms mesh the same prism at the same domain.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/user/TokenEfficiencyEngine/server/tests")
from fixtures_windtunnel import wait_job  # noqa: E402

from tee.app import TeeApp  # noqa: E402
from tee.kernel.adapter import FakeAdapter  # noqa: E402
from tee.windtunnel import airfoil, engines  # noqa: E402
from tee.windtunnel.physics import write_stl_ascii  # noqa: E402
from tee.windtunnel.tools import register_windtunnel_tools  # noqa: E402

WORK = Path(sys.argv[1])
WORK.mkdir(parents=True, exist_ok=True)
CHORD, SPAN = 0.3, 0.4


def say(label, obj):
    print(f"\n=== {label} ===")
    print(json.dumps(obj, indent=1, default=str)[:1200])


# -- the geometry both arms mesh --------------------------------------------
stl = WORK / "prism.stl"
tris = airfoil.extrude_stl(stl, airfoil.naca4("0012", 24), span=SPAN, chord=CHORD, name="body")
print(f"geometry: {stl.name}, {tris} triangles, chord {CHORD} m, span {SPAN} m")

app = TeeApp({"fake": FakeAdapter()}, project_root=WORK / "project")
store = register_windtunnel_tools(app, WORK / "project")
call = lambda tool, **a: app.registry.call(tool, a)  # noqa: E731

try:
    # -- arm 1: the lane as it ships (snappyHexMesh) -------------------------
    created = call("wt_case", action="create", stl=str(stl), V_mps=20, aoa_deg=0)
    cid = created["case_id"]
    rec = store.load(cid)
    say("domain the lane chose", rec.get("domain"))
    t0 = time.time()
    started = call("wt_mesh", case_id=cid, base_cell_m=0.15, levels=[1, 2], layers=2)
    st = wait_job(app, started["job"], timeout_s=1800)
    snappy_wall = time.time() - t0
    snappy = st.get("result") or {}
    say("snappyHexMesh", {**{k: snappy.get(k) for k in ("cells", "kind", "checkMesh", "layers")},
                          "wall_s": round(snappy_wall, 1)})
    case_dir = Path(store.load(cid)["engine_dir"])
    log = next((p for p in case_dir.glob("log.snappyHexMesh*")), None)
    if log:
        text = log.read_text(errors="replace")
        rows = [ln.strip() for ln in text.splitlines() if re.search(r"^\s*body\s+\d", ln)]
        print("snappy layer rows (patch, faces, layers, thickness):")
        for r in rows[-4:]:
            print("   ", r[:160])
        m = re.findall(r"Overall.*", text)
        for x in m[-2:]:
            print("   ", x[:160])
finally:
    app.shutdown()

# -- arm 2: cfMesh -----------------------------------------------------------
dom = rec.get("domain") or {}
print("\n=== cfMesh arm ===")
b = dom.get("bounds") or dom
print("domain bounds from the case record:", json.dumps(b, default=str)[:300])
