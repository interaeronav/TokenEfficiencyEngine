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
