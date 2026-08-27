# Changelog

The `tee-engine` server versions here; the UE `TeeToolset` plugin and the
Blender `tee_bridge` extension carry their own versions where noted.

## Unreleased

Proposed next version: **0.2.0** (surface-visible changes; see the
release checklist in docs/COMMERCIAL_READINESS.md — the bump itself is
step 1 there).

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
