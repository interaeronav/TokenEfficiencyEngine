# Claude: review the Aider browser fix

GPT-6 has frozen TEE-20260911-A82-HF1 revision 1. Please review this exact
release-manifest.json and its checksum under the standing protocol 1.0.1.
The earlier CLAUDE_READY.md and draft manifest are preparation history.

Your delivery is the claude directory in
/Users/john/Downloads/TEE_AIDER_BROWSER_FIX_20260911.
The correct artifact is tee-engine-0.30.1-a82-hf1-local.mcpb.
The codex directory contains the matching source delivery, not a Desktop installer.

Review root-review.md, execution-final.md, evidence/single-file.patch and the
source/member inventories. Run VERIFY_FROZEN.py against your directory using
the existing server/.venv/bin/python; do not synchronize dependencies.
Return a received/review receipt naming the final manifest SHA before rollout.
GPT-6 will coordinate the selective Codex cutover and supported Claude installation.
Do not install or claim actual acceptance solely from this review request.

The one changed TEE file gives the Aider child a trusted no-op browser controller.
Unknown-model and missing-key warnings still print. QMAX and both approved grants
remain in force, with general code execution disabled. The Aider job that opened
the page was cancelled. Tests used the installed worker without paid calls or GUI
launches. No incomplete A83 BIM/cabinet code is included in this update.

After coordinated installation and reconnect, supply the actual-client receipt
from receipt-template.md. Preserve the main project and borrowed interpreter.
If the MCP session is unavailable, report that stage honestly. Do not infer
running source from version labels or a file found on disk.
