# The garment lane (A53)

`seamkiln` is a garment CAD and drape kernel: 2D pattern pieces, sewing
relationships, drape on a parametric body, fit measurement. It joins TEE
through the `Adapter` protocol, so it arrives with **no new always-loaded
tools** — `tee_scene_summary`, `tee_batch`, `tee_diff`, `tee_checkpoint` and
`tee_rollback` already know this shape.

```bash
uv pip install -e seamkiln            # the kernel
tee serve --adapter seamkiln --project ~/patterns
```

The surface before A53 was 17 tools / 2,033 tok. After it: 17 tools /
2,033 tok.

## The loop

The same one Marvelous Designer and CLO3D established:

```
2D panels -> sewing -> arrange on a body -> simulate -> measure fit -> export
```

The difference is which surface is primary. The incumbents' automation is
in-app and sold on an enterprise tier. Here the script **is** the product: a
`Session` holds the garment, every mutation is a `Command`, every Command is
recorded, and `Session.replay(script)` rebuilds the garment exactly. The Qt
shell and this adapter both drive that same session, so there is no path
through one client that another cannot take.

```python
from seamkiln.session import Command, Session

s = Session()
s.apply(Command("block", {"block": "tee"}))
s.apply(Command("allowance", {"mm": 10.0}))
s.apply(Command("body", {"kind": "anny", "stature_m": 1.72}))
s.apply(Command("arrange", {"particle_distance_mm": 12.0}))
s.apply(Command("drape", {"fabric": "cotton_jersey", "frames": 250}))
s.save_script("tee.json")          # replays to the same garment, anywhere
```

## Through TEE

One batch does the lot. Ops are declarative and enumerable; there is no
arbitrary-code door.

```json
[{"op": "create", "kind": "block", "props": {"block": "tee"}},
 {"op": "set", "id": "panel:FRONT", "props": {"seam_allowance_mm": 10}},
 {"op": "arrange", "props": {"body": "anny", "stature_m": 1.72,
                             "particle_distance_mm": 12}},
 {"op": "drape",  "props": {"fabric": "cotton_jersey", "frames": 250}},
 {"op": "export", "props": {"format": "glb", "out": "tee.glb"}}]
```

Panels and seams are entities with stable ids (`panel:FRONT`,
`seam:side-right`). `tee_checkpoint` writes the command history and
`tee_rollback` **replays** it, so a checkpoint cannot restore a state the
commands could not produce.

Long tail, behind progressive disclosure: `sk_blocks`, `sk_fabrics`,
`sk_body`, `sk_fit`, `sk_plot`, `sk_interchange`, `sk_techpack`, `sk_look`.

## The three rules that will bite you first

**1. Particle distance has a floor, and it is not cosmetic.** A garment
meshed too coarsely does not merely look blocky — its shoulder and armhole
seams get three or four points each, which is not enough structure to hold
the garment up, and it slides off with every other number still looking
healthy. `triangulate_panel` refuses anything coarser than a quarter of a
panel's narrowest dimension. For the tee block, use 20 mm or finer.

**2. "Nothing inside the body" is only half the question.** A drape that
fell off scores a *perfect* zero for interpenetration, lying on the floor.
Read `contact.worn` as well — it is in every drape report for exactly this
reason.

**3. An edit that changes a panel's corner count invalidates its seams.**
Edges are derived as the runs between corners, so their indices move. Seam
allowance no longer does this (the outline is the sew line, and the cut line
is derived), but a hand edit that adds or removes a corner will, and the
refusal names the cause.

## Interchange

- **DXF**, both dialects, via the 23-layer map. ASTM D6673's table is
  verified here; **the AAMA layer map is second-hand and `AAMA.verified` is
  `False`** — a test asserts it stays that way. AAMA defines no
  internal-cutout layer, so writing one to AAMA refuses rather than putting
  a cut line where a cutter reads decoration. `sk_interchange` with
  `action="dialects"` prints both tables.
- **Plotter sheets** at true 1:1, tiled with a 100 mm ruler on every tile.
- **3D** as OBJ / glTF / PLY / STL — **with UVs, free and exact**, because
  the flat pattern *is* the UV map. Every other 3D pipeline pays an unwrap
  step and guesses seams; a garment already knows where its seams are.
- **Tech pack** PDF: pieces, fabric card with its tier flag, seam schedule,
  fit and strain.

## Fabric, and what its numbers mean

`sk_fabrics` returns a tier flag on every row, and every bundled row is
`plausible`: the weights and thicknesses are published ranges, the
stiffnesses are solver constants chosen to behave like the cloth. They are
not laboratory measurements and the tech pack says so on the page. Real
KES-F or fabric-kit output belongs in tier `measured`, with its test report
cited. ArcSim's measured set is non-profit-only and cannot ship (research
doc 34).

## Licences — read this before adding a dependency

This domain is mined, and the mines are the obvious choices:

| Trap | Replacement |
| --- | --- |
| GarmentCodeData's simulator (NVIDIA Source Code Licence, non-commercial) | seamkiln's own XPBD |
| SMPL / SMPL-X (non-commercial) | **Anny** (Apache-2.0, CC0 MakeHuman assets) |
| `anny[smpl]` — Anny's own optional extra pulls `smplx` | plain `anny` |
| Shewchuk's Triangle, `meshpy`, the `triangle` wheel (no commercial use) | CDT (MPL-2.0), or seamkiln's own constrained Delaunay |
| ArcSim measured cloth (non-profit only) | published GSM ranges, tier `plausible` |

`seamkiln/tests/test_licences.py` fails the build if any of them enters the
dependency closure, and names the replacement in the failure. Research doc
67 §2 has the citations.

## The GUI

```bash
uv pip install 'seamkiln[gui]' && python -m seamkiln.gui.app
```

`import seamkiln` works with no Qt installed, and a test asserts it. The 3D
panel is a rendered image refreshed after each drape, not an interactive
viewport — seamkiln already has a Blender preview lane that makes a properly
lit garment, and a second renderer inside Qt would be a worse picture. Every
button builds a Command, so "Save script" hands over the history the session
was keeping anyway.
