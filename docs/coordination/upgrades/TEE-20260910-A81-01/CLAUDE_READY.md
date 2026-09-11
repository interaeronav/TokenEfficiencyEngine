# Claude: review the Cline/Aider update, then coordinate installation

GPT-6 prepared **TEE-20260910-A81-01, revision 1** under the accepted upgrade
protocol 1.0.1. John's request is documentation automation in any connected
project, including TEE. Source work and both packages are ready for review.
This document is the handoff; it does not supply a new execution grant.

1. Read `release-manifest.json`, verify `release-manifest.sha256`, and compare
   the full `source-manifest.json` against both artifacts. Your artifact is
   `tee-engine-0.30.1-a81-local.mcpb` in the `claude` folder. The neighboring
   `codex` folder carries `tee-a81-codex-source-snapshot.zip` with the same
   279-file runtime payload. Review the new documentation workflow and evidence.
2. Return a `received / review PASS` receipt identifying the exact manifest and
   artifacts, or concrete discrepancies. Do not rebuild, install dependencies,
   edit the launcher, replace source, or modify the shared ledger during review.
3. After review, John installs that MCPB through Desktop's extension controls,
   retaining `/Users/john/TokenEfficiencyEngine` as the selected enabled project.
   Reconnect the actual Claude TEE client. Codex refreshes its existing source
   connection after verifying the current checkout still matches the manifest.
4. **Keep the current sole `call-paid-engine` grant until both refreshed
   clients recognize all five `doc_*` tools.** GPT-6 then applies exactly
   `run-doc-agent` only if John has separately approved it. Older A79/A80
   parsers reject that unknown capability. The existing QMAX pin stays intact.
5. Follow `execution.md` and the receipt template for actual-client acceptance:
   17 core tools, 250 virtual tools with the main corpus, both worker versions,
   all 15 retained guide topics, five learning tools, dependency completeness
   and project continuity. No paid model probe, DCC mutation, synthetic feedback
   or model promotion is required. `doc_status` establishes worker readiness;
   a fixture test is not evidence of actual prose quality.

The five new tools prepare selected files, run Cline/Aider as a job, review a
bounded diff, and apply its exact checksum only while the original source is
unchanged. Source writes, policy/coordination records and automatic Git commits
are excluded from application. External workers can invoke host commands:
staging and CLI restrictions are not an OS sandbox. External worker usage is
separate from TEE's internal model meter.

The real CLIs passed local deterministic provider fixtures. The affected suite
passed 256 tests with warnings treated as errors, plus eight A77 canaries;
Ruff passes. No paid inference was used. Both earlier failed probes and their
corrections are preserved in the evidence. Private project/settings backups and
the exact accepted A79/A80 rollback deliveries are retained.

Claude owns its receipt; GPT-6 owns final manifest/progress/outcome edits and
the minimal approved grant application. A build or one client's success does
not complete this rollout. Nothing in this packet requests a commit or push.
