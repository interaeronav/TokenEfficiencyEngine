# CLAUDE_A65_SCRIPT.md — the garment lane, audited: what A53 and its follow-ups actually built, what they broke, and what is still owed

**Owner directive (2026-09-02, verbatim):** *"Debug and improve the whole
script"* — *"Meant the A53 SCRIPT and follow up suggested and attempted
improvements."*

`CLAUDE_A53_SCRIPT.md` is **complete and superseded by this document as the
plan of record for the garment lane.** Do not work A53's phases again. Its
research doc 67 remains the design of record for licences and platform facts.
This script exists because A53 was marked COMPLETE on 2026-09-01 and then
eleven owner-directed campaigns (A54–A64) built on it *outside any script* —
which CLAUDE.md forbids ("amend the script instead, then follow it"). This is
that amendment, written after auditing every phase of A53 and every follow-up
against the code, the tests, and a live `TeeApp`.

## Orientation for a cold session

- Repo `/Users/john/TokenEfficiencyEngine`, branch
  `claude/token-efficiency-engine-5jv1dj` ONLY. Read `docs/PROGRESS.md`
  first (the A53 close-out and the A54–A65 records are at its tail).
- Kernel: `seamkiln/` (own `pyproject.toml`, own tests). Adapter:
  `server/src/tee/adapters/seamkiln/`. User guide: `docs/seamkiln-lane.md`
  (rewritten in A65; it was three campaigns stale).
- Suites, measured at the end of A65 (this machine):
  `cd seamkiln && PYTHONPATH=src uv run --project ../server python -m pytest -q tests/`
  → **244 passed / 8 skipped** (2026-09-02); `uv run --project server python -m pytest server/tests -q`
  → **1,214 passed / 10 skipped** (2026-09-02). Lint `uv run --project server ruff check server/ seamkiln/` exit 0.
- Surface invariant: **17 always-loaded tools / 2,033 tok on the wire**
  (measured by `run_surface_scenario()` in `benchmarks/run_benchmarks.py`
  at A65's close); **126 virtual tools**, 14 of them `sk_*`. **Every
  campaign since A53 added ZERO always-loaded tools.** Keep it that way.
- The seamkiln suite takes ~7 minutes; run it in the background and do
  something else. The physics tests are converged-resolution tests by law
  and will not be made faster by lowering the resolution.
- Upgrade trap (unchanged): every `.mcpb` install wipes the extension
  venv's extras; restore with the command in A53's orientation.

## What the audit found (2026-09-02)

The audit drove every A54–A64 verb through `TeeApp.run_batch`, read the A53
acceptance criteria against the tree, and searched the tool registry for the
follow-up capabilities. Findings, each with what was done about it:

| # | Finding | Status |
| --- | --- | --- |
| 1 | A53 script stale: said COMPLETE, recorded none of A54–A64, and listed "animation and pose sequences" as **out of scope** while A54 blend shapes and A58 gait were built at the owner's request. | Superseded by this script. The owner's override is recorded below. |
| 2 | **P4 acceptance violated by the follow-ups**: `tee_search_tools` returned an *empty* result for "zipper", "fasten a button", "walk cycle animation". A capability a model cannot find is one it does not have. | **Fixed (A65 P0):** `sk_hardware`, `sk_avatar`, `sk_touch`, `sk_handoff`. All six follow-up queries land their tool top-3; pinned by test. |
| 3 | A zipped, buttoned, locked garment on a walking figure listed the same entities as a bare tee (`panel`, `seam`, `garment` only), so `tee_diff` could not name what a batch changed. | **Fixed:** `zipper`, `button`, `locks`, `body` entities. |
| 4 | `top_arrangement` mis-fits any non-mannequin body: on the figure it hung a jacket's top edge at 2.02 m for shoulders at 1.40 m, at half the girth. The "custom avatar" and "figure" bodies could therefore not be dressed. | **Fixed (A65 P1):** `drape/dressing.py` — `wrap_arrangement` (radius from the pattern), `dress` (pin shoulders, baste, settle, release). `arrange` chooses explicitly and records the choice. |
| 5 | A garment that closes into a tube falls off: seams at 4.7 mm, jacket at y = −0.79, `worn=False`. There was no dressing step anywhere in the kernel. | **Fixed:** same module. Coat on the figure: worn, 27–35 % contact. |
| 6 | `walk` ignored the session's body — it built a posed mannequin whatever body was chosen. "Walk a custom avatar" was not actually delivered through the Session. | **Fixed (A65 P2):** walks the session body; `figure` articulates, jointless bodies travel rigidly and say so; `travel` at the gait's own speed. |
| 7 | The character used in the two rendered shots lived in a temp directory; the kernel had no clothable figure. | **Fixed:** `seamkiln/figure.py`. |
| 8 | Sleeves were drafted to the armhole only; a 122 mm tube for a 194 mm arm. | Fixed in A63/A64 (`biceps=`, refusal on impossible geometry). |
| 9 | `docs/seamkiln-lane.md` documented none of A54–A64 (29 verbs; it listed 11). | **Fixed:** rewritten. |
| 10 | A53 Gap 3 (adapter tests `importorskip` the kernel). | **Partly closed:** `server/tests/test_seamkiln_translate.py` tests the adapter's own logic with no kernel. Kernel-backed tests still need the kernel, and say so. |
| 11 | A53 Gap 1 (USD via trimesh impossible). | Closed in A53's own close-out: refuses by name with two routes. Stands. |
| 12 | A53 Gap 2 (C-IPC tier-2 bake never attempted). | **Open.** See P4. |
| 13 | A53 Gap 4 (DXF round-trip has only seen its own output). | **Open — needs the owner.** See P5. |
| 14 | The GUI covers six A53 verbs and none of the follow-ups. Law 3 holds (it is a client); the "GUI as well as headless" thesis is thin for A54+. | **Open.** See P3. |
| 15 | The two rendered shots (cape, fur walk) are reproducible only from scratchpad scripts. | **Open.** See P3. |
| 16 | Replay determinism (Law 7) is tested for the A53 loop only; the follow-up verbs' fingerprints are asserted in their own tests but not through a full-script replay. | **Partly closed:** A65's session test replays a figure + wrap + dress script to an identical fingerprint. Extend in P3. |

## Status of every feature the owner asked for

Requested 2026-09-01 (two lists). *Done* means built, tested and reachable
through `tee_batch`; the evidence column names the commit or test.

| Asked for | State | Evidence |
| --- | --- | --- |
| Solid ball as the test subject; true-to-life physics | Done | A54: Cusick drape test, 6/7 fabrics in BS 5058 bands |
| Denim wet washes; real-time fur | Done | `finishing.py`; fur regrown per frame from a fixed seed in the fur-walk shot |
| Parametric grading | Done | `pattern/grading.py`, `grade` |
| Ripping and tearing along seams, frayed edges | Done | `drape/tearing.py`, `rip` |
| Symmetric pinching | Done | `drape/pinching.py`, `pinch` |
| Lacing | Done | `drape/lacing.py`, `lace` |
| Blend-shape animation | Done | `animation.py`, `animate` |
| Import/export; material quality; material library; cutting module | Done | `materials.py`, `cutting.py`, `export`, tiers on every card |
| Move the test subject; environment room (gravity/wind/temp/pressure) | Done | `BodySDF.moved`, `environment.py`, `sk_room` |
| Collision direction = render direction; restitution + friction | Done | A55 `collision.py`; restitution on the velocity |
| Symmetry sync | Done | `pattern/symmetry.py` |
| Lock graphics | Done, then **two holes fixed** (A60) | delete/redraw/re-sew/block now refuse; a no-scope lock refuses |
| Blender + TEE-connected tool integration; 3D pipeline | Done | A57 handoff, verified in headless Blender 5.2; Godot honest refusal |
| Real-time interactive adjustment | Done | A59, 43 fps measured, `pull`/`fold`/`ease` |
| Fabric library: custom textures, roughness, friction, damping, stiffness | Done for physics (friction, restitution, bending, tensile, thickness, GSM) | **Roughness is a render property and is not on the card** — see P3 |
| Avatar rigging & animation; custom avatars; walking/running; adjust anatomy | Done, **now on the session's own body** (A65) | `figure`, `custom_avatar`, `adjust`, `walk travel` |
| Zipper tool (all sub-features) | Done | A56 `hardware/zipper.py` |
| Buttons (all sub-features, custom OBJ/PNG) | Done | A56 `hardware/buttons.py` |
| Superhero cape shot; fur-jacket walk shot | Delivered as videos | scratchpad pipelines only — P3 makes them examples |

**Owner override recorded:** A53 §Out-of-scope listed "animation and pose
sequences beyond a single static pose". The owner asked for blend-shape
animation (A54) and walking/running avatars (A58) explicitly; they are IN
scope from A54 onward. The other out-of-scope items stand.

## Laws (A53's ten stand; these were learned since)

11. **Never rely on a coarse preview** (owner, 2026-09-01). A drape that has
    not converged is a different answer, not a rougher one. The fit report
    and tech pack refuse to quote one; tests assert `converged` first.
12. **Cloth time is derived from fps.** `frames_per_step` is not a free
    parameter; a mismatch is refused. Accuracy comes from `substeps`.
13. **Travel at the gait's own speed, or the feet skate.** Frame a shot with
    duration and lens, never with the speed.
14. **The line you changed last beats the line that looks suspicious.**
    (SLEEVE_R everted because of a restitution added that hour, not the
    rotation everyone suspected.)
15. **A constraint that learns its rest length from a wrong pose preserves
    the wrong pose.** Rest lengths come from the flat pattern.
16. **`alpha` in this solver is a relative softening, not m/N.** Four decades
    of compliance were indistinguishable from rigid; the range that bites is
    single digits to tens.
17. **A self-describing format is left alone.** glTF states +Y up in metres;
    adding our own rotation put the jacket on its face through the floor.
18. **Probe capability on the object you will assign to**, never on the
    class RNA — it reports the unfiltered enum. (Now a firewall fault.)
19. **Use it, don't just test it.** Every A60–A64 defect survived a green
    suite and was found by driving the batch path or rendering a shot.
20. **An unclothable body reads as a broken cloth solver.** Proportions are
    a garment's numbers before they are a comic's.

---

## P0 — the long tail is findable, the state is nameable (DONE in A65)

`sk_hardware`, `sk_avatar`, `sk_touch`, `sk_handoff` registered (read-scene;
`sk_handoff` write-artifacts). Entities for zippers, buttons, locks and the
body. *Acceptance, met:* the six follow-up queries land top-3; entities
appear after a batch; surface 17 / 2,033; tests in
`server/tests/test_seamkiln_adapter.py`.

## P1 — dressing in the kernel (DONE in A65)

`seamkiln/figure.py`, `seamkiln/drape/dressing.py`. `arrange` gains
`arrangement=auto|cylinder|wrap` and `dress`; the choice is recorded and
replays. *Acceptance, met:* the jacket on the figure is worn with > 15 %
contact after `arrange`; a replay fingerprints identically; the mannequin's
every measured number is untouched because it keeps the cylinder path.
`seamkiln/tests/test_figure_dressing.py`.

## P2 — walk the session's own body (DONE in A65)

`walk` articulates a `figure`, travels at the gait's speed when asked, and
moves a jointless body rigidly with a note saying so. `animate()` gained an
`advance` hook so a travelling body carries its cloth. *Acceptance, met:*
cloth travels at 1.37 m/s against the gait's 1.35; worn every frame.

## P3 — make the follow-ups reproducible and complete (DONE in A65)

1. **Examples, not scratchpads.** `seamkiln/examples/cape_shot/` and
   `seamkiln/examples/fur_walk/`: the two delivered shots as headless
   pipelines (`sim`, `render`, `sound`, `encode`, `all`) with argparse, a
   `--probe` short run, and a smoke test that runs `sim --probe` in CI (no
   Blender). Every bug those shots found is already in the kernel; the
   examples are what let the next session re-run them in minutes.
2. **Replay every verb.** Extend `test_session.py`'s replay test to a script
   that uses every follow-up verb with a fixed seed; assert one fingerprint.
3. **Render properties on the material card.** `roughness` (and a
   `texture` path) as *render* fields on `Fabric`, carried by `sk_materials`,
   `handoff` manifest and the tech pack — explicitly labelled non-physical.
4. **The GUI catches up**, or says what it covers. Add the follow-up verbs
   to the shell as buttons that build Commands (Law 3), or record in the
   guide the exact list it lacks. Prefer the former for `zip`, `button`,
   `walk`, `pull`.
5. **Benchmark row.** Add a follow-up scenario to `benchmarks/` ("dress a
   zipped jacket on a figure, walk it, hand it off") and its tokens-saved
   number to `RESULTS.md`; note the `sk_*` count is now 14, not six.

*Acceptance:* both examples run end to end from the repo; the replay test
covers every verb in `VERBS`; RESULTS has the new row; surface unchanged.

*Done (2026-09-02):* `seamkiln/examples/{cape_shot,fur_walk}` run `sim`,
`sound`, `render`, `encode` and `all` from the repo (`examples/showcase`
cuts them into one film); `test_examples.py` runs both `sim --probe` in CI
without Blender. `test_session_every_verb.py` uses all 29 verbs in one
script and replays to one fingerprint. `Fabric.roughness`/`texture` are
render fields labelled non-physical in `describe()`, the library,
`sk_materials`, the tech pack and the handoff manifest. The shell has
buttons for `zip`, `button`, `walk`, `pull` (plus the jacket block and the
figure), Qt-free and tested; the 19 verbs it still lacks are listed in
`gui/app.py` and the guide, asserted against `VERBS`. The benchmark has the
follow-up row (RESULTS.md, "dress, zip, walk, hand off"); the A53 row now
says fourteen `sk_*` tools. Surface unchanged.

## P4 — the tier-2 bake, attempted honestly (ATTEMPTED 2026-09-02, BLOCKED)

Attempt the C-IPC (`ipc-sim/Codim-IPC`, Apache-2.0) build on this Mac once,
as A53 P2 specified: run out-of-process through `tee_job`, never in the
editor loop. If the build is hostile, **record the actual error in PROGRESS**
and close the item as "attempted, blocked by <error>". If it builds, wire it
as an opt-in `drape quality="bake"` with intersection-free thickness as its
acceptance. Either outcome closes A53 Gap 2; not attempting does not.

*Outcome:* attempted once, out of process, in a scratch directory, with no
change to the machine. It does not build here. CMake 4.4.3 refuses the
project's `cmake_minimum_required(VERSION 3.2)` and its Kokkos 3.1.01 /
kokkos-kernels 3.1.01 pins (`Compatibility with CMake < 3.5 has been
removed`; the `-D` policy override does not reach DownloadProject's child
configures, exporting `CMAKE_POLICY_VERSION_MINIMUM=3.5` does);
`find_package(OPENMP)` on Apple reports `Could NOT find OpenMP`; configure
then completes with Boost 1.92, Homebrew Eigen3 and the GLUT framework, and
the build stops at the first Kokkos object because the project's
`CMakeLists.txt` hard-codes x86 flags — `-mfma -mbmi2 -mavx2` — which
`g++-16` on an Apple M5 Max rejects (`unrecognized command-line option`).
Closed as "attempted, blocked by x86-only compiler flags baked into
Codim-IPC on Apple Silicon"; `quality="bake"` is not offered. Details in
`docs/PROGRESS.md`.

## P5 — CLOSED, both halves (2026-09-04)

- **A real industry DXF** to close A53 Gap 4. **Done.** The owner supplied two
  CLO 2024 exports and purchased an Optitex AAMA block. Both read; the round
  trip is lossless against files another system wrote (20 CLO panels, worst
  area delta 0.000000 mm²). What they taught outranks the round trip: the
  reader read **zero pieces** until it learned R12 heavy polylines and that
  `UNITS: METRIC` means centimetres; a notch is a POINT on layer 4, confirmed
  by two independent vendors; and the Optitex file declares `$INSUNITS 6`
  (metres) over inches, so a **control piece outranks any declaration**. Six
  AAMA layers verified where none were. Ten remain, and rather than buy more
  files the reader now reports what an unknown layer HOLDS so the next real
  file teaches us.
- **A character model** if the shots are to move past the primitive-built
  figure. **Done, and the ask was half wrong** — the blocker was never the
  model but that `custom_avatar` threw the skeleton away, so any rigged body
  walked as a statue. `seamkiln/rig/` generates a licence-clean rigged
  humanoid from one number and articulates it: foot spread swings 0.484 m
  where rigid motion holds it at exactly 0.000. A production-quality body is
  still Anny (Apache-2.0, assets CC0); SMPL and its relatives cannot ship.

*Still genuinely owed by the owner:* a DXF from a system other than CLO or
Optitex — Gerber or Lectra — to settle the ten remaining layers, and a
studio rig (a real Maya or Character Creator export) that the mapping layer
has never met. Neither blocks the lane; both would strengthen it.

## Out of scope (unchanged from A53, minus the owner's override)

Marker making and nesting; industrial grading beyond simple rules; ML-based
drape prediction; fabric parameters from photographs; `.zprj`/`.zpac`;
multi-user editing; a render engine of TEE's own (Blender renders); matching
incumbent performance without numbers.
