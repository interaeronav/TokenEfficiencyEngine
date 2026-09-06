"""L13b: the adopted airFoil2D tutorial with forces= added to the run copy."""
import json, tempfile, time
from pathlib import Path
from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.kernel.waiting import wait_until
from tee.windtunnel.tools import register_windtunnel_tools

P0 = Path(__file__).resolve().parent
TUT = P0 / "tut/usr/share/doc/openfoam-examples/examples/incompressible/simpleFoam/airFoil2D"
project = Path(tempfile.mkdtemp(prefix="wt_l13b_"))
app = TeeApp({"fake": FakeAdapter()}, project_root=project)
store = register_windtunnel_tools(app, project)
call = app.registry.call
row = {}
ad = call("wt_case", {"action": "adopt", "path": str(TUT)})
acid = ad["case_id"]
call("wt_mesh", {"case_id": acid})
# 1. without forces: residual-only verdict
r = call("wt_run", {"case_id": acid, "confirm_cost": True})
wait_until(lambda: app.jobs.status(r["job"])["state"] in ("done", "error", "cancelled"), 900, max_delay_s=1.0)
st = app.jobs.status(r["job"])
res = call("wt_result", {"case_id": acid})
row["without_forces"] = {"job": st["state"], "cl": res.get("cl"), "verdict": res.get("verdict"), "note": res.get("note"), "iters": res.get("iters_used")}
print("L13b no forces", json.dumps(row["without_forces"])[:600], flush=True)
# 2. with forces
t0 = time.time()
r = call("wt_run", {"case_id": acid, "confirm_cost": True, "forces": {"patches": ["walls"]}})
wait_until(lambda: app.jobs.status(r["job"])["state"] in ("done", "error", "cancelled"), 900, max_delay_s=1.0)
st = app.jobs.status(r["job"])
try:
    res = call("wt_result", {"case_id": acid})
    row["with_forces"] = {"job": st["state"], "wall_s": round(time.time() - t0, 1), "cl": res.get("cl"), "cd": res.get("cd"), "cm": res.get("cm"), "verdict": res.get("verdict"), "iters": res.get("iters_used"), "uncertainty": (res.get("uncertainty") or {}).get("trust"), "forces": store.load(acid)["runs"][-1].get("forces"), "error": st.get("error")}
except TeeError as exc:
    row["with_forces"] = {"job": st["state"], "refusal": exc.code, "message": exc.message[:300], "error": st.get("error")}
print("L13b forces", json.dumps(row["with_forces"])[:900], flush=True)
row["source_untouched"] = sorted(p.name for p in TUT.iterdir())
row["note"] = "the tutorial's controlDict has no functions entry; the run copy got forceCoeffs1 with U from 0/U (25.75, 3.62), lRef 1, Aref = lRef x slab depth read from points; the adopted copy and the source are untouched"
d = json.loads((P0 / "p0-rows.json").read_text())
d.setdefault("L13_adopt_tutorial", {})
if isinstance(d["L13_adopt_tutorial"], dict):
    d["L13_adopt_tutorial"].update({"with_and_without_forces": row})
(P0 / "p0-rows.json").write_text(json.dumps(d, indent=1))
print("written L13b")
app.shutdown()
