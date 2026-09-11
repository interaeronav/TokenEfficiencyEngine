# Completed delivery state

Update ID: TEE-20260910-A79-A80-01, revision 1.  
Frozen release-manifest SHA-256:
`1846119f418092dee3a3b76c39d9a920be21823c49bb3e1378a75773ccb5b469`

| Stage | Claude Desktop | Codex |
|---|---|---|
| Built | Verified local MCPB, 274-file payload | Verified source snapshot and existing wrapper, same payload |
| Delivered | Downloads `TEE_A79_A80_UPDATE_20260910/claude/` | Downloads `TEE_A79_A80_UPDATE_20260910/codex/` |
| Recipient review | PASS in Claude receipt 08; both artifacts, rollback, current source and core contract independently verified | Delivered bytes reviewed here; Claude's other-party review now also complete |
| Applied / reconnected | Actual client receipt 09 confirms the installed 274-file payload, main project, QMAX and existing paid grant; all 282 installed members match | Owner restarted; actual client returns 245 tools and healthy learn_status, main project/QMAX/existing paid grant preserved |
| Accepted | Accepted in [Claude receipt 09](receipts/20260910T214600Z-claude-accepted.md) | Accepted in [Codex receipt 02](receipts/20260910T214057Z-codex-accepted.md) |

**Rollout complete:** GPT-6 reconciled both actual-client receipts against the
unchanged frozen manifest at 2026-09-10T21:48:50Z. The
[completion record](completion-20260910T214850Z.md) identifies both receipts,
final checks, evidence limits and retained rollback sets.

Preparation gates pass: exact delivered hashes/source sets, four isolated MCP
probes, all 15 lesson guides and five learning controls, 17 equal core schemas,
14 focused packaging tests and dependency completeness. A corpus-present project
has 245 virtual tools; a corpus-absent project has 241. The exact four-tool
difference is independently explained in the supplied evidence.

Claude receipt 07 is the prior activation baseline: 252-file old bundle, `-a71`,
q14b, no extra grants. The intended main namespace already has the owner's QMAX
pin and sole paid-engine grant. Keep `-a71` state; do not copy grants or merge
state. Runtime/source/setting changes are not performed by this preparation.

Both delivery folders carry rollback artifacts and instructions. Consistent
private state backups remain in ignored `.tee/update-backups/`. Preparation
changed no installed extension; the owner subsequently installed the candidate
and restarted. Verification changed no source code, dependencies, plugin
configuration or DCC designs. No commit or GitHub push was performed. Evidence:
`output/updates/TEE-20260910-A79-A80-01/`.

Claude receipt 08 is [retained unchanged](receipts/20260910T211323Z-claude-received.md).
Its two non-blocking notes are resolved in
[the post-review clarification](review-08-clarifications.md): check the selected
project first after installation, and reproduce the canonical schema checksum
with its exact JSON serialization. Reviewed artifact/manifest bytes are unchanged.

Post-install filesystem/process observations are in
`output/updates/TEE-20260910-A79-A80-01/post-install-observations.json`.
Claude's installed files and intended project selection match, and its actual
client acceptance is recorded in receipt 09. After the owner restarted, Codex's
actual connection passed all 15 guide checks and five learning descriptions,
with enabled/healthy learning. No model has been promoted; zero snapshots were
reported at acceptance. Source, wrappers and dependency metadata match the
frozen candidate. Evidence is under the same output directory's `acceptance/`;
the sidecar metadata follow-up corrects an audit normalization error while
retaining the initial record.

Both recipients have accepted. No further installation, restart, rebuild or
acknowledgment is required for this update. Retain rollback and private backups
under the standing policy; the predecessor's 30-day minimum runs through
2026-10-10T21:46:00Z. Completion does not authorize cleanup or publication.
