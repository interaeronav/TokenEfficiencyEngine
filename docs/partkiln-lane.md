# The mechanical CAD lane (A66)

`partkiln` is a parametric mechanical CAD kernel on OCCT: constrained
sketches, a feature tree, named topology, assemblies with mates and joints,
drawings whose dimensions are read back from the model, and exports that
declare their own units. It joins TEE through the `Adapter` protocol, so it
arrives with **no new always-loaded tools** — `tee_scene_summary`,
`tee_batch`, `tee_diff`, `tee_checkpoint` and `tee_rollback` already know
this shape.

```bash
# dev: OCP is already in server/.venv, so NEVER add [brep] there -
# cadquery-ocp-novtk ships the same top-level OCP package and would clobber it
uv pip install --python server/.venv/bin/python -e partkiln

tee serve --adapter partkiln --project ~/parts
```

The surface before A66 was 17 tools / 2,033 tok. After A66: 17 tools /
2,033 tok. Fourteen `pk_*` tools sit behind progressive disclosure; find them
with `tee_search_tools("export STEP")`, not by reading a list.

## The loop

The Inventor core loop, headless, one batch at a time:

```
sketch (constrained, dimensioned) -> features (extrude/revolve/sweep/loft/hole/
fillet/chamfer/shell/draft/pattern/mirror) -> part (feature tree + parameters)
-> assembly (mates, joints, DOF, interference, BOM) -> drawing (views, dims READ
from the model) -> export (STEP/IGES/BREP/STL/OBJ/3MF/GLB/DXF) -> Blender/Unreal
```

The script **is** the state. Every mutation is a `Command`, every Command is
recorded, and replaying the script rebuilds the part to the same fingerprint —
which is why a checkpoint is the script (the `.brep` beside it is only a
cache) and why a part family is `pk_script(action="replay", overrides={...})`.

A whole bracket in one batch:

```json
[{"op":"param_set","props":{"W":"120mm","H":"80mm","T":"10mm"}},
 {"op":"create","kind":"part","name":"bracket","props":{"material":"steel_s275"}},
 {"op":"create","kind":"sketch","name":"base",
  "props":{"plane":"XY","profile":[{"rect":["W","H"],"tag":"outer"}]}},
 {"op":"create","kind":"extrude","name":"plate","props":{"sketch":"base","distance":"T"}},
 {"op":"create","kind":"fillet","name":"f1","props":{"edges":"plate:edges(dir=Z)","r":"5mm"}},
 {"op":"create","kind":"hole","name":"h",
  "props":{"on":"plate.end","at":[[10,15],[110,15],[10,65],[110,65]],
           "std":"M6 clearance normal"}}]
```

One round trip; the diff answers with `feat:plate {delta_mm3: 96000, faces: 6}`,
`feat:f1 {delta_mm3: -214.602, resolved: {"plate:edges(dir=Z)": 4}}`,
`feat:h {delta_mm3: -1368.478, assumed: {dia: "6.6mm from ISO 273:1979 …"}}`.
Never a mesh, never a coordinate list.

## Verbs (the `tee_batch` vocabulary)

Every op takes `name` (≤ 24 chars, `[a-z0-9_]`; omitted → `<kind><n>`).
Children of a multi-instance op are `h.1, h.2 …`. A parameter name or an
expression (`"W/2 - 5mm"`) is legal wherever a length is.

| op / kind | what it does | required props |
| --- | --- | --- |
| `param_set` | create-or-set named parameters; expressions allowed | `{name: value…}` |
| `set doc` | `units`, `standard` ISO\|ANSI\|DIN, `angle` first\|third, `strict_units` | — |
| `create part` | a body to hang features on | — (`material` optional) |
| `create sketch` | a constrained, dimensioned profile | `plane`, `profile` |
| `create extrude` | prism from a sketch; `mode` new\|join\|cut\|intersect, `taper` | `sketch`, `distance`\|`to` |
| `create revolve` / `sweep` / `loft` | the other three sweeps | `sketch`+`axis` / `profile`+`path` / `sections` |
| `create hole` | drilled holes with seats and cosmetic threads | `on`, `at`, one of `dia`\|`std` |
| `create fillet` / `chamfer` | edge blends — **no default radius: design intent** | `edges` + `r` / `d` |
| `create shell` / `draft` | hollow out; taper faces off a neutral plane | `faces`+`t` / `faces`+`angle`+`neutral` |
| `create pattern` / `mirror` | `layout` rect\|circ\|sketch; `suppress:[i]` | `of` + the layout's own props |
| `create combine` / `split` | boolean between bodies; cut a body by a plane or face | `bodies`+`mode` / `body`+`plane` |
| `create plane` / `axis` / `point` | datums (`offset`, `through`, `angle`, `normal_at`, `midplane`) | — |
| `create component` / `mate` / `joint` | assembly instances and constraints | `part` / `kind`+`a`+`b` |
| `create drawing` | sheet, views, dims, hole table, parts list, title block | `of` |
| `create sheet` | sheet metal: thickness, width, flanges, K | `t`, `width`, `flanges` |
| `set` / `delete` | any creation prop, `suppressed`, `material`, `name` / `id` (+`cascade`) | `id` |
| `export` / `check` | write a file / verify a spec | `format`+`out` / `spec` |

## The fourteen tools

| tool | what it is for |
| --- | --- |
| `pk_probe` | kernel health: OCCT version, mode (in-process\|sidecar\|absent), warm state, licences |
| `pk_verbs` | the vocabulary above, with one example op per kind |
| `pk_lint` | pre-flight a batch: schema, units, unresolvable refs, sketch DOF — applies nothing |
| `pk_query` | resolve a selector to names with sub-shape facts; the feature tree; changes since a revision |
| `pk_measure` | mass, clearance, interference, min wall, section area, face inventory — live or from a file |
| `pk_check` | verify a spec → verdict + violations, each with `got`, `limit` and the fix |
| `pk_standards` | clearance/tap/drill for a bolt, ISO 4762/4014/4017/4032/7089, with source and licence |
| `pk_materials` | material cards (density, E, yield) with an honesty tier per value |
| `pk_bom` | bill of materials: structured or parts-only, qty, material, mass |
| `pk_drawing` | write a dimensioned sheet to SVG/DXF/PDF |
| `pk_export` | STEP AP242/214/203, IGES, BREP, STL, OBJ, 3MF, GLB, DXF + a handoff manifest |
| `pk_flat` | sheet-metal flat pattern: BA/BD per bend, flat extents, bend lines, DXF layers |
| `pk_import` | STEP/IGES/BREP in as a base body with fingerprint-named faces |
| `pk_script` | dump / replay / replay-with-overrides (the part family) / compare fingerprints |

Three of them write files (`pk_drawing`, `pk_export`, `pk_flat`) and two
mutate the document (`pk_import`, `pk_script`), so all fourteen are tabled
**individually** in the trust kernel — there is deliberately no `pk_` family
row that would hand a writer the open read tier.

A tool whose kernel method is not registered in your install answers
`pk_bad_op` and lists the methods that are. That is the honest signal a lane
under construction owes you; it is never a crash.

## The rules that will bite you first

1. **A sub-shape is addressed by name, never by an index.** `plate.end`,
   `h.1.wall`, `fillet1.face[0]` — or a selector like
   `plate:edges(dir=Z, not(of=hole))`, which resolves at regen and reports how
   many it caught (`resolved: {"plate:edges(dir=Z)": 4}`). Seam edges are
   excluded by default and the count says so.
2. **A bare number is millimetres (or degrees), and the diff says so once.**
   `"0.5in"`, `"3/8in"`, `"90deg"` are all accepted; an unknown suffix refuses
   and names the ones that work. `set doc strict_units=true` makes a bare
   number an error instead.
3. **A boolean that changes no topology is a failed boolean** — `pk_no_effect`,
   not a silent success.
4. **An edit reports its blast radius.** `param_set T=12mm` answers
   `changed: [{feature: plate, delta_mm3: 19200}, …]`, `unchanged_features:
   ["c1"]`, `failed: []` and the part's new volume — 162 tokens instead of
   re-reading the part.
5. **A drawing dimension is read back from the model, never typed.**
6. **Cold import never blocks a call.** `import OCP` costs 26 s in a fresh
   venv, so it is submitted as a job at boot; a batch that lands inside it
   waits two seconds and then refuses `pk_warming` with the job id.
   `pk_probe`, `tee_scene_summary` and `tee_checkpoint` answer anyway, from
   the in-process mirror.
7. **A hole's `at` is in the face's own frame**, whose origin is the world
   origin projected onto that face — the diff echoes the frame it used.

## Units, and what each format declares

Everything on the wire is **mm and degrees**, both directions. What comes out
is another matter, and the export manifest says which:

| format | declares its unit? |
| --- | --- |
| STEP (AP242 default), 3MF | yes — mm |
| GLB | yes — metres, Z-up corrected by the writer |
| IGES, BREP | implicitly mm |
| STL, OBJ, DXF | **nothing** — the manifest carries the unit instead |

## Checkpoints

`tee_checkpoint` writes `{script, fingerprint, names}` plus one `.brep` per
body under `<project>/.tee/partkiln/`. `tee_rollback` reloads the script; if
every `.brep` still matches it reads the shapes back (about a millisecond),
and otherwise it replays the script. A missing checkpoint refuses
`pk_checkpoint_missing` naming `tee_purge` — a purge is the usual reason one
went away.

## Refusals

Every refusal is one line with a code and the exact fix:
`pk_bad_op`, `pk_kernel_absent`, `pk_not_served`, `pk_warming`, `pk_too_long`,
`pk_plane_missing`, `pk_plane_mismatch`, `pk_unit_unknown`, `pk_unit_kind`,
`pk_unitless`, `pk_ref_unknown`, `pk_ref_stale`, `pk_ref_ambiguous`,
`pk_ref_empty`, `pk_no_effect`, `pk_sketch_overconstrained`, `pk_sketch_open`,
`pk_spec_conflict`, `pk_needs`, `pk_part_ambiguous`, `pk_delete_blocked`,
`pk_op_failed`, `pk_checkpoint_missing`, `pk_checkpoint_mismatch`,
`pk_bad_expr`, `pk_bad_request`, `pk_internal`, `pk_worker_timeout`,
`pk_worker_dead`, `pk_worker_down`, `pk_capture_text_first`.

Each one names the geometry it is talking about: the frame's origin and
normal, the bbox, the history event that removed a face ("removed by hole h"),
the nearest candidate with its Δ in mm, or `NbFaultyContours` with the edge
and the height of the smallest face the fillet had to roll across.

## No pixels

`tee_capture` refuses `pk_capture_text_first`. The numbers are the evidence:
`pk_drawing` writes an SVG sheet whose dimensions were read from the model,
`pk_measure` answers mass, bbox, clearance and interference, and
`tee_entity_detail` answers one entity. A JPEG through Blender is opt-in and
lands with the handoff work, not before it.

## Licences

`partkiln` is MIT. OCCT (LGPL-2.1-only WITH OCCT-exception-1.0, reached
through the Apache-2.0 OCP wheel and dynamically linked, NOTICE shipped) is
the one weak-copyleft dependency. GPL never runs in-process: `py-slvs` and
SolveSpace are GPL-3.0 and `cadquery` drags casadi (LGPL-3.0+) plus nine VTK
dylibs, so the lane writes its own scipy sketch and assembly solvers. The
standards data comes from bd_warehouse (Apache-2.0) and threadlib (BSD-3);
FreeCAD Fasteners, BOLTS and Wikipedia tables are never vendored. A licence
gate test enforces all of it, and `pk_probe` prints the summary.

## Measured (2026-09-04, M5 Max, OCCT 7.9.3)

The nine-op bracket above plus a slot and a chamfer: **0.29 s**, 26 faces,
64 edges, 91,159.605 mm³, 715.603 g. As tokens
(`benchmarks/RESULTS.md`): 1,532 tok / 2 calls, against 8,404 tok / 6 calls
for a face-and-edge inventory plus three screenshots plus the SVG sheet, and
25,311 tok for the STEP file as text. The follow-up `param_set T=12mm`:
**162 tok**, one call, against 6,156 tok to re-read everything.

## What this lane does not do

FEA, CAM, tube & pipe, harness, frame generators, mould features, direct
edit, presentations, 3D PDF/DWF/DWG, USDz, and every proprietary format in
both directions (Parasolid, SAT, JT, CATIA, NX, SolidWorks, Creo, Rhino, IFC,
and `.ipt`/`.iam`/`.idw`).

## What arrived after the first release

- **ISO 286 fits** (`standards fit`, and `fit:` on a hole). No tolerance
  table was transcribed: the grades are computed from the standard's own
  published formulas with the clause cited, and a fit that cannot be derived
  **refuses by name** rather than being guessed. Ask for `8H7/g6` or
  `20H2/h2` and it says which value it does not have.
- **A helical `coil` and a modelled `thread`**, beside the cosmetic one.
  Cosmetic stays the default and stays cosmetic — same shape object, delta
  exactly zero, fingerprint bit-identical. A modelled M6 costs ~0.6 s and 22
  faces where the cosmetic one costs 2 ms, so it is asked for, never assumed.
- **A Qt shell** (`partkiln[gui]`), a client of `partkiln.document` in the
  same sense seamkiln's is: every control builds the same command dict a
  batch accepts and shows the diff the kernel returned. It covers 10 of 37
  kinds; the rest are listed in `docs/partkiln-gui.md` and asserted against
  the kernel, so the list cannot rot silently.
- **Overlapping sketch profiles are one region.** Draw three closed profiles
  that cross and you meant a dumbbell, so they are unioned and the diff says
  `assumed["overlap"]` once. Before this, they were classified as nested or
  disjoint by a single sample point and silently built the wrong solid.
- **A self-crossing loop refuses** (`pk_sketch_open`), naming both curves and
  the point where they cross. A bowtie used to extrude to a face of zero
  area and report `status: ok`.
