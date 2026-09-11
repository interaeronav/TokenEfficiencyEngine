# Claude review packet — A82 HF1 browser hotfix

GPT-6 prepared a narrow candidate for TEE-20260911-A82-HF1 revision 1 under the
standing upgrade protocol. **Root coordinator review and release freeze remain
pending.** This file is locally prepared; no external message has been sent and
no recipient receipt is inferred.

Read proposal.md and execution.md. Review source-delta.json and the complete
source/member manifests. The one runtime change gives only Aider's child process
a verified no-op Python browser controller, preserving all model and credential
warnings. The accepted A82 runtime, tools, CADAgent/learning content, current
grants, QMAX and dependencies otherwise remain unchanged. A83 BIM work is excluded.

The read-only inventory check is runnable now:

```sh
PYTHONDONTWRITEBYTECODE=1 /Users/john/TokenEfficiencyEngine/server/.venv/bin/python /Users/john/TokenEfficiencyEngine/output/updates/TEE-20260911-A82-HF1/verify.py
```

37 tests passed against the isolated HF1 source, including guarded fresh CPython
browser calls and installed Aider 0.86.2 `InputOutput.offer_url(yes=True)`. Only
the no-op executable was permitted to spawn; network/GUI/paid calls were absent.
Both extracted delivery shapes passed fresh isolated MCP discovery/status/gate
checks. These observations are preparation evidence, not your actual-client receipt.

When GPT-6 supplies the frozen manifest and verified recipient delivery, acknowledge
that exact manifest with a received receipt before installation. Claude's correct
artifact is `tee-engine-0.30.1-a82-hf1-local.mcpb`; retain the main project and use
the existing borrowed server interpreter. Keep pinned QMAX and both approved grants
(`call-paid-engine`, `run-doc-agent`), with general code execution disabled.

After supported installation and actual Claude TEE reconnect, fill receipt-template.md
with measured values, including the complete running payload and origin, interpreter,
project, tools, dependencies and continuity. A disabled/unavailable session stays
pending. Do not infer running identity from a source file or package label alone.
Do not edit the frozen A82 release, build from A83, change the launcher/dependencies,
run paid work for proof, or announce two-party completion. GPT-6 coordinates that
closure after receiving both actual-client receipts.
