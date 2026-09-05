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
  Blender/Unreal) is driven by `CLAUDE_A68_SCRIPT.md`; research doc 70 is its
  design of record. Owner directive (2026-09-05): *"allow to bypass Blender if
  not required; decentralize the use of Blender or Unreal Engine."* The kernel
  routes a batch by what it contains (entity id → create kind → op verb) and
  says where it went; the declared default is opt-in (`--default-adapter`) and
  the Desktop manifest declares none; a headless lane never touches a DCC; an
  export lands in a scene lane only when `into=` says so. Every adapter may
  declare its vocabulary with ONE optional `vocab()`; a `write-scene` virtual
  tool must name its lane in `kernel/lanes.py` or the server refuses to boot.

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
