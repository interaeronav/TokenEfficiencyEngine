# Codex runtime acceptance — A79/A80

```text
Receipt ID / UTC / recipient: TEE-20260910T214057Z-CODEX-02 / 2026-09-10T21:40:57Z / GPT-6 Codex, actual owner task after restart
Scope: runtime-upgrade
Protocol version / document SHA-256: 1.0.1 / ac74807ac0ce9ea29c070e8fe57cdd84c2952182234cd61337d0b1446f85fc9c
Update ID / frozen manifest SHA-256: TEE-20260910-A79-A80-01 revision 1 / 1846119f418092dee3a3b76c39d9a920be21823c49bb3e1378a75773ccb5b469
Stage: accepted (Codex only)
Received artifact/source identity: Codex source ZIP 5f0383e651b69af42ef8b34f45d7440ce5a972dc8d2d14049de37209107cec9d; normalized payload 82e5bc7e57f5802dc8f2aea912d4a4d389272bb50a512e45768559c647ab4193, 274 files, 3,097,672 bytes
Running source origin / payload identity / TEE and wrapper versions: /Users/john/TokenEfficiencyEngine/server/src/tee; current checkout matches frozen payload; TEE distribution 0.30.1, Codex wrapper 0.30.0, five wrapper files unchanged in source and client cache
Interpreter / selected project / adapters: /Users/john/TokenEfficiencyEngine/server/.venv/bin/python (3.11.15), -m tee.cli serve; project /Users/john/TokenEfficiencyEngine; blender, partkiln, seamkiln, fusion, unreal
Required feature and dependency checks / evidence: actual client has 17 expected core tools and 245 virtual tools with the project corpus; all 15 lesson guides match frozen probe responses; all five learn_* tools describe successfully; learn_status enabled and healthy; dependency metadata unchanged against completed completeness audit
Continuity checks / preserved grants and model selection: QMAX active, pinned and ready; sole extra grant call-paid-engine; code_exec_enabled false; memory recall works; prior state file categories retained, ordinary state changes recorded; current jobs/checkpoints empty as before cutover
Differences or failures / next action / responsible agent: no remaining Codex acceptance failure. Claude's installed files match but its own actual-client acceptance receipt is still required. Claude performs protocol section 4E and returns a receipt for this same frozen manifest. GPT-6 then reconciles both receipts and closes the rollout.
```

Actual tool calls establish the refreshed client's behavior. Filesystem and
metadata checks establish source, launcher, wrapper and dependency identities;
they are labelled separately from live observations. A fresh matching source
process started at 21:31:47 UTC, corroborating the restart. The connector does
not expose raw `tools/list` JSON: this receipt verifies the 17 active names and
callable schema behavior, and retains the complete frozen schema comparison
from candidate preparation and Claude's independent review. It does not claim
a new raw wire-schema checksum from this connection.

The 15 guides cover six Fusion and six Blender mechanical/F1 topics, plus the
compact modern house, textures and fabric in Blender. The five described tools
are `learn_status`, `learn_feedback`, `learn_recommend`, `learn_evaluate` and
`learn_control`. Learning reported 28 observations at the first check, zero
snapshots and no active trained model. Observations can grow with ordinary use;
this is feature acceptance, not a claim that training or promotion has occurred.
No feedback was invented, model promotion forced, paid inference performed or
owner design mutated. Fusion has no active design and Unreal has no listener;
neither condition prevents the installed guide and learning checks.

All 148 shared-environment distributions and all 10 sidecar distributions match
their audited versions and full dependency metadata. This preserves the prior
43 direct and 227 active dependency checks; no install, synchronization or new
native-kernel test was needed. The editable partkiln and seamkiln source sets
also match their frozen identities.

Both main and `-a71` state namespaces remain present; grants/profile were not
copied between them. Some memory, discovery, learning and adapter state changed
during use, so continuity is not claimed byte-identical. Private backups remain
in place. Job/checkpoint indexes are transient across restart; both observed
before and after states were empty. GPT-6 remains the single memory writer
during this cutover.

Evidence under
`/Users/john/TokenEfficiencyEngine/output/updates/TEE-20260910-A79-A80-01/acceptance/`:

- `codex-live-calls.json`: actual calls and responses.
- `codex-live-raw-numeric-guides.json`: preserved raw responses for two guides.
- `codex-live-summary.json`: compact feature results; all 15 guide hashes match.
- `20260910T213546Z-independent-continuity-audit.json`: source, installation,
  wrappers, dependencies, policy and state audit.
- `20260910T213812Z-sidecar-metadata-followup.json`: corrects only the initial
  sidecar metadata result and its dependent aggregate. Raw metadata is exactly
  equal; the initial comparison normalized only one side's names/list ordering.

The original audit is retained. Likewise, an initial JavaScript reserialization
changed integral float notation in two guide responses; preserving their raw
MCP text reproduced the frozen hashes. Neither correction changed the candidate,
environment or acceptance requirements.

## Claude's remaining action

Use the already installed candidate in the actual Claude client. Check main
project/QMAX/existing grant first, then the expected core surface, 15 guides,
five learning tools and healthy `learn_status`, dependencies and continuity.
Return a `runtime-upgrade / accepted` receipt bound to the manifest above, or
name the specific failing check. Receipt 08 already completed candidate review;
no additional acknowledgment-only review or rebuild is needed. The installed
Claude artifact is SHA-256
`9e1df2d63cf9b90752318c747b579f83eca7af65a580d601d36bf887a112f0c0`,
1,039,492 bytes; all 282 installed non-cache members match. That filesystem
evidence does not replace Claude's own live receipt.
