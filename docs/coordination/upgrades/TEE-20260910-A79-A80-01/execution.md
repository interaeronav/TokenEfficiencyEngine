# Install the CADAgent and learning updates in both TEE clients

Update: **TEE-20260910-A79-A80-01**, candidate revision 1.  
Coordinator: GPT-6 / Codex. Protocol: accepted version 1.0.1.  
Status: candidate prepared; recipient review and actual installation/acceptance
are separate steps. Receipt 07 proves only activation of the previous bundle.

Sections 2–5 describe the authorized rollout to perform after preparation.
Candidate review verifies the package; it does not itself authorize installation,
project selection or client restart. Existing owner authorization persists.
This task prepares and delivers the artifacts for review.

## What this package adds

The common 274-file TEE payload includes CADAgent integration, six advanced
Fusion/F1 lessons, nine Blender lessons including a compact modern house,
textures and fabric, and five learning controls. Learning observes real work
locally and trains only when enough suitable evidence exists; installing it
does not create a trained model. Existing execution and paid-engine policies
still apply to lesson execution. No new grants or model calls are needed to
check the installed guides and learning status.

## The two deliveries

Both folders are under `/Users/john/Downloads/TEE_A79_A80_UPDATE_20260910/`:

- `claude/tee-engine-0.30.1-a79-a80-local.mcpb` is the Claude Desktop installer.
- `codex/tee-a79-a80-codex-source-snapshot.zip` preserves the matching source,
  build inputs and existing plugin wrapper. Codex already points at the matching
  checkout, so no wrapper replacement or pip installation is needed. It needs
  a source check followed by a TEE reconnect.

Each folder carries identical release/source manifests, the accepted protocol,
this execution packet, evidence and a receipt form. Exact artifact hashes are
in `release-manifest.json`; its own checksum is in `release-manifest.sha256`.
The TEE package version remains 0.30.1, so identify this candidate by its update
ID and hashes. The Codex wrapper label remains 0.30.0 and is recorded separately;
its source/cache files and shared skill are already identical and compatible.

## 1. Claude reviews the concrete candidate

Review the frozen release manifest and compare the MCPB's complete normalized
`src/tee` payload to `source-manifest.json`. Required identity:

`82e5bc7e57f5802dc8f2aea912d4a4d389272bb50a512e45768559c647ab4193`

It covers 274 files and 3,097,672 bytes, including the six recipe JSON files and
CADAgent licence. Verify the launcher names
`/Users/john/TokenEfficiencyEngine/server/.venv/bin/python` and imports the
bundle's own `src/tee`. Verify the skill and required resources. Review both
target deliveries, validation limits and rollback below; return a `received`
receipt referencing this candidate's manifest checksum, with review outcome.
An internal Codex audit does not substitute for this other-party review.

GPT-6 explicitly reassigned this candidate build to itself in `proposal.md`,
using the unchanged existing local builder in an isolated snapshot. Claude's
launcher/source ownership remains unchanged. Both artifact payloads were
compared exactly; neither installer files nor owner settings were altered.

## 2. Establish a quiet cutover

Before applying the reviewed candidate, re-read actual client status, outstanding
jobs and project state. Drain active work before reconnecting. The initial Codex
baseline had no active jobs or checkpoints; Claude supplies its own fresh check.
Job/checkpoint indexes and scene ID maps are in memory and reset on reconnect;
do not promise old IDs survive. Read a fresh scene summary when work resumes.

Private backups are at:
`/Users/john/TokenEfficiencyEngine/.tee/update-backups/TEE-20260910-A79-A80-01/`.
They include both project namespaces and Claude's settings. SQLite databases
were backed up through SQLite's online backup API, not by copying a lone WAL
database file. Refresh backups before cutover if state has changed, under a new
timestamped subdirectory; do not overwrite the initial backup. Never publish
these private files. Retain at least the protocol's rollback minimum.

GPT-6 is the single project-memory writer during cutover. `tee_remember` is not
a concurrent merge mechanism; other agents supply proposed notes in receipts.
Do not copy stale cached memory over newer disk state. Learning-event growth
does not invalidate a frozen source manifest and is expected during real work.

## 3. Apply the Claude Desktop package

After Claude's candidate review passes, John opens the exact `.mcpb` from the
`claude/` delivery folder in Desktop and applies it to the existing TEE
extension. In the extension settings, select the intended project:

**`/Users/john/TokenEfficiencyEngine`**, with the extension enabled.

This is an explicit change from the currently selected `TokenEfficiencyEngine-a71`
namespace to the existing main project. It follows the owner's TEE/QMAX choice;
the prior namespace stays intact and no state/grants are merged or copied.
The bundle's generic README says to keep the project setting; this packet names
the specific transition required for this candidate. If John intends to keep
`-a71` instead, record that project choice before applying and amend the target
contract; do not copy main-project grants to make that different root pass.

Desktop's controls perform the installation/settings operation. Reconnect the
actual Claude TEE session afterwards and inspect the effective settings. Do not
rewrite settings behind Desktop's controls or treat a successful isolated probe
as an installed-client receipt. No dependency sync or grant edit is required.

## 4. Refresh Codex

Recompute the checkout's complete `server/src/tee` fingerprint immediately before
reconnect and compare it to the frozen source manifest. It matched at preparation.
If source changed, stop this candidate and issue a revision; do not overwrite,
reset, clean or stash owner work to recreate it. The source archive is retained
for review/recovery, not an instruction to unpack it over the checkout.

The existing enabled `tee@personal` wrapper already launches that checkout with
the five adapters and the intended main project. Keep those matching wrapper
files. Reconnect TEE through Codex's client controls after the quiet cutover.
No `.mcpb` installation or Python package/environment replacement is needed for
this source-backed client. Record a new connection/process identity; matching
files on disk alone do not establish that an older process has imported them.

## 5. Both actual clients verify and accept

Each recipient measures and records:

1. This update ID, frozen release-manifest hash, received artifact hash and the
   complete installed/source payload hash. Identify actual launcher, source
   origin, process/connection freshness and TEE versus wrapper versions.
2. `tee_status`: intended main project, QMAX, existing `call-paid-engine` grant
   and `code_exec_enabled: false`. Read the profile file to verify the pin is
   preserved; status alone reports selection. Check the main memory/state
   namespace; retain the separate `-a71` data untouched. No new authorization
   or paid inference is needed for this read-only verification.
3. List the 17 core tools and compare their schemas with the supplied canonical
   core schema file. Describe all five tools: `learn_status`, `learn_feedback`,
   `learn_recommend`, `learn_evaluate`, `learn_control`. Invoke only `learn_status`
   for this smoke; no invented feedback, promotion or control-state change.
4. Through `tee_call(name="lane_guide", args=...)`, inspect all six Fusion
   `cadagent_*` lesson topics and the nine Blender topics: the same six plus
   `house`, `textures`, `fabric`. Check licence/resource membership. These guide
   reads work without changing a DCC document or granting code execution.
5. Recheck dependency constraints and actual interpreter/sidecar origins against
   the supplied inventories; record differences and required binary/feature
   limits. Confirm post-reconnect state compatibility and no unexpected reset.

With the five adapters and the main project's existing knowledge-base corpus,
the measured candidate has **245 virtual tools**. An isolated project without
that corpus has **241**: it omits only `kb_search`, `kb_read`, `kb_facts` and
`kb_propose`. `kb_status` remains. Both contexts were tested. Name the context;
do not infer a five-tool upgrade solely from arithmetic. The five named learning
controls and complete payload identity are the decisive A80 checks.

Record adapter observations with the tool and timestamp. Receipt 07 found a
reachable Fusion 2705.1.15 bridge with no active design, and a running Unreal
editor without its MCP listener. Those are not blockers for these offline guide,
learning and package checks. Opening designs or starting Unreal's MCP service
is outside this candidate's required acceptance steps.

Return a Markdown receipt with `scope: runtime-upgrade`, exact frozen manifest
hash and stage `accepted` only after your actual client passes. GPT-6 closes
the update only after both matching receipts. Report any failed/partial stage
and its specific next action; receipt 07 and these isolated probes cannot close it.

## Validation already completed

- Exact source/resource equality across checkout, frozen snapshot, Desktop
  archive and Codex source archive; shared skill and all expected resources match.
- Four fresh isolated MCP probes: both deliveries with and without the existing
  corpus, 17 identical core schemas, all five learning controls and all 15 guides.
- 14 focused packaging tests pass. Dependency audit passes 43 direct and 227
  active constraints; all 148 borrowed-venv packages and 10 sidecar packages are
  compatible. No environment repair is indicated.
- Prior source evidence remains applicable because its payload is unchanged:
  536 affected tests passed after correcting one stale test from the initial
  full run (2,547 passes, one failure). No new all-pass full-suite claim. Native
  lesson evidence is reused; no owner designs were modified by packaging.

GPU/MONAI/PySide6 optional groups remain absent. External solver/bridge readiness
and design quality were not broadly re-tested. A successful guide replay is not
proof of autonomous model skill; learning starts or continues from actual local
observations, with no synthetic training seed.

## Rollback and partial rollout

The reconstructed previous Desktop bundle is in this delivery's `rollback/`
folder with its exact artifact hash in the release manifest. It preserves the
installed 252-file payload and wrapper; its archive bytes are newly reconstructed,
not the original distributor's bytes. Reinstall through Desktop only when a
rollback is chosen. Keep the borrowed venv, sidecar and editable headless kernels
unchanged; this update neither provisions nor changes dependencies.

Choose the project root deliberately on rollback. The old runtime ignores A80's
additive schema-1 learning database; leave that database and subsequent user
work intact. Restore private configuration only when it is still appropriate;
never overwrite newer project data wholesale or revive stale PID files.

The frozen Codex snapshot preserves current disk source, not its old in-memory
modules. Exact reconstruction of that older process is unavailable. If Codex's
new connection fails, diagnose from preserved evidence and prepare a reviewed
compatible recovery target rather than blindly replacing dirty source or
pointing its wrapper at the old Desktop bundle. This recovery limitation is
explicit; a transient partial rollout cannot be reported as both clients accepted.

Keep the preceding bundle and all unresolved predecessor state, at least the
two most recent accepted sets when available, and at least 30 days after both
clients accept a replacement. No automatic cleanup, commit or GitHub push is
part of this packet. GPT-6 owns shared PROGRESS/DECISIONS/RESULTS edits.
