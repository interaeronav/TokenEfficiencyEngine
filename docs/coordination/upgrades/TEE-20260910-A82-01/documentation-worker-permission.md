# Documentation worker permission — pending owner decision

Both A82 clients now recognize `run-doc-agent`. Installation acceptance leaves
execution unavailable, as the frozen packet permits. No permission was changed.

The prepared change, if John approves, is only for
`/Users/john/TokenEfficiencyEngine/.tee/config.toml`:

```toml
[trust]
grants = ["call-paid-engine", "run-doc-agent"]
```

GPT-6 must re-read the then-current configuration, preserve all other settings
and any intervening owner edits, and add exactly the missing capability. Keep
QMAX pinned and general code execution disabled. The grant refreshes on the next
TEE call; verify `doc_status.execution_allowed` through the actual client.

This permits the installed Cline/Aider workers to run documentation jobs. These
workers can execute host commands; their staging directory is not an operating-
system sandbox. Paid-model calls continue to use the existing paid grant and
selected QMAX profile. Applying this permission does not authorize a new model
selection, publication, automatic commits, other project grants, or a paid test.

Protocol 1.0.1 sections 4A and 5, and A82 execution.md's permission section,
require this distinct owner decision. Package installation or a receipt does
not supply it. This note records the concrete proposed change for approval.
