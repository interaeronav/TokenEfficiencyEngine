# TEE shared upgrade protocol

Protocol version: 1.0.1 · Owner decision: 2026-09-10  
Coordinator and protocol author: GPT-6 / Codex  
Applies when Claude or Codex proposes an extension or TEE runtime upgrade.

John's decision is that GPT-6 composes the coordination protocol whenever either
party upgrades, preserving commonality and continuity for all stakeholders and
delivering the appropriate package to both parties. This is the standing rule.
Both agents must read it before preparing an upgrade; each upgrade gets a short
GPT-6-authored execution packet following this protocol.

Revision 1.0.1 clarifies receipt format and scope following Claude receipt 03.
The [accepted version 1.0](coordination/protocols/upgrade-protocol-v1.0.md) and
its original Downloads delivery remain unchanged. Acceptance of 1.0 does not
claim acceptance of this revision; the coordination index records that separately.

## 1. Responsibilities and meaning of completion

| Stakeholder | Responsibility |
|---|---|
| John | Owns the intended project, deployment scope and any new permissions or disruptive choices. Existing authorization persists. |
| GPT-6 / Codex | Coordinates the update, resolves evidence discrepancies, freezes the common source identity, assigns files, prepares the execution packet and records completion. |
| Initiating agent | Reports the proposed change before altering shared source, packages, launchers or dependencies. Supplies the source and validation evidence whether the initiator is Claude or Codex. |
| Claude | Reviews its delivery, performs its assigned build/client work and returns a receipt from the actual Claude client. |
| Codex | Reviews its delivery, performs its assigned source/plugin/client work and returns a receipt from the actual Codex client. |
| GitHub repository | Stores approved source and review history when publication is in scope. GitHub availability is not proof either local client was updated. |

Either agent can initiate; neither silently updates the other. GPT-6 owns the
coordination packet and shared ledger edits. Implementers own explicitly assigned
files. The agents can work independently on disjoint files and write their own
receipts. If GPT-6 built a deliverable, the other agent reviews its source and
package identity before rollout; self-reporting alone does not close the update.

**Complete** means both recipients received the correct delivery and both actual
clients accepted the intended runtime, source/resources and project contract.
“Built,” “delivered,” “installed,” “reconnected” and “accepted” are separate states.
A fresh harness launch is useful preparation evidence, not a recipient's receipt.
A disabled or unavailable client remains pending. An owner-approved exception is
recorded as a partial rollout with that exception, never as two-party acceptance.

## 2. One approved source, two appropriate deliveries

Commonality means the same approved TEE source and resource payload, a compatible
tool/API contract, and each client's explicitly recorded project/runtime choices.
It does not mean identical outer package bytes, identical wrapper version labels,
or copying private project configuration between clients or projects.

| Recipient / installation shape | Correct delivery | What loads the new code |
|---|---|---|
| Codex's current `tee@personal` source plugin | Verified source snapshot in its declared checkout, plus the compatible `.codex-plugin/plugin.json` / `.mcp.json` wrapper when those change; include exact source receipt and launch instructions. | Reconnect that client's TEE server after the intended snapshot is in place. The thin plugin contains no TEE source itself. |
| Claude Desktop local bundle, preferred for this Mac | A newly built local `.mcpb` containing the same TEE payload, `launch.py`, its manifest and required resources; record the borrowed interpreter. | Install that exact artifact, inspect enabled/settings state, then reconnect the actual client. Restarting an older copied-source bundle does not update it. |
| Claude Desktop portable bundle, only when selected | Portable `.mcpb`, its dependency plan/inventory and complete restoration/verification instructions for its own runtime. | Provision/install, reconcile approved dependencies, reconnect and verify. It is a different deployment shape. |
| Another configured client or host | An explicitly described compatible wrapper/source/package using the same source manifest, with its own environment and acceptance record. | Follow its measured installation mechanism; do not assume it understands `.mcpb`. |

Actual current shapes were inspected on 2026-09-10: Codex's wrapper is under
`/Users/john/plugins/tee` and launches the source venv; Claude Desktop has a local
Python bundle that executes its own `src/tee`. Re-inspect at each update.
Record wrapper version, TEE distribution version, source identity and artifact
identity separately. A wrapper label of 0.30.0 and runtime label of 0.30.1 is a
discrepancy to explain, not proof of which source is loaded.

**Default packaging decision for this Mac:** use the local Python MCPB for
Claude Desktop. Claude is the default builder/custodian of that artifact and
its launcher; GPT-6 prepares the Codex source/plugin delivery and checks their
common payload. GPT-6 may reassign either build explicitly in the packet when
availability requires it. A portable bundle requires a named target/reason and
its own dependency/rollback plan before preparation; it is never substituted
because it has the same filename or version. Both current integrations use
stdio MCP; their deployment formats/source origins differ.

For a source client, a mutable checkout is not a release artifact. Freeze its
agreed payload long enough to verify and deliver, preserving uncommitted owner
work. Record untracked dependencies too. A clean separate worktree at HEAD will
omit them. If other work continues, use an agreed isolated snapshot and a
separately reviewed launch target; never discard or automatically stash owner
changes to manufacture a clean tree. Any runtime payload edit after freeze
invalidates that candidate and requires a new manifest revision.

## 3. Identity, records and continuity

Use one directory per update:

```text
docs/coordination/upgrades/<update-id>/
    proposal.md
    release-manifest.json
    release-manifest.sha256
    source-manifest.json
    environment-before.json
    execution.md
    receipts/<UTC>-<recipient>-<stage>.md
    outcome.md
```

Build outputs live under `output/updates/<update-id>/`. Give each recipient its
own delivery folder containing its compatible artifacts, a copy of the same
release/source manifests, concise installation instructions and a receipt form.
Never overwrite a previously delivered artifact under the same update identity.
Record the exact destination and SHA-256 after delivery, not just the build path.
Keep the previous usable artifacts and configuration restoration instructions.

**Retention decision:** GPT-6 maintains the shared rollback inventory; each
recipient keeps its preceding receipt and the exact prior delivery location.
Retain at least the two most recent accepted delivery sets and every unresolved
rollout's predecessor. Retain a superseded set for at least 30 days after both
clients accept its replacement, and longer while any continuity issue remains.
Private configuration/state backups belong under the ignored
`.tee/update-backups/<update-id>/`, with restricted local access; large artifacts
remain under `output/updates/`. These are minimum retention rules, not an
automatic cleanup job or permission to delete the owner's work. If dependencies
will change, prepare a usable restoration source for their recorded versions,
not merely a list that cannot be reinstalled. Never roll back project data over
newer user changes.

**Version-control decision:** yes, the protocol, per-update plans, sanitized
manifests, receipts and outcomes under `docs/coordination/` are intended as
version-controlled project records. GPT-6 reviews and stages only the explicitly
agreed paths in the next authorized coordination/upgrade commit. Strip secrets,
private payloads and unnecessary personal details from publication copies; keep
configuration backups, project/learning databases, raw logs and build artifacts
local unless separately approved. Do not report GitHub durability until the
specific commit is pushed and checked. Existing untracked receipts remain local
until that happens; adopting this policy is not itself a commit/push request.

**Shared ledger decision:** GPT-6 is the sole editor for PROGRESS and DECISIONS
during an update and owns the final RESULTS append when measurements change.
Another model supplies a proposed entry in its own receipt. Reassignment is
explicit and temporary, and the recipient acknowledges it before editing.
Before each write, re-read the file; if it changed since review, reconcile first.
No response or silence is not a file-ownership transfer. Individual timestamped
receipts remain separate immutable files so reviewers need no shared write lock.

The release manifest must identify:

- Protocol version, unique update ID/revision, UTC time, initiator, GPT-6
  coordinator, intended change, existing authorization and assigned files.
- Git repository, branch, commit, dirty/untracked source coverage, TEE package
  version, complete normalized source/resource manifest and its SHA-256.
- Each target's actual registration, shape, wrapper version, interpreter and
  Python/OS/architecture, resolved launch command, source origin, selected lanes,
  intended project root, required features and expected core-tool contract.
- Every delivery artifact's path, byte length and SHA-256, its member manifest,
  resource completeness evidence, test commands/results and relevant omissions.
- Actual dependency inventories, required extras and constraints for the intended
  package/version, shared-environment relationships, and state-schema compatibility.
- Per-target previous identity, rollback artifacts and checks; an explicit policy
  for preserving new user work if state migration or a partial rollout occurs.

The frozen release manifest is immutable. Put its own checksum in the separate
`.sha256` file, avoiding a self-referential hash. Its artifact hashes refer to
final bytes. Put source identity inside artifacts when supported; do not embed
the final artifact hash in the artifact itself. Store later approvals, stages
and receipts separately, all referencing the frozen manifest checksum. A
correction creates a new revision; recipients must explicitly accept that one.

### Common source manifest algorithm

Manifest the **entire shipped TEE runtime tree**, including Python, recipes,
JSON, licences and other required data, not only `*.py`. Normalize source roots
(`server/src/tee` versus bundled `src/tee`) to the common prefix `tee/`.
Exclude only declared non-runtime cache files (`__pycache__`, `.pyc`, `.pyo`,
`.DS_Store`); list the exclusions. Never include project `.tee/` state, secrets,
credentials, model weights or unrelated design/output files.

For every regular payload file, record `path`, `bytes`, and lowercase SHA-256 of
the bytes. Sort records by normalized POSIX path. Paths must be relative, unique
and contained in the payload; external symlinks or unexpected archive members
need explicit resolution, not silent inclusion. Compute the source fingerprint
as SHA-256 of UTF-8 JSON serialized with `sort_keys=True`, `ensure_ascii=True`,
`separators=(",", ":")`, **no trailing newline**, over:

```json
{"algorithm":"tee-payload-v1","files":[{"path":"tee/example.py","bytes":0,"sha256":"<64 lowercase hex characters>"}]}
```

That example is a schema illustration, not a valid file record. Store build and
wrapper inputs such as pyproject, launchers, manifests and dependency locks in
a separate manifest with their own paths/hashes. Compare the normalized TEE
payload from the source candidate, Claude artifact and Codex source delivery
for complete set equality and byte equality. Compare wrapper/build inputs
against each shape's explicit expectations, not against another shape.

Shared usage instructions are also part of the delivery contract. Record the
canonical `skills/tee-usage/SKILL.md` hash and verify the copy each client uses.
Intentional client-specific instructions may differ, but their differences must
be reviewed; an old skill must not silently teach one recipient an obsolete
workflow. Include relevant release notes and the same protocol revision in both
delivery packets.

## 4. Execute an upgrade in these stages

### A. Propose and reconcile

The initiator writes a compact proposal. GPT-6 reads current PROGRESS, both
receipts, active campaign plans, source state and actual client registrations.
Record existing jobs and file ownership. Inspect/fetch without merging by
surprise. Resolve divergent/untracked source before building. Identify whether
an upgrade request already covers installation; do not ask again for existing
authorization. New permissions, another project or a disruptive change need
their own explicit scope. This protocol alone is not permission to activate a
disabled integration or publish a release.

### B. Capture continuity and prepare

Read actual launcher/interpreter/project/enabled state for each recipient.
Capture compact TEE memory, scene stamps, checkpoints and jobs when available;
label filesystem fallback evidence as such. Record grants and explicit model
selection without exporting secrets. Preserve prior configuration privately.
Account for outstanding tasks and project state before any restart or migration.

Run appropriate source tests and isolated functional checks. Name skipped/live
checks honestly. When schemas change, measure core/virtual surfaces with the
adapter composition stated. Retain failures that explain a correction. Do not
rerun every live design merely to produce another update receipt.

### C. Build and verify both deliveries

Build both target deliveries from the same frozen candidate. For this Mac,
`make -C server mcpb-local` is the existing local Desktop builder. Inspect the
actual artifact's type, command and content; its filename/version is insufficient.
A portable `zip -qr` rebuild can retain deleted members in an existing archive:
use a fresh output and verify the complete member set.

For Codex, verify the complete source snapshot that its wrapper will import.
If a wrapper change is necessary, prepare the appropriate Codex plugin format;
do not offer the Desktop `.mcpb` as a Codex installer. Preserve unrelated MCP
entries and derive the launcher from the measured interpreter and selected root.

Both targets need payload equality, expected resources, package/launcher checks
and isolated start/discovery evidence before delivery. Freeze the release
manifest only after final artifact hashes and evidence exist. Present concrete
deliverables, changes, limitations and rollback before any still-required owner
approval; complete all independent preparation first.

### D. Deliver, apply and reconnect each target

Copy the appropriate artifact/source packet to **both recipients** and verify
the destination checksums. Obtain a receipt acknowledging the exact manifest.
Then perform each authorized installation/source update and client reconnect.
Observe enabled state after installation: one measured installation left Claude
disabled, but that does not prove every installation disables it. If enabling
is outside the update's scope, keep it pending and say so.

**Desktop hands-on step:** when the authorized rollout needs an operation only
the owner can perform, GPT-6 gives John one concise action request naming the
verified artifact, intended project folder and expected enabled state. John
uses Desktop's extension controls to install/enable and save the chosen project;
Claude then obtains the live receipt. An explicitly authorized automation may
perform supported steps, but do not rewrite disabled settings to bypass a UI
review or assume a screenshot/file copy is the resulting server state. This
is a request for the necessary action, not another request for already-granted
paid-engine permission. Record pending owner steps instead of declaring success.

Validate the intended project; do not blindly restore a stale root or switch
roots merely to gain grants. Missing `.tee/config.toml` means default
`read+baseline`, not a blanket scene-write prohibition. Choosing a project also
chooses its memory/state namespace. Verify the capabilities actually needed.

### E. Verify through both actual clients

Each client returns its own receipt for:

1. Exact update/manifest/artifact identity received, installed source origin and
   payload verification, actual launcher/interpreter and runtime package version.
2. Intended project, preserved grants/model pin, selected adapters and expected
   tool names/schema behavior. The current core contract is 17 tools; a deliberate
   future change must be part of the approved manifest. Virtual counts name their
   adapter composition and dynamic connections.
3. Dependency presence **and completeness** in the real runtime, plus one relevant
   installed-feature check. For A79/A80, inspect expected guide topics and discover
   the five `learn_*` tools with `learn_status`; do not invent feedback or force
   model promotion to create proof. Live DCC mutation checks use owned scratch work.
4. Continuity of project memory, jobs/checkpoints and learning/state compatibility,
   with any intentional transition recorded. Compare against the before record.
5. Acceptance or a concrete failure, evidence paths and next responsible agent.

An offline DCC does not by itself mean the extension failed. A receiver's
unavailable MCP session is not satisfied by the coordinator's successful probe.
If the two sources differ, stop calling the upgrade common even if both display
the same version. GPT-6 reconciles the mismatch and issues a new candidate or
rollback plan; it does not silently change a receipt or widen an acceptance gate.

### F. Close or recover

GPT-6 marks complete only after both live acceptance receipts match the frozen
manifest and required checks. Update PROGRESS, short TEE memory, and the current
coordination index. Publish to GitHub only when authorized and after reviewing
the exact source/artifact scope; do not commit owner state or arbitrary outputs.

If only one target succeeds, keep an explicit partial state. Use the recorded
compatibility assessment to determine whether it can temporarily remain newer.
Do not automatically downgrade working source or overwrite new user work.
Rollback covers the code, wrappers, configuration and any changed **shared**
dependencies; preserve post-update project/learning data and check schema
compatibility. If reversal would lose data or interrupt unrelated work, report
the concrete choice to the owner after completing safe independent diagnosis.

## 5. Dependency and permission rules learned on this machine

- The local bundle borrows an environment that Codex also uses. Any dependency
  repair in that interpreter affects both targets and requires both to recheck.
  A local source-only install does not provision dependencies, but its borrowed
  environment can still change independently.
- Ordinary `uv run` is inexact on measured uv 0.12.5 and retains extraneous
  packages; required versions may still change. `uv sync` is exact by default;
  `uv run --exact` opts into exactness. Prefer the prepared interpreter or
  `uv run --no-sync` for these launchers. Recheck version-specific behavior when
  tools change; do not reuse the disproved outage attribution.
- For a portable install, derive base fleet groups from the **installed**
  `WITNESS` minus `NOT_IN_TEE_VENV`, preserve other required optional groups,
  and verify full dependency completeness in the actual interpreter. Use the
  intended exact TEE version and approved constraints; never accidentally
  resolve a different TEE release during restoration. `.[group]` can replace
  the installed package and is not the restoration form. Do not blindly install
  every optional feature or move CadQuery out of its sidecar.
- John already authorized QMAX and `call-paid-engine` for
  `/Users/john/TokenEfficiencyEngine`. Preserve that decision without asking
  again. It is not authorization to copy grants elsewhere, broaden to
  `workstation+paid`, enable code execution or audition a paid model. A grant
  cannot be manufactured by the learner or the installer.

## 6. First application and receipt format

Delivery of **this protocol** changes documentation only. Before version 1.0
was delivered, Claude's extension was observed disabled and pointing to
`TokenEfficiencyEngine-a71`. Later settings/runtime observations belong in
timestamped receipts; the earlier snapshot is not a declaration of current
state. In receipt 03, Claude disclosed an owner-authorized enable setting;
activation remains unverified until Desktop applies it and the actual Claude
client responds. Neither protocol acceptance nor that setting proves delivery
of the A79/A80 runtime. GPT-6 will compose the concrete execution packet when
either side initiates the next upgrade.

The canonical receipt is a Markdown (`.md`) file containing the filled text form
below and optional evidence links or prose. Release, source and environment
manifests remain JSON. A JSON receipt export is optional and must identify its
canonical Markdown receipt; it is not a second authority. Existing Markdown
receipts remain valid historical records and are not rewritten to add fields.

For `protocol-review`, identify the protocol version and document SHA-256;
acceptance covers that standing text only. There is no frozen runtime manifest,
and unobserved runtime fields must say so. For `runtime-upgrade`, identify the
update ID and frozen release-manifest SHA-256; `accepted` requires the actual
client checks in §4E. Protocol review cannot satisfy runtime acceptance.

Each recipient uses this compact form, filled with measurements rather than
copied expectations:

```text
Receipt ID / UTC / recipient:
Scope: protocol-review | runtime-upgrade
Protocol version / document SHA-256:
Update ID / frozen manifest SHA-256:
Stage: received | installed | reconnected | accepted | failed
Received artifact/source identity:
Running source origin / payload identity / TEE and wrapper versions:
Interpreter / selected project / adapters:
Required feature and dependency checks / evidence:
Continuity checks / preserved grants and model selection:
Differences or failures / next action / responsible agent:
```

A partial or missing receipt remains partial or missing. No scheduled daemon,
automatic client toggle, new MCP tool or paid-model call is introduced by this
protocol. Its trigger is the upgrade workflow, read by both agents through
AGENTS.md, CLAUDE.md and the execution script.
