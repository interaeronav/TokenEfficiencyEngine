# The garment lane (A53, and the follow-ups A54–A65)

`seamkiln` is a garment CAD and drape kernel: 2D pattern pieces, sewing
relationships, hardware, drape on a body, fit measurement, animation, and a
handoff into the next application. It joins TEE through the `Adapter`
protocol, so it arrives with **no new always-loaded tools** —
`tee_scene_summary`, `tee_batch`, `tee_diff`, `tee_checkpoint` and
`tee_rollback` already know this shape.

```bash
uv pip install -e seamkiln            # the kernel
tee serve --adapter seamkiln --project ~/patterns
```

The surface before A53 was 17 tools / 2,033 tok. After A65: 17 tools /
2,033 tok. Fourteen `sk_*` tools sit behind progressive disclosure.

## The loop

The same one Marvelous Designer and CLO3D established, plus the parts a
finished garment needs:

```
2D panels -> sewing -> hardware -> body -> arrange + dress -> simulate
          -> pull / fold / ease live -> walk it -> measure fit -> hand off
```

The script **is** the product: a `Session` holds the garment, every mutation
is a `Command`, every Command is recorded, and `Session.replay(script)`
rebuilds the garment to the same fingerprint. The Qt shell and the TEE
adapter drive that same session; there is no path through one client that
another cannot take.

```python
from seamkiln.session import Command, Session

s = Session()
s.apply(Command("block", {"block": "jacket-zip", "half_chest": 420,
                          "shoulder": 250, "sleeve_length": 480, "biceps": 480}))
s.apply(Command("body", {"kind": "figure", "stature_m": 1.80}))
s.apply(Command("arrange", {"particle_distance_mm": 12}))   # wrap + dress
s.apply(Command("zip", {"opening": "centre-front", "material": "metal", "size": 8}))
s.apply(Command("walk", {"gait": "walk", "cycles": 1.0, "fps": 12, "travel": True}))
s.apply(Command("handoff", {"out": "shot/", "target": "blender"}))
s.save_script("coat.json")          # replays to the same garment, anywhere
```

## Verbs

| verb | what it does | added |
| --- | --- | --- |
| `block`, `panel`, `seam`, `allowance`, `delete` | draft the pattern | A53 |
| `body` | `mannequin` · `anny` · `posed` · **`figure`** · `custom` | A53 / A58 / A65 |
| `arrange` | place panels; `arrangement` = `auto` · `cylinder` · `wrap`; `dress` | A53 / A65 |
| `drape`, `fit`, `techpack`, `export` | simulate, measure, document, write files | A53 |
| `grade`, `cut` | parametric grading; darts, slashes, pleats | A54 |
| `rip`, `pinch`, `lace`, `finish`, `animate` | tearing, symmetric pinching, lacing, washes and fur, blend shapes | A54 |
| `lock`, `unlock` | protect a panel, the body, the fabric or everything | A55 |
| `zip`, `unzip`, `button`, `unfasten` | hardware, as trim with its own weight | A56 |
| `handoff` | mesh + UVs + hardware in the TARGET's units and axis, with load ops | A57 |
| `walk` | drape along a walk or run; `travel` moves the body at the gait's own speed | A58 / A65 |
| `pull`, `fold`, `ease` | live adjustment at ~43 fps; stitch adjustment | A59 |

Every verb is a `tee_batch` op. `tee_search_tools` finds the long tail:
`sk_hardware`, `sk_avatar`, `sk_touch`, `sk_handoff` describe the follow-up
capabilities and hand back the exact ops.

## Bodies, and which arrangement they get

- **`mannequin`** — the capsule stand-in, no download. Every measured number
  in the physics tests was produced on it, so it keeps the **cylinder**
  arrangement (`top_arrangement`), which measures the body by cross-section.
- **`figure`** — a clothable figure with joints (`seamkiln.figure`): eight
  heads tall, shoulders, a waist narrower than the ribcage, boots, gloves, a
  cowl, six tagged parts a renderer can paint. It is built facing +Z and can
  be turned. It gets the **wrap** arrangement and is **dressed** on arrange.
- **`anny`**, **`posed`**, **`custom`** — parametric, posed-mannequin, and
  your own mesh (units and up-axis inferred and reported). Wrap arrangement.

`arrangement="auto"` records the choice it made, so a replay makes it too.

**Why two arrangements.** The cylinder path measures a chest radius by
cross-section, and on the figure that measurement cascaded: 0.082 m read for
a 0.19 m chest, a top edge at 2.02 m for shoulders at 1.40 m, and the jacket
collapsed into a muff round the ears. The wrap path takes nothing from the
body it cannot be sure of — the radius comes from the pattern (the panels
must wrap the cylinder exactly once, so radius = width / 2π), the sleeves'
radii from the sleeves' own widths, and the collar clearance from the
shoulder cap and the pattern's own neck-to-shoulder drop.

**Why dressing.** A cylinder arrangement leaves front and back meeting at the
sides, so when the seams pull together the garment closes into a tube whose
shoulders are on the wearer's flanks — and a tube with no shoulders slides
off. Measured: seams closed to 4.7 mm and the jacket ended at y = −0.79, on
the floor, with `worn` correctly False. `dress` pins the shoulder seams on
the shoulders, bastes every other seam to its own midpoint, settles, and
lets go. On the figure a coat then holds 27–35 % contact at a 37–40 mm
standoff, which is what a bulky coat should do.

## Hardware is trim, not cloth

A #5 brass chain is 33 g/m against a poplin's 130 g/m²; on a 590 mm opening
that is 23 g of metal hanging on an edge that weighs 12 g/m. Hardware that
weighs nothing drapes like a decal, so zippers and buttons enter the solver
as **named attachments** with their own compliance and per-particle mass —
named, because unzipping has to *replace* the chain's constraints, and an
append-only list cannot.

- **Zippers**: nylon coil, moulded plastic, brass; #3–#10; one-way, two-way
  head-to-head (opens the middle) and bottom-to-bottom (opens the ends);
  tape, teeth, slider, puller and stopper generated. Dragging a slider is one
  number, so the GUI drag, the script and the TEE op are the same code.
- **Buttons**: 2-hole, 4-hole, shank, snap, rivet, toggle; five materials;
  weight from the disc's own volume (a 24L polyester is 0.755 g). A hole a
  button will not pass is refused with the size to cut. A rivet refuses to be
  undone. Custom buttons register from an OBJ and are *weighed*; custom
  buttonholes from a black-on-transparent PNG.
- **Openings**: a seam declared `kind="zipper"` or `"placket"` is paired
  like a seam and not sewn. `jacket-zip` and `jacket-placket` ship with one.
- **Sleeves fit the arm.** `jacket_block` drafts its sleeve cap to its own
  armhole *and* its width to the arm (`biceps=`); a combination the geometry
  cannot satisfy is refused with both ways out named.

## Animation

- **Blend shapes** (`animate`): keyframes on Anny's phenotype channels,
  solved along the track with the cloth carried forward.
- **Gait** (`walk`): walk and run from standard clinical kinematics. On a
  figure the limbs articulate and the bob is *emergent* — the lowest foot is
  put on the ground each frame and the pelvis rises because the stance leg
  straightens (76 mm peak-to-peak, twice per stride, unscripted). On a body
  with no joints (`anny`, `custom`) it travels as one piece and says so.
- **Cloth time is derived from fps.** Each animation frame gets exactly
  1/fps seconds of cloth time; a `frames_per_step` that disagrees is refused
  with the number to use. With the old free parameter a t-shirt slid 270 mm
  down a running body in one stride while every frame reported `worn=True`.
- **Travel is at the gait's own speed.** Moved slower or faster than its
  stride, a body slides every foot through its own stance — the skate that
  gives away hand-animated walks.

## Live adjustment

`pull`, `fold` and `ease` drive a `LiveSession` that prepares the constraint
graph once and reuses it: 23 ms a step on a 4,549-particle tee (43 fps),
against 56 ms rebuilt. The output is bit-identical to the batch solver, and a
prepared graph that no longer matches its garment is refused rather than
used. `ease` rebuilds (~30 ms) because a rest length is graph data; nobody
scrubs a seam allowance at 60 fps.

## Handoff

`handoff` writes the mesh with UVs from the flat pattern, the hardware, and a
manifest, in the *target's* units and up-axis. glTF states +Y up in metres
and conforming importers convert, so a `.glb` gets **no** transform from us
— checked in a headless Blender 5.2, where adding one anyway put the jacket
on its face through the floor. OBJ defines nothing, so there the transform is
baked into the vertices. Blender and Unreal get load ops; Godot gets files
and the reason its bridge cannot import a mesh.

## The rules that will bite you first

1. **Never rely on a coarse preview.** A drape that has not converged is a
   different answer, not a rougher one; the fit report refuses to quote one
   unless told to.
2. **Particle distance has a floor.** Too coarse and the shoulder seams get
   three points each and the garment slides off with every other number
   healthy. The tee block converges at 12 mm; the jacket at 11.
3. **"Nothing inside the body" is only half the question.** Read
   `contact.worn` as well; a drape on the floor scores a perfect zero for
   interpenetration.
4. **A corner-count edit invalidates seams**, and the refusal names the
   cause.
5. **A lock covers the verbs that destroy a panel, not only those that edit
   it** — and a lock that names no scope refuses rather than locking nothing.

## Interchange, fabric and licences

Unchanged from A53 and still enforced: DXF in both dialects (AAMA unverified
and flagged), 1:1 plotter sheets, 3D with exact UVs, the tech pack; every
bundled fabric card is tier `plausible` and says so; the licence gate
(`seamkiln/tests/test_licences.py`) fails the build if Triangle, `smplx` or
ArcSim data enters the dependency closure and names the replacement.

## The GUI

`uv pip install 'seamkiln[gui]' && python -m seamkiln.gui.app`. It is a
client of the core and covers the A53 loop (block, allowance, body, arrange,
drape, fit); the follow-up verbs are script- and TEE-driven and the shell has
not caught up — that is recorded as open work, not hidden.
