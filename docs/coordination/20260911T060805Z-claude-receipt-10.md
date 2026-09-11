# Claude receipt 10 — candidate review, TEE-20260910-A82-01 rev 1

```text
Receipt ID / UTC / recipient: TEE-20260911T060805Z-CLAUDE-10 / 2026-09-11T06:08:05Z /
  Claude (Fable 5.1, Claude Code)
Scope: runtime-upgrade
Protocol version / document SHA-256: 1.0.1 / ac74807a…fc9c
Update ID / frozen manifest SHA-256: TEE-20260910-A82-01 revision 1 /
  961adc95f587a287e97ce09c5daeac51748398ad76e67a1df824acb7b7df6339
Stage: received      Review outcome: PASS — no blocking defect found
Received artifact/source identity:
  claude/tee-engine-0.30.1-a82-local.mcpb
  sha256 98f5116fe1c51b62062571cdf81d4f0039d3bc34815aafcf7c951c0768c3c3e2
  1,138,535 bytes; payload tee-payload-v1 ac6474ba…ea52, 293 files / 3,428,263 bytes
Running source origin / payload identity / TEE and wrapper versions:
  UNCHANGED — the installed client still serves A79/A80 (82e5bc7e…4193,
  274 files). Nothing installed by this review; restarting it would not
  install A82, as the handoff says.
Interpreter / selected project / adapters: unchanged — checkout venv,
  project /Users/john/TokenEfficiencyEngine, five adapters
Required feature and dependency checks / evidence: candidate verification
  below; live A82 checks are NOT possible until installation
Continuity checks / preserved grants and model selection: unchanged; nothing
  installed, restarted, granted or reconfigured. run-doc-agent NOT added.
Differences or failures / next action / responsible agent: none blocking;
  notes below. Next: John installs via Desktop's extension controls, keeping
  the project at /Users/john/TokenEfficiencyEngine; then a fresh Claude receipt
  at stage accepted.
```

## Independent verification — recomputed here, your verify_candidate.py not used

| Check | Declared | Measured | |
|---|---|---|---|
| release-manifest self-checksum | `961adc95…6339` | `961adc95…6339` | ✅ |
| Claude artifact | `98f5116f…c3e2`, 1,138,535 B | identical | ✅ |
| Codex artifact | `e908840f…53e1` | identical | ✅ |
| MCPB `src/tee` payload | `ac6474ba…ea52`, 293 files | identical | ✅ |
| Codex snapshot payload | same | **identical to the MCPB** | ✅ |
| **live checkout payload** | same | **identical — freeze still valid** | ✅ |
| rollback payload (A79/A80) | `82e5bc7e…4193`, 274 | = what is installed **now** | ✅ |
| shared skill | `a98fe56b…cbd1` | identical | ✅ |
| dependency inventory (prior audit, reused) | 148 | 148 live, no drift, PEP 503 | ✅ |

**Launcher.** `command` is the checkout venv python; `args` begin
`${__dirname}/launch.py serve` with all five adapters; `PYTHONDONTWRITEBYTECODE=1`.
`launch.py` is **byte-identical to `packaging/launch.py`** — builder used
unmodified, my ownership intact.

**What A82 adds, counted from the archives, not the prose.** Exactly 19 files
and nothing removed: `architecture/` (14, the archkiln app incl. `gui.html`,
`unreal_export.py`, `data/rule-pack.schema.json`) and `docagents/` (5).

**Core contract reproduced from source.** A server built from the candidate
payload lists **17** tools whose names, descriptions and `inputSchema` are
**byte-identical** to `evidence/probes/…-claude-corpus-core-schemas.json`.

**Descriptors from source.** All 16 `new_tools` (five `doc_*`, eleven `ak_*`)
and all five preserved `learn_*` tools register from the candidate source.

**Delivery parity.** No differing common file between the two folders. 129
common files, not 127: the two extra are the carried A79/A80 acceptance
receipts under `rollback/receipts/` — record-keeping, not payload.

## Notes, none blocking

1. **Virtual-tool composition.** My rebuild used `FakeAdapter` and no corpus
   and saw 216 registered tools; the contract's 257/261 are for the five real
   adapters. Different composition, not a mismatch — the protocol says to name
   the composition, so I do. The decisive count is the live one after install.
2. **Finding 2 from receipt 08 still stands.** `core_schema_sha256_expected`
   (`95373e1c…`) has no stated derivation; I verified the contract by
   reconstruction instead. The per-context probe files are a good addition.
3. **Finding 1 has inverted, in our favour.** The bundle default is still
   `${HOME}/TEE`, but Desktop preserves the current setting, which is now the
   required `/Users/john/TokenEfficiencyEngine`. Safe as long as the folder is
   **not** changed during install.
4. **Limits I will carry into acceptance, not upgrade:** `global_law_coverage:
   not_verified`, `live_unreal_export_verified: false`; `run-doc-agent` is
   pending the owner's separate decision, so doc-worker execution will be
   recorded as unavailable.

## Recommendation

**Proceed.** Internally consistent, matches its frozen manifest on every
recomputable identity, carries the complete 293-file payload, preserves the
core contract, registers every declared descriptor, and ships a rollback that
reproduces what is running today.
