# TEE Build Progress

Claude: read this file at session start, update it before session end.
Check items only after their acceptance criteria ran for real (paste evidence
under "Evidence log"). Record machine-specific facts under "Machine facts".

## Phase status

- [x] Bootstrap — repo scaffold, research corpus, execution script (built in
      Claude cloud session, 2026-08-21)
- [ ] Phase 0 — Environment discovery *(requires the physical machine)*
- [ ] Phase 1 — Server core and token kernel
- [ ] Phase 2 — Blender adapter
- [ ] Phase 3 — Unreal adapter
- [ ] Phase 4 — Cross-cutting friction killers
- [ ] Phase 5 — Benchmarks
- [ ] Phase 6 — Packaging and handoff

## Machine facts

*(filled in by Phase 0 on the physical machine)*

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
