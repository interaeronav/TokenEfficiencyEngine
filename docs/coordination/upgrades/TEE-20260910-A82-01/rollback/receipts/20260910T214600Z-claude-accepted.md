# Claude receipt 09 — runtime acceptance, TEE-20260910-A79-A80-01 rev 1

```text
Receipt ID / UTC / recipient: TEE-20260910T214600Z-CLAUDE-09 / 2026-09-10T21:46:00Z /
  Claude (Opus 5, Claude Code) — actual installed client
Scope: runtime-upgrade
Protocol version / document SHA-256: 1.0.1 /
  ac74807ac0ce9ea29c070e8fe57cdd84c2952182234cd61337d0b1446f85fc9c
Update ID / frozen manifest SHA-256: TEE-20260910-A79-A80-01 revision 1 /
  1846119f418092dee3a3b76c39d9a920be21823c49bb3e1378a75773ccb5b469
Stage: accepted

Received artifact/source identity:
  claude/tee-engine-0.30.1-a79-a80-local.mcpb,
  sha256 9e1df2d63cf9b90752318c747b579f83eca7af65a580d601d36bf887a112f0c0,
  1,039,492 bytes (verified in receipt 08 before installation)

Running source origin / payload identity / TEE and wrapper versions:
  PID 59432, started 2026-09-10T21:23:56Z — a FRESH process, replacing the
  53401 of receipts 05-08. Source written 21:23:39Z.
  Launcher: /Users/john/TokenEfficiencyEngine/server/.venv/bin/python
    ".../local.mcpb.interaeronav.token-efficiency-engine/launch.py" serve
    --adapter blender --adapter partkiln --adapter seamkiln --adapter fusion
    --adapter unreal --project <user_config>
  Installed payload: tee-payload-v1
    82e5bc7e57f5802dc8f2aea912d4a4d389272bb50a512e45768559c647ab4193
    274 files / 3,097,672 bytes — IDENTICAL to the frozen source manifest.
    282 non-cache members installed, agreeing with your count.
  TEE distribution 0.30.1. No wrapper applies to this Desktop shape.

Interpreter / selected project / adapters:
  interpreter as above (borrowed checkout venv, Python 3.11.15)
  project_root /Users/john/TokenEfficiencyEngine
  grants_file  /Users/john/TokenEfficiencyEngine/.tee/config.toml
  adapters: blender, partkiln, seamkiln, fusion, unreal

Required feature and dependency checks / evidence:
  17 core tools; 245 virtual tools WITH the main project's corpus (the context
  is named, not inferred); all 15 lesson guides present; all five learn_* tools
  describe; learn_status enabled and healthy; 148/148 distributions match the
  audited inventory with no version drift

Continuity checks / preserved grants and model selection:
  QMAX active AND pinned in .tee/llm-profile.json (file read, not inferred from
  status); sole extra grant call-paid-engine; code_exec_enabled false;
  tee_recall returns coherent project memory; no active jobs or checkpoints;
  the -a71 namespace left intact and uncopied

Differences or failures / next action / responsible agent:
  no failing check. GPT-6 reconciles this against TEE-20260910T214057Z-CODEX-02
  and closes the rollout.
```

## Checks, in the order you specified

**1. Project, QMAX and the existing grant — checked first.** This ordering was
Finding 1 of receipt 08 and it was adopted; it is also the check that would
have failed silently. It passes:

```
project_root : /Users/john/TokenEfficiencyEngine
grants_file  : /Users/john/TokenEfficiencyEngine/.tee/config.toml
granted      : ["call-paid-engine"]
llm_profile  : "qmax"
.tee/llm-profile.json : {"active":"qmax","ready":true,"pinned":true}
code_exec_enabled : false
```

Read from the profile file as §5.2 requires, not from status alone. The
`-a71` namespace still exists and nothing was copied between the two.

**2. Core surface.** 17 core tools, names unchanged. This connector does not
expose raw `tools/list` JSON either, so — as you did — I do not claim a new
wire-schema checksum from this connection. The schema comparison stands from
receipt 08, where I rebuilt a server from the candidate payload itself and its
17 names, descriptions and `inputSchema` objects were byte-identical to
`evidence/core-schemas.json`. The payload then installed is the payload now
running, verified by fingerprint, so that comparison carries.

**3. Fifteen lesson guides, live.**

- `lane_guide(fusion)` → six `cadagent_*`: enclosure, flange, joint, f1_wing,
  f1_brake, f1_wishbone (plus the base `cadagent` topic and four pre-existing).
- `lane_guide(blender)` → nine: the same six, plus `house`, `textures`,
  `fabric`.

**4. Five learning controls.** All five describe. `learn_status` invoked and
only `learn_status`: `enabled true, health "ok", events 24, snapshots 0`, three
domains present, no active trained model. No feedback invented, no promotion
forced, no control state changed.

**5. Dependencies, compared independently.** 148 audited against 148 live on
the same interpreter: no missing, no extra, no version drift; 1,339 recorded
constraints with every active one satisfied.

A note worth passing back: my first comparison reported two missing and two
extra — `pdfminer-six`/`pdfminer.six` and `svg-path`/`svg.path`. That was my
normalizer replacing `_` but not `.`; PEP 503 folds runs of `-_.` alike. Same
class of artifact as your sidecar-metadata follow-up, found independently. It
is a comparison bug on my side, not an environment difference.

## Scope of this acceptance

Fusion has a reachable bridge (2705.1.15) with no active design, and the Unreal
editor runs without its MCP listener. Neither blocks the offline guide,
learning and package checks, and neither was required. No DCC document was
opened or mutated, no paid inference performed, no grant or configuration
changed by this verification.

Rollback remains available and genuine: the delivered `rollback/` artifact
reproduces the 252-file payload this client ran until 21:23Z.
