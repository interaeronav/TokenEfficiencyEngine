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
- status: open (mitigated for this machine 2026-08-27: `[kb] root` written to /Users/john/TEE/.tee/config.toml per docs/setup-kb.md, so the installed co-pilot activates kb_* from its next start; the product fix stays owed)

## SI-B2 — tee_search_tools has no "no strong match" signal
- seen: 2026-08-27, SI-0 session start
- call: `tee_search_tools {"query": "look vlm describe viewport"}` → ex_prepare, ex_store_facts, bl_render; `{"query": "kb knowledge base"}` → as_materials, bl_assign_material, roof
- hurt: weak matches are returned bare, indistinguishable from good ones — can't tell "tool doesn't exist" from "bad query" without describe round-trips. `tee_describe_tool` already computes closest-match hints on unknown_tool; search itself never says "nothing scored well".
- proposed: relevance floor + a `note: no strong match` line naming nearest tool names (reuse the unknown_tool closest-match machinery).
- status: open

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
- status: open (2026-08-27: method located — run_benchmarks uses model_dump(by_alias, exclude_none) with spaced separators; both figures now recorded side by side in PROGRESS: canonical 1,935 vs true stdio 1,848 after SI-1)

## SI-B5 — RESULTS.md regeneration silently drops skipped scenarios
- seen: 2026-08-27, SI-0 benchmark reproduction
- call: `uv run python ../benchmarks/run_benchmarks.py` with no UE editor up
- hurt: the regenerated RESULTS.md deleted the whole "Unreal: level population" section (the 93.9% row) because that scenario skipped — a re-run on any machine without a DCC erases recorded evidence from the tracked file (git diff: −29 lines).
- proposed: preserve sections for skipped scenarios (carry forward with a "not re-run this pass" stamp) or refuse to rewrite when a previously-recorded scenario skipped.
- status: open

## SI-B6 — `adapter` default "fake" fails on every real deployment
- seen: 2026-08-27, SI-0 session (co-pilot = installed 0.1.1, blender-only)
- call: `tee_scene_summary {}` (adapter omitted) → `{"ok":false,"error":{"code":"unknown_adapter","message":"No adapter 'fake'.","fix":"Configured adapters: blender."}}`
- hurt: the wire-visible schema default ("fake") is wrong in every real session — omitting the param (the reasonable reading of a default) costs a failed round-trip, then ~6-8 tok of `"adapter":"blender"` on every later call in the session. The error itself is rule-6-clean; the default is the defect.
- proposed: `adapter=None` + resolve to the sole configured adapter when exactly one exists (tests keep working — their single adapter IS fake); error naming choices only on real ambiguity.
- status: done (5301424)
