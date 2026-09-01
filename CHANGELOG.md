# Changelog

The `tee-engine` server versions here; the UE `TeeToolset` plugin and the
Blender `tee_bridge` extension carry their own versions where noted.

## 0.18.0 — 2026-08-31

**A smart quote no longer destroys a report, and a camera checks its own work.**

### PDFs can write ordinary prose

The core PDF fonts are Latin-1, so curly quotes and em dashes did not
degrade — they **raised**. One `“` killed a whole compose, and they appear
in almost any text a model writes or a person pastes.

Now: pass `font` (a TTF path or a system font name like
`"Arial Unicode.ttf"`) for full Unicode — Greek, CJK, symbols, all
round-tripping. Without one, the handful of typographic characters Latin-1
lacks are **transliterated with the answer saying so** — a curly quote
becomes a straight one, meaning preserved, never silent. Characters Latin-1
*can* encode (`façade`, `m²`, `45°`) are left alone.

### And the attributes a real document has

`author` / `subject` / `keywords` metadata, `page_numbers`, headings as
**PDF bookmarks**, per-block `color`, and shaded table headers.

### `sense_frame` — the model grades the shot, TEE re-aims

The camera fit now sets the lens and solves the distance from the field of
view and aspect, so `distance: 1.0` means *framed* (it used to multiply a
raw bounding radius by a guess). `sense_frame` then renders, has the local
vision model grade the framing, moves and retries — converging live from a
deliberately bad start (10% fill) to a graded-good shot in three attempts.

It returns **every attempt with its grade**, says plainly when it did not
converge, and labels the verdict *advice rather than measurement*. Prose
instead of the requested form is marked unusable rather than passed,
because a loop that cannot tell those apart converges on noise.

### Faster launches

Launch waits polled on a fixed 0.5 s tick while the Blender bridge is ready
at 0.422 s. Now a backoff tuned to the measured probe cost: **0.506 s →
0.428 s**, and the benchmark's bridge-up stage drops 0.5s → 0.4s.

## 0.17.0 — 2026-08-31

**Godot, headlessly, as a first-class adapter.**

```bash
tee serve --adapter godot --project ~/GodotProjects/my-game
```

Because it honours the `Adapter` protocol, Godot arrives with **no new
always-loaded tools** — `tee_scene_summary`, `tee_batch`, `tee_diff` and
the checkpoint machinery already drive it. Surface unchanged at 17.

### Building and running

Declarative ops (`add_node`, `set_props`, `remove_node`, `save_scene`,
`load_scene`) refuse unknown types and ops **with the allowed list**.
Arbitrary GDScript is a separate door behind `exec-code`.

`run_scene` runs your game's real logic headless — `_ready` fires,
`_process` advances — and returns the game's own printed output:

```json
{"ok": true, "frames": 120, "script_errors": 0,
 "output": ["TEE_SAMPLE ready: spawning props", "TEE_SAMPLE spawned=3"]}
```

**Script errors are counted, not inferred from the exit code**: measured, a
game whose `_ready` raises still exits 0, so a lane trusting the exit code
would call a broken game a pass.

### Rendering is refused, honestly

Headless Godot **cannot render** — measured across `--rendering-driver`
vulkan, opengl3 and dummy, the viewport texture yields no image.
`tee_capture` says exactly that instead of returning a black frame that
looks like an answer. Text is the evidence channel.

An opt-in `capture_windowed()` renders with a real display server, which
**opens a window on your screen** — your trade to make, never automatic.

### First launch

A Godot project that has never been imported hangs `--headless -s` with no
output at all. The adapter runs `--import` for you, as a duty rather than a
footnote.

## 0.16.0 — 2026-08-31

**TEE can write and edit PDFs.**

`uv pip install 'tee-engine[pdf]'`

### `pdf_compose`

Build a document from blocks — headings, paragraphs, tables, images, page
breaks. **HEIC embeds with no conversion**, straight off the phone. Returns
a summary (`path`, `pages`, `bytes`), never the document: a PDF in a
model's context is a token catastrophe that answers no question.

### `pdf_edit`

`merge`, `split`, `reorder`, `rotate`, `delete_pages`, `extract_pages`, and
`stamp` for watermarks and image overlays. Every operation **reads A and
writes B** — the input is never modified, `out` is always required, and an
existing file refuses unless you pass `overwrite: true`.

### What it refuses, and why

**Rewriting the text inside an existing PDF is declined by name.** A PDF
stores positioned glyph runs, not paragraphs — line breaks and kerning were
baked in by a layout engine that is no longer present. Re-flowing them
produces a document that opens perfectly and is subtly wrong. The refusal
gives the reason and the two honest alternatives: `stamp` to add a mark, or
`pdf_compose` to build a corrected document.

### Verified by TEE's own eye

A stamped watermark is drawn, not text — pdfplumber cannot extract it. So
the test renders the page and asks `sense_describe`, which answers: *"Yes,
there is a large diagonal watermark word across this page. The word is
'DRAFT'."* The senses lane checking the PDF lane.

### Also

Tool search dropped one- and two-letter query words. Matching is by
substring, so the "a" in *"add a watermark to a document"* scored against
every tool whose name merely contains an 'a' — outranking the tool that
actually stamps watermarks.

## 0.15.0 — 2026-08-31

**Aim the borrowed eye, and stop guessing what it costs.**

### `sense_viewport` and `sense_camera`

Unreal has had `ue_look` since 3.7 — viewport to local model to text.
Blender never got one, so a model that cannot read images could mutate a
scene and never see the result. Both now exist for either DCC, and
`sense_camera` goes further: **aim** at a named object from an angle you
choose. The temporary camera is removed and the scene left exactly as
found (verified live: identical object and camera lists before and after).

The capture goes to the local model and never enters your context, so the
byte budget is generous — bigger image, better answer, **zero image tokens
for the host**.

### The eviction warning now works

It was driven by a stopwatch: *if the vision call takes over 6 s, assume it
evicted the host's model.* Measured properly, the inference was backwards —

```
text 10.75s | vision 3.03s | vision 0.85s | text 10.34s | text 0.79s
```

The cost is paid by the **next text turn**, not the vision call, which
never crossed the threshold. The warning had never fired once. It is now
driven by the configured fact (`evicts` on the provider row) and stays
silent on machines whose eye coexists with the host.

### Portable for other users

A `[senses]` config section carries any machine's endpoint, model,
footprint and eviction facts. This machine's measured values are a
fallback example, not baked into the code.

### Benchmarked

New RESULTS section: one question about a 4K site frame costs a seeing host
**756 tokens** (budgeted) or **10,764** (full frame); a blind host using
`sense_describe` pays **65** — 11.6x and 165.6x. This supersedes an
informal "33x" quoted earlier, which measured the provider's side rather
than what a host pays.

### A small vision model was auditioned and rejected

Qwen2-VL-2B (1.4 GB, would coexist with the 86 GB host and remove the ~10 s
eviction) read an unguessable test card perfectly — then **inverted a
judgment**, reporting that a wall *matches* a plastered spec the 30B
correctly reports it violates. The 17 GB model stays.

## 0.14.0 — 2026-08-31

**Senses a model can borrow when it has none of its own.**

The owner ran DeepSeek locally as the HOST model, in opencode, and asked
TEE about an image. TEE answered that machine vision was not a feature it
offered. That was **true**: decision A9 makes the default extraction
channel in-band — `ex_prepare` hands the host file paths because *"it reads
media with its own tools"* — which assumed the host was Claude, and
`tee_media`/`tee_capture` return pixels a blind host cannot read.

### New: `sense_describe` and `sense_transcribe`

Ask one question about one image and get **text** back, or turn speech into
text. Both run on this machine — free, nothing leaves it.

```
search "describe what is in an image"  ->  sense_describe RANKS FIRST
   (before: med_instance_tags, whose summary reads
    "Pixel data is never returned" — truthful, and useless)
```

`context` is honoured, so the answer addresses what you already know rather
than merely captioning: given *"the drawings say gable G3 is solid plastered
brick"*, it reports the **delta** against that spec. HEIC works with no
conversion. Repeats are served from an exact-content cache. Every answer
names the provider that actually looked, and says plainly: *a description,
not the image — the model reading this never saw the pixels.*

### The machine now declares what it can perceive

`tee doctor` states both senses with measured costs, and the cost nobody
could see before: on a 128 GB machine an 84 GB session model and the 17 GB
vision model cannot coexist, so an image **evicts** the host's model and
its next turn pays ~10 s. Ask image questions together to pay it once.

### `tee_status` says where it is rooted

`serve --project` defaults to the launching client's cwd, so a terminal host
that omits it boots away from its grants and loses tiers without being told.
Status and doctor now name the root, the grants file, and the exact fix.
**They report; they never grant.**

Corrected before release: the first version of that report hardcoded a tier
list and named `mutate-scene` denied. `mutate-scene` gates **zero** tools;
scene edits are governed by `write-scene`, granted all along. The list is
now derived from capabilities that gate real tools.

## 0.13.0 — 2026-08-31

**TEE notices when an upgrade deletes its own extras.**

Installing a bundle rebuilds the extension venv from its lock and drops
anything added on top — and the fleet extras live on top by design, since
A46 P1 keeps them out to hold the base venv at 586 MB. Three upgrades in a
row wiped them (0.10.0, 0.11.0, 0.12.0), each taking the venv from ~1.1 GB
to 34 MB.

The defect was never the deletion; it was the message afterwards.
`probe.need()` said *"uv pip install 'tee-engine[medimg]'"* — which reads as
**you never set this up**, to someone who did. Two rounds of documentation
did not help, because the reader was being sent to the wrong problem.

TEE now records which groups are installed and, when one goes missing, says
so and dates it:

```
[medimg] was installed here on 2026-08-30 and is missing now. Installing a
new TEE bundle rebuilds the venv from its lock and drops anything added on
top - this is that, not a setup you never did.
```

`tee doctor` reports the same, with the restore command for exactly the
groups that vanished. `cad` is exempt — it lives in a sidecar by design, so
its absence is correct. TEE installs nothing itself; restoring stays the
owner's command.

## 0.12.0 — 2026-08-31

**ODM runs now report what they achieved, not just where they wrote.**

ODM was already integrated — container run, `--dsm --dtm`, artifact
collection, rolling-shutter correction from the resolver. What it did not
do was tell you whether the reconstruction worked. `capture_reconstruct`
returned `{artifacts, seconds, provenance}`, so **137-of-147 images and
12-of-147 were indistinguishable**: both write files and both succeed.

Every figure needed was already in ODM's own `odm_report/stats.json`. TEE
now reads it and returns `images_used` / `images_total` / fraction,
`points`, and `reprojection_error_px`, plus two judgements that came out of
running it for real on the Okongo footage:

- **`georeferenced` and `frame`.** With no GPS the geometry is sound and
  every distance is meaningless — yet ODM still reports an "area covered"
  in its arbitrary frame. The payload now says so in the same breath.
- **`orthophoto_coverage` and its warning.** 29% coverage is not a broken
  renderer; it is a pan being asked to be a map. Orthophoto and DSM
  generation assume nadir coverage flown as a grid.

A run below 75% of images reconstructed carries a warning naming the
capture rather than the engine, because that was the real case: the engine
was fine and the frames were 6 seconds apart.

Also: an empty output file is no longer reported as an artifact.

## 0.11.0 — 2026-08-31

**Two owner-requested fixes.**

### HEIC reads and writes (SI-B21)

TEE could not open the format the owner's iPhone shoots. `PIL.Image.open`
was called bare in **nine places across seven modules** and Pillow ships no
HEIF plugin, so every one raised `UnidentifiedImageError` — while the
capture protocol says photos arrive "HEIC/DNG/JPG as shot".

`tee/kernel/imaging.py` is now the single door for opening and saving image
files, registering the plugin once before the first open. A test walks the
AST of the whole source tree and fails on any new bare `Image.open(<path>)`
— reaching nine call sites unnoticed is what made this invisible.

Licence recorded in DECISIONS.md: pillow-heif's *wheels* are GPLv2 via
bundled codecs. TEE is not distributed and this is an optional extra the
owner installs, so nothing GPL ships in the `.mcpb`.

### Estimated dimensions, under a named mitigation (SI-B22)

New tool `ex_estimate`: a length in millimetres from a photograph, using
something of known size in the same plane. It extends the A40 law rather
than relaxing it —

- **no reference, no estimate** (the refusal is the feature);
- the band propagates reference tolerance and pixel-picking error in
  quadrature, and an *unstated* tolerance assumes 2%, so vagueness widens
  the band rather than hiding in it;
- the value lands in `estimated_mm` with `measured: false`, so nothing
  reading for a measurement can find it;
- `coplanar` must be affirmed — a scale off the near wall does not measure
  the far wall, and no arithmetic here can notice.

**TEE never supplies the reference's own size.** A hallucinated "standard
door height" becomes a structural dimension downstream. The only built-in
sizes are ISO 216 paper, which is exact by standard.

### Also

`hb_status`'s 32 mm system-holes warning was requested and found **already
shipping** — recorded closed rather than built twice.

## 0.10.0 — 2026-08-31

**A46: leaner, faster, and fitted to this machine.**

### The local engines are reachable (P3a, P3b)

`.tee/config.toml` declared only the PAID `qmax`, and the persisted active
profile *was* `qmax` — so every chore either billed or fell back to the
deterministic path, and the free models on this machine could not be
reached at all. The shim's real routes are now declared and registered,
with the active profile on the free one.

- Both local engines are **reasoning models**, and the chores were asking
  for 160–220 output tokens. Below 256 the reasoning pass consumes the
  whole budget: `q27b` returns `content: ""` with the text stranded in
  `reasoning_content`, and `dsflash` returns its own scratchpad. Neither
  reads as an exhausted budget; both read as a model that answered badly.
  `MIN_CHORE_TOKENS = 256` is enforced in `_run` so no call site can
  undercut it.
- The routing ladder is **derived from the measured cost table** instead of
  hand-written. The old one led with a 14B this machine does not serve and
  never reached the engine that answers in 4.41 s.
- The paid engine stays structurally unreachable: `qmax` has no `ENGINES`
  row, so no ordering or policy can promote it.
- Fixed: a rung whose profile a machine had not declared was recorded as a
  *verification failure*, inflating the escalation rate with hardware that
  was never asked anything.

### Lighter (P1)

Extension venv **2,246 MB → 586 MB (−74%)**, no capability lost. MONAI/torch
replaced by direct reader dispatch; CadQuery moved to a sidecar. Guarded by
a test that fails if a heavyweight re-enters the interpreter.

### Honest state (P2a)

`tee_status` reported the pre-A43 `allow_code_exec` flag while `tee_trust`
reported the capability, so one payload answered the same question both
ways. It now reports what the kernel would enforce.

### Measured and deliberately not changed

- **P2c — tool search.** 0.098 ms median at 133 tools, 0.272 ms at 400.
  Not slow, so not touched.
- **P1c — the bundle strip.** Would save ~262 KB of an 868 KB bundle and
  make `uv pip install 'tee-engine[solve]'` unsatisfiable. Not taken.

### Pipeline lane

`cosm-inspired-chair` adopted (P3c), after writing and verifying the render
and export steps it had never had. TEE refused the first declaration for a
free-string output path; both are enums now.

## 0.9.0 — 2026-08-31

The A45 campaign: **permissions that help instead of block**, a **money
meter**, and the **headless fleet** (suite 885 → 1,015; always-loaded
surface unchanged at 17 tools / 2,028 tok — every new capability is
virtual).

- **Permissions (P0)**: grants reload on config change, so an edit takes
  effect on the next call rather than the next restart. `[trust] profile`
  presets (`readonly` / `build` / `workstation` / `workstation+paid`) grant
  a coherent set in one line. Refusals name the loaded file, the exact
  line, and the smallest covering profile. A config that stops parsing
  fails closed rather than retaining the previous grants.
- **Money meter (P1, `kernel/spend.py`)**: closes SI-B16 and SI-B18. Exact
  tokens sent/returned, reasoning tokens the provider billed but never
  showed, bytes on the wire and the endpoint host — plus a cost estimate
  ONLY from a rate declared beside the profile. TEE ships no price table:
  a stale rate is worse than none. `report_spend`, and a `spend` line in
  `report_savings`.
- **The fleet (P2)**: `solve_` (HiGHS / SCIP / Cbc / OR-Tools CP-SAT),
  `quant_` (PyPortfolioOpt / skfolio), `med_` (Orthanc over HTTP + MONAI),
  `cad_` (OpenSCAD subprocess + CadQuery), `bi_` (Cube), `trade_`
  (backtesting). All optional extras with lazy imports and honest refusals;
  see `docs/setup-fleet.md`.
- **Trading safety**: `place-order` is reserved and **ungrantable**; no
  `trade_` family prefix, so an order-shaped tool name is a startup error;
  a registry-wide name sweep and a source assertion that the module holds
  no HTTP client or credential. TEE places no orders and reads no live
  broker account.
- **Two holes closed in the same campaign that opened them**: the
  `('trade_', 'read-compute')` prefix, and `place-order` being grantable
  through a hot-reloaded config.
- **Fixed**: SI-B10 reopened and re-closed — pinning the paid engine had
  silently disabled the kb-rerank judge, and the weak-band fallback then
  asserted an unjudged hint. The fallback now drops.

## 0.8.0 — 2026-08-30

The A43 build: the **trust kernel** first, then the **pipeline lane** as
its first tenant (suite 788 → 885/9; always-loaded surface unchanged —
every new capability ships virtual).

- **Trust kernel (`tee/kernel/trust.py`, `trustctx.py`)**: one decision
  point replacing four scattered permission flags. Capabilities are
  verb+RESOURCE (`write-artifacts` ≠ `write-config` ≠ `write-policy`), so
  a path cannot silently become privilege escalation. Default deny
  outside the read tier; the read tier fails OPEN because it cannot
  change a byte, side effects fail CLOSED. Every shipped tool carries a
  capability — an untabled tool is a startup failure, not a runtime
  surprise. Overhead measured at 0.2 µs per check.
- **Taint tracking**: a task whose inputs include untrusted content may
  never invoke a side-effecting capability, and only a live human turn
  lifts it. Taint is a property of an ID rather than a string, which is
  affordable precisely because TEE passes ids and not payloads; it
  crosses the job hop with the caller DOWNGRADED (live-turn → job), and
  it survives the persistence boundary bound to a content hash, so a
  remembered value cannot launder its own origin.
- **`tee_trust`**: what is granted, what the baseline covers, what this
  task carries, recent shadow denials and recent side effects — plus the
  rollout evidence, measured rather than asserted.
- **Pipeline lane (`tee/pipeline/`)**: projects declare build and query
  steps in their own tracked `.tee/pipeline.toml`. argv arrays only
  (never a shell string, `shell=False` by construction, asserted against
  the AST); typed params that must be bounded by `enum` or `pattern`, or
  the step is refused as "an arbitrary-execution grant wearing a
  declaration's clothes"; declared `env` under the same law; hash-pinned
  approval per machine, with a changed declaration refusing until it is
  read again.
- **Answers, not logs**: a produce step reports an artifact diff over
  what it declared it would write; a query step returns its own output in
  the declared format held to the declared budget, and a successful
  answer is recorded so the same unchanged question is answered for free.
  A failure is one line naming the step plus a bounded tail.
- **A DAG nobody writes**: if one step reads what another writes, the
  edge exists. Runs hash declared inputs against a manifest and execute
  only what is stale, naming every skip; staleness propagates to
  dependents; only SUCCESSFUL runs are recorded, so a retry retries and a
  failing check is never cached into looking fixed.
- **Steps are ordinary jobs**: admitted, dispatched, ledger-registered
  and metered beside chores and reconstructions, with the meter gaining a
  row rather than a lane. With the scheduler off they run sequentially
  and produce byte-identical artifacts.
- **Three authoring routes**: `pipeline_init` drafts from the project's
  own scripts with every block COMMENTED OUT (a scan is a guess about
  intent, not permission to run anything); hand-write; or
  `pipeline_adhoc` → `pipeline_adopt`, the discovery route, which opens
  for a live human turn only and needs both an opt-in and a separate
  grant.
- **Two real customers**: `~/DiversionPlanner-BaseMap` declares five
  steps from its own runbook, and `~/OkongoSim` runs three — including
  one headless inside Blender — with nothing in `server/` changing.
  Measured at −74.5% on a produce step, and honestly +8–40 tokens on
  short-output queries. Closes SI-B15.
- **Fixed**: a readiness probe that returned true when any endpoint
  answered, so a proxy serving other model groups passed for a local
  stack and then failed every chore with a 400; taint enforcement that
  reused HIGH_RISK and therefore left execution and egress in the shadow
  band; and a param that broke its declared constraint being accepted
  whenever the step happened to be fresh.

## 0.7.0 — 2026-08-29

The A42 grand campaign through Gate A: the reality-capture lane, the
verifier-gated router, and the kernel scheduler's shadow-to-law arc
(suite 716 → 788+/2; always-loaded LAW 2,028 tok / 17 tools unchanged —
every new capability ships virtual).

- **Reality capture (`tee/capture/`)**: `capture_ingest` (extract-store
  sets + the DJI-spectrum resolver — correction mode by shutter type,
  honesty band from the files' own RTK evidence, priors, per-camera
  splits), `capture_reconstruct` (PhotogrammetrySession ladder
  preview→raw; ODM-in-Docker with `--dsm --dtm` and per-verdict
  rolling-shutter correction; disk/engine/count gates), `capture_terrain`
  (contours/hillshade/dem_diff headless), `capture_register` (ICP with a
  refusing RMS gate; 7-DOF scale REPORTED and degenerate collapses
  REFUSED; the aligned cloud feeds C2M), `capture_deviate` (budgeted
  per-region facts, severities, element names, the decision menu — never
  auto-applied), `capture_apply` (owner-decision only; three lanes with
  per-adapter units — UE cm, FreeCAD mm — checkpointed with read-back;
  the fabrication leg regenerates its TechDraw sheet). The capture
  protocol doc ships with the dry run's lessons folded in.
- **The router (A39 heart)**: verifier-gated cascade — resident engine
  first, deterministic verdicts, ledger-gated swaps, a budgeted
  pointer-only client brief; the owner's TEE/Q pin suspends roaming
  (TEE/AUTO lifts). Swap costs measured, not assumed: 1.1 s to the
  14B+a2, 18.0 s to the 27B bf16 — an order under the spec guesses.
- **ONE machine ledger + merged meter**: engine registry in the K-layer
  schema; jobs register as residents (swaps refused with the honest
  line while they run); `report_savings` carries per-engine
  calls/verified, escalation rate, swap and queue columns together.
- **The kernel scheduler (K0–K3)**: task descriptors + a shadow recorder
  tracing every dispatch at ~27 µs (off-switch honors degrade-to-
  static); QoS as law — interactive never behind batch, aging, admission
  control, worker reservation, backpressure — FIFO restored exactly by
  one switch; greedy dispatch exists behind `[scheduler] dispatch` plus
  a replay gate over the campaign's own traces.
- **Chores r4**: `phrase_deviation` under the numbers-verbatim verifier.
- **Docs**: setup-reality-capture.md; the router section of
  setup-local-llm.md with the measured swap costs and 0.30 ms route
  wall.
- **The adoption rows, all won**: R4 four-arm — the routed cascade is
  the only arm matching the reference tier's 24/24 verified quality,
  at 91.5% fewer client tokens (1,667 vs 19,603); K2's replay gate
  passed on real traces and greedy dispatch is LIVE by default; K4
  mixed-load — interactive p95 11.65 → 7.18 s (−38%) at a stated
  +1.4 s makespan premium. The dry run delivered a real deviation
  report from the owner's site video (rigid-ICP RMS 3.6 cm onto the
  design export) and its finding list is protocol §B now.

## 0.5.1 — 2026-08-29

The A38 shrink round two: the 0.5.0 surface dieted with every bar held
(suite 716/2; always-loaded LAW 2,028 tok / 17 tools unchanged).

- **Web fetch cache is bounded on disk**: swept at fetcher start —
  entries older than `[web] cache_max_age_days` (default 14) deleted,
  then oldest-first down to `[web] cache_max_mb` (default 50). A cache
  delete is always safe (refetch/revalidate).
- **`tee doctor` gains a `state` check**: `.tee/` size by store, the
  cache caps in effect, kb-staging drafts awaiting review, orphan
  FreeCAD checkpoint dirs in TMPDIR; warns only past 1 GB, fix named.
- **Chore prompts dieted (template revision r2 → r3)**: 948 → 807 tok
  at equal trap scores (q14b 6/6 with tee-triage-a2; q27b bare 6/6);
  lint chore pinned to one actionable sentence.
- **Token shaves, battery-gated**: gateway describe loses its
  in-payload budget echo (the injected max_tokens schema property
  carries default/cap) — gateway row 1,629 → 1,614 at 95.4%; settle
  reports carry the same determinism claims in 19 tok instead of 33
  (222 → 202 on the fixture); eight fattest virtual-tool descriptions
  tightened (flat catalog 11,396 → 11,274; reach-one 570 → 545);
  kb_search's stale "401 files" dropped from the text.
- **setup-gateway.md** now states the measured bill: ~0.7 s connect
  once per backend, 570-token reach, +0.005 ms per call over a direct
  backend call.
- **Benchmark battery**: per-stage wall-time lines; the web scenario
  reuses the product's own fetch cache across runs (byte-identical
  rows, 6.5 → 0.5 s); a 5 s live-dispatch probe turns the blocked-GUI
  FreeCAD hang into a clean skip naming the modal-dialog fix
  (SI-B12). Warm battery 14.6 → ~7 s.

## 0.5.0 — 2026-08-29

The A37 merged-campaign release (owner-approved bump): the roadmap
(gateway, meter, handoff, kit, kb_propose) times the fabrication lane
(FreeCAD, Home Builder joinery, joinery_check, boards) — eleven
features, zero always-loaded surface growth (17 tools / 2,028 tok,
held by test).

- **TEE Gateway**: front ANY MCP stdio server through the existing
  meta-tools — prefixed virtual tools, untrusted-content caps, budgeted
  results, declared-only caching, crash respawn, and a fingerprint
  drift firewall (`gw_status` / `gw_accept`; `[gateway]` config;
  docs/setup-gateway.md). Live row: 35,238 → 1,629 tok (95.4%) on the
  filesystem reference server.
- **FreeCAD fabrication lane**: a full adapter (`tee serve --adapter
  freecad`) over the neka-nat bridge — solved-sketch/pad/pocket batches
  compiled to one script per batch, saveCopy checkpoints, budgeted
  capture, `fc_drawing` (TechDraw sheets with document-read dimension
  values; svg/pdf/dxf) and `fc_export` (STEP/GLB). Row: 10,654 → 805
  tok per completed drawing-set (92.4%). docs/setup-freecad.md.
- **Home Builder joinery lane** (`hb_*` on the Blender adapter): rooms,
  parametric cabinets, cut lists read from the model's geometry-node
  inputs, HB's own dimensioned plan/elevation layouts rendered to
  files — plus the Blender-5.2 compat shim for HB 5.1.0's removed
  modifier-input idiom (SI-B11).
- **joinery_check**: 7 source-cited rules (32 mm system, hinge boring/
  collisions, hardware-first carcass/runner fit, role-aware part
  envelopes, hanging depth), each re-verified at its cited source per
  A30 with the verification state on every finding; missing model data
  answers `not_evaluated`. `hb_joinery_spec` collects specs from live
  scenes.
- **kb_propose**: gated KB authoring into `.tee/kb-staging/` only
  (A31 preserved by construction; owner review workflow in
  docs/setup-kb.md).
- **Savings meter + handoff**: a real request/response ledger,
  `report_savings` with labelled naive estimates priced by the measured
  benchmark ratios, a compact recap block, and a ≤500-token portable
  `handoff` brief.
- **Chore-engine switch profiles**: `llm_switch` (the TEE/Q14B ↔
  TEE/Q27B chat phrases), q14b default everywhere, persisted choice,
  opt-in managed lifecycle with verified single occupancy and job-token
  cold loads (docs/setup-local-llm.md §Switch profiles).
- **board_compose**: styled SVG technical boards from live artifacts
  (renders, sheets, tables, fact lines); deck polish stays host-side by
  design.
- **kb_search honesty + the kb_hint floor**: weak top matches carry a
  note (no-strong / single-word); the web answer's KB hint suppresses
  on no-strong and routes single-word matches through the kb-rerank
  chore (SI-B10 closed — threshold picked from measured score
  distributions).
- Kernel: `AdapterContract` ships in the wheel as the adapter kit's
  runnable acceptance (docs/adapter-kit.md); `ToolRegistry.unregister`
  for runtime re-pins. Always-loaded surface unchanged: 17 tools /
  2,028 tok.

## 0.4.0 — 2026-08-29

The A35 shrink-campaign release (owner-approved bump): smaller, faster,
more efficient — no tool-surface changes.

- **Installed Desktop bundle shrinks 98 → ~32 MB.** Claude Desktop
  provisions the bundle venv with a plain `uv sync`, which included the
  dev group (ruff/pytest/fpdf2, ~58 MB the server never runs); the
  bundle's copy of `pyproject.toml` now ships `[tool.uv]
  default-groups = []`. Measured after: 29 MB venv / 29 packages, same
  17 tools, same 0.32 s first answer.
- **Dependency diet: `mcp[cli]` → bare `mcp`.** The extra only added
  typer + python-dotenv (dragging rich/pygments/shellingham) for the
  SDK's own CLI, which TEE never invokes.
- **`ex_ingest` no longer dies on a missing optional lane dependency.**
  One absent package (e.g. `imagehash` in the no-extras bundle) used to
  kill the whole job with a raw `ModuleNotFoundError`; now that file is
  skipped with a one-line fix naming the package and the extra, other
  files still ingest, and a missing `tee.*` module still fails loud.
- mcpb manifest tool list caught up to the 17-tool surface
  (`tee_web_lookup` was missing) and a lint canary now pins the
  manifest to the served surface.
- **Serve no longer imports torch at startup.** Asset generation drivers
  build on first use instead of at registration; with the ML extras
  installed the dev server idled at 242 MB and started in 0.65 s —
  now 74 MB / 0.28 s, identical surface (measured, A35 P2).
- **tee_web_lookup no longer sleeps ~2 s on the first lookup of a
  host.** The robots.txt request obeys the per-host interval but does
  not arm it; content fetches keep their ≥2 s spacing and Crawl-delay
  still wins. Loopback first-fetch 2,025 → 5 ms.
- **Web quotes stop repeating themselves.** Budget-cut extracts skip
  verbatim-duplicate blocks (boilerplate, repeated promos), spending the
  budget on distinct content; live documentation battery row improved
  2,382 -> 2,367 tok with identical citations.
- **voxkiln: 72x faster UV unwrap and a byte-reproducible artifact**
  (chart optimization skipped - full lever matrix in
  voxkiln/BENCHMARKS.md; the bake's reference sampling is now seeded,
  fixing pre-existing run-to-run texture jitter). Export 1,037 -> 151 s
  on the frozen T fixture; two independent generations now produce
  byte-identical GLBs.
- **UE: scripted batches stop double-checkpointing** (the script-scope
  checkpoint owns atomicity; the inner one was two redundant
  game-thread dispatches per batch) **and snapshots run as ONE editor
  script reading transforms only for TEE-moved actors** (labels were
  never restored). Live editor: tee_script single-create 13.7 → 4.7 s,
  checkpoint with 5 created actors 4.3 → 2.7 s.

## 0.3.1 — 2026-08-28

- Packaging only: the released 0.3.0 `.mcpb` embedded a 0.2.0 manifest —
  the RC bumped the build OUTPUT while `make dist` regenerates it from
  `packaging/mcpb_manifest.json`. Source manifest is now the single
  bumped truth and the artifact is verified by extraction before release.

## 0.3.0 — 2026-08-28

The A34 campaign release: the web lane and the local code-model chore
layer (owner-approved bump after the rung-1 outcome settled the chore
surface).

- **New always-loaded tool `tee_web_lookup`** {url, question, max_tokens,
  media=auto|off|confirm}: budgeted cited extracts from one URL —
  SSRF-guarded (resolve-then-pin), robots/Crawl-delay honoring, TTL'd
  ETag cache, sanitizing extractor; media arms caption page images and
  transcribe direct audio/video via local models with structured
  degrades. Surface 17 tools, 2,028 tok compact canonical wire.
- **Local code-model chore layer** ([llm] config, `kernel/local_llm.py`,
  `tee/llm/chores.py`): script-repair drafts on tee_script refusals,
  `llm_explain`, and extractive-by-verification web-quote refinement —
  each schema-gated, provenance-stamped, degrading to deterministic
  paths with nothing running. Traceback triage (`llm_triage`) ships
  gated by the **tee-triage-a2 LoRA adapter** (rung 1): blocked on the
  bare base by the trap suite, adopted when the adapter passed the full
  suite plus latency/quality/held-out gates; `[llm] adapters` /
  `TEE_LOCAL_LLM_ADAPTERS` serve it (see docs/setup-local-llm.md).
- **BREAKING (SI-3.2)**: the primary list field of tool responses is
  now uniformly `items` — previously `tools` (tee_search_tools,
  ue_search_tools), `hits` (kb_search, ex_search), `materials`
  (as_materials), `entities` (tee_scene_summary, uefn scene reads).
  Detail fields, counts, and third-party document keys (glTF, Epic
  toolsets) are unchanged.
- **Measure change (SI-B4)**: the canonical wire surface measure now
  uses compact JSON separators, matching true stdio bytes (~4.5% lower
  than the old spaced measure; historical rows keep their values, noted
  in benchmarks/RESULTS.md).
- `tee doctor`: new `web` and `local models` rows.

## 0.2.0 — 2026-08-28

The A33 self-improvement campaign release (owner-approved bump;
surface-visible changes throughout).

- Always-loaded tool schemas slimmed on the wire (pydantic titles,
  anyOf-null wrappers, null defaults stripped): 16 tools cost
  2,465 → 1,935 tokens by the canonical measure. (SI-1)
- `adapter=` may be omitted on every kernel tool: it resolves to the
  sole configured adapter (every real deployment); multi-adapter
  servers answer `adapter_required` naming the choices. The wire
  default `"fake"` — which failed on every real deployment — is gone.
- Batch reports carry news, not echoes: request-matching detail fields
  (float-tolerant) and unchanged pre-batch state are dropped; measured
  state, adapter renames and computed side effects stay; created ids
  get a compact `names` map. 30-create report: 663 → 205 tokens.
- `tee_status(recap=true)` no longer duplicates checkpoints/stamps
  inside its own response (208 → 139 tokens on the fixture).
- `tee_search_tools`: one-line summaries are sentence-capped and weak
  or empty results carry a `note` instead of silent noise; responses
  are UTF-8 (no `\uXXXX` escape tax on corpus content).
- `kb_status` stays registered when no corpus resolves and answers
  `kb_inactive` with the exact `[kb] root` config line — the module
  never silently vanishes.
- `as_materials` with an unknown category fails loud naming the known
  categories; an unreadable asset manifest now fails SAFE to
  attribution-required; a broken (vs absent) diarization lane leaves a
  visible `diarization_unavailable` marker fact.
- `tee doctor`: the unreal check explains the ~2–3 minute MCP settle of
  a just-launched editor and names the CrashReportClient port squatter.
- voxkiln: `mesh_stats` counts components/boundary loops by graph
  labeling instead of building submeshes/paths (275.8 s → 13.7 s on the
  491,888-tri reference mesh; boundary-loop definition documented in
  BENCHMARKS.md).
- Benchmarks: `run_benchmarks.py` preserves the recorded section of any
  scenario that skips (stamped) instead of erasing it; stale hardcoded
  fix-loop percentages removed from generated prose.
- Docs: quickstart cold-start-tested word-for-word (stale wheel
  filename, surface cost, and tool counts fixed); README benchmark
  numbers re-measured (scenes total 87.7% → 90.3% saved); explicit
  no-telemetry statement in security.md; MIT LICENSE file added to the
  server package.

## 0.1.1 — 2026-08-27

- `.mcpb` launch anchored (`uv run --directory ${__dirname} --no-dev`),
  required `project_root` user_config, icon, tools listing; empty
  `serverInfo.version` fixed; dev group no longer installed for end
  users; state no longer written into the wipeable extension dir.

## 0.1.0 — 2026-08-22

- First packaged release: 16-tool kernel, Blender + Unreal adapters,
  extraction, assets, design, physical, UEFN modules, benchmarks, docs;
  wheel + sdist + Blender extension zip + UE TeeToolset zip + `.mcpb`.
