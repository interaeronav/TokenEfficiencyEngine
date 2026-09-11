# HF2 coordinated execution packet

Update TEE-20260911-A82-HF2, revision 1; protocol 1.0.1. GPT-6 coordinates and
builds both deliverables in isolation; Claude independently reviews before rollout.
This supersedes the pending HF1 installation proposal and includes its browser fix.
Preserve the immutable HF1 artifacts as history. Neither HF1 nor HF2 is installed.

Existing owner authorization covers the Aider/QMAX repair and paid worker use.
GPT-6 owns the two changed documentation runtime files, the new metadata module,
the configuration addition and shared ledger. Claude owns its review and actual
Desktop client installation/receipt. The unchanged launcher/builder remain under
Claude custody; this packet uses their exact accepted bytes. No new grant is needed.

1. Review release-manifest.json, source-delta.json, evidence/runtime.patch,
   qmax-model-grounding.md and the proposed configuration. Run VERIFY_FROZEN.py
   against your recipient directory with the existing server/.venv/bin/python.
   Claude returns a received/review receipt referencing the full frozen checksum.
   This is the pre-rollout independent review required by protocol section 1.
2. After that review, GPT-6 refreshes actual continuity and private backups. Check
   that the whole served source still matches accepted A82 and that no worker is
   active. Preserve live scene state/checkpoints before reconnect. If other work
   changed the baseline, reconcile it under a new manifest; do not overwrite it.
3. Apply only tee/docagents/backends.py, tee/docagents/tools.py and the new
   tee/docagents/model_metadata.py from the verified Codex archive. Do not unpack
   the whole source ZIP over owner work. Verify the entire resulting payload.
4. Recheck the actual qmax proxy mapping and dated provider evidence. Append the
   exact configuration/qmax-docagent-metadata.toml table to the main project's
   .tee/config.toml only if absent and its parent still names claude-qwen-max,
   localhost:4000/v1 and paid=true. If present/different, reconcile before editing.
   Preserve every existing byte outside that table, file mode and the current pin,
   grants and credentials. Parse the completed TOML and validate with aider_metadata.
   Retain its prior bytes privately; never copy the full config into this delivery.
5. Reconnect actual Codex. Install the exact Claude local MCPB using supported
   Desktop controls, then reconnect actual Claude. Both use the main project
   /Users/john/TokenEfficiencyEngine and borrowed server/.venv/bin/python.
   A restart of the old Desktop bundle does not load new source.
6. Each actual client reports source origin and complete payload, interpreter,
   project, core/virtual tools, current QMAX pin/grants, metadata-table identity,
   memory/learning/scene continuity, active jobs and installation state. Do a
   metadata-only recognition check first; the supplied tests require no paid
   request. A small separately recorded staged document run can verify generation
   after cutover; review its diff before applying. Do not revive cancelled jobs.
7. GPT-6 closes only with matching actual-client receipts. Harnesses and package
   checks are preparation evidence. Claude absence remains pending honestly.

Current observed contract: qmax pinned; grants call-paid-engine, exec-code,
run-adhoc, run-declared-step and run-doc-agent. Actual tee_status says code
execution enabled. environment-before.json's legacy allow_code_exec=false is
only a raw older config field; grants determine effective permission. The fix
changes none of those permissions. Reconcile later owner changes at cutover.

Rollback: use the exact accepted A82 artifacts in each rollback directory. Restore
only the two reviewed source files, remove the new module only if its hash still
matches HF2, and remove only the newly added metadata table if it remains unchanged.
Reinstall the prior Claude bundle and reconnect both clients. Preserve newer owner
edits, current model choice, grants, learning and document state. No dependency or
state-schema migration is included. Never restore stale PID files or databases
over newer work. Retain both accepted predecessors per protocol section 3.

This package adds no A83 architecture/BIM/cabinet implementation. That campaign
remains in its isolated development tree, with its own incomplete acceptance matrix.
