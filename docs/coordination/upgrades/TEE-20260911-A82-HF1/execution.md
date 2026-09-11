# Proposed HF1 execution packet

Status: candidate prepared; GPT-6 root review and release freeze pending.
Update TEE-20260911-A82-HF1 revision 1 follows protocol 1.0.1. No installation or
actual-client acceptance is represented by this packet.

## Intended change and current contract

Only `server/src/tee/docagents/backends.py` changes from accepted A82. Aider
0.86.2's authorized automatic yes also accepts help-page offers. Its Python
browser controller is now a verified system no-op, supplied only to that child.
Warnings still appear in worker logs, including credential diagnostics. Cline,
QMAX model/weak/editor roles, paid classification, approval gates and host browser
environment retain their behavior. This is separate from unfinished A83 BIM work.

Both recipients keep `/Users/john/TokenEfficiencyEngine` as their project, pinned
and ready `qmax`, `call-paid-engine` and `run-doc-agent`, disabled general code
execution, and the five adapters blender/partkiln/seamkiln/fusion/unreal. Current
filesystem evidence confirms those settings. Runtime liveness and active jobs
must be measured by GPT-6 and the actual clients immediately before cutover.

The wrapper remains 0.30.0 and runtime distribution remains 0.30.1. These labels
do not identify the upgrade; the complete payload and frozen manifest hashes do.
Core remains 17 with the complete schema SHA-256
`95373e1c2d9e171476c90c475d7046772bdaaa345990a4e3c4cf605730e32963`.
Virtual count is 261 with the main corpus and stated five adapters. No state
schema, tool descriptor or shared dependency changes are included.

## Preparation and ownership

GPT-6 assigned candidate packaging to the cabinet implementation agent for this
narrow fix; Claude retains review responsibility for its delivery. The preparer
owns only the new HF1 packet/output directories. GPT-6 alone reviews/freezes,
coordinates cutover, changes served source and writes shared ledgers. Claude
receives a local ready file and returns its own receipt; no message was sent.

The candidate starts from the verified accepted A82 source archive and independently
matches the current checkout's 293-file baseline before replacement. Complete
archive member comparisons show one changed Codex member; Claude additionally
updates only generated README build provenance. All packaging inputs, launchers,
resources and source files besides the fix retain accepted bytes.

Preparation commands already run successfully, using the existing interpreter:

```sh
PYTHONDONTWRITEBYTECODE=1 /Users/john/TokenEfficiencyEngine/server/.venv/bin/python /Users/john/TokenEfficiencyEngine/output/updates/TEE-20260911-A82-HF1/prepare.py
PYTHONDONTWRITEBYTECODE=1 /Users/john/TokenEfficiencyEngine/server/.venv/bin/python /Users/john/TokenEfficiencyEngine/output/updates/TEE-20260911-A82-HF1/probe.py
```

These scripts deliberately refuse to overwrite their first snapshot/evidence.
For read-only re-verification use the `verify.py` command in CLAUDE_READY.md.

## Review, freeze and cutover

1. GPT-6 reviews proposal, one-file patch, tests, member inventories, source delta,
   dependency inventory and isolated MCP evidence. Reconcile active jobs, source
   drift and both client registrations. Capture current memory/checkpoints/jobs
   through TEE when available; label fallback observations. Create private state
   backups under `.tee/update-backups/TEE-20260911-A82-HF1/` with directory mode
   0700 and file mode 0600, using online backup for SQLite. Do not publish these.
2. GPT-6 finalizes the draft manifest only after review; write immutable
   `release-manifest.json` and its separate `.sha256`. Deliver the same common
   packet plus recipient-specific artifact to both recipients, checking destination
   hashes. Draft files cannot substitute for this freeze.
3. Claude independently reviews the MCPB and common payload before rollout and
   records a received receipt referencing the frozen manifest. Local Python MCPB
   is the only proposed Claude shape. Never substitute the portable builder.
4. For Codex, GPT-6 verifies the whole served tree is still accepted A82, then
   preserves a private copy and replaces **only** the reviewed backends.py from
   the candidate snapshot. Verify the resulting entire payload equals HF1 before
   reconnecting the actual Codex TEE. Never unzip the whole snapshot over owner
   work, change the plugin wrapper, or import the A83 development tree.
5. Install the exact HF1 MCPB in Claude Desktop using its supported controls;
   preserve the main project and observe enabled state, then reconnect that actual
   client's TEE. Owner interaction, if needed, is one specific install/enable step,
   not another grant request. Restarting the old A82 bundle is insufficient.
6. Each actual client supplies its own runtime-upgrade receipt using the template.
   Verify source/import origin, full payload, version/launcher/interpreter/project,
   grants/QMAX/adapters, core/virtual surface, worker metadata, architecture/learning
   status and state continuity. Import the running backend and inspect its returned
   verified controller without opening a browser; record evidence source. The guarded
   CPython and actual-Aider tests already exercise URL offers without GUI or paid
   calls; do not run paid work solely for an acceptance checkbox. A subsequent
   authorized documentation job must retain warnings and no longer open help tabs.
7. GPT-6 closes only after both actual receipts match the frozen manifest. Record
   partial/failed states honestly and preserve all evidence. No GitHub publication
   or additional model invocation is part of this packet.

## Delivery and dependency preservation

Codex receives `tee-a82-hf1-codex-source-snapshot.zip`; its unchanged `tee@personal`
wrapper launches `server/.venv/bin/python -m tee.cli serve` with the declared
adapters/project. Claude receives `tee-engine-0.30.1-a82-hf1-local.mcpb`; its
`launch.py` prioritizes its own bundled `src` on that same borrowed interpreter.
Neither artifact provisions a venv, changes installed Aider/Cline, downloads
models or modifies dependencies. Run no `uv sync`, `pip install`, or exact
environment synchronization. Recheck complete inventories if external work
changes them before or during cutover.

`environment-before.json` is sanitized filesystem evidence; the accepted A82
actual receipts and the later 06:29:12Z worker permission record are separately
retained. Their observations have timestamps and are not claimed current runtime
observations. Current project learning counts can naturally grow during this work.

## Rollback and limits

The accepted A82 payload is
`ac6474bab36e1c52e6b92276a97af060f3ca37db85645a5d55b5aac0a687ea52`.
Its exact source ZIP and local MCPB are retained in the HF1 delivery rollback
folders and their original accepted delivery. The manifest lists artifact hashes.
For Codex, restore only the original backends.py after checking that the current
file is still the HF1 version and no subsequent owner edit would be lost. Verify
the full baseline payload; other source drift requires reconciliation, not forced
replacement. Claude may reinstall the exact accepted A82 MCPB and reconnect.
Rollback revives the known browser-offer behavior until HF1 is repaired; do not
restart a documentation worker merely to exercise it.

There is no state migration to reverse. Preserve both grants, QMAX, memory,
learning observations and documentation output created after the backup. Do not
restore stale project configuration/data or alter the separate `-a71` namespace.
During partial rollout, the two versions remain protocol/state compatible; record
the temporary payload difference and complete or roll back explicitly. Retain at
least the last two accepted sets, every unresolved predecessor, and each superseded
set for at least 30 days after both actual clients accept its replacement.

The no-op browser strategy is verified here on macOS/POSIX with `/usr/bin/true`.
Other hosts must meet the same fixed-path/ownership checks or Aider refuses; no
cross-platform runtime claim is made. It prevents Aider's Python browser offers,
not arbitrary GUI launch code in unrelated tools. Missing keys/model metadata
remain visible and must be handled normally. This hotfix does not complete or
deliver the broader A83 architectural/cabinet capabilities.
