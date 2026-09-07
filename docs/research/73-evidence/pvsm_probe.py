"""A73 P0: does a ParaView state file survive being moved? Build a real case
through the lane, save a .pvsm over it, and read back what paths it holds."""
import json, subprocess, tempfile
from pathlib import Path
from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.windtunnel.tools import register_windtunnel_tools

project = Path(tempfile.mkdtemp(prefix="wt_a73_"))
app = TeeApp({"fake": FakeAdapter()}, project_root=project)
register_windtunnel_tools(app, project)
call = app.registry.call
c = call("wt_case", {"action": "create", "naca": "0012", "V_mps": 30, "aoa_deg": 4})
cid = c["case_id"]
m = call("wt_mesh", {"case_id": cid, "nj": 30, "n_surface": 40})
print("case", cid, "cells", m.get("cells"))
from tee.kernel.waiting import wait_until
r = call("wt_run", {"case_id": cid, "iters": 200, "confirm_cost": True})
wait_until(lambda: app.jobs.status(r["job"])["state"] in ("done", "error", "cancelled"), 900, max_delay_s=1.0)
print("run:", app.jobs.status(r["job"])["state"])
foam = call("wt_export", {"case_id": cid, "format": "foam"})
print("foam stub:", foam["path"], foam["bytes"], "bytes")
case_dir = str(Path(foam["path"]).parent)
app.shutdown()

script = f'''
from paraview.simple import *
r = OpenFOAMReader(registrationName="case.foam", FileName={foam["path"]!r})
r.MeshRegions = ["internalMesh"]
r.UpdatePipeline()
Show(r); Render()
SaveState("{project}/state.pvsm")
print("saved")
'''
p = subprocess.run(["xvfb-run", "-a", "pvpython", "-c", script], capture_output=True, text=True, timeout=300)
print("pvpython rc", p.returncode, (p.stdout + p.stderr).strip()[-300:] if p.returncode else "ok")
state = Path(f"{project}/state.pvsm")
if state.exists():
    text = state.read_text()
    print("state bytes:", len(text))
    print("mentions the absolute case path:", str(foam["path"]) in text)
    print("how many times:", text.count(str(foam["path"])))
    import re
    for line in text.splitlines():
        if "FileName" in line and ".foam" in line:
            print("path line:", line.strip()[:200])
            break
    print("proxy groups present:", sorted(set(re.findall(r'group="(\\w+)"', text)))[:8])
