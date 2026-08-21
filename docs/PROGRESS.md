# TEE Build Progress

Claude: read this file at session start, update it before session end.
Check items only after their acceptance criteria ran for real (paste evidence
under "Evidence log"). Record machine-specific facts under "Machine facts".

## Phase status

- [x] Bootstrap — repo scaffold, research corpus, execution script (built in
      Claude cloud session, 2026-08-21)
- [x] Phase 0 — Environment discovery *(cloud container; re-run on the
      physical machine when it joins)*
- [x] Phase 1 — Server core and token kernel *(cloud container, 2026-08-21)*
- [ ] Phase 2 — Blender adapter *(in progress in cloud: headless-testable
      parts; live-GUI validation needs the physical machine)*
- [ ] Phase 3 — Unreal adapter *(requires the physical machine — UE editor
      cannot run in the cloud container)*
- [ ] Phase 4 — Cross-cutting friction killers
- [ ] Phase 5 — Benchmarks *(Blender scenarios done in cloud: 87.7% total
      saving measured — see benchmarks/RESULTS.md; UE scenarios need the
      physical machine)*
- [ ] Phase 6 — Packaging and handoff

## Machine facts

### Cloud build container (Claude Code on the web, 2026-08-21)

- OS: Linux x64 (ephemeral container; work persists only via git push)
- Python: 3.11.15 (default), 3.12, 3.13 available; `uv` installed
- Blender: 5.2.0 LTS extracted at `/home/user/blender-5.2.0-linux-x64/`
  (headless verified: `bpy OK (5, 2, 0) py 3.13.13`); official Blender MCP
  extension NOT installed; no GUI/display
- Unreal: not installed, not installable here (size + EULA + editor GUI)
- MCP Python SDK: 2.0.0 (see DECISIONS 2026-08-21 — `MCPServer` API)
- Adapter tiers: Blender primary (5.2 LTS headless); UE n/a in cloud

### Physical machine

*(filled in by Phase 0 when the repo is first opened there)*

- OS:
- Python interpreters / uv:
- Blender installs (path, version, official MCP extension present?):
- Unreal installs (path, version, ModelContextProtocol plugin present?):
- Adapter tiers selected:

## Blockers

*(none recorded)*

## Evidence log

*(paste real command output here when checking off acceptance criteria)*

### 2026-08-21 — Bootstrap
- Deep-research pass completed (11 agents, ~1.15M tokens): corpus committed
  under `docs/research/` (10 digests + index).
- Execution script authored from the corpus; architecture decisions A1–A7
  recorded in `docs/research/00-index.md`.

### 2026-08-21 — Phase 0 + Phase 1 (cloud)
- `server/` scaffolded with uv; `make check` = ruff + pytest.
- Kernel implemented: adapter contract + fake adapter, differential scene
  cache (epoch/revision stamps, net-diff merging, bounded log), response
  budgeter + per-tool size log, progressive-disclosure registry
  (search/describe/call with argument validation), checkpoint manager with
  auto-checkpoint per batch, async job manager, project memory (.tee/).
- MCP surface: 14 always-loaded tools on `mcp` SDK 2.0 `MCPServer`,
  `structured_output=False` everywhere (A6), inline-JPEG capture tool.
- Evidence: `uv run pytest` → **50 passed** (units + A6 lint suite + 6
  end-to-end in-memory MCP client scenarios); `ruff check` clean.
- Measured: full 14-tool definition surface ≈ **2,307 tokens** (budget 8K;
  wild-average is ~710 tokens/tool, so the whole surface costs ~3 tools).
- `tee serve` (stdio, fake adapter) and `tee doctor` (stub) run.

### 2026-08-21 — Phase 2 (cloud-testable parts) + adversarial review
- Blender adapter over the official Blender Lab MCP add-on wire protocol
  (verified against the real add-on source and live headless Blender 5.2);
  generic batch interpreter (N ops = 1 round-trip), `session_uid` entity
  ids, API firewall over the ten catalogued 4.x/5.x fault lines,
  snapshot/rollback, byte-budgeted JPEG capture, `bl_*` virtual tools.
- TEE bridge add-on (`adapters/blender/tee_bridge/`): same protocol,
  hardened threading (I/O thread + single persistent timers pump / blocking
  background loop), 5.1+ extension manifest, denylist guard. Live suite runs
  against BOTH bridge flavors.
- **Adversarial review workflow** (32 agents, ~2.2M tokens): 28 findings
  confirmed empirically, 0 refuted — including three majors: the mcp 2.0
  SDK dispatches tool calls concurrently on worker threads (torn state), the
  SDK pretty-prints dict returns (≈2x wire size; fixed by returning compact
  JSON strings), and mid-batch failures left the DCC and scene cache
  silently divergent (fixed: batches are atomic — auto-restore to the
  checkpoint on failure). All 28 fixed with regression tests.
- Evidence: `uv run pytest` → **85 passed**; `uv run pytest -m dcc` →
  **20 passed** (both bridge flavors, real Blender 5.2); ruff clean.
- Follow-up for next session: adversarial review round over the fix diff +
  bridge add-on; GUI-mode bridge validation needs the physical machine.
