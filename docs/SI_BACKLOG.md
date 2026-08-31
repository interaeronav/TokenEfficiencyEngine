# Self-improvement backlog (A33) — dogfooding friction log

Append-only, numbered. Every moment where TEE's own surface was
confusing, verbose, slow, or wrong during campaign work gets a row
here, with the evidence (what was called, what came back, why it hurt).
Items graduate into SI-phase work with a PROGRESS entry and get their
resolution noted here — struck through, never deleted.

Format per item:

```
## SI-B<N> — <one-line title>
- seen: <date>, <phase/session context>
- call: <tool + args, or CLI command>
- hurt: <what was confusing/verbose/slow/wrong, with numbers if any>
- proposed: <the fix, one line>
- status: open | in SI-<phase> | done (<commit>) | rejected (<why>)
```

## SI-B1 — kb module silently absent on the installed bundle
- seen: 2026-08-27, SI-0 session start (co-pilot = installed 0.1.1 .mcpb, project_root=/Users/john/TEE)
- call: `tee_search_tools {"query": "kb knowledge base"}` then `tee_describe_tool {"name": "kb_status"}`
- hurt: all 4 kb_* tools silently unregistered — `resolve_root(/Users/john/TEE, None)` → None (no knowledge-base/, no `[kb]` config) and `register_kb_tools` just skips; nothing anywhere says the module exists but is inactive. Root-causing took a bundle inspection + source read that a one-line answer would have avoided. The campaign's own co-pilot contract (kb_search/kb_read) was unfulfillable over MCP this session.
- proposed: always register `kb_status`; with no root it answers `inactive` + the exact fix (`add [kb] root=... to .tee/config.toml`), doctor-voice. 
- status: done (8aa4847: inactive kb_status registers with kb_inactive + the config line; previously mitigated for this machine 2026-08-27: `[kb] root` written to /Users/john/TEE/.tee/config.toml per docs/setup-kb.md, so the installed co-pilot activates kb_* from its next start; the product fix stays owed)

## SI-B2 — tee_search_tools has no "no strong match" signal
- seen: 2026-08-27, SI-0 session start
- call: `tee_search_tools {"query": "look vlm describe viewport"}` → ex_prepare, ex_store_facts, bl_render; `{"query": "kb knowledge base"}` → as_materials, bl_assign_material, roof
- hurt: weak matches are returned bare, indistinguishable from good ones — can't tell "tool doesn't exist" from "bad query" without describe round-trips. `tee_describe_tool` already computes closest-match hints on unknown_tool; search itself never says "nothing scored well".
- proposed: relevance floor + a `note: no strong match` line naming nearest tool names (reuse the unknown_tool closest-match machinery).
- status: done (SI-1.2: weak/empty searches carry the note; one-line summaries sentence-capped — 'kb read' query 648→427 tok, reach-one 725→580; 2 registry tests)

## SI-B3 — virtual-tool count differs by registration path (81 vs 82)
- seen: 2026-08-27, SI-0 baseline measurements
- call: `benchmarks/run_benchmarks.py` surface scenario → "81 virtual tools / flat 97"; stdio `tee serve --adapter blender` → `tee_status.virtual_tools: 82`
- hurt: "how many tools does TEE have" answers differently depending on who registered them; docs/benchmarks cite drifting counts.
- proposed: find the one-tool delta in SI-1's surface audit; make both paths share one registration list.
- status: done (explained 2026-08-27, SI-1 PROGRESS entry: flavor composition, not drift — benchmark harness registers fake+pins = 81, blender serve = 74 + 5 bl_* + 3 handoff = 82, fake serve = 74; counts must name their flavor when cited)

## SI-B4 — the canonical "wire" surface measure isn't wire bytes
- seen: 2026-08-27, SI-0 baseline measurements
- call: `run_benchmarks.py` surface row = 2,465 tok ("wire") via `model_dump(exclude nulls)` with spaced separators; a real stdio `tools/list` response, compact-dumped = 2,330 tok (2,342 with JSON-RPC envelope)
- hurt: the published wire figure overstates the real wire by ~5.8%; two sessions measuring "the" wire number get different answers.
- proposed: measure the actual stdio frame (or compact separators) and state the method next to the number.
- status: **closed 2026-08-28** (owner-directed): every estimate_tokens site in run_benchmarks now passes objects (compact separators, estimate_tokens' own dump) instead of pre-dumped spaced JSON. Compact canonical surface with tee_web_lookup: 2,028 tok (spaced measure said 2,123); the web entry's delta 180 (was 188). Historical rows keep their recorded values with the measure change noted in RESULTS.md.

## SI-B5 — RESULTS.md regeneration silently drops skipped scenarios
- seen: 2026-08-27, SI-0 benchmark reproduction
- call: `uv run python ../benchmarks/run_benchmarks.py` with no UE editor up
- hurt: the regenerated RESULTS.md deleted the whole "Unreal: level population" section (the 93.9% row) because that scenario skipped — a re-run on any machine without a DCC erases recorded evidence from the tracked file (git diff: −29 lines).
- proposed: preserve sections for skipped scenarios (carry forward with a "not re-run this pass" stamp) or refuse to rewrite when a previously-recorded scenario skipped.
- status: done (SI-1.2: `_carry_forward` in run_benchmarks.py, verified by a live no-editor run that preserved the UE section stamped — and again the same evening when a concurrent-run abort skipped the UE scenario)

## SI-B6 — `adapter` default "fake" fails on every real deployment
- seen: 2026-08-27, SI-0 session (co-pilot = installed 0.1.1, blender-only)
- call: `tee_scene_summary {}` (adapter omitted) → `{"ok":false,"error":{"code":"unknown_adapter","message":"No adapter 'fake'.","fix":"Configured adapters: blender."}}`
- hurt: the wire-visible schema default ("fake") is wrong in every real session — omitting the param (the reasonable reading of a default) costs a failed round-trip, then ~6-8 tok of `"adapter":"blender"` on every later call in the session. The error itself is rule-6-clean; the default is the defect.
- proposed: `adapter=None` + resolve to the sole configured adapter when exactly one exists (tests keep working — their single adapter IS fake); error naming choices only on real ambiguity.
- status: done (5301424)

## SI-B7 — doctor calls a just-booted UE editor "not answering as MCP"
- seen: 2026-08-27, SI-1.2 session (TeeZipProbe, UE 5.8.1)
- call: `tee doctor` / short-timeout initialize probes during the editor's first ~2.5-3 minutes
- hurt: the MCP HTTP port binds at boot but tool dispatch waits for editor startup to settle; every short probe in that window reads "listening but did not answer as Unreal's MCP server (TeeError)" — a healthy editor looks broken, and one benchmark pass concluded "no editor" and skipped the UE scenario. Measured: same endpoint, 0-byte reply during startup, 0.18 s initialize once settled.
- proposed: doctor's unreal hint (and the benchmark probe) should say "an editor that just launched may need ~2 minutes before MCP dispatches - retry before concluding it is broken", and probes that find the port bound by UnrealEditor should retry longer before reporting down.
- status: done (8aa4847: doctor warn leads with the settle-and-retry hint and names the CrashReportClient squatter; longer benchmark-probe retries stay open as a nice-to-have)

- **A34 follow-ups (2026-08-28):** `tee doctor` has no probe rows for the
  new lanes — a `[web]` connectivity/cache line and a `[llm]`/local-VLM
  endpoint line (available/unreachable + the start-the-stack fix) would
  make degradation visible before first use. Also: web image ranking is
  alt-text-overlap only (the Wikipedia tagline ranked #2 before the
  svg/ico filter); a size-hint heuristic (width/height attrs) would pick
  content images better.

## SI-B8 — tee_checkpoint answers an object; tee_rollback wants its id
- seen: 2026-08-28, A35 P0 session (latency harness against live Blender)
- call: `tee_checkpoint {label}` → `{"ok":true,"checkpoint":{"id":"cp6","label":...,"adapter":...,"revision":...}}`; then `tee_rollback {ref: <that object>}` → pydantic validation reject (ref must be str)
- hurt: the natural client move — pass back what checkpoint returned — fails a round-trip; the id must be dug out of the nested payload. tee_batch responses carry the checkpoint as a bare id, so the surface is inconsistent with itself.
- proposed: either flatten tee_checkpoint to `{"ok":true,"checkpoint":"cp6",...}` (matches the batch report; breaking, stage for 0.4.0) or accept an object/ref string union in tee_rollback (non-breaking).
- status: open

## SI-B9 — ex_ingest answers `job`; tee_job takes `job_id`
- seen: 2026-08-28, A35 P0 session (media-lane latency row)
- call: `ex_ingest {path}` → `{"job":"job1","files":1,"note":"poll tee_job for the report"}`; `tee_job` requires `job_id`
- hurt: the response key and the parameter it feeds don't match; a client keying on `job_id` gets None and never polls. One failed harness pass before the eye caught it.
- proposed: one name for the handle on both sides (`job` param alias or `job_id` response key; alias is non-breaking).
- status: open

## SI-B10 — kb_hint relevance is off-topic on non-domain questions
- seen: 2026-08-28, research-54 session (installed 0.3.1 co-pilot)
- call: tee_web_lookup on a Blender bmesh page → hint 'industry.case_studies'; on nasa/XPlaneConnect → 'industry.sa_contractors'; on stereopipeline docs → 'gxgd.game_disciplines'
- hurt: three for three off-topic hints on questions outside the KB's domains — the hint spends ~40 tok/response teaching the client to distrust it; there is no score floor, so the best of 401 files is offered even when the best is irrelevant.
- proposed: relevance floor on the hint (suppress below threshold) — same machinery as SI-B2's weak-match note; the kb-rerank chore (A34 M2 chore 7) is the deeper fix.
- status: done (A37 P0-F: raw score measured to separate NOTHING — misfires 10.5–20.5 vs in-domain 5.0–15.5, stop-word substring inflation — so the floor is identity hits: content words word-bounded in title/id/tags. 0 hits ⇒ kb_search carries the SI-B2-style "no strong match" note and the hint stays away; 1 hit ⇒ "weak match" note, hint routed through the kb-rerank chore against a none-of-these sentinel when an endpoint answers (labelled `[kb-rerank: model]`), floor-only keep otherwise; ≥2 ⇒ hint as before. All six misfire-class questions suppressed on the live corpus, all seven in-domain kept; kb benchmark row byte-identical 1,865 tok/96.7%.)
- **REOPENED and re-closed 2026-08-30 (A45).** The A37 fix held for its own
  test cases and still failed live, three times in one session, on
  `tee_web_lookup` licence questions. Three distinct causes, all fixed:
  1. **The judge was structurally unreachable.** A37's weak band defers to
     the kb-rerank chore. A web lookup taints the task by definition
     (`fetch-web` is a taint source), so once the owner pinned a PAID
     profile the A43 trust kernel refused that chore EVERY time - correctly.
     Pinning qmax silently resurrected SI-B10.
  2. **The fallback was `keep`.** `_judge_hint` returned `(True, None)` on
     any failure, so an unreachable judge produced a hint that looked
     judged - no `[kb-rerank]` label to show otherwise. INVERTED to drop:
     no judgement, no hint. The fix is never to route around the taint law;
     it is to stop asserting what could not be checked.
  3. **Duplicate words inflated the band.** `identity_hits` counted every
     occurrence, so "What licence ... State the exact licence name" scored 2
     on ONE distinct word and was promoted from the judged band to the
     unjudged strong band. Now deduplicated.
  Also: a `_META` stop set for words that describe the act of asking
  (`file`, `title`, `version`, `quote`, `repository`, `page`, `document`)
  which are not subjects in this corpus. A frequency defence was tried
  FIRST and measured to be useless - `file` is in 1.2% of identity fields,
  rare and meaningless at once - so the stop list is the honest instrument.
  Deliberately conservative: `line`, `source`, `licence`, `section`,
  `value`, `state` stay OUT because each is a real subject somewhere here.
  Regression tests use the three live misfires verbatim; in-domain controls
  assert no floor was raised onto real questions. Suite 918 passed.

## SI-B11 — Home Builder 5.1.0 is API-broken on Blender 5.2 (shimmed; upstream material)
- seen: 2026-08-29, A37 P5.1 live closet run
- call: hb lane first run → `set_input` raised "id properties not supported for this type"; probes proved Blender 5.2 moved NodesModifier input writes to `mod.properties.inputs.<ident>.value` and dropped the `mod[identifier]` idprop idiom HB uses everywhere (reads, writes, driver data paths).
- hurt: without intervention every HB prompt write and modifier-input driver fails on 5.2 — GUI included.
- done in-lane: the hb_* lane applies a session shim (old-idiom-first) over GeoNodeObject/CabinetPartModifier set/get/var/driver_input; wall+cabinet+cutlist+layouts verified live.
- REMAINING defect (recorded, not hidden): interior cages (Doors/Interior) read Dim X/Y/Z = 1.0 defaults — some deeper carcass-driver chain doesn't bind on 5.2, so interior shelf boards derive oversize (994 mm in a 600 mm carcass). Cut list reports the model's truth; engine export excludes interior parts with the reason; joinery_check (P5.3) should catch the mismatch as a real defect case.
- proposed: upstream patch to HB (the shim's four methods); revisit the interior chain after upstream or with a deeper probe.
- status: open (shim shipped; interior chain open)

## SI-B12 — a blocked FreeCAD GUI reads as "No FreeCAD RPC (timed out)"
- seen: 2026-08-29, A38 S0 session (battery fabrication row failed twice)
- call: port 9875 accepts TCP, `execute_code` never answers; stack sample proved the GUI thread parked in `DocumentRecoveryFinder::showRecoveryDialogIfNeeded()` → `QDialog::exec()` — the crash-recovery modal from an earlier killed instance (stale `FreeCAD_Doc_*` + `.lock` under `~/Library/Caches/FreeCAD/v1-1/Cache/`).
- hurt: the wire's timeout error names server-down ("No FreeCAD RPC at ... (timed out)") when the server is up and the GUI is waiting for a human click; nothing points at the dialog. One battery pass lost; diagnosis needed a process stack sample.
- proposed: (a) troubleshooting.md entry: symptoms, the stack signature, the fix (dismiss the dialog, or clear stale autosaves+locks before relaunch); (b) wire error wording: distinguish connect-refused ("no server on :9875") from accepted-but-silent ("FreeCAD answered TCP but never ran the code - a modal dialog (e.g. document recovery) may be holding the GUI; check the FreeCAD window").
- status: done (A38 S4: troubleshooting.md#freecad-rpc-hangs written; the wire now answers TimeoutError with the modal-dialog line + doc anchor while refused connections keep the start fix; the battery probes and skips with the same diagnosis)

## SI-B13 — hb_cabinet's unknown-wall refusal doesn't name the walls that exist
- seen: 2026-08-29, A38 S0 closet-run measurement
- call: `hb_cabinet {wall: "wall_1", ...}` → "Home Builder op failed: RuntimeError: no wall 'wall_1'"
- hurt: the fix (use a name from hb_room's `walls` answer) isn't in the message; hb_layout's sibling refusal ("Unknown layout view(s) ... Views: plan, elevations.") shows the house style.
- proposed: the wall-lookup error lists current wall object names (they are one `bpy.data.objects` filter away), e.g. "no wall 'wall_1' - walls present: Wall".
- status: open

## SI-B14 — structure_facts could carry an extractive verifier
- seen: 2026-08-29, A42 R3 (calibration-or-static survey of unverifiable chores)
- today: structure_facts is schema-validated only ("only facts stated in the text" is instructed, not enforced), so it stays statically routed - the cascade cannot gate it.
- proposed: verify each emitted fact's load-bearing tokens (numbers, quoted names) appear in the source text - the refine_extract/phrase_deviation pattern; a fact that fails dies and the parser's output stands. Would move the chore from static to verifier-gated routing for free.
- status: open

## SI-B15 — the virtual surface is scene-side; build pipelines have no lane
- seen: 2026-08-30, owner report (DiversionPlanner-BaseMap build attempt)
- call: the 103-tool virtual surface vs ~/DiversionPlanner-BaseMap/builder/ (build_basemap.py + analysis scripts)
- hurt: every virtual tool assumes live scene state (epoch/revision, diffs, checkpoints); a file-in/file-out build pipeline has none of that, so TEE cannot drive the owner's basemap build at all. ONE op earned its place: capture_terrain's dem_diff, because it is a DECLARED HEADLESS OPERATION (qgis:rastercalculator, typed inputs/outputs, jobs pattern, compact report) — the seed pattern for the fix.
- proposed: the pipeline lane — projects declare owner-authored steps in their own tracked .tee/pipeline.toml (name, command, inputs/outputs, cost hint); TEE runs declared steps only (never model-invented shell), as jobs: ledger-registered, QoS batch under the K-layer scheduler (steps with declared inputs/outputs ARE task-graph nodes), budgeted progress, artifact diffs (changed outputs, sizes, hashes), rule-6 failures with the failing step's tail. First customer: the DiversionPlanner basemap build. dem_diff generalizes from one wrapped op to any declared step.
- status: **CLOSED 2026-08-30 (A43 P0–P6, v0.8.0).** The lane ships: projects declare steps in their own tracked `.tee/pipeline.toml` (argv arrays only, typed+constrained params, declared env, inputs/outputs, cost hints, answer budgets), hash-pinned per machine, run as ordinary batch jobs under the K-layer scheduler with artifact diffs, budgeted query answers and rule-6 failures. Three authoring routes: `pipeline_init` (draft from the project's own scripts, every block commented out), hand-write, and `pipeline_adhoc` → `pipeline_adopt` (the discovery route). dem_diff generalized as predicted. First customer delivered — `~/DiversionPlanner-BaseMap` declares five steps from its own runbook and the builder runs end to end from one sentence; second project `~/OkongoSim` runs three steps with nothing in `server/` changing. Measured: −74.5% on a produce step, and honestly +8–40 tokens on short-output queries (`benchmarks/RESULTS.md`). Guide: `docs/setup-pipeline.md`; recorded exchanges: `docs/pipeline-first-customer.md`.

## SI-B16 — `paid = true` is declarative; nothing enforces it
- seen: 2026-08-30, wiring the owner's qmax (hosted Qwen-Max) profile
- call: `[llm.profiles.qmax] paid = true` in .tee/config.toml
- hurt: the flag documents intent but no code reads it. The router could in principle select a paid profile while unpinned (automatic off-machine spend), and report_savings has no paid-call/cost column, so spend would be invisible next to the free local rows.
- proposed: (1) router hard-excludes profiles with `paid = true` from automatic selection — pin-only, fixture-proven; (2) the meter gains paid-call count + a spend estimate column, labelled as an estimate; (3) llm_switch's report says "PAID, off-machine" on every switch INTO such a profile.
- status: open (the three proposals above are all unbuilt). UPDATED 2026-08-30, post-0.8.0: A43 added a FOURTH, stronger guard the entry predates — `paid = true` is now read at the call site (`llm/chores.py`), which demands the `call-paid-engine` capability, default-deny and high-risk. The owner granted it this session, so that gate now passes for untainted callers. Re-checked what the grant does NOT open: the router structurally cannot select qmax at all — it is not a registered engine (`ENGINES` holds only `q14b+a2`/`q27b-bare`; `_PROFILE_TO_ENGINE` has no `qmax` key; `LADDER` is hardcoded to the two local engines), so "automatic off-machine spend" is impossible by construction rather than by flag. Still genuinely open: the meter has no paid-call/spend column, and `llm_switch` does not say "PAID, off-machine".

## SI-B17 — the installed co-pilot's project_root is not the repo (config edits land nowhere)
- seen: 2026-08-30, wiring the qmax profile
- call: wrote `[llm.profiles.qmax]` into `<repo>/.tee/config.toml`; llm_switch kept refusing
- hurt: the Desktop extension's settings say `project_root = /Users/john/TEE`, so the running server reads `/Users/john/TEE/.tee/config.toml` — NOT the repo's. A config edit in the repo is invisible to the installed co-pilot, silently, with no hint anywhere that two configs exist. (A stale memory note claiming the root had moved compounded it.) Cost: three failed switches before the settings file was read.
- proposed: `tee_status` (and doctor) report the ACTIVE project_root and the config file actually loaded; `llm_unknown_profile` (and config-shaped refusals generally) name the file they read, so "I edited the config" and "the server read a different config" cannot look identical.
- status: PARTLY DONE (A43 T-1 L1), verified 2026-08-30 post-0.8.0. Done: `tee_trust` answers with both `"project"` and `"config"` — the live call on the installed server returned `{"project":"/Users/john/TEE","config":"/Users/john/TEE/.tee/config.toml",...}` — and capability refusals name the granting file (`trust.py`: "Add '<cap>' to [trust] grants in <where>"), so an edit that landed nowhere no longer looks like a bug. Confirmed useful in practice this session: it named the right file before the qmax grant was written. STILL OPEN: `tee_status` itself reports neither `project_root` nor the loaded config path (checked live — the response carries adapters/jobs/checkpoints/virtual_tools/llm_profile and no config identity), so the original proposal is only half met; doctor unchecked. Also newly seen: grants are read ONCE at `TeeApp` construction (`app.py:134`), so a config edit is invisible to the running server until Desktop restarts, with nothing saying so — arguably the same class of trap this item is about.

## SI-B18 — meter idea: a "sent" column (what left the machine)
- seen: 2026-08-30, owner idea filed for later ("a send column"), raised while qmax (hosted, paid) was being wired
- hurt: not a defect — a gap. With a paid/hosted profile pinned, chore inputs leave the machine (tracebacks, file excerpts, KB passages, web extracts). report_savings accounts for TOKENS but says nothing about EGRESS: nothing tells the owner how much content went off-machine, to which endpoint, on whose behalf.
- proposed: a `sent` column beside the token columns — per session and per engine: calls that went off-machine, bytes/tokens sent, the endpoint, and (cheap and useful) the chore kinds involved. Local-only sessions read a clean zero, which is itself the reassurance. Pairs with SI-B16's spend column: B16 answers "what did it cost", B18 answers "what did it disclose".
- note: if the owner meant "spend", that half is already SI-B16 — this item is filed as the egress reading; either way the two columns ship together.
- status: open (idea, for later)

## SI-B19 — RESULTS.md loses sibling-runner sections and grows on every re-run
- seen: 2026-08-30, the v0.8.0 post-release health check (a plain `run_benchmarks.py` on this machine)
- call: `uv run python ../benchmarks/run_benchmarks.py` with no UE editor and no FreeCAD RPC
- hurt: THREE defects in one file, all from `run_benchmarks.py` rewriting RESULTS.md wholesale. (1) `_carry_forward` is called by explicit header, and only for sections this runner owns — the A42 scheduler row (`run_k4_mixed.py`) and the A43 pipeline row (`run_p6_pipeline.py`) are in neither list, so a single re-run deleted both: `git diff` −74 lines, the two most recent campaigns' headline evidence gone. (2) the `*Generated by ...*` footer sits at end of file, so whichever section is carried last swallows it and a fresh one is appended — **three had already accumulated in the tracked 0.8.0 file**. (3) stripping the old stamp left the blank line that followed it, growing each carried section by one blank per run — measured +1/run, 13 already banked in the Unreal section.
- proposed: carry the sibling-owned sections unconditionally; strip the footer in `_carry_forward` alongside the stamp; collapse leading blanks before re-adding the stamp.
- status: done (this session; all three fixed in `_carry_forward` / `write_results`, verified by three consecutive runs holding steady at 13 sections / 1 footer / 5 blanks, and by RESULTS.md's remaining diff being only real re-measurement)

## SI-B20 — benchmarks/ is outside the lint gate
- seen: 2026-08-30, while patching `run_benchmarks.py` for SI-B19
- call: `uv run ruff check ../benchmarks/run_benchmarks.py` → **15 errors**, while the project gate `ruff check .` (run from `server/`) says "All checks passed!"
- hurt: `[tool.ruff]` lives in `server/pyproject.toml` and the gate runs from `server/`, so `benchmarks/` — tracked code that produces the numbers this project is judged on — is never linted. The 15 include one real bug: `run_benchmarks.py:1903` is `print(f"\nwrote {out}")` AFTER a `return`, referencing an undefined `out` (F821). Dead today; it would raise if ever reached. Pre-existing, not a regression.
- proposed: bring `benchmarks/` into the gate (run ruff from the repo root, or add the path to the server invocation), then fix the 15 — most are E501 in embedded FreeCAD source strings and can be `noqa`'d in place.
- status: open

## SI-B21 — TEE cannot open HEIC, the format the owner's iPhone shoots
- seen: 2026-08-31, owner request; verified against the live extension venv
- call: `Image.open("/Users/john/Downloads/IMG_2984.HEIC")` in the installed venv
- hurt: `UnidentifiedImageError: cannot identify image file`. Pillow 12.3.0
  registers no HEIF plugin, and **every image TEE reads goes through
  `PIL.Image.open`** — `extract/images.py` (3 call sites), `extract/video.py`,
  `capture/dji.py`, `uefn/export.py`, `adapters/unreal/vision.py`,
  `fleet/med.py`. So the whole extract lane silently rejects the native
  format of the owner's capture device, and
  `docs/okongo-capture-protocol.md` explicitly says photos arrive
  "HEIC/DNG/JPG as shot". Research 12 anticipated this and deferred it —
  "add `exifread` only if HEIC/RAW ingestion is in scope". It is now.
- proposed: `pillow-heif` (registers a real Pillow plugin, so read AND write
  land at every existing `Image.open`/`save` call with no call-site changes)
  as an extract-extra dependency, registered once at import. Check its
  licence before adopting — it wraps libheif, and the codec's terms matter
  more than the wrapper's. Confirm DNG/RAW separately rather than assuming
  the same plugin covers it.
- status: DONE 2026-08-31 - tee/kernel/imaging.py, nine call sites rewired, pillow-heif added to [extract], AST guard against regression, licence position recorded in DECISIONS.md

## SI-B22 — extraction discipline forbids estimated dimensions outright
- seen: 2026-08-31, owner request
- call: the extract lane reports measurements only where a measurement exists
- hurt: the rule is too strict for the case it most often meets. On a site
  photo with no scale bar and no drawing, TEE currently returns nothing
  rather than a qualified estimate, so a usable answer is withheld because
  it cannot be a perfect one. The owner wants estimation permitted **where
  its accuracy can be mitigated** — a reference object of known size, a
  known camera height, a door or brick course, a solved camera pose.
- proposed: allow an estimate ONLY when it carries (a) the mitigation that
  made it possible, named, (b) an honest accuracy band, and (c) a field
  that marks it as estimated, never merged into a measured field. An
  estimate with no stated mitigation stays refused. This mirrors the A40
  law already in `docs/DECISIONS.md` — "accuracy claims carry their
  source's honesty band" — so the discipline is being *extended* to a new
  source, not weakened. Design the schema before writing code: the danger
  is an estimate that later reads as a measurement.
- status: DONE 2026-08-31 - tee/extract/estimate.py + ex_estimate; refuses without a named mitigation, band widens when the caller is vague, value lands in estimated_mm and never mm

## SI-B23 — hb_status 32 mm warning: ALREADY SHIPPED, no work needed
- seen: 2026-08-31, owner request to add it
- call: `hb_status` in `adapters/blender/homebuilder.py:308`
- hurt: none — it already returns
  `"HB 5.1 models no 32 mm system holes; hb_cutlist reports dimensions only
  and says so"`, unconditionally (outside the installed/not-installed
  branch, so it shows even when Home Builder is absent). The same fact is
  stated in two more places: `hb_cutlist`'s note and the cabinet-spec
  builder's note, which says the affected `joinery_check` rules answer
  `not_evaluated` rather than passing.
- proposed: nothing. Recorded so the request is not re-opened as missing.
- status: closed on inspection

## SI-B24 — a blind HOST model cannot use TEE's media lanes at all
- seen: 2026-08-31, owner request. First researched against the wrong
  topology; corrected when the owner said the real case is **opencode in
  the terminal, DeepSeek running locally as the HOST model** driving TEE
  over MCP, where TEE reported machine vision as a feature it does not offer.
  Full write-up: `docs/research/66-senses-for-blind-models.md`.
- call: `tee_search_tools "describe what is in an image, machine vision,
  look at a photo"` — the question a blind host would actually ask
- hurt: the answer contains nothing that describes an image
  (`as_photo_material`, `med_instance_tags`, `med_volume_stats`,
  `ex_estimate`, `quant_optimize`, `trade_backtest`), and two results
  advertise the opposite — "Pixel data is never returned", "Never the voxel
  array". **TEE was telling the truth.** The cause is decision A9 in
  `extract/vlm.py`: the default extraction channel is in-band, where
  `ex_prepare` hands the host file paths because "it reads media with its
  own tools". That assumed the host was Claude. With a blind host both
  shipped drivers fail — in-band because the host is the blind model, and
  `ApiDriver` because it needs `ANTHROPIC_API_KEY`, a paid cloud call that
  defeats running locally. `tee_capture`/`tee_media` compound it by
  returning pixels, spending tokens to deliver something the host cannot
  read. Meanwhile `kernel/local_vlm.py` is a working local vision client -
  free, measured at 7.5 s on a real frame - wired to the web lane ONLY.
- proposed: (1) `LocalVlmDriver` as a third extraction driver on the
  existing `local_vlm` client, so the in-band channel has a local free
  fallback instead of requiring either sight or a cloud key; (2)
  `sense_describe` / `sense_transcribe` as plain tools, so a blind host can
  ask for text rather than being handed pixels — faster-whisper is already
  installed and transcribes verbatim in 0.62 s; (3) declare senses on
  `machine.ENGINES` so the surface can say what it can and cannot perceive
  instead of leaving a host to infer it from an empty search. Every answer
  names its provider: a description is a summary someone else wrote, and
  the model reasoning over it never saw the pixels.
- secondary (different path, still true): the owner's LiteLLM hook already
  reroutes image-bearing requests to Qwen3-VL, silently, and that reroute
  evicts the 84 GB session model for the 17 GB vision model — measured at
  ~10 s per modality alternation against 0.67-0.82 s warm, a cost that
  appears in no ledger or answer. Relevant to Claude Desktop, not to the
  opencode case.
- status: open (researched, not built)
