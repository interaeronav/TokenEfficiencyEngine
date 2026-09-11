# QMAX metadata and headless documentation fix

Owner requested use of Aider again on 14B, superseding the session stop, and
continued work on the QMAX fix. TEE q14b is now pinned; do not switch it for testing.
HF1's frozen QMAX target selection is superseded by this later owner choice and
must not be restored during deployment. HF1 bytes remain immutable historical evidence.

This new isolated candidate extends HF1 with explicitly configured Aider model
metadata. The live localhost:4000 proxy maps claude-qwen-max to
hosted_vllm/qwen3.8-max at DashScope International, but reports null limits and
zero prices. Read-only proxy configuration confirms the mapping. Those zeros
must not be promoted as paid-model prices.

Grounding: Alibaba's current qwen3.8-max model page and international pricing,
plus installed Aider 0.86.2 sources and its advanced model settings guide. No
upstream pricing/capability metadata is inferred from the alias spelling.

Plan: validate route-bound, dated metadata from the selected profile; generate
private Aider metadata/settings files and pass them explicitly; retain diagnostic
checks and the child-only no-op browser; cap requested output separately from
provider capacity. Preserve original route/model roles, paid grants and active pin.
Verify negative cases and actual Aider startup with no paid calls. Keep source
isolated until matching delivery review and both-client upgrade receipts.

A one-off 14B task uses accepted TEE staging/job/grant/pin/result handling in an
owned runner with a per-process BROWSER setting. It installs no extension or
third-party package and does not substitute for an HF1/HF2 client receipt.

Latest owner direction supersedes the earlier 14B target: TEE/QMAX, then
"might as well go back to using QMAX". Actual llm_switch succeeded and doc_status
resolves the paid claude-qwen-max profile. Preserve that current QMAX pin.
Observed current grants additionally include exec-code, run-adhoc and
run-declared-step. This preparation changes no grants. Actual tee_status reports
code_exec_enabled=true from those grants; the older filesystem helper's legacy
allow_code_exec=false field is not the effective capability.
