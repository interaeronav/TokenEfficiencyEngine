# A82 execution packet

Update **TEE-20260910-A82-01**, revision 1; coordinator GPT-6. Follow protocol
1.0.1 and the frozen manifest. Preparation is authorized. Runtime installation,
owner-only UI actions, new permission and actual-client receipts remain pending
while the owner sleeps. Do not wake him or message another client externally.

## Verify one complete candidate

Check `release-manifest.sha256`, all common file hashes, each archive hash and
its full member inventory **before extracting or executing any launcher**.
Reject duplicate, absolute, traversal, backslash and symlink members. Compare
the normalized `tee-payload-v1` manifest across the current checkout, isolated
snapshot and both archive payloads. It is canonical sorted-key compact ASCII
JSON `{algorithm,files}` with records sorted by normalized `tee/` path, each
containing path, byte length and SHA-256; UTF-8, no trailing newline. Exclude
only `__pycache__`, `.pyc`, `.pyo` and `.DS_Store`.

The approved helper snapshots complete runtime/resources and explicit build/docs
inputs, verifies the accepted Codex source/cache wrapper, and uses the unchanged
`packaging/build_local_mcpb.py`. No environment synchronization or dependency
installation belongs in this update. If any identity differs, GPT-6 prepares a
reviewed new revision; never repair an immutable candidate in place.

Expected actual configuration serves blender, partkiln, seamkiln, fusion and
unreal: 17 unchanged core tools; 261 virtual tools with the main corpus, 257
without it. The smaller canonical benchmark fixture is 220, a different adapter
composition. Preserve 15 prior lesson guides and five learning controls; verify
the five `doc_*` and eleven `ak_*` descriptors, the packaged GUI HTML and exact
optional-worker paths. Candidate probes are explicitly isolated fixtures.

## Preserve continuity before cutover

Both actual clients report their project, source/launcher/interpreter, QMAX
profile-file pin/readiness, current grants, memory, learning, jobs and checkpoints.
Use the main project and preserve the separate `TokenEfficiencyEngine-a71`
namespace. Finish active work before reconnecting; old transient scene/job IDs
need not survive. GPT-6 is sole shared-memory writer during cutover.

Recheck shared dependencies (148 distributions), mechanical sidecar (10),
editable kernel inventories and optional workers against retained evidence.
Create fresh private backups at the quiet cutover boundary if state changed
since preparation. Use SQLite online backup for WAL databases, private file
modes and new timestamps. Do not copy a lone live database, publish private
state, overwrite previous backups or restore PID files. Preserve architecture
documents, generated deliverables, documentation runs/backups and learning.

## Install only when the owner resumes

Claude reviews the exact candidate first and can return a `received` review
receipt. The owner installs the exact local MCPB through Desktop controls,
keeping the main project enabled, then reconnects the actual Claude session.
The launcher borrows the existing shared Python interpreter and must import
its own installed `src/tee` payload.

For Codex, verify the current checkout still matches the frozen complete source
immediately before refreshing the source connection. Keep the matching existing
`tee@personal` source/cache wrapper. The ZIP is a snapshot/recovery artifact;
do not unpack over dirty work. If UI refresh cannot reload this task, preserve
continuity for an owner app restart. Do not kill unidentified processes or use
an invented internal RPC. Disk equality and fresh fixtures do not prove either
actual client has loaded the candidate.

## Keep permission separate

Preserve the existing `call-paid-engine` grant. `run-doc-agent` remains pending
the owner's explicit decision. It permits workers that can invoke host commands;
staging is not an operating-system sandbox. Only after BOTH new clients recognize
the capability, and only if approved, may GPT-6 add exactly `run-doc-agent` to the
then-current configuration while preserving subsequent owner edits. Older
A79/A80 parsers reject that name. No code-execution, model or QMAX change follows.

If permission is pending/declined, record documentation execution unavailable
with its reason. Preparation and review still work. No paid inference is needed
for readiness or installation acceptance.

## Obtain both actual receipts

Each recipient records protocol §4E evidence against the same frozen manifest:

1. Update/revision, artifact and full payload identity, fresh actual connection,
   running source, launcher/interpreter, runtime and wrapper labels.
2. Main project, QMAX pin/readiness, exact grant state, code execution disabled,
   and continuity relative to the quiet before state.
3. Expected core and virtual context, all new descriptors and preserved lessons/
   learning. Preserve any raw-schema observation limit the actual connector has.
4. `doc_status` reports expected workers and permission/profile readiness;
   `ak_status` reports architecture readiness without starting a GUI. A disposable
   explicit house fixture may exercise edit/undo/export/check if needed. Do not
   edit an owner's real design or start a DCC/model for acceptance.
5. Dependency/resource completeness, GUI resource identity, learning health,
   and honest coverage: missing worldwide law remains `not_verified`; IFC/IDS
   and geometry do not certify a building. No live Unreal or CNC claim follows
   from the isolated tests.

Return `runtime-upgrade / accepted` only for observed complete checks. GPT-6
reconciles both actual receipts before closing rollout. The owner's new worker
permission decision is recorded independently and is never inferred from sleep.

## Rollback and retention

Retain exact accepted A79/A80 artifacts/receipts and A81's immutable held packet.
If rollback is chosen, quiesce jobs and reconcile any newly added `run-doc-agent`
grant under that owner decision before starting older parsers; preserve the paid
grant and all other configuration. Reinstall accepted MCPB through Desktop.
For Codex, GPT-6 prepares a reviewed recovery target from the exact prior snapshot,
preserving later dirty source and state; no automatic checkout overwrite.

New architecture/docagent state and exported artifacts remain owned data even
when an older runtime cannot use them. Do not delete them or uninstall optional
workers as an automatic rollback. Retain at least two accepted sets and unresolved
predecessors; keep the predecessor at least 30 days after both recipients accept
its replacement. No cleanup, commit, push or GitHub publication is authorized.
