"""A74 P5, the other arm: the lane's own O-mesh on the SAME case, through the
lane, so both numbers come from this session rather than from a document."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/user/TokenEfficiencyEngine/server/tests")
from fixtures_windtunnel import wait_job  # noqa: E402

from tee.app import TeeApp  # noqa: E402
from tee.kernel.adapter import FakeAdapter  # noqa: E402
from tee.windtunnel.tools import register_windtunnel_tools  # noqa: E402

os.environ.setdefault("TEE_MACHINE_TOTAL_GB", "128")
WORK = Path(sys.argv[1])
AOA = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
WORK.mkdir(parents=True, exist_ok=True)
app = TeeApp({"fake": FakeAdapter()}, project_root=WORK / "project")
store = register_windtunnel_tools(app, WORK / "project")
app._wt_store = store

cid = app.registry.call(
    "wt_case", {"action": "create", "naca": "0012", "V_mps": 30, "aoa_deg": AOA}
)["case_id"]
t0 = time.time()
mesh = app.registry.call("wt_mesh", {"case_id": cid, "nj": 80})
mesh_wall = round(time.time() - t0, 1)
print(f"O-MESH  cells {mesh['cells']}  mesh {mesh_wall} s  ok {mesh['ok']} "
      f"skew {mesh.get('max_skew')} aspect {mesh.get('max_aspect')}")
t0 = time.time()
started = app.registry.call("wt_run", {"case_id": cid, "iters": 600, "confirm_cost": True})
st = wait_job(app, started["job"], timeout_s=3600)
solve_wall = round(time.time() - t0, 1)
print("run:", st["state"])
res = app.registry.call("wt_result", {"case_id": cid})
print(f"  solve {solve_wall} s  iterations {res.get('iterations')}  "
      f"Cl {res.get('cl')}  Cd {res.get('cd')}  Cm {res.get('cm')}  "
      f"verdict {res['verdict']['state']}  trust {res['uncertainty']['trust']}")
app.shutdown()
