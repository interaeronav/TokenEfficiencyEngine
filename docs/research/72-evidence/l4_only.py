"""L4 re-measured with the root-MPI override: 1, 2 and 4 cores on the same case."""
import json, tempfile, time
from pathlib import Path
from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.waiting import wait_until
from tee.windtunnel.tools import register_windtunnel_tools

P0 = Path(__file__).resolve().parent
project = Path(tempfile.mkdtemp(prefix="wt_l4b_"))
app = TeeApp({"fake": FakeAdapter()}, project_root=project)
store = register_windtunnel_tools(app, project)
call = app.registry.call
c = call("wt_case", {"action": "create", "naca": "0012", "V_mps": 30, "aoa_deg": 4})
cid = c["case_id"]
call("wt_mesh", {"case_id": cid, "nj": 60})
timings = {}
for cores in (1, 2, 4):
    t0 = time.time()
    r = call("wt_run", {"case_id": cid, "iters": 400, "cores": cores, "confirm_cost": True})
    wait_until(lambda: app.jobs.status(r["job"])["state"] in ("done", "error", "cancelled"), 900, max_delay_s=1.0)
    st = app.jobs.status(r["job"])
    res = st.get("result") or {}
    timings[str(cores)] = {"state": st["state"], "wall_s": round(time.time() - t0, 1), "iters": res.get("iters_used"),
                           "cl": res.get("cl"), "cd": res.get("cd"), "verdict": (res.get("verdict") or {}).get("state"),
                           "error": (st.get("error") or "")[:200]}
    print("L4 cores", cores, timings[str(cores)], flush=True)
rec = store.load(cid)
run2 = rec["runs"][1]
d = json.loads((P0 / "p0-rows.json").read_text())
d["L4_parallel"] = {
    "case": "16,000-cell NACA 0012 O-mesh, 400 iterations cap (residualControl stops earlier)",
    "timings": timings,
    "mpi_root_override": run2.get("mpi_root_override"),
    "route": "decomposePar -force -> mpirun -np N simpleFoam -parallel inside the bashrc environment -> reconstructPar -latestTime",
    "first_attempt": "died in 1.1 s: Open MPI refuses to run as root ('We strongly suggest that you run mpirun as a non-root user'); runs.mpi_env sets OMPI_ALLOW_RUN_AS_ROOT(_CONFIRM)=1 for root only, and the run record says mpi_root_override",
}
(P0 / "p0-rows.json").write_text(json.dumps(d, indent=1))
print("written L4")
app.shutdown()
