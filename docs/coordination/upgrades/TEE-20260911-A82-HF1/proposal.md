# A82 HF1 candidate — headless Aider browser offers

Update: TEE-20260911-A82-HF1, proposed revision 1. Protocol 1.0.1.
Coordinator: GPT-6 / Codex. Preparation assigned to the cabinet implementation
agent by GPT-6; root coordinator review and freeze remain pending.

The owner's authorized documentation run repeatedly opened Aider's model-warning
help page. Aider 0.86.2 calls `InputOutput.offer_url()` for the unknown QMAX alias,
and its authorized `--yes-always` answers that offer affirmatively. Python's
`webbrowser.open()` then launches the operating system browser. This is separate
from the ongoing A83 architecture/cabinet campaign and needs only one A82 source
file changed: `tee/docagents/backends.py`.

The fix gives only the Aider child process `BROWSER=/usr/bin/true` (or verified
`/bin/true`). The controller must resolve to one of those fixed system paths,
be root-owned, executable, regular, and not group/world writable. Unsupported
hosts refuse with an actionable error. Python browser offers then succeed as a
no-op. Model and credential warnings remain visible: `--no-show-model-warnings`
is intentionally absent because Aider's same check also diagnoses missing keys.

Only the accepted A82 293-file payload is eligible as the baseline. The candidate
must differ in exactly that one existing file; all A83 BIM, drawings, cabinet
production and CNC development remain outside this delivery. No tools, schemas,
dependencies, model aliases, paid classifications or project settings change.
Keep the main project, pinned QMAX, `call-paid-engine` and the separately approved
`run-doc-agent` grant. No new permission is requested.

Preparation may create candidate artifacts, sanitized evidence and this proposed
packet only. It does not change served source, install the extension, alter
workers, run a paid model, reconnect a client, publish, or contact Claude.
GPT-6 reviews and freezes the finished packet. The other recipient reviews the
candidate identity before rollout. Both actual clients must then supply their
own matching acceptance receipts; isolated harness launches are preparation only.

Rollback retains the accepted A82 local MCPB and source ZIP plus their immutable
manifest and acceptance receipts. Restore only the changed source file after a
current-file check; never overwrite the dirty checkout, current grants, learning
data or later owner work. No data schema migration is involved.
