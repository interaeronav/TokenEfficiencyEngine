# CLAUDE.md — Token Efficiency Engine

## What this project is

TEE's mission is to help **any AI** optimize its token usage and improve its
work efficiency (A32) — refined by A39 into two pillars: make every exchange
small, and run work on the cheapest capable engine (AI resource management
between metered cloud intelligence and unmetered local intelligence; the
client model remains the only party that ever touches a cloud API). Concretely it is an MCP server + API layer between an
AI model and the tools the model drives; its core metric is **tokens per
completed user task**, and every design decision is judged by that metric
first. Unreal Engine and Blender are the two shipped adapters and the proving
ground where every pattern is implemented and measured — not the boundary of
the product. The kernel (compact state + diffs, checkpointed batches,
budgeted responses, progressive tool disclosure, project memory, extraction,
KB retrieval) is tool-agnostic; all DCC knowledge lives in the adapters.

## How to work in this repo

- The build is driven by `CLAUDE_EXECUTION_SCRIPT.md`. Do not improvise a
  different plan while it exists; amend the script instead, then follow it.
- The self-improvement campaign (A33) is driven by
  `CLAUDE_SELF_IMPROVEMENT_SCRIPT.md` the same way: work its phases from
  where the PROGRESS evidence says they stand, with TEE's own tools as
  co-pilot.
- The A34 build (web_lookup + the TEE-native code model) is driven by
  `CLAUDE_A34_SCRIPT.md`; research docs 49 and 50 are its design of
  record.
- The A35 shrink campaign (smaller, faster, more efficient) is driven
  by `CLAUDE_A35_SCRIPT.md`, inheriting the A33 rules.
- The A37 merged build (gateway/meter/handoff/kit/kb_propose ×
  fabrication: FreeCAD, Home Builder joinery, joinery_check, boards)
  is driven by `CLAUDE_A37_SCRIPT.md`; research docs 51, 52 and 53 are
  its designs of record. `CLAUDE_A36_SCRIPT.md` is superseded — do not
  work it.
- The A38 shrink round two (post-0.5.0: faster, more efficient,
  smaller, leaner) is driven by `CLAUDE_A38_SCRIPT.md`, inheriting the
  A35/A33 rules.
- The A42 grand campaign (router × reality capture × kernel
  scheduler) is driven by `CLAUDE_A42_SCRIPT.md`; research docs 55–59
  are its designs of record. `CLAUDE_A39_SCRIPT.md`,
  `CLAUDE_A40_SCRIPT.md` and `CLAUDE_A41_SCRIPT.md` are superseded —
  do not work them.
- The A43 build (the trust kernel THEN the pipeline lane) is driven by
  `CLAUDE_A43_SCRIPT.md`; research docs 60–65 are its designs of
  record. It is DEFENSIVE security work on the owner's own machine;
  the adversarial language threat-models TEE's own surface. Let stakes
  pick the model tier and accept safety-review escalation on the
  security phases — never weaken, disable, or route around the client's
  safety policy or its model routing, and never use a local/uncensored
  model to avoid review.
- The A45 campaign (unblock the permission surface, meter paid-model
  spend and egress, land the fifteen headless open resources) is driven
  by `CLAUDE_A45_SCRIPT.md`. It builds ON the A43 trust kernel: friction
  goes, the taint law stays, and TEE still never grants itself.
- The A53 build (`seamkiln`: a garment CAD + drape kernel with the same
  core loop as Marvelous Designer / CLO3D, headless FIRST with the GUI as a
  client of that same core) is **COMPLETE**, P0–P6, and was followed by
  eleven owner-directed campaigns (A54–A64: physics calibrated against
  BS 5058, grading/cutting/tearing/pinching/lacing/finishing/animation,
  collision alignment, locks, zippers and buttons, a verified Blender
  handoff, avatars and gait, live adjustment, and the defects that using it
  found). **`CLAUDE_A65_SCRIPT.md` is now the plan of record for the
  garment lane** — the A53 script audited against what was built, with its
  acceptance debt paid (findable long tail, nameable entities, a dressing
  lane, a clothable figure, `walk` on the session's own body) and the open
  phases named. Research doc 67 remains the design of record for licences
  and platform facts; `docs/seamkiln-lane.md` is the user-facing guide. The
  licence audit is load-bearing and enforced by
  `seamkiln/tests/test_licences.py`: the best-documented open garment
  pipeline ships a NON-COMMERCIAL simulator, SMPL is non-commercial, and
  Shewchuk's Triangle cannot ship in a commercial product — doc 67 §2 names
  every mine and its replacement. **A65 P5 is now closed on both halves
  (2026-09-04):** the DXF round trip is verified against real CLO 2024 and
  Optitex exports rather than only against our own output, and an imported
  rigged body walks on its own legs (`seamkiln/rig/`, a generated
  licence-clean character — never SMPL, never a download). Four laws learned
  since A53 outrank taste: never rely on a coarse preview; cloth time per
  animation frame is DERIVED from fps; **a declaration is a claim and a
  measurement is evidence** (a real Optitex file declares metres over inches,
  so a control piece labelled `10"X10"` outranks `$INSUNITS`); and **a body's
  plane of symmetry is its skeleton, not its tessellation**.
- The A66 build (`partkiln`: a headless, AI-native mechanical CAD kernel —
  the Autodesk Inventor-class loop sketch → features → part → assembly →
  drawing → export, on OCCT through the already-installed OCP wheel, with
  the TEE adapter adding ZERO always-loaded tools) is **COMPLETE**, P0–P6,
  shipped as 0.20.0; `CLAUDE_A66_SCRIPT.md` is the plan of record, research
  doc 68 the design of record and `docs/partkiln-lane.md` the user guide, with
  ten numbered gaps at the tail of PROGRESS. Its measured facts outrank memory:
  OCCT does every core operation in milliseconds and fingerprints
  identically across processes; FreeCAD is NOT the kernel (`freecadcmd`
  crashed on the headless sketch+drawing probe; TechDraw SVG is GUI-bound;
  it embeds OCCT 7.8.1); `py-slvs` is GPL-3.0 and `cadquery` drags casadi
  (LGPL-3) + VTK, so the kernel talks to OCP directly and writes its own
  scipy solvers; the licence gate `partkiln/tests/test_licences.py` is
  load-bearing. Owner decisions (2026-09-02): shippable MIT posture like
  seamkiln, headless-first with the GUI as a later phase, name `partkiln` /
  prefix `pk_`, v1 = parts + assemblies + drawings + exports with sheet
  metal last. Two laws the build taught: a hole table counts holes, not round
  faces (a corner fillet is the same cylinder with the material on the other
  side, and a drawing that invents a hole gets it drilled); and a check that
  samples a grid is not a check — `min_wall` passed a 0.600 mm web because it
  only sampled UV cell centres.
- The `drafting/` package (A67 addendum, 2026-09-04) is a two-tier drafting-
  standards critic: tier 1 checks a sheet SPECIFICATION against SANS 10143
  building drawing practice, tier 2 checks the PLOTTED sheet for collisions,
  and `loop.run` corrects to a fixed point reporting every change. Its rules
  come from the KB entry `arch.drawing_documentation` (`confidence: medium`,
  NOT checked against the purchased SANS text), so every rule carries a
  `firmness` of sans10143 / convention / house - do not cite it to a building
  authority. It will not invent a value a human owns: an unset checker prints
  `— NOT SET —`.

- The A67 build (`pc_*`: a headless point-cloud scan-prep lane that turns a raw
  scan into scale-verified, axis-aligned DXF/SVG tracing templates while the
  model never sees a point) is **COMPLETE**; `CLAUDE_A67_SCRIPT.md` is the plan
  of record, research doc 69 the design of record, `docs/pointcloud-lane.md` the
  user guide. It is the FRONT half of reality capture and does not duplicate the
  back half: `capture_register` still owns ICP, gate and degeneracy guard
  included. Its measured laws outrank memory: `plyfile` is GPL-3.0-or-later and
  BANNED (doc 43's recorded replacement, trimesh, is what the lane uses); trimesh
  writes PLY as float32, so a UTM cloud loses 250 mm unless origin-shifted; LAS
  scale 1e-4 costs no extra bytes while 1e-3 spends a quarter of a +-2 mm budget;
  the floor is the LOWEST dominant horizontal plane, not the most populous; and
  wall azimuth comes from 3D normals over the full-height band, never from a
  slice. Every `pc_*` tool is tabled individually in the trust table - there is
  deliberately no `pc_` family row.

- The A68 build (no lane is the hub: content-routed lanes, decentralised
  Blender/Unreal) is **COMPLETE**, P0–P4 (2026-09-05), measured before and
  after in `benchmarks/RESULTS.md`; `CLAUDE_A68_SCRIPT.md` is its plan of
  record and research doc 70 its design of record. Owner directive (2026-09-05): *"allow to bypass Blender if
  not required; decentralize the use of Blender or Unreal Engine."* The kernel
  routes a batch by what it contains (entity id → create kind → op verb) and
  says where it went; the declared default is opt-in (`--default-adapter`) and
  the Desktop manifest declares none; a headless lane never touches a DCC; an
  export lands in a scene lane only when `into=` says so. Every adapter may
  declare its vocabulary with ONE optional `vocab()`; a `write-scene` virtual
  tool must name its lane in `kernel/lanes.py` or the server refuses to boot.

- The A69 build (the Fusion lane: Autodesk Fusion as a live GUI lane on the
  owner's own document, through a bridge add-in that marshals every request
  onto Fusion's primary thread) is **built through P4 on the shim and
  verified live by A71** (2026-09-06), driven by `CLAUDE_A69_SCRIPT.md`; research doc 71 is its
  design of record and `docs/fusion-lane.md` the user guide. Its law: nothing
  goes into the codegen that is not a reference-verified row in doc 71 §3 -
  Fusion has no Linux build, so the lane is built on a hermetic shim and
  **nothing was claimed live until the Mac smoke in `docs/fusion-lane.md`
  had run** — it ran (A71), filled §3's live column and left the Desktop
  manifest to the owner. Millimetres on the wire with the unit always
  written, centimetres inside; the timeline plus every parameter expression
  is the checkpoint, and it says what it cannot restore. **v2 (A70) is built
  through P5 on the shim (2026-09-06)**, driven by `CLAUDE_A70_SCRIPT.md` —
  holes, chamfers, revolves, sketch constraints and dimensions, joints, the
  iges/sat/3mf/usd exports, each a verified row (doc 71 §3, 31–50) and an
  emitter, measured in `benchmarks/RESULTS.md`; its inverted premise
  outranks memory: **the Fusion API cannot create a drawing** (row 49), so
  `fu_drawing` is the partkiln route, and a rectangle's sides are named by
  position because the API does not state their order. Both campaigns stay
  verified live by A71 (`docs/fusion-lane.md`, steps 1–11, on Fusion 2704.1.53).
  **`CLAUDE_A71_SCRIPT.md` is that smoke as a plan for a session local to
  the owner's Mac** — the live test, the other live suites A68 touched,
  the fact-driven fixes (a measurement outranks a declaration), and the
  three decisions that are the owner's: the manifest, the version cut,
  and marking PR #1 ready.

- The A71 session (the Fusion lane goes live, 2026-09-06, on the owner's Mac)
  ran `CLAUDE_A71_SCRIPT.md` with amendments the machine dictated, recorded in
  the script's Amendments block, DECISIONS and PROGRESS: the Mac runs the
  **FusionMcpBridge** (HTTP :8766, auto-starting) and no TEE add-in, so the
  lane gained a second transport and an auto wire rather than waiting for a
  GUI install; the smoke's scratch design is the HARNESS's (opt-in,
  `TEE_FUSION_SCRATCH_DESIGN=1`), never the lane's. Five live runs on Fusion
  2704.1.53 ended **2 passed, 7.8 s**; `docs/research/71-fusion-live-facts.json`
  is the evidence and doc 71 §8.2/§9 read it out. Four laws it taught outrank
  memory: **resolving a token minted in another document crashes Fusion**
  (segfault in `findEntityByToken`; the id map is per document, keyed by
  `Document.creationId` — the root component's token is identical across
  untitled designs); **STEP and the archive take a component or the whole
  design, never a body**; **USD is written as `<name>.usdz`**; and the kernel
  trims diff fields that echo the op, so a lone joint's row has no `kind` —
  `created` is the address. The three P4 decisions (manifest, version cut,
  PR #1 ready) were NOT taken by the session and are the owner's. A fourth,
  a second Fusion lane on the default branch, was **withdrawn on 2026-09-07**:
  measured against `origin`, no branch but this one carries a Fusion adapter,
  bridge, test or `fu_*` tool, so there is nothing to reconcile. A branch you
  have not fetched is a declaration, not a measurement.

  **And unpushed work on the machine you are working on is still part of the
  state.** The withdrawal above is right about every remote head and was
  re-verified; the conclusion that nothing had to be reconciled was not. The
  second lane was real, in **six unpushed commits on the owner's own machine**
  - 3,069 lines at these same paths, live-verified, stamped 0.22.0. The owner
  then chose: keep this lane and port the three tools only the other had
  (`fu_design_stats`, `fu_search_docs`, `fu_api_detail` - a live API index of
  the build you are connected to, 13,498 symbols in 0.2 s, cached per
  version, listing calls the codegen deliberately never emits).
- The A72 build (`wt_*`: a headless wind-tunnel lane that drives OpenFOAM, SU2
  and OpenVSP/VSPAERO from one budgeted loop and reads the answer back through
  ParaView's `pvpython`, while the model never sees a cell) is **COMPLETE**,
  P0–P6, shipped as 0.22.0; `CLAUDE_A72_SCRIPT.md` is the plan of record,
  research doc 72 the design of record, `docs/windtunnel-lane.md` the user guide
  and `docs/setup-windtunnel.md` the install. Its laws outrank memory: every
  engine is a SEPARATE PROCESS (OpenFOAM GPL-3, SU2 LGPL-2.1, OpenVSP NOSA-1.3;
  `foamlib` is GPL-3.0-only and BANNED with `PyFoam`, `fluidfoam`, `vtk`,
  `pyvista` and the OpenVSP Python bundle, by `test_windtunnel_licences.py`);
  no tutorial case is ever vendored and the lane downloads nothing; Ubuntu's
  apt `openfoam` 1912 cannot report a force (its function objects die on an
  IOstream "sha1" error) so openfoam.com's package is the Linux install; a 2-D
  slab's Aref is chord × thickness; the verdict's stationarity test has an
  absolute floor because Cm ≈ 5e-4 makes a relative one meaningless; an
  adopted case runs as-is, its chord MEASURED from the wall patch (lRef 1 on
  the apt tutorial's 35 m section gave Cl 34); `vspscript` exits 2 after a
  complete sweep and Open MPI refuses root — both are claims the outputs
  overrule; `tee_job cancel` kills the solver process group through the
  kernel's `on_cancel` hook (a real simpleFoam gone in 0.05 s). Every `wt_*`
  tool is tabled individually — no `wt_` family row. The GUI handoff it
  deferred is **A73**, below.

- The A73 build (the wind-tunnel GUI handoff: `wt_open`, ParaView state files
  and a Qt panel) closes A72's gap 1; `CLAUDE_A73_SCRIPT.md` is the plan of
  record, research doc 73 the design of record and `docs/windtunnel-gui.md`
  the panel's guide. Owner decisions (2026-09-07): prepare always and launch
  only on request, the panel is in scope, ParaView and OpenVSP only (FreeCAD
  with CfdOF declined). Its measured laws: ParaView builds its Qt application
  BEFORE parsing arguments, so with no display even `paraview --help` aborts
  on signal 6 — the lane never asks the binary anything and decides about the
  display before it spawns; a state file carrying a view is ~206 kB and needs
  a display to WRITE, while a pipeline-only one is ~17 kB and writes
  anywhere, so the tool writes the best the machine can do, says which, and
  REFUSES rather than downgrading an explicit ask; a state names its case
  exactly once, so a moved case is a string swap; `vsp` takes the model
  positionally. The window is an escalation asked for by name through
  `registry.require`, the panel renders nothing (A67 stands), and neither adds
  a tool: the surface is still 17. **P2 then ran on the real ParaView** — the
  owner's local session, which had been looking for a replacement, reported it
  working properly on 2026-09-07 (the instability was OURS: `pvpython` wrote 201
  `.pyc` files into ParaView's signed `.app`, breaking its notarization seal so
  macOS refused to launch it; `PYTHONDONTWRITEBYTECODE=1` in `run_script` is the
  fix, and deleting the bundle's `__pycache__` dirs repairs an install) — **and
  it found three defects a fake pvpython
  can never find**: `ColorBy(d, None)` RAISES on data with no arrays (the
  meshed-but-unsolved case the mesh view exists for); a state that sets only
  `rv.ViewTime` reloads at **t=0**, because `SaveState` carries the ANIMATION
  SCENE's time — a handoff that opens the initial field while the human
  believes it is the solution; and `wt_open` on an SU2 case died with
  `NameError: ts`, the reader block having bound that name for `.foam` and not
  for `.vtu`. Doc 73 §4b keeps the three instabilities
  measured here and the five-row specification a replacement would have to
  meet: the application is an enum and the ParaView-specific code sits in two
  modules, so the swap stays cheap if the question returns.

- The A74 campaign (**cfMesh** in the wind-tunnel lane) is driven by
  `CLAUDE_A74_SCRIPT.md`; research doc 74 is the design of record and
  `docs/research/74-evidence/` holds what produced its numbers. It opened when
  "can you download and integrate HELYX" turned out to be **no** — ENGYS ships
  it to paying customers only, with no macOS build — and the owner asked for an
  analogue: the mesher HELYX sells is already inside the openfoam.com v2606
  this lane drives. A72 already RUNS `cartesianMesh` for adopted cases; A74
  writes for it. Its measured facts: `cartesianMesh` needs the `openfoam2606`
  wrapper (direct, it cannot find `libmeshLibrary.so`); on one prism, snappy
  took 46,160 cells and 12.0 s and its own log admits **1.32 of 2 boundary
  layers at 41.6 % of the requested thickness**, while cfMesh took 37,960 cells
  in 1.6 s and creates layer cells on every boundary face by construction —
  **but FAILS `checkMesh` on skewness** (5.55, twelve faces at the sharp
  trailing edge) where snappy passes at 0.70, which is the campaign's blocker
  and is never to be hidden by widening `TOLERATED_CHECKS`. Two more laws it
  starts with: cfMesh meshes the volume bounded by a CLOSED surface, so an
  external-aero case needs the domain box and the body as ONE multi-solid STL
  (each `solid` becomes a patch); and a dictionary key nearly inverted its own
  P0 — a global `boundaryCellSize` refines at the farfield and cost 630,980
  cells, where `localRefinement` on the body is the idiom. The campaign closes
  with a measured **no** if solving on the better mesh does not move Cd.

- The A51 campaign (faster headless boots, a camera that grades its own
  framing via the local VLM, and PDFs that can write ordinary prose) is
  driven by `CLAUDE_A51_SCRIPT.md`. Its three premises were all measured
  first, and one INVERTED: headless Blender boots in 0.55 s and TEE's own
  0.5 s poll interval is most of the wait, so the boot phase is about the
  waiting, not the engine.
- The A49 build (Godot as a headless first-class adapter: socket bridge,
  declarative commands, the run-scene game lane) is driven by
  `CLAUDE_A49_SCRIPT.md`. Its design rests on measured facts recorded in
  the script itself — including that headless Godot CANNOT render (dummy
  rasterizer), so capture refuses honestly and game evidence flows
  through run_scene output instead.
- The A48 build (close A47 P5, then the PDF write/edit lane:
  `pdf_compose` on fpdf2, `pdf_edit` on pypdf, round-tripped through the
  existing extract lane) is driven by `CLAUDE_A48_SCRIPT.md`. It is
  written for a cold session: orientation, the upgrade trap, and the
  measured facts it builds on are all inside the script.
- The A47 campaign (senses for blind hosts: machine vision and sound for
  host models that lack them, the opencode/DeepSeek case) is driven by
  `CLAUDE_A47_SCRIPT.md`; research doc 66 (revised) is its design of
  record. The core finding: `extract/vlm.py` already holds a working
  `LocalVlmDriver` that nothing can invoke — the campaign gives it a
  steering wheel rather than building new machinery.
- The A46 campaign (leaner, faster, fitted to this machine: cut the 2.2 GB
  extension venv, stop blocking on first imports, and wire TEE to the
  owner's ACTUAL local engines) is driven by `CLAUDE_A46_SCRIPT.md`. It is
  measured-before-and-after by law; a phase without a number did not happen.
- Progress state lives in `docs/PROGRESS.md`. Read it at session start; update
  it (check items off, note blockers) before ending any session.
- Research grounding lives in `docs/research/`. Consult it before designing or
  claiming facts about UE/Blender APIs — both APIs drift between versions, and
  hallucinated calls are the #1 friction point this project exists to fix.
  Verify any API you are unsure of against local docs or a smoke test, never
  from memory.
- `knowledge-base/` is a DIFFERENT thing: a 38-domain reference library the
  owner imported (A30), written elsewhere, never verified by this project.
  It grounds nothing on its own. To use a fact from it, re-check it against
  the source its own frontmatter cites, then carry that citation into
  whatever TEE file you put it in. `confidence: low` and
  `status: needs-verification` mean exactly what they say.
  **Never take a `bpy`/`unreal` API fact from `knowledge-base/13_*`,
  `14_*` or `15_*`** — third-party prose about a drifting API is the exact
  failure mode above. The rule in the previous bullet outranks it, always.

## Hard rules (token-efficiency dogma)

1. **Never return full scene dumps by default.** Tools return compact summaries
   with stable IDs; detail is opt-in via explicit query tools.
2. **Diffs over snapshots.** After a mutation, report what changed, not the new
   world state.
3. **Batch over chatter.** Prefer one macro-command / one code-execution call
   over N single-op tool calls.
4. **Text over pixels.** Screenshots are a last resort; structured text state
   is the default evidence.
5. **Small tool surface, progressive disclosure.** Keep the always-loaded tool
   schemas minimal; expose long-tail capability through a `run_python` /
   `run_console` escape hatch and searchable docs, not hundreds of tools.
6. **Fail loud and cheap.** Validation errors must come back in one short
   message with the exact fix, not a stack-trace novel.

## Conventions

- Python 3.11+, `ruff` for lint/format, `pytest` for tests.
- MCP server uses the official Python SDK (`mcp` package, FastMCP style)
  unless the script says otherwise.
- Type hints everywhere in `server/`; adapters may relax where DCC-embedded
  interpreters (Blender's bundled Python, UE's) constrain versions.
- Commit style: imperative subject, body explains the *why*. Small commits per
  script step.

## Testing

- `pytest` for the server core (runs anywhere, no DCC needed — DCC calls are
  faked behind adapter interfaces).
- Adapter smoke tests require a machine with Blender / Unreal installed; they
  are marked and skipped otherwise (`-m "not dcc"` in CI).
- `benchmarks/` measures tokens-per-task on scripted scenarios; run before and
  after any change to state representation or tool schemas.
