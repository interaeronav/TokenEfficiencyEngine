# Claude receipt 11 — runtime acceptance, TEE-20260910-A82-01 rev 1

```text
Receipt ID / UTC / recipient: TEE-20260911T061956Z-CLAUDE-11 / 2026-09-11T06:19:56Z /
  Claude (Fable 5.1, Claude Code) — actual installed client
Scope: runtime-upgrade
Protocol version / document SHA-256: 1.0.1 / ac74807a…fc9c
Update ID / frozen manifest SHA-256: TEE-20260910-A82-01 revision 1 /
  961adc95f587a287e97ce09c5daeac51748398ad76e67a1df824acb7b7df6339
Stage: accepted

Received artifact/source identity:
  claude/tee-engine-0.30.1-a82-local.mcpb, sha256
  98f5116fe1c51b62062571cdf81d4f0039d3bc34815aafcf7c951c0768c3c3e2,
  1,138,535 bytes — re-hashed immediately before handover for install

Running source origin / payload identity / TEE and wrapper versions:
  PIDs 86724/86790, started 2026-09-11T06:17:00Z — FRESH, replacing
  83904/83971 (the 06:04Z restart of the old bundle). Source written
  06:16:30Z. Launcher: checkout venv python + the bundle's own launch.py,
  five adapters, PYTHONDONTWRITEBYTECODE=1.
  Installed payload: tee-payload-v1
    ac6474bab36e1c52e6b92276a97af060f3ca37db85645a5d55b5aac0a687ea52
    293 files / 3,428,263 bytes — IDENTICAL to the frozen source manifest.
  301 non-cache members; architecture/gui.html present. TEE 0.30.1.
  No wrapper applies to the Desktop shape.

Interpreter / selected project / adapters:
  checkout venv (borrowed); project_root /Users/john/TokenEfficiencyEngine,
  grants_file present; blender, partkiln, seamkiln, fusion, unreal

Required feature and dependency checks / evidence:
  core 17; virtual_tools 261 WITH the main project corpus (context named);
  15 lessons live; 21/21 descriptors discovered live (5 doc_*, 11 ak_*,
  5 learn_*); ak_status, doc_status, learn_status all ok; 148/148
  distributions, no drift, 1,339 constraints satisfied; sidecar 10

Continuity checks / preserved grants and model selection:
  qmax pinned (file read: {"active":"qmax","ready":true,"pinned":true});
  granted ["call-paid-engine"] only; code_exec_enabled false; jobs [] and
  checkpoints [] as before; tee_recall coherent; fresh scene read taken
  (13 objects, IDs reissued b728–b740); -a71 untouched

Differences or failures / next action / responsible agent:
  no failing check. run-doc-agent recorded UNAVAILABLE, not granted.
  GPT-6 reconciles against TEE-20260911T060123Z-CODEX-A82-01 and closes.
```

## Checks, in the packet's order

**1. Identity and fresh connection.** Payload on disk equals the frozen
manifest byte-for-byte (`ac6474ba…`, 293). New process at 06:17:00Z; the
06:04Z restart had relaunched the OLD bundle, which is why the 06:14Z pending
note was correct at the time.

**2. Project, QMAX, grant, continuity.** Project preserved through the install
— Finding 1 of receipt 08 inverted and held. qmax pinned per the file, not
status. Sole grant `call-paid-engine`. Code execution off. Jobs and checkpoints
empty before and after. Memory recall intact across the reconnect.

**3. Core, virtual, descriptors, lessons.** 17 core. **261** virtual with the
main corpus, matching `virtual_tools_with_main_corpus_expected`. All 16
`new_tools` and all five `learn_*` discovered live via `tee_search_tools`.
Fusion guide: six `cadagent_*`; Blender guide: the same six plus `house`,
`textures`, `fabric` — 15. Raw wire-schema checksum: not claimable from this
connector, as Codex also found; receipt 10 rebuilt the 17 schemas from this
exact payload and matched the probe byte-for-byte, and the installed payload is
that payload.

**4. `doc_status` and `ak_status`, observed.**
- `doc_status`: workers aider 0.86.2 and cline 3.0.61 present,
  `version_verified: true` via package metadata; model qmax, paid, ready;
  **`execution_allowed: false`, capability `run-doc-agent`**. Recorded as
  execution unavailable, pending the owner's separate decision. Not granted.
- `ak_status`: archkiln 0.1.0, units mm, no models, GUI optional via
  `ak_open` (not started), jurisdiction coverage "explicit rule packs;
  unverified until assessed". No fixture exercised; none required.

**5. Dependencies, resources, learning, honest coverage.** 148/148 with no
drift against the reused prior audit; `gui.html` present. `learn_status`:
enabled, healthy, events 24→151 through ordinary use, snapshots 0. An
evaluation ran (train 90 / holdout 16): the candidate beat baseline on Brier
(0.077 vs 0.164) and the gate still **refused promotion —
`insufficient_coverage`**. No active model. That is the guard working, and no
training or promotion is claimed. Limits preserved verbatim:
`global_law_coverage: not_verified`; `live_unreal_export_verified: false`.
Fusion has a bridge but no design; Unreal has no listener — unchanged and
irrelevant to these offline checks. No owner design edited, no DCC started,
no paid inference performed.

## For closure

GPT-6's memory fact "Claude disk still A79/A80" is now superseded by this
receipt; GPT-6 is the sole memory writer, so I have not corrected it. The
A79/A80 rollback set is retained in the delivery and should now be counted as
the second most recent accepted set.
