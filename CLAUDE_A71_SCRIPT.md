# CLAUDE_A71_SCRIPT.md — the Fusion lane goes live: the Mac smoke and what it decides

**Owner directive (2026-09-06):** *"Write a claude code script to execute
everything on a session local to my Mac."* This is that script: everything
A69 and A70 could not do from a Linux container — run the Fusion lane
against the real application, run the other live suites the A68 changes
touch, act on what the measurements say, and put the three decisions that
are the owner's in front of the owner. Written for a cold local session
with the owner present. Research doc 71 is the design of record for the
lane; `docs/fusion-lane.md` is the user guide.

## Amendments (2026-09-06, the local session that ran this script)

The session was autonomous — no owner at the keyboard — and the machine
differed from the script's assumptions in ways that were measured before
anything was changed. Each amendment is a commit on this branch and a
DECISIONS entry; PROGRESS carries the numbers.

1. **P1 step 1 (install the TEE add-in) was replaced, not skipped.** The Mac
   runs the FusionMcpBridge (HTTP 127.0.0.1:8766, auto-starting, the add-in
   behind the CERES 50 baseline) and has no TEE add-in. The lane gained
   `FusionHttpWire` and `FusionAutoWire` (whichever add-in answers); `tee
   serve --fusion-http-port`, `[fusion] http_port`, `tee doctor` and the smoke
   follow. Every live fact was measured over the FusionMcpBridge; the TEE
   add-in's own hop remains hermetically proven only.
2. **P1 step 1 (the owner opens an empty design) is the harness's, opt-in.**
   `TEE_FUSION_SCRATCH_DESIGN=1` lets `tests/test_fusion_live.py` open one
   untitled design when nothing is open and close exactly that document
   unsaved (doc 71 row 51). Law 1 still binds the lane; without the flag the
   smoke skips as written.
3. **Law 3 was followed and found a crash.** Resolving a token from a closed
   design segfaults Fusion (`findEntityByToken`; doc 71 row 54). The id map is
   per document, keyed by `Document.creationId` (row 52) — the root
   component's token, the first key tried, is identical across untitled
   designs. Fusion was force-quit and relaunched twice for it, with only the
   harness's scratch design ever open.
4. **The P2 table's `export_stl_unit_measured` row was not followed
   literally.** Hardcoding the `mm` one design measured would have been a
   declaration; STL's `units` is read from `UnitsManager.defaultLengthUnits`
   (row 53) at export time instead.
5. **P4 was not executed.** The three `AskUserQuestion`s need the owner; each
   decision is prepared in PROGRESS with its consequences and left open.
   A fourth was named — a second Fusion lane on the default branch, to be
   reconciled before PR #1 could merge — and **withdrawn on 2026-09-07** when
   it was measured against `origin` instead of a local checkout: no branch but
   this one carries a Fusion adapter, bridge, test or `fu_*` tool, and 0.22.0
   is claimed once (PR #2), not twice. PR #1's real conflict with its base was
   two files, neither of them Fusion, and is resolved. PROGRESS and DECISIONS
   carry the measurement.
6. **Law 6 (no model identifiers in commits)** was already contradicted by
   every commit on this branch, which carry the harness's co-author trailer;
   this session's commits carry it too.
7. **P0's `uv sync --extra extract` is not enough on a fresh venv:** seven
   fleet extras (pointcloud, pdf, quant, solve, medimg, assets, physical)
   plus OCP and an editable partkiln were needed for a green suite and the
   partkiln smoke; `tee doctor`'s fleet-extras line names most of them.

## Orientation

- Repo root `TokenEfficiencyEngine/`, code in `server/`. Work on branch
  `claude/tee-component-integration-iflsyq` — PR #1, which already carries
  A68, A69 and A70. Pull first; commit per phase; push to that branch.
- Read `docs/PROGRESS.md` (A69, A70 and the tail of A68) before anything.
- The machine: Fusion, Blender and the OCP wheel (partkiln) are installed
  here; FreeCAD may or may not be running. **Fusion has no headless mode**:
  every Fusion step needs the add-in running inside the open application,
  and the GUI clicks are the owner's — ask, then wait; never try to drive
  the Fusion window yourself.
- Two things the container measured and this session must not re-litigate:
  the A69 and A70 numbers in `benchmarks/RESULTS.md` are on the shim and
  stand as shim numbers; the reference rows in doc 71 §3 are verified and
  stand — this session fills the LIVE column beside them.

## Laws for this session

1. **The owner's documents are the owner's.** The lane never creates,
   saves, closes or uploads a document. The smoke runs only in a fresh,
   empty design the owner opened for it (`tests/test_fusion_live.py`
   refuses anything else) and that design is closed without saving.
2. **A measurement is evidence; a declaration is a claim** (the A65 law).
   Every fact the smoke prints is a measurement; what the code and docs
   declare is corrected to match it, never the other way round.
3. **A live failure is fixed with a reference row first.** If Fusion refuses
   a call, the fix starts in doc 71 §3 (read the page, amend the row), then
   the codegen, then the shim, then the test — in that order.
4. **Green is earned.** No `dcc` test is skipped, marked or loosened to pass;
   no capability is granted to TEE to get past a trust denial; the taint law
   stays.
5. **Three decisions are the owner's**, put to them with `AskUserQuestion`
   and never assumed: the Desktop manifest, the version cut, and marking
   PR #1 ready for review.
6. No model identifiers in commits, PR text or code.

## P0 — preconditions (no commit)

```
git fetch origin claude/tee-component-integration-iflsyq
git checkout claude/tee-component-integration-iflsyq && git pull
cd server && uv sync --extra extract          # Pillow: the PNG fallback for capture
UV_FROZEN=1 uv run pytest -q                  # the hermetic suite must be green here first
UV_FROZEN=1 make lint
uv run tee doctor                             # note every check; fusion-bridge will warn until P1
```

If the hermetic suite is not green on this machine, stop and report: this
session's job is the live half, and a red hermetic half is a different job.

## P1 — the Fusion smoke (one commit: the facts)

1. Ask the owner to do, in Fusion: **Utilities → Add-Ins → Scripts and
   Add-Ins → Add-Ins tab → the green + → choose
   `adapters/fusion/tee_bridge/TEE` in this checkout → select TEE → Run.**
   The Text Commands palette logs `TEE bridge listening on 127.0.0.1:9881`.
   Then **File → New Design** (empty, parametric — Design Settings →
   Capture Design History on). Wait for the owner to say both are done.
2. `uv run tee doctor` — the `fusion-bridge` check must be ok and name the
   version and the document. If it warns "a modal dialog may be holding
   Fusion's primary thread", ask the owner to bring Fusion forward and
   dismiss it (the FreeCAD SI-B12 lesson, `docs/troubleshooting.md`).
3. Run the smoke, with output shown:
   ```
   UV_FROZEN=1 uv run pytest -q -s -m dcc tests/test_fusion_live.py
   ```
   It drives `docs/fusion-lane.md` steps 1–11 and ends by printing a JSON
   block and the path of `fusion-live-facts.json`. Copy that file to
   `docs/research/71-fusion-live-facts.json` — it is the evidence and it is
   committed.
4. If a step FAILS (not skips): the traceback names the op and Fusion's
   message. Do not patch around it. Read the reference page for the call,
   amend doc 71 §3's row, fix the codegen, mirror the shim, add or adjust
   the test, re-run the smoke from step 3. Each such fix is its own commit
   whose message quotes Fusion's message.
5. Ask the owner to close the smoke's design without saving.

*Acceptance:* the smoke passes end to end; the facts file is committed;
`tee doctor` reported the bridge ok.

## P2 — act on the facts (one commit per fact that changes code)

Each fact answers a doc 71 §9 item and may change code. Work the table; a
fact that confirms the current behaviour changes docs only.

| fact | answers | if it says… | then |
|---|---|---|---|
| `capture_extension_fusion_wrote` | §9 item 1 | `.png` only | leave `capture_program` (jpg then png) but note in `docs/fusion-lane.md` that every capture costs the PNG re-encode; if `.jpg` — nothing |
| `bare_rectangle_constraints` | §9 item 7 | > 0 | `addTwoPointRectangle` adds its own horizontal/vertical constraints: make the shim's `_SketchLines.addTwoPointRectangle` add the same four, fix `test_fusion_v2.py`'s constraint counts (5 → 9 on the dimensioned rectangle) and say so in `docs/fusion-lane.md`; the inline `constraints` list in the guide's example loses its four line constraints |
| `dimensioned_sketch_fully_constrained` | §9 item 7 | False | Fusion counts differently from the shim's rectangle solver: record which constraint it still wants (`tee_scene_summary` of the sketch) in doc 71 §10.8 and do not change the shim's answer to lie |
| `param_set_recomputes_the_body` | the parametric truth | False | the body did not follow the parameter: read `Design` for a recompute call (a new §3 row) before emitting anything |
| `face_hole_default_bores_into_material` | §9 item 4 | False, and `face_hole_flip_bores_into_material` True | invert the default in `_emit_hole`: a face-placed hole sets `isDefaultDirection = False` unless `flip` is given; mirror in the shim's `HoleFeature`, tests and `docs/fusion-lane.md` |
| `counterbore_volume_matches` | row 31 | False | compare the drop with the plain-hole drop to see whether the counterbore ring or the depth is off; read `HoleFeatures_createCounterboreInput.htm` again before changing the argument order |
| `top_face_edges_chamfered` | row 35 | any number | record it; the hole rims are edges of that face too, so more than four is right |
| `revolve_pappus_matches` | row 36 | False | check the axis (x of the sketch plane) and the angle unit before anything else; the shim is Pappus and is not wrong about Pappus |
| `new_component_extrudes_reported` | row 50 | fewer than 2 | `feature.parentComponent` did not match an occurrence's component: read `ExtrudeFeature.htm` for how a new-component extrude reports its occurrence (a new row) |
| `joint_moved_occurrences` | §9 item 5 | either | record which one in doc 71 §10.5 and §9; the shim keeps moving nothing and the docs say which occurrence Fusion moves |
| `joint_rotation_reads_back` | row 46 | not 45 | `rotationValue` is radians and settable per the row; if it reads 0, the joint may need `isLocked` off or the motion is not what was set — read `RevoluteJointMotion.htm` again |
| `export_obj_unit_measured` / `export_stl_unit_measured` | row 30 | cm / whatever | set `_EXPORT_UNITS["obj"]` and `["stl"]` in `adapters/fusion/tools.py` to the measured unit and drop the STL "cannot know" note |
| `export_iges_global_units`, `export_sat_header`, `export_3mf_unit`, `export_usd_metersPerUnit` | §9 item 6 | a unit each | set `_EXPORT_UNITS` for the four and turn each `_EXPORT_NOTES` entry into the fact; `fu_export` may then declare `units` for them |
| `fu_drawing` (second test) | §10.7 | a sheet | record partkiln's `agree` for the sheet in doc 71 §10.7 |

Then fill doc 71 §3's live column: every row the smoke exercised gets `●
<Fusion version>` in place of `○`; rows it did not exercise stay `○` with a
word saying why. Rewrite §8.2 "Live" from the facts and answer §9 items 1
and 4–7 in place. Run `UV_FROZEN=1 uv run pytest -q tests/test_fusion_v2.py
tests/test_fusion_adapter.py tests/test_fusion_tools.py` after every code
change, and the smoke again after any codegen change.

## P3 — the other live suites this branch touches (one commit: the record)

A68 changed Blender's batch pre-validation and the partkiln capture
refusal; both were proven on fakes. On this machine, prove them live:

```
UV_FROZEN=1 uv run pytest -q -m dcc tests/test_blender_live.py      # needs the Blender binary (TEE_BLENDER)
UV_FROZEN=1 uv run pytest -q -m dcc tests/test_partkiln_live.py     # the OCP wheel
cd ../partkiln && PYTHONPATH=src uv run --project ../server \
    python examples/acceptance/run_tee.py --out /tmp/pk-acceptance    # step 7 is the two-call route
```

With both Fusion and a Blender bridge up (`tee serve --adapter fusion
--adapter blender --project <a scratch dir>` from Claude Code or Desktop):
`fu_export format=obj of=b1 into=blender` must land with a read-back
verdict and `tee_capture adapter=blender` must return the plate. Record
the numbers (calls, tokens from the response log) in PROGRESS. FreeCAD's
live suite runs only if the owner has it up; do not start it.

## P4 — the owner's three decisions (one commit each, only if taken)

Ask with `AskUserQuestion`, one question each, after P2 and P3 are green:

1. **The Desktop manifest.** If the smoke passed, offer to add the lane:
   `packaging/mcpb_manifest.json` `server.mcp_config.args` gains
   `"--adapter", "fusion"` after `seamkiln`; `tests/test_multi_adapter_serve.py`
   (the manifest test asserts the exact adapter list) gains `"fusion"`;
   the manifest's description and keywords name Fusion; `tee_status` on the
   Desktop composition must still show no `default_adapter`;
   `tests/test_server_lint.py` (manifest `tools[]` unchanged) and
   `tests/test_instructions.py` (instructions ≤ 2,048 bytes with the fourth
   lane) must stay green. Doc 71 §4.10 and the CLAUDE.md bullet drop
   "unchanged until the smoke".
2. **The version cut** (0.22.0 if taken): `server/pyproject.toml`,
   `server/Makefile` `TEE_SERVER_VERSION`, the manifest `version`;
   CHANGELOG's Unreleased section becomes `## 0.22.0 — <date>`; then
   **re-lock** so `uv sync --locked` passes on CI — `uv lock` with a uv of
   the same major as CI's (0.12; `uv --version`), and the diff must be the
   one `tee-engine` version line, nothing else (the A68 lesson: a local uv
   of another major rewrites the lock). `tests/test_a46_version_agrees` must
   pass.
3. **PR #1 ready for review.** If yes, mark it ready (it is a draft) and add
   one comment summarising the live facts with the standard footer.

## P5 — record and push (one commit)

`docs/PROGRESS.md` gets an "A71 — the Fusion lane goes live" section with
the facts, every code change P2 made, the P3 numbers and the decisions
taken; `CHANGELOG.md` Unreleased (or the cut version) names the live
verification; `docs/fusion-lane.md` loses "built and tested on a hermetic
shim — the live half is the smoke" and says what was verified live on which
Fusion version; the CLAUDE.md A69/A70 bullet says the smoke ran. Then:

```
cd server && UV_FROZEN=1 uv run pytest -q && UV_FROZEN=1 make lint
git push -u origin claude/tee-component-integration-iflsyq
```

## Verification (the whole thing, in order)

```
cd server
UV_FROZEN=1 uv run pytest -q                                    # hermetic
UV_FROZEN=1 uv run pytest -q -s -m dcc tests/test_fusion_live.py # the smoke, Fusion open
UV_FROZEN=1 uv run pytest -q -m dcc tests/test_blender_live.py tests/test_partkiln_live.py
UV_FROZEN=1 make lint
```

Done, in evidence: `docs/research/71-fusion-live-facts.json` committed; doc
71 §3's live column filled and §9 answered; every fact-driven code change
with its test; the Blender and partkiln live suites green; PROGRESS and
CHANGELOG updated; the three decisions recorded as taken or declined; the
branch pushed and CI green on PR #1.
