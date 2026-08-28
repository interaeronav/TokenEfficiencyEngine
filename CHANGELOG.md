# Changelog

The `tee-engine` server versions here; the UE `TeeToolset` plugin and the
Blender `tee_bridge` extension carry their own versions where noted.

## Unreleased (A35 shrink campaign)

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
