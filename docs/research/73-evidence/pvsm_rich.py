"""generated-by: tee.windtunnel - A73 P0: the realistic ParaView state.

Reader, p colouring, scalar bar, camera, last time step, then SaveState.
Run as written on 2026-09-07 over the case pvsm_probe.py had just solved;
it printed 203,042 bytes. Paths are the ones the run actually used."""
from paraview.simple import *
r = OpenFOAMReader(registrationName="case.foam", FileName="/tmp/wt_a73_qjp3xz3z/.tee/windtunnel/cases/wt_268ad05e37/openfoam/case.foam")
r.MeshRegions = ["internalMesh"]
r.CellArrays = ["U", "p"]
r.UpdatePipeline()
tk = GetTimeKeeper(); times = list(r.TimestepValues or [])
view = GetActiveViewOrCreate("RenderView")
d = Show(r, view)
ColorBy(d, ("POINTS", "p"))
d.RescaleTransferFunctionToDataRange(True, False)
d.SetScalarBarVisibility(view, True)
if times:
    view.ViewTime = times[-1]
view.ResetCamera()
Render()
SaveState("/tmp/rich.pvsm")
print("saved | timesteps:", len(times), "| last:", times[-1] if times else None)
