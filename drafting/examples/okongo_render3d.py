"""Z-buffered point-cloud renderer: 1.5 M coloured points, no GPU, no viewer."""
import sys; sys.path.insert(0,'/Users/john/TokenEfficiencyEngine/server/src')
import json
import numpy as np
from pathlib import Path
from PIL import Image
from tee.pointcloud.store import CloudStore

SCRATCH=Path("/private/tmp/claude-501/-Users-john-TokenEfficiencyEngine/1d43fd51-eeff-4925-b1bd-bb2fba2d38c1/scratchpad")
WORK=SCRATCH/"okongo-work"
lid=json.loads((WORK/"outputs.json").read_text())["lid"]
store=CloudStore(WORK)
P=store.points(lid); C=store.attr(lid,"rgb")
print(f"{len(P):,} points, colour={C is not None}")

def camera(az_deg, el_deg):
    a,e=np.deg2rad(az_deg),np.deg2rad(el_deg)
    Rz=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
    Rx=np.array([[1,0,0],[0,np.cos(e),-np.sin(e)],[0,np.sin(e),np.cos(e)]])
    return Rx@Rz

def render(az, el, W=1500, H=1100, splat=1, clip_z=None, bg=255):
    pts, cols = P, C
    if clip_z is not None:
        m = pts[:,2] < clip_z
        pts, cols = pts[m], (cols[m] if cols is not None else None)
    R = camera(az, el)
    Q = (pts - pts.mean(0)) @ R.T
    x, y, depth = Q[:,0], Q[:,2], Q[:,1]      # screen x, screen y(up), depth
    sx = (x - x.min())/(x.max()-x.min()+1e-9)
    sy = (y - y.min())/(y.max()-y.min()+1e-9)
    pad = 0.04
    ix = ((pad + sx*(1-2*pad))*W).astype(np.int32).clip(0,W-1)
    iy = ((1-(pad + sy*(1-2*pad)))*H).astype(np.int32).clip(0,H-1)
    img = np.full((H,W,3), bg, np.uint8)
    zbuf = np.full((H,W), np.inf)
    order = np.argsort(-depth)                 # far to near, painter's order
    ix, iy, dz = ix[order], iy[order], depth[order]
    cc = (cols[order] if cols is not None else np.full((len(ix),3),120,np.uint8))
    for dx in range(-splat, splat+1):
        for dy in range(-splat, splat+1):
            jx=(ix+dx).clip(0,W-1); jy=(iy+dy).clip(0,H-1)
            img[jy,jx]=cc; zbuf[jy,jx]=dz
    return Image.fromarray(img)

views = {"iso-ne":(45,22), "iso-nw":(135,22), "iso-se":(-45,22), "plan-oblique":(30,60)}
for name,(az,el) in views.items():
    render(az,el).save(SCRATCH/f"v_{name}.png"); print(f"  v_{name}.png")
# a cutaway: ceiling removed so the interior reads
render(35, 35, clip_z=2.35).save(SCRATCH/"v_cutaway.png"); print("  v_cutaway.png")
