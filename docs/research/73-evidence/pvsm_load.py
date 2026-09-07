"""generated-by: tee.windtunnel - A73 P0: the state read back.

A FRESH pvpython loads what pvsm_rich.py wrote and prints what survived:
the reader and its file, the view time, the camera, the coloured array."""
from paraview.simple import *
LoadState("/tmp/rich.pvsm")
srcs = GetSources()
print("proxies restored:", len(srcs))
for (name, _id), s in srcs.items():
    fn = getattr(s, "FileName", None)
    print(f"  {name}: {type(s).__name__} file={fn}")
v = GetActiveView()
print("view time:", v.ViewTime, "| camera:", [round(x, 3) for x in v.CameraPosition])
d = GetDisplayProperties(list(srcs.values())[0], v)
print("coloured by:", d.ColorArrayName[:])
