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
# or, as the Desktop extension serves it - several lanes, none of them the hub (A68):
tee serve --adapter blender --adapter partkiln --adapter seamkiln --project ~/patterns
#   a batch of seamkiln kinds or verbs (block, panel, seam, sew, drape...) routes here by
#   content and the reply says so; name the lane only when two could take it
#   an editable `-e seamkiln` install is a .pth read at interpreter start: restart the server after it
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
| `load` | a pattern from a DXF (AAMA/ASTM) in place of the current one; `units_mm` overrides the file's unit | A65 |
| `sew` | two runs of edges joined at shared breakpoints: a sleeve cap across a three-edge armhole in one command, the gather the runs' own ratio | A65 |
| `body` | `mannequin` · `anny` · `posed` · **`figure`** (`build` male · female, `chest_m`) · `custom` | A53 / A58 / A65 |
| `arrange` | place panels; `arrangement` = `auto` · `cylinder` · `wrap`; `dress`; `roles` names a CAD pattern's front, back and sleeves | A53 / A65 |
| `drape`, `fit`, `techpack`, `export` | simulate, measure, document, write files; `fit` reports a `chest` row: the trunk's widest slice below the armpit against the cloth's own length round it | A53 / A65 |
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
- **`custom` from a glTF that carries a SKIN keeps its skeleton and walks on
  its own legs.** Everything else walks as one piece, and the answer says
  which in `articulated`. See below.

### A body you bring, that actually bends

Until A65 P5b every imported body slid along the floor as a statue: the mesh
loader flattens a scene, so trimesh could not see a skin even when the file
carried one, and `walk` sent every non-figure body to the rigid path. Hand it
a skinned `.glb` now and it articulates.

The measurement that settles it — rigid motion can travel, rise and turn, but
it cannot change the distance between two of a body's own vertices. Over one
walk cycle, left hand to right foot: **0.932 → 1.116 m articulated, a spread
of 183 mm; 0.000 mm rigid.** The pelvis rise of 46 mm is *earned* — the feet
are put on the ground each frame and the pelvis lifts because the stance leg
straightens — where the rigid rise is the gait's scripted number echoed back.

Three things it refuses rather than guesses, because each one otherwise ends
as a confident fit report about a body that never moved: a file with **no
skin** falls back to the mesh loader and says so (an honest property of the
file); bones that cannot be **mapped** onto seamkiln's nine joints refuse by
name, never by string similarity or position, because a mis-mapped limb bends
the wrong way and reads as a solver bug; and a body whose height is not a
body's refuses outright. `adjust` reshapes the mesh, so the bind pose no
longer fits it — the rig is dropped and the answer says which, because
skinning against a stale bind pose tears a limb.

**Bring your own, or generate one.** `seamkiln.rig.character.build_character`
authors a clothable rigged humanoid from one number, its stature — licence
clean, deterministic to the byte, no download and no dependency (the skinned
glTF is written and read by hand, because trimesh ignores skins and adding a
glTF library was not worth it). For a production-quality body, research doc 67
§2 names **Anny** (Apache-2.0, assets CC0). **SMPL/SMPL-X/STAR are
non-commercial and cannot ship here.**

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

Unchanged from A53 and still enforced: DXF in both dialects (AAMA's low
layers now confirmed against a real Optitex export; the table stays flagged
until the rest are), 1:1 plotter sheets, 3D with exact UVs, the tech pack; every
bundled fabric card is tier `plausible` and says so; the licence gate
(`seamkiln/tests/test_licences.py`) fails the build if Triangle, `smplx` or
ArcSim data enters the dependency closure and names the replacement.

**The writer emits R12, because that is what pattern CAD reads.** Measured
across four real files from three vendors, every one is `AC1009`. Gerber's
parser is stricter still - it wants R12 with no `*Model_Space`/`*Paper_Space`
block definitions, no TABLES section and 7-bit ASCII - so the file goes out
through `ezdxf.addons.gerber_D6673`. We used to write R2000 to keep
`$INSUNITS`, which was backwards: real files do not set it, and the one that
did set it was wrong (below). R12 carries no `$INSUNITS`, so the writer emits
the standard's mandatory Style System Text instead, in Title Case - the form
the standard describes and Optitex writes; CLO's ALL CAPS is the
non-conforming one, and the reader takes either. `version="R2000"` remains a
named opt-out for a generic CAD viewer and reports `gerber_safe: False`.

**A declaration is a claim; a measurement is evidence.** `read_dxf` resolves
the unit from `units_mm=` first, then **a control piece**, then a non-zero
`$INSUNITS`, then the header's "UNITS: METRIC / ENGLISH" text (METRIC is
centimetres), else millimetres with a note. The control piece sits above the
declarations because a purchased Optitex block declared `$INSUNITS 6`
(metres) over geometry drawn in inches - trusting it made a 36-inch dress
36 metres long, with every seam still closing. That file carried its own
antidote, as pattern CAD does: a square marked `DO NOT CUT` and labelled
`10"X10"`, there so the receiving system can check its own scale. When the
two disagree the control piece wins, `units_conflict` reports both numbers
and the ratio, and a note says so - loudly, because a file that contradicts
itself is one you want to know about. A control piece is metadata and never
comes back as a panel.

`read_dxf` also reads R12 heavy `POLYLINE`s as well as `LWPOLYLINE`s, and
`ReadReport.units_source` says which rung won; a piece outside 20 mm-3 m is
noted rather than handed back. **An unknown layer says what it holds** -
`layer 15 holds 15 TEXT across 6 pieces` - and `strict=True` refuses rather
than guessing, because seamkiln will not invent a meaning for someone else's
convention; `observed_layers` records which of the defined layers a file
actually exercised, which is the evidence a `verified` flag needs.
"PIECE NAME:" names the piece, SIZE /
QUANTITY / "# n" land in `meta`, the style header in provenance. Layers
84-87 are the standard's quality-validation curves, not geometry: counted,
measured against the boundary (`qv_deviation_mm`, the chord error the import
carries), never imported. A file that keeps its sew line on layer 14 reads
back with `meta["outline_is"] == "cut_line"` and the allowance measured, so
`sew_line()` returns the piece. The `load` verb reads a DXF in place of the
pattern and enters the script (a replay re-reads the path; the fingerprint
catches a file that changed); through TEE it is the `load` batch op and
`sk_interchange` `action="read"`, which calls the same verb.

**A pattern from CAD, draped.** A DXF carries no seams and names its pieces
as its maker did, so the import is three commands: `load`; one `sew` per
join - two runs of edges walked from a shared landmark to a shared
landmark (the shoulder point to the underarm), split at the union of
their vertex breakpoints, a sleeve cap across a three-edge armhole in one
command (a run's edge directions are read off how they touch; a
single-edge run takes `reverse`); then `arrange` with `roles` (`front` ·
`back` · `sleeve_l` · `sleeve_r`). One convention to
know: seamkiln's arm `R` is the one beside the front's +x armhole, and CLO
draws the front as worn, so CLO's "Manga Esquerda" (the wearer's left) goes
on arm `R` - given the other way round the seams drag each sleeve across
the body. On the figure the same commands take the wrap arrangement and
the dressing; a short cap sleeve is dressed with `baste_head_mm: 0` and
`baste_sleeves: false`, because the head basting that keeps a block's
130 mm cap on the deltoid folds a 98 mm one (measured: sleeves facing 0.10
with it, 0.93 without). The measured drapes of a CLO women's M tee on the
mannequin and on the figure are in PROGRESS (2026-09-04).

**The figure's builds.** `body figure build=female` is the figure with
every proportion moved by the female/male ratio of mean-over-stature from
ANSUR II (2012, 1,986 women and 4,082 men, public data): chest 0.96,
waist 0.99, hips 1.08, shoulders 0.95, upper arm 0.92, neck 0.89, head
1.05, lengths within 3 %. `build=male` is the figure exactly as it was,
pinned by mesh digest. `chest_m` fits the trunk to a girth measured as the
widest trunk slice below the deltoids, and the rest of the body follows
the chest by the survey's slopes at fixed stature (shoulders 0.09, upper
arm 0.84, waist 1.12, hips 0.60 on the female build), because a trunk
scaled alone left the shoulder girdle in free air and folded both sleeve
caps. Both builds have a trapezius: the shoulder line slopes from the neck
base down to the deltoid tops by the survey's cervicale-minus-acromial
drop, women's rows for the female build and men's for the male. The
figure's trunk top used to be flat with the deltoids standing proud of
it, and on that flat top a walking tee's shoulder ratcheted outward 36 mm
in two strides; on the slope it holds to a millimetre on either build.
The male figure's numbers were re-based on 2026-09-04 (PROGRESS). A
women's M tee on the female figure at 1.65 m and 0.86 m:
`camiseta_female_1_65_0_86.json` in the session scratchpad.

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
