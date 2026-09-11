# A81 execution packet — candidate review and rollout

Update: **TEE-20260910-A81-01**, revision 1. GPT-6 coordinates both deliveries
under accepted upgrade protocol 1.0.1. The final source, real CLI mechanics and
256 affected tests pass. Both artifacts are built. Verify the frozen manifest
and candidate evidence before proceeding; actual-client acceptance is pending.

## 1. Verify the frozen common candidate

GPT-6 completed the CLI/provider checks and affected tests and approved the
complete payload SHA-256. The helper in
`output/updates/TEE-20260910-A81-01/prepare_packet.py` produced both artifacts
from an isolated snapshot. It requires `build --approved-payload <exact SHA-256>`,
rejects drift, and does not install anything or modify grants. Do not rebuild a
delivered candidate in place. The unchanged local builder is
`packaging/build_local_mcpb.py`; no `uv sync`, pip installation or `uv run --exact`
belongs in this build. Ordinary `uv run` is inexact by default, but the explicit
existing interpreter avoids synchronization entirely.

Verify identical full `tee-payload-v1` manifests for checkout, frozen snapshot,
Claude archive and Codex archive. Include every runtime/resource file; ignore
only `__pycache__`, `.pyc`, `.pyo` and `.DS_Store`. Sort records by normalized
`tee/` path; encode `{algorithm,files}` with sorted JSON keys, ASCII escaping,
compact separators, UTF-8 and no trailing newline. Each record contains path,
byte length and SHA-256. A package-version string is not the source identity.

The expected context is 17 core tools, 250 virtual tools with the main corpus,
or 246 without it, serving blender/partkiln/seamkiln/fusion/unreal. Measure those
numbers against the candidate evidence; the smaller benchmark fixture has a different adapter
composition. Preserve the accepted core schemas, old 15 lesson guides, five
learning controls and shared skill. Verify all five new `doc_*` tools and
document new resource/environment requirements and measurement limits.

The final release manifest binds these checks and artifact bytes. Claude reviews the
concrete MCPB and both delivery identities before Desktop installation. A
`received` candidate-review receipt is separate from runtime acceptance.

## 2. Record a quiet before state

Both actual clients report their selected project, grants, QMAX selection,
profile-file pin/readiness, jobs and checkpoints. Both accepted A79/A80 clients
selected `/Users/john/TokenEfficiencyEngine`; keep that project. Preserve the
separate `TokenEfficiencyEngine-a71` namespace without copying or merging it.
Finish active work before any reconnect. Job/checkpoint indexes and scene IDs
can reset; do not promise that old transient IDs survive.

Record current shared dependency and sidecar inventories and worker metadata.
Draft evidence rechecked 148 shared and 10 sidecar distributions against the
accepted complete metadata audit; no drift was found. Refresh at cutover if
anything has changed. The optional workers are separate private installations:

- Cline: `/Users/john/.local/share/tee/docagents/cline-3.0.61/node_modules/.bin/cline`.
- Aider: `/Users/john/.local/share/tee/docagents/aider-0.86.2/bin/aider`.

Private project/settings backups were prepared before delivery; their sanitized
inventory is included in the evidence. Refresh them immediately before cutover
if user work, configuration or project state has changed.
Use timestamped new copies and SQLite online backup for WAL databases; do not
copy one live database file, overwrite the earlier backup, publish private state
or restore PID files. Draft metadata is not a replacement for a rollback backup.
GPT-6 is the sole project-memory writer during cutover.

## 3. Install and reconnect while keeping existing grants

After the frozen candidate passes Claude's review, the owner uses Desktop's
existing extension controls to install the exact local MCPB and keep the main
project selected/enabled. Reconnect the actual Claude TEE client. Its launcher
must borrow the existing shared interpreter while importing the candidate's
own installed `src/tee`; do not provision a replacement environment.

For Codex, verify the complete current checkout payload still matches the
frozen source manifest immediately before reconnect. Preserve the existing
matching `tee@personal` source/cache wrapper. The source ZIP is a verified
snapshot and recovery artifact; do not unpack it over dirty owner work. Refresh
the actual source connection. If client controls do not reload this task,
save a checkpoint before the owner fully quits and reopens the hosting app;
do not kill unidentified processes or invent an internal RPC workaround.

If source drifts, stop the candidate and ask GPT-6 for a reviewed revision or
recovery plan; do not reset, clean, stash or discard owner work. Neither disk
equality nor a newly spawned fixture proves the actual client refreshed.

## 4. Apply only the separately approved new execution grant

The existing main grant remains `call-paid-engine`. This packet proposes adding
exactly `run-doc-agent`; it proposes no other capability and no model change.
The owner decides whether to authorize autonomous documentation workers,
which can invoke host commands. Staging is not an OS sandbox. QMAX is still
paid through its configured route; the new capability is not a spending cap.

**Order is mandatory:** first verify BOTH actual clients recognize A81's
`doc_*` tools and the new capability. Only then may GPT-6 add the new grant,
if the owner has approved it. Do not tell the owner to paste it into the main
configuration while either A79/A80 process remains in use: that parser rejects
unknown capabilities and can make side-effecting calls fail closed.

The minimal change, for review only, is the existing `[trust]` grant list from
`["call-paid-engine"]` to `["call-paid-engine", "run-doc-agent"]`. Re-read the
actual current configuration at application time and preserve any other
subsequent owner changes. Do not rewrite the file from an old template. This
packet does not perform or authorize that change.

If the decision is pending or declined, record execution as unavailable with
its exact reason. Preparation/review remain useful, but do not call autonomous
worker execution enabled. A new grant does not enable Python escape hatches,
change the QMAX pin or override paid/taint checks.

## 5. Obtain both actual-client receipts

Each recipient checks protocol §4E against the same frozen manifest:

1. Update/revision, artifact and payload identities, installed source origin,
   actual launcher/interpreter, connection freshness, runtime and wrapper labels.
2. Main project, QMAX profile-file pin/readiness, existing paid grant, exact
   separately decided new-grant state and `code_exec_enabled: false`. Preserve
   both state namespaces; compare memory/jobs/checkpoints/learning with before.
3. Expected 17 core names/schema behavior and five new `doc_*` descriptions.
   Call `doc_status` to verify both expected CLI versions and permission/profile
   readiness. No paid inference is required to establish readiness. Preserve
   the connector's raw-schema observation limit if it cannot expose tools/list.
4. All 15 prior Fusion/Blender guide topics and all five learning controls;
   invoke `learn_status` without invented feedback or forced promotion. Learning
   event counts are shared dynamic project totals; record actual call times.
5. Complete shared/sidecar dependencies and optional worker paths/metadata. Use
   an explicitly owned, tiny documentation fixture for preparation/diff/apply
   checks if required; never use owner policy or real project files as fixtures.
   A deterministic fake endpoint tests CLI mechanics, not model skill. No paid
   probe, DCC mutation or forced local-model switch is an acceptance requirement.

Return `runtime-upgrade / accepted` only for the checks actually completed;
name pending permission/install steps and failures precisely. GPT-6 reconciles
both receipts before closing the rollout. A build, fixture run, old accepted
receipt or one client's success does not close this update.

## Rollback and retention

The exact accepted A79/A80 Desktop MCPB and Codex source ZIP are the rollback
artifacts, with their accepted hashes; no reconstruction is needed. Retain the
old packet/receipts and both old deliveries. The new snapshot does not grant
permission to overwrite owner source.

If rollback is chosen, quiesce documentation jobs first. If `run-doc-agent` was
added, reconcile that one capability under the owner's rollback decision before
starting old clients, while the new parser can still read the configuration.
Do not remove the existing paid grant or replace the entire configuration.
Reinstall the accepted prior MCPB through Desktop. For Codex, GPT-6 prepares a
reviewed source recovery target from the exact prior ZIP while preserving all
later dirty source and project changes; no automatic checkout overwrite.

Preserve generated/applied documentation, .tee/docagents runs/backups, learning
schema-1 observations and newer memory. The prior runtime can leave new docagent
state unused. Optional CLI installations are outside both runtime artifacts;
do not uninstall them or alter shared dependencies as an automatic rollback.

Keep at least the two most recent accepted sets and unresolved predecessor
state, and retain the predecessor at least 30 days after both recipients accept
its replacement. No cleanup, commit, push or GitHub publication is authorized
by this packet. GPT-6 owns the shared coordination/progress ledger updates.
