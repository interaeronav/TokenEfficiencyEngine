# CLAUDE_A53_SCRIPT.md — `seamkiln`: a garment CAD + drape kernel, headless first, with a GUI on top

**Owner directive (2026-09-01, verbatim):** *"deep research a software that
has the same core features as marvelous designer and clo3d, the idea is to
create such a software that has a graphical interface as well as a headless
feature with TEE."*

Written for a fresh Opus session (max effort) with no memory of the one that
researched it. **`docs/research/67-garment-cad-lane.md` is the design of
record** — every licence and platform claim here is cited there and was
verified on 2026-09-01. Build ON these facts; do not re-litigate them.

## Orientation for a cold session

- Repo `/Users/john/TokenEfficiencyEngine`, TEE code in `server/`. Branch
  `claude/token-efficiency-engine-5jv1dj` ONLY. Read `docs/PROGRESS.md`
  first; real command output into it per phase; commit + push per item.
- Suite `uv run pytest -q -m "not dcc"` from `server/` — expect **1,194
  passed / 17 skipped**, `make lint` exit 0 (it lints `src tests
  ../benchmarks` since SI-B20 — a summary line is not a detail to skip).
- Surface invariant: **17 always-loaded tools, ~2,034 tok** (`surface:`
  line of `uv run --project server python benchmarks/run_benchmarks.py`),
  budget ±10 around 2,028. **A53 adds ZERO always-loaded tools.**
- **Upgrade trap:** every `.mcpb` install wipes the extension venv's
  extras. Restore with `uv pip install --python "<extension venv>/bin/python"
  'tee-engine[medimg]' 'tee-engine[quant]' 'tee-engine[solve]'
  'tee-engine[extract]' 'tee-engine[pdf]'`.
- New code lives in **`seamkiln/`** at repo root — self-contained package,
  own `pyproject.toml`, own tests, following the `voxkiln/` precedent so it
  can move to its own repository without surgery. The TEE-side adapter
  lives in `server/src/tee/adapters/seamkiln/`.
- Phases are independently shippable. Stopping at a phase boundary must
  leave the tree green and the feature honest about what it does not do.

## Measured facts (2026-09-01, this machine — build ON them)

1. **Apple M5 Max, 128 GB unified, macOS 26.6.2, `os.cpu_count() = 18`.**
2. **TEE's own venv already carries the garment kernel's dependency set:**
   `shapely 2.1.2`, `ezdxf 1.4.4`, `trimesh 5.0.0`, `numba 0.67.0`,
   `numpy 2.4.6`, `scipy 1.17.1`, `fpdf2 2.8.8`, `pypdf`, `pypdfium2`,
   and **`torch 2.13.0` with MPS available=True, built=True**.
   Absent: `mlx`, `PySide6`, `warp-lang`.
3. **"GPU" does not mean CUDA here.** NVIDIA Warp is Apache-2.0 and ships
   macOS Apple-Silicon wheels, but *"The macOS wheels support CPU
   execution but not Metal acceleration."* Metal is reachable via
   `torch` MPS (installed) or `mlx.core.fast.metal_kernel` (not installed).
4. **The best open garment pipeline cannot be shipped.** GarmentCode /
   PyGarment is MIT, but GarmentCodeData drapes through
   `NvidiaWarp-GarmentCode`, a fork under the **NVIDIA Source Code
   Licence — non-commercial**. Copy the paper's stack and you inherit that
   silently.
5. **C-IPC (`ipc-sim/Codim-IPC`) is Apache-2.0** — thickness, coupled
   strain limiting, accurate friction, no intersections ever. Offline
   speed: it is a *bake*, not an editor loop.
6. **Anny (`naver/anny`) is Apache-2.0** with CC0 MakeHuman/MPFB2 assets —
   differentiable PyTorch body model, infants to elders. **SMPL/SMPL-X are
   non-commercial.** Anny's optional `smplx` topology download is *also*
   non-commercial: never fetch it.
7. **Shewchuk's Triangle (and `triangle`/`meshpy` wrappers) may not be
   included in commercial products.** Use **CDT (artem-ogre, MPL-2.0)** or
   an own constrained-Delaunay implementation.
8. **ASTM D6673-10 was withdrawn in 2019** and is still the de facto
   interchange. DXF R13, one style per file, **one block per pattern
   piece**, **23 predefined layers** (table in doc 67 §4). AAMA and ASTM
   assign features to *different* layer numbers — this is a dialect table,
   never a hardcoded map. ezdxf's default layout blocks break ASTM
   importers: emit piece blocks only.
9. **Blender's cloth is already reachable headlessly from TEE**
   (`modifiers.new('CLOTH')`, synchronous `ptcache.bake`, free
   `solver_result` health report, five extractable presets — doc 32).
   **It is the zero-new-code baseline every candidate solver must beat.**
10. **The incumbent's automation is paywalled and in-app.** Marvelous
    Designer's Python API runs inside the app (Script → Python) and ships
    only on an Enterprise-tier subscription; no documented headless mode.
    Inverting that — headless as the primary surface, GUI as a client —
    is the product thesis, not a clone.

## Laws

1. **Measured before and after.** A phase without a number did not happen.
   P0's bake-off picks the default solver backend; the winner is whichever
   number wins, not whichever library is fashionable.
2. **The licence minefield is enforced by a test, not by memory** (P0c).
   A human forgets; CI does not.
3. **The GUI is a client of the headless core.** Every GUI action is a
   core command object. There is no code path the GUI can reach that a
   script cannot. `import seamkiln` must work with no Qt installed.
4. **Zero new always-loaded TEE tools.** The Adapter protocol is the whole
   point: `tee_scene_summary`, `tee_batch`, `tee_diff`, checkpoints and
   `tee_capture` drive garments with the surface unchanged. Long tail goes
   to `sk_*` virtual tools, tabled explicitly.
5. **Diffs over snapshots, text over pixels.** After a drape, report what
   moved and what it measures — not a vertex dump, not a screenshot by
   default.
6. **A refusal names its reason and the fix.** "Non-commercial licence,
   use Anny instead" — never "unsupported".
7. **Determinism is a feature.** Same fixture + same backend + same seed →
   same vertex hash. A solver that cannot reproduce itself cannot be
   benchmarked, and a fit map that changes between runs is theatre.
8. **The model's eye is advice, not measurement** (A51's finding). A VLM
   may say a drape "reads as a shirt"; it may not decide that a seam
   closed. Geometry decides that.
9. **Feature parity, not container parity.** Open interchange only. No
   `.zprj`/`.zpac` reverse engineering, no incumbent UI chrome or branding.
10. The metric is TEE's metric: **tokens per completed garment task**,
    measured in `benchmarks/`.

---

## P0 — clear the path, then let the numbers choose (do this first)

**P0a — the PDF hole in `tee_web_lookup`.** An `application/pdf` URL
currently returns **raw PDF bytes as the quote** (`%PDF-1.7 %âãÏÓ 3085 0
obj …`). `server/src/tee/web/fetch.py` has no content-type branch, while
`web/extract.py:229` already tells callers to use "the media lane for
images/PDF" — advice the code never routes to. TEE ships `pypdfium2` and
`pypdf`. Textile and apparel standards live in PDFs, so this is on A53's
path, not a detour. Route `application/pdf` through TEE's own extract
lane; if the extras are missing, refuse with the exact restore command.
*Acceptance:* the IEEE 3DBP fabric-properties PDF
(`standards.ieee.org/wp-content/uploads/import/governance/iccom/3DBP-Measurement_Fabric_Properties-Virtual_Simulation.pdf`)
returns readable prose or an honest refusal — never bytes. Regression test
with a fixture PDF, no network.

**P0b — the solver bake-off.** One fixture garment (a 4-panel tee, ~5k /
~30k / ~120k particles), one frame count, four contenders:

| Backend | Notes |
| --- | --- |
| `torch` MPS (installed) | XPBD with graph-coloured Gauss–Seidel as batched tensor ops |
| `numba` CPU (installed, 18 cores) | same constraints, parallel prange |
| `warp-lang` CPU | install it; **verify the no-Metal claim rather than quoting it** |
| Blender headless cloth | the zero-new-code baseline (doc 32) |

Record ms/frame, peak RSS, and whether the result is deterministic, for
every cell, into PROGRESS. **If Blender wins on every axis, say so and
make the Blender lane the tier-1 backend** — that is a legitimate outcome
and A51's premise-inversion precedent covers it.

**P0c — the licence gate.** `seamkiln/tests/test_licences.py`: a test that
fails if the resolved dependency graph or the import path ever contains
`triangle`, `meshpy`, `smplx`, `NvidiaWarp-GarmentCode`, or ArcSim data,
and that asserts the allow-list (`ezdxf` MIT, `shapely` BSD, `trimesh`
MIT, `anny` Apache-2.0, `CDT` MPL-2.0, `torch` BSD). Include the reason
string in the failure so the next session learns *why* from the error.
*Acceptance:* the test fails loudly when `pip install triangle` is
simulated in a fixture, and passes on the real tree.

Commit each of P0a/b/c separately.

## P1 — the pattern kernel (`seamkiln/pattern`) — no simulation at all

The half of the product with no physics risk and the highest reuse.

- **Model:** `Panel` (closed outline of line/arc/cubic segments), `Edge`
  with stable IDs, `Seam` (edge→edge, segment→segment, N:1, with gathering
  ratio), `Notch`, `Dart`, `Pleat`, `InternalLine`, `DrillHole`,
  `GrainLine`, `FoldLine`, `GradeRule`. Stable IDs are non-negotiable —
  they are what makes `tee_diff` cheap in P4.
- **Operations:** seam allowance (shapely offset with mitre control),
  mirror/unfold, true-up (seam length matching, with the mismatch reported
  in mm, not a boolean), measurement-driven parametrics, simple grading.
- **I/O:** DXF read + write in **both AAMA and ASTM dialects** via `ezdxf`
  and the 23-layer table (doc 67 §4); piece blocks only; grade-rule tables
  as the separate ASCII sidecar. SVG out. **Plotter PDF at true 1:1 via
  `fpdf2`** — reuse A48's compose lane rather than a second PDF stack.
- **Fabric table:** the KES-F vocabulary (tensile / shear / bending in
  warp, weft and bias; thickness; GSM; friction), every value carrying a
  `measured` (cited) vs `plausible` (tuned) tier flag, per doc 34's law.
  Never ship ArcSim's numbers.

*Acceptance:* a real multi-piece pattern DXF round-trips
model→DXF→model with piece count, layer usage, notch count and panel area
preserved (area within 0.1%); seam-length mismatches are reported per seam
in mm; the plotter PDF measures 1:1 when a known rectangle is extracted
back with `pypdf`; an unknown layer number refuses by name with the
dialect it was read as. Tests run with no Blender, no GPU, no network.

## P2 — the drape kernel (`seamkiln/drape`)

- **Triangulation:** constrained Delaunay honouring outline, internal
  lines, cutouts and notches, with a target edge length ("particle
  distance" — the same knob the incumbents expose). **Not Triangle.**
- **Stitching:** seams become constraints between panel boundary vertices,
  resampled to a common arc-length parameterisation; gathering is a ratio
  on that parameterisation.
- **Arrangement:** panels placed on arrangement volumes around the body
  before the solve (the incumbents' bounding-cylinder idiom), driven from
  the body measurements of P3, with a deterministic fallback layout.
- **Solve, tier 1:** XPBD/VBD on P0b's winning backend, behind a
  `SolverBackend` protocol so the loser backends stay swappable and
  testable. Constraints: stretch (warp/weft anisotropic), shear, bending,
  seam, pin, gravity, damping, body collision, self-collision.
- **Solve, tier 2 (opt-in bake):** the barrier/IPC route for guaranteed
  intersection-free thickness-accurate drape, run out-of-process as a job
  through the existing `tee_job` machinery — never blocking the editor
  loop. If C-IPC's build proves hostile on macOS, record the attempt with
  the actual error and ship tier 1 alone; do not let this phase grow.

*Acceptance:* the fixture tee drapes on a real body mesh with **zero body
interpenetration** (measured by signed distance, not by eye), every seam
closed within a stated tolerance in mm, the same seed and backend
producing the same vertex hash twice, and the whole thing holding at 3×
resolution. Report the drape as a diff + measurements; a mesh dump is
opt-in.

## P3 — the body lane (`seamkiln/body`)

Anny (Apache-2.0) as the parametric body: phenotype parameters, poses via
the skeletal rig, mesh out through `trimesh`. Cold start parses MakeHuman
assets and caches to `~/.cache/anny/` — measure it and warm the cache
behind TEE's job lane rather than blocking a call (A46's law).

Then the measuring tools, which are what makes this a *fashion* tool and
not a cloth toy: girth measurements from the body mesh (bust/waist/hip/
inseam via plane intersection + convex hull for tape-measure semantics),
garment measurements from the draped mesh, **ease** = garment − body per
landmark, and a strain/pressure fit map from the solver state.

*Acceptance:* body measurements reproduce a known reference within a
stated tolerance; ease is reported per landmark in mm; the fit map renders
as numbers first (max/mean strain per panel) and only optionally as
colour; any attempt to fetch the non-commercial `smplx` topology refuses
with law 6's message.

## P4 — the TEE adapter (`server/src/tee/adapters/seamkiln/`)

Honour the `Adapter` protocol exactly as Godot and Blender do:
`info()`, `probe()`, `list_entities()` (panels, seams, garments with
stable IDs), `execute(batch)` → Diff, `snapshot`/`restore` (checkpoint the
pattern + drape state), `capture()` (render through the Blender adapter,
or refuse honestly if no renderer is configured — never a black image).

Declarative op set for `tee_batch` (the trade-rule lesson: enumerable, not
arbitrary code): `add_panel`, `edit_panel`, `add_seam`, `set_fabric`,
`arrange`, `drape`, `measure`, `export`. Arbitrary Python stays a separate
door behind `exec-code`, named honestly.

Long tail as `sk_*` virtual tools, each an explicit trust-table entry.
Tool-search ranks: "sewing pattern", "drape a garment", "fit a shirt",
"export DXF pattern" must land top-3.

*Acceptance:* surface still **17 tools / ~2,034 tok**; `tee_scene_summary`
returns a compact garment state; `tee_batch` adds a panel and the **diff
names it**; checkpoint/rollback round-trips a pattern edit; a fake-adapter
test suite means CI needs no solver. Add a `benchmarks/` scenario —
"draft, sew and drape a tee, then report fit" — and put the tokens-saved
number in `benchmarks/RESULTS.md` with the others.

## P5 — the GUI shell (`seamkiln/gui`, extras `[gui]`)

PySide6 (LGPLv3), installed as an extra so the core never depends on it.
`QGraphicsView` for the 2D pattern editor — it is the right widget for
this and the Qt docs say so — plus a 3D viewport (Qt Quick 3D or a
`QOpenGLWidget`; pick after a spike, record which and why).

**The architecture is the feature.** Every GUI interaction constructs the
same command object the headless API takes; the GUI holds no state the
core does not. Ship **session recording**: a GUI session exports the
equivalent headless script, and replaying that script must reproduce the
garment exactly. That single property is what makes the tool AI-drivable
in a way the incumbents are not.

*Acceptance:* build a garment in the GUI, export the script, replay it
headlessly, and get an identical vertex hash. `python -c "import
seamkiln"` succeeds in an environment with no Qt. The GUI is never
required by any test.

## P6 — evidence, interop, ship

Exports: OBJ / glTF / USD via `trimesh` (UVs come free — the 2D panel *is*
the UV layout); DXF/SVG/PDF from P1; a **tech pack PDF** (pieces, fabric
table with tier flags, measurements, ease, seam list) through
`pdf_compose`. A `sense_*` fit read-out, labelled advice and never allowed
to fail a build. `docs/seamkiln-lane.md`, DECISIONS entries for every
licence call in doc 67 §2, PROGRESS throughout, version bump, bundle,
clean-unzip MCP verify.

## Out of scope (say no to these in writing)

Marker making and nesting; industrial grading beyond simple rules;
animation and pose sequences beyond a single static pose; ML-based drape
prediction; fabric parameter estimation from photographs; `.zprj`/`.zpac`;
cloud collaboration or multi-user editing; a render engine of TEE's own
(Blender is the renderer); and any attempt to match incumbent performance
before P0b's numbers exist.
