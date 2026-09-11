# Claude receipt 08 — candidate review, TEE-20260910-A79-A80-01 rev 1

```text
Receipt ID / UTC / recipient: TEE-20260910T211323Z-CLAUDE-08 /
  2026-09-10T21:13:23Z / Claude (Opus 5, Claude Code)
Scope: runtime-upgrade
Protocol version / document SHA-256: 1.0.1 / ac74807a…fc9c  (matches
  release-manifest.protocol_sha256 — the revision I accepted in receipt 04)
Update ID / frozen manifest SHA-256: TEE-20260910-A79-A80-01 rev 1 /
  1846119f418092dee3a3b76c39d9a920be21823c49bb3e1378a75773ccb5b469
Stage: received      Review outcome: PASS — no blocking defect found
Received artifact/source identity:
  claude/tee-engine-0.30.1-a79-a80-local.mcpb
  sha256 9e1df2d63cf9b90752318c747b579f83eca7af65a580d601d36bf887a112f0c0
  1,039,492 bytes; payload tee-payload-v1 82e5bc7e…4193, 274 files / 3,097,672 bytes
Running source origin / payload identity / TEE and wrapper versions:
  unchanged from receipt 07 — PID 53401 still serving the OLD bundle
  (8b6b58e0…6aed, 252 files, 240 virtual tools). Nothing installed by this review.
Interpreter / selected project / adapters: unchanged — checkout venv,
  project_root /Users/john/TokenEfficiencyEngine-a71, five adapters
Required feature and dependency checks / evidence: candidate verification table
  below; live A79/A80 feature checks are NOT possible until installation
Continuity checks / preserved grants and model selection: unchanged; nothing
  was installed, restarted, granted or reconfigured by this review
Differences or failures / next action / responsible agent: two non-blocking
  findings below. Next action is John's (install + project selection), then a
  fresh Claude receipt at stage `accepted`.
```

## Independent verification — computed here, not read from your evidence

Every identity in the frozen manifest was recomputed with my own
`tee-payload-v1` implementation and `shasum`, per receipt 04's independence
argument. Your `verify_candidate.py` was deliberately **not** used.

| Check | Declared | Measured | |
|---|---|---|---|
| `release-manifest.json` self-checksum | `1846119f…b469` | `1846119f…b469` | ✅ |
| protocol identity | `ac74807a…fc9c` | = accepted 1.0.1 | ✅ |
| Claude artifact | `9e1df2d6…f0c0` | `9e1df2d6…f0c0` | ✅ |
| Codex artifact | `5f0383e6…ec9d` | `5f0383e6…ec9d` | ✅ |
| rollback artifact | `9c0fbee8…6d28` | `9c0fbee8…6d28` | ✅ |
| MCPB `src/tee` payload | `82e5bc7e…4193`, 274 / 3,097,672 | identical | ✅ |
| Codex snapshot payload | same | **identical to the MCPB** | ✅ |
| **live checkout payload** | same | **identical — freeze still valid** | ✅ |
| rollback payload | `8b6b58e0…6aed`, 252 | = what is installed **now** | ✅ |
| shared skill | `a98fe56b…cbd1` | `a98fe56b…cbd1` | ✅ |
| `evidence/core-schemas.json` file | `60d31b76…5e8c` | `60d31b76…5e8c` | ✅ |

**§4's stop-condition does not apply.** The live checkout's payload still equals
the frozen source manifest, so the candidate has not been invalidated by
concurrent work.

**Launcher and resources.** `command` is
`/Users/john/TokenEfficiencyEngine/server/.venv/bin/python`; `args` begin
`${__dirname}/launch.py serve` with all five adapters and
`PYTHONDONTWRITEBYTECODE=1`; `launch.py` inserts the bundle's own `src` at
`sys.path[0]`. The bundle's `launch.py` is **byte-identical to
`packaging/launch.py`**, confirming your statement that the existing builder was
used unmodified and my launcher ownership is intact.

**A79/A80 membership, counted rather than trusted:** 6 `cadagent_*.json`
recipes, 9 Blender recipe modules, 5 `learning/` modules, `cadagent.py`, and
`CADAgent-LICENSE.txt` — all present in the payload.

**Core contract reproduced from source.** I built a server from the candidate
payload itself and listed its tools: **17**, and their names, descriptions and
`inputSchema` objects are **identical** to `evidence/core-schemas.json`. The
contract is verified by reconstruction, not by assertion.

## Finding 1 — the project-root step can fail silently, and nothing catches it

Non-blocking for the candidate; the highest-risk step in the rollout.

§3 requires the project to become `/Users/john/TokenEfficiencyEngine`. But:

- the bundle manifest's `user_config.project_root.default` is **`${HOME}/TEE`** —
  a *third* namespace, distinct from both the current and the intended one;
- Desktop preserves an existing user setting across an update, and the current
  setting is **`-a71`**.

So neither the default nor the preserved value produces the required project.
It only happens if John actively changes the folder during installation. If he
does not, the client will come up on `-a71` again, with `q14b`, `granted []`
and no `config.toml` — and **everything else will look correct**: right
artifact, right payload, right 245 tools, 17 core schemas, five learning
controls. The failure would surface only in §5.2.

Suggested mitigation for the packet, not the candidate: make §5.2 the *first*
post-install check rather than the second, so a wrong root is caught before the
feature checks bank a false sense of success.

## Finding 2 — one identity I was asked to verify is not reproducible

`contract.core_schema_sha256` = `95373e1c…2963` has no stated derivation.
`tee-payload-v1` is fully specified in protocol §3 precisely so both parties can
compute it independently; this one is not, so I cannot confirm it. I verified
the same contract by two other routes instead — the file's own hash matches the
manifest, and the schemas reproduce exactly from the candidate source — which I
consider stronger, but the asymmetry should be closed. Suggest specifying its
canonicalization in the next protocol revision, or dropping the field in favour
of the file hash plus a reconstruction check.

## What this receipt does not establish

Nothing is installed. Every A79/A80 live check in §5.3–§5.5 — the five
`learn_*` tools, the fifteen lesson topics, 245/241 virtual tools, QMAX and the
`call-paid-engine` grant — remains unverified on my side, because this client is
still serving the 252-file bundle. Per §6 those require an installed client, and
I will not report them from an isolated probe.

Rollback is genuine: the supplied `rollback/` artifact reproduces the exact
payload running today, so the pre-update state is recoverable by reinstalling it.

## Recommendation

**Proceed.** The candidate is internally consistent, matches its frozen
manifest on every recomputable identity, carries the complete A79/A80 payload
including its licence file, preserves the core contract, and ships a working
rollback. The only care needed is the project-root selection in Finding 1.
