"""First end-to-end loop through the registry on the real engines (OpenFOAM v2606, SU2, VSPAERO)."""

import json
import sys
import tempfile
import time
from pathlib import Path

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.waiting import wait_until
from tee.windtunnel.tools import register_windtunnel_tools

project = Path(tempfile.mkdtemp(prefix="wt_smoke_"))
app = TeeApp({"fake": FakeAdapter()}, project_root=project)
register_windtunnel_tools(app, project)
call = app.registry.call


def wait(job):
    wait_until(lambda: app.jobs.status(job)["state"] in ("done", "error", "cancelled"), 1800, max_delay_s=2.0)
    st = app.jobs.status(job)
    return st


def show(label, obj, keys=None):
    if keys:
        obj = {k: obj.get(k) for k in keys if k in obj}
    s = json.dumps(obj, default=str)
    print(f"{label}: {len(s)} chars ~{len(s) // 4} tok :: {s[:600]}")


which = sys.argv[1:] or ["probe", "conditions", "openfoam", "su2", "vsp"]

if "probe" in which:
    p = call("wt_probe", {})
    show("wt_probe", {k: (v if k != "engines" else {e: (d.get("version"), d.get("found")) for e, d in v.items()}) for k, v in p.items()})
if "conditions" in which:
    show("wt_conditions", call("wt_conditions", {"V_mps": 45, "L_m": 1.2, "alt_m": 1500}))

if "openfoam" in which:
    c = call("wt_case", {"action": "create", "naca": "0012", "V_mps": 30, "aoa_deg": 4})
    show("wt_case create", c)
    cid = c["case_id"]
    m = call("wt_mesh", {"case_id": cid, "nj": 60, "n_surface": 60})
    show("wt_mesh", m)
    try:
        r = call("wt_run", {"case_id": cid})
        show("wt_run (no confirm)", r)
    except Exception as exc:
        print("wt_run refused:", type(exc).__name__, str(exc)[:200])
    r = call("wt_run", {"case_id": cid, "confirm_cost": True, "iters": 600})
    show("wt_run", r)
    t = time.time()
    for _ in range(3):
        time.sleep(1.5)
        show("wt_status", call("wt_status", {"case_id": cid}))
    st = wait(r["job"])
    print("job", st["state"], "in", round(time.time() - t, 1), "s")
    show("job result", st.get("result") or st.get("error"), keys=["cl", "cd", "cm", "l_over_d", "verdict", "uncertainty", "wall_s", "iters_used"])
    res = call("wt_result", {"case_id": cid})
    show("wt_result", res, keys=["cl", "cd", "cm", "verdict", "uncertainty", "mesh_hash", "engine_version", "wall_s"])
    show("wt_probe_field", call("wt_probe_field", {"case_id": cid, "what": "line", "field": "U", "p1": [0.5, 0, 0.05], "p2": [0.5, 0.3, 0.05], "n": 16}), keys=["n", "U_mag", "stats"])
    show("wt_view", call("wt_view", {"case_id": cid, "view": "pressure"}))
    show("wt_export csv", call("wt_export", {"case_id": cid, "format": "csv"}))
    show("wt_export md", call("wt_export", {"case_id": cid, "format": "md"}))
    show("wt_case show", call("wt_case", {"action": "show", "case_id": cid}))

if "su2" in which:
    c = call("wt_case", {"action": "create", "naca": "0012", "mach": 0.8, "aoa_deg": 1.25, "fidelity": "euler", "need_viscous": False})
    show("wt_case su2", c)
    cid = c["case_id"]
    show("wt_mesh su2", call("wt_mesh", {"case_id": cid, "nj": 40, "n_surface": 60}))
    r = call("wt_run", {"case_id": cid, "confirm_cost": True, "iters": 1500})
    show("wt_run su2", r)
    st = wait(r["job"])
    show("su2 result", st.get("result") or st.get("error"), keys=["cl", "cd", "verdict", "uncertainty", "wall_s", "iters_used"])

if "vsp" in which:
    c = call("wt_case", {"action": "create", "wing": {"span": 10, "root_chord": 1, "airfoil": "0012"}, "V_mps": 34, "aoa_deg": 4})
    show("wt_case wing", c)
    cid = c["case_id"]
    r = call("wt_sweep", {"case_id": cid, "aoa": [0, 2, 4, 6], "cores": 4})
    show("wt_sweep", r)
    st = wait(r["job"])
    show("sweep result", st.get("result") or st.get("error"), keys=["polar", "cl_alpha_per_rad", "verdict", "uncertainty", "wall_s"])
    show("wt_result vsp", call("wt_result", {"case_id": cid}), keys=["cl", "cd", "cl_alpha_per_rad", "verdict", "uncertainty"])

print("project", project)
app.shutdown()
