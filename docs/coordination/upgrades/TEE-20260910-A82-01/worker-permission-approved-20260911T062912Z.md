# Cline/Aider capability approved and applied

Owner instruction: “approve capability for cline/aider”. Applied at
2026-09-11T06:29:12Z after both A82 clients had accepted and recognized the
capability. This supersedes the earlier pending permission proposal; original
receipt and completion bytes remain historical records.

Only the main project `/Users/john/TokenEfficiencyEngine` changed:

```toml
[trust]
grants = ["call-paid-engine", "run-doc-agent"]
```

The previous 0600 configuration was backed up privately. The update preserved
every other parsed setting and retained 0600 permissions. Actual Codex
doc_status now reports execution_allowed=true, Aider 0.86.2 and Cline 3.0.61
available/version_verified, and QMAX paid/ready. tee_status confirms both grants
and code_exec_enabled=false. The shared project file is the same approved
configuration used by both clients; this note does not invent an additional
actual Claude call. No worker/model invocation was needed to enable it.

Evidence: output/updates/TEE-20260910-A82-01/acceptance/20260911T062912Z-docagent-grant.json.
No other project grant, model pin, dependency, source artifact or published file
was changed by this configuration action.
