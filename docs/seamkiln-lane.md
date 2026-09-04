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
the shoulders, bastes every other seam, settles, and lets go. On the figure
a coat then holds 27–35 % contact at a 37–40 mm standoff, which is what a
bulky coat should do.

**The sleeve, and the solver bias it uncovered.** The fur shot's jacket
dressed with its front armholes 109 mm open at the shoulder point, and
after that was fixed one sleeve slid 60 mm down the arm in every walk. The
first was three faults in the wrap and the dressing: the sleeve tube was
aligned to the arm with a *minimal* rotation, which leaves its roll about
the arm unset (the cap apex landed at the front of the arm and the sleeve
twisted a quarter turn to meet its armhole); the block drafts one sleeve
piece for both arms, and a proper rotation can only place it the right way
round on one of them (the other is laid face-down, read from the seams, as
a cutter does); and the cap was hung at the shoulder joint, at the ball's
equator, instead of a cap height above it. Dressing now pins to the surface
and never to the bone, bastes a sleeve to the body's armhole rather than a
midpoint, and bastes the sleeve *head* with its apex, so both caps start
the release hooked over the shoulder.

The slide was something else, and it took excluding everything: the sleeve
width, the deltoid's size, the dressing pose, the arm-swing phase, wind,
friction, the zipper, the field's resolution, the panel order, the piece's
winding, the mirrored garment on the same body, the same garment on a
mirrored body. The weak side was always the figure's left. The cause was
the solver's collision normal, taken by central differences at the *floor
corner* of the particle's voxel: the surface normal half a voxel toward −x,
−y and −z of where the particle is. On a curved body that tilt is
systematic — a square dropped on a ball was shoved 55–66 mm toward −x
whichever side of the origin the ball stood — and on the right shoulder it
hooked a cap inboard while on the left it tipped the cap off. The normal is
now the gradient of the same trilinear interpolant the distance comes from,
at the particle; the mirror test drapes to 0.8 mm, and both caps climb onto
the ball in the first half second of the walk and stay. Every drape the
kernel had ever produced carried that sideways push.

Two body facts came out of the same investigation and stayed: the deltoid
is 1.06 wide across the shoulder, not 1.24 (178 mm on a 122 mm arm was 1.46
times the arm, and no sleeve a block will draft could pass it), and the
trunk is elliptical in section (width 1.10, depth 0.78 of the round radius)
because a jacket on a body of revolution has nothing to stop it turning.
The solver also takes its friction from the fabric card now; it had used
0.35 for every cloth. A piece placed by a reflection has its winding
reversed so its normals face out (its fur would otherwise grow inward), and
the mannequin path hangs its sleeves with the same frame.

**The seam that would not close, and the sleeve that was never on.** With
the sleeves properly on the mannequin's arms the tee's right side seam
opened 82 mm at the armpit corner — one pair, every other pair closed —
and nothing about the arrangement moved it: not the roll (every angle to
180°), the handedness, a cap raise, the tube's radius, a zero-gravity
baste, dressing, lower arms, or the whole arrangement mirrored (the
pattern's side-right stayed the open one). The seam pair tables did: the
right side seam was sewn one vertex out of register along its whole
length. `_pair_one_seam` matched each vertex to the first partner at or
after its parameter, and two runs of the same length differ in parameter
by rounding only, so which side got the register error was a coin toss of
1e-17 — and every last edge of an outline was one vertex short, because the
loop-closing vertex has parameter 0. Matched to the nearest vertex with the
loop closed, the tee's worst seam is 19 mm and the zipped jacket's 6, both
sleeves on the arms and facing out. The old
"converged" 25.8 mm had been a garment whose right sleeve had slid off the
arm and hung inside out at the flank — 0 % on the arm — which the seam gap
cannot see and `sleeve_wear()` now asserts. The mannequin's sleeve tube
takes its radius from the piece's own width, as the wrap path's does.

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

**The body moves within a frame.** The animator used to move the body
between frames as a jump: rebake, teleport the garment by the travel, solve
on a body standing still. Each jump up into the cloth resolved as a full
push in one substep — a kick of tens of metres per second — and nothing on
the way down pulled the cloth back, so a jersey tee rode up 16 mm per
walking stride and 40 per running stride without saturating. The solver
now takes a per-substep schedule of the body (`BodyMotion.between`,
`drape(motion=)`): the rigid part — travel, the gait's rise, a figure's
standing lift — is exact and free, and a deforming body is two fields on
one lattice (`sdf_from_mesh(bounds=)`) blended across the frame, so a limb
that swings between two poses is a surface that moves continuously.
Friction acts on the slip relative to the body, so the static regime pins
cloth to the body rather than to the world; the numerical damping acts in
the body's frame for cloth that touches it; the garment is never
teleported and its velocity is carried from frame to frame. A
`body_factory` may return `(mesh, offset)` — the mesh body-local, the
offset the rigid placement — and a rigid body is baked once. The blend's
own limit is stated on every frame as `sweep_mm` (the largest move of any
body vertex between poses): two fields pinch a limb of radius R moved δ by
about δ²/8R, below the field's half-voxel while δ ≤ 2√(voxel·R), which is
41 mm a frame for a forearm on a 10 mm voxel — the knob for that is fps,
and the error falls with δ². What looked like tunnelling on a run — three
or four particles 28–38 mm inside the body at one frame per cycle, at
every frame rate — was friction: sliver-fringe vertices thrown into the
shoulder-arm crease by their 2.5 mm rest edges were pushed out by the
collision and put straight back by a friction plane taken 20 mm inside the
body, 97° off the surface. Friction's plane now comes from the pushed
point and friction may never re-enter the body; the run reads 0.0 mm at
24 and 48 fps. What remains honest is the blend's envelope: a rigid move
larger than 2√(voxel·R) modelled as a blend leaves particles inside, so a
rigid move goes in the rigid schedule. The static path is bit-identical to
what it was.

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

## Render properties on the card

A `Fabric` carries `roughness` (0 gloss .. 1 matte) and `texture` (a path or
name for an albedo) as **render** fields. The solver never reads them, and
every place they appear says so: `describe()["render"]["physical"]` is
`False`, the material library and `sk_materials` list them, the tech pack
prints them as "render only, not physical", and a handoff manifest carries
them as `fabric_render` for the artist on the other side. Deriving a
glossier card keeps the base's tier and test report — a render change is not
a physical change; a heavier cloth is a different drape, a rougher one is
only a different picture.

## The examples: the two shots, from the repo

```bash
cd seamkiln
python -m examples.cape_shot all --out /tmp/cape     # sim, sound, render, encode
python -m examples.fur_walk  sim --out /tmp/fur --probe
```

`examples/cape_shot` is the superhero in a cape of the Namibian flag (two
jumps, a bouncy mat, a pool, wetness per vertex, sound cut from the sim's own
record); `examples/fur_walk` is the fur jacket walking toward camera (the
jacket wrap-arranged and dressed by the kernel, the walk's bob emergent, the
fur regrown each frame from one seed). Each has four stages — `sim` needs
only seamkiln, `sound` only numpy, `render` and `encode` a headless Blender
started with `--factory-startup` so the owner's open file is never touched —
and `all`. `--probe` is a short, coarse run whose only claim is that the
pipeline runs; its manifest says so in words, and the CI smoke test runs
exactly that, without Blender. Every bug those shots found is in the kernel;
the examples are what let the next session re-run them in minutes.
`python -m examples.showcase all --cape /tmp/cape --fur /tmp/fur --to film.mp4`
cuts the two finished shots, two Blender-rendered stills (the flat pattern;
the jacket arranged on the figure before the solver) and title cards into one
film. It simulates nothing itself.

## The GUI

`uv pip install 'seamkiln[gui]' && python -m seamkiln.gui.app`. It is a
client of the core: every button builds a `Command` from the session as it
stands and hands it to `Session.apply` (Law 3), and the action table is
Qt-free so a machine with no Qt still tests it. Buttons: tee block, jacket
block, allowance, mannequin, figure, arrange, drape, fit, **zip**,
**button** (one button a third of the way down the opening, hole on the
other side), **walk** (half a stride, travelling), **pull hem** (60 mm
outward from where it hangs lowest).

Verbs the shell still has **no button for** — script- and TEE-driven only:
`animate`, `cut`, `delete`, `ease`, `export`, `finish`, `fold`, `grade`,
`handoff`, `lace`, `lock`, `panel`, `pinch`, `rip`, `seam`, `techpack`,
`unfasten`, `unlock`, `unzip`. The list is asserted against `VERBS` by
`test_gui_actions.py`, so it cannot drift silently.

## The tier-2 bake: attempted, blocked

A53 named C-IPC (`ipc-sim/Codim-IPC`, Apache-2.0) as the intersection-free
bake behind an opt-in `drape quality="bake"`. A65 P4 attempted the build on
this Mac once, out of process in a scratch directory, as specified. It does
not build here: CMake 4 refuses the project's `cmake_minimum_required` floor
and its Kokkos 3.1.01 pin (worked around with the policy-minimum override),
`find_package(OPENMP)` fails on Apple, and then the compile stops at the
first Kokkos object because the project's own `CMakeLists.txt` hard-codes
x86 flags — `-mfma -mbmi2 -mavx2` — which GCC on Apple Silicon rejects. The
exact errors are in `docs/PROGRESS.md`. The XPBD solver stays the only tier;
`quality="bake"` is not offered rather than offered and broken.
