# A81 documentation-agent upgrade — review candidate

Update ID: **TEE-20260910-A81-01**, revision 1. Coordinator: GPT-6.
Protocol: accepted version 1.0.1. Both packages are built from the approved
payload. Final release identity is in `release-manifest.json` and its separate
checksum. Actual installation, execution permission and acceptance are pending.

The owner requested Cline and Aider integration for documentation automation
in any connected project, including TEE. Add the five progressively disclosed
tools `doc_status`, `doc_prepare`, `doc_run`, `doc_diff` and `doc_apply`, keeping
the 17 core tools, all 15 CADAgent/Blender guides and five learning tools.
Stage explicitly selected text inputs and documentation outputs; execute the
chosen worker only with the distinct `run-doc-agent` permission; review and
apply exact allowed changes with source-conflict checks and rollback copies.

The approved source contains 279 runtime/resource files, 3,166,135 bytes;
`tee-payload-v1` SHA-256 is
`3d41e182129c82f62f8a6675685098a28d38061c6c232b9f894fe2667bc50e40`.
The normalized manifest covers all runtime/resources, including untracked source. Preserve
owner edits and use an isolated snapshot; a clean checkout at HEAD is not the
candidate. No shared Python requirement is added.

GPT-6 explicitly owns both builds and this packet under protocol §2: use the
unchanged `packaging/build_local_mcpb.py` from the isolated snapshot for Claude,
and archive the same source plus verified existing Codex wrapper for Codex.
This assignment changes no source/launcher ownership. Claude remains the
other-party candidate reviewer and owns its actual installed-client receipt.
Codex supplies its own actual-client receipt. Fixture success is preparation
evidence and cannot stand in for either recipient.

The local MCPB borrows `/Users/john/TokenEfficiencyEngine/server/.venv/bin/python`
for dependencies while importing its own bundled source. The Codex plugin
continues to load the main checkout. Runtime version 0.30.1 and Codex wrapper
label 0.30.0 remain distinct from the release/source identities.

Cline 3.0.61 and Aider 0.86.2 are optional, separately installed workers under
`/Users/john/.local/share/tee/docagents/`. They are not vendored in either
artifact and are not dependencies of TEE's shared environment. Both clients on
this host discover those same installations by metadata. No model weights,
credentials, worker state or project inputs are bundled.

Preserve the current main project, QMAX pin and existing `call-paid-engine`
grant. **Do not add `run-doc-agent` before both clients have loaded A81.** The
accepted A79/A80 trust parser does not know that capability. The new grant
requires the owner's decision, which may be obtained earlier but may be
applied only after both refreshed clients identify the new runtime. Staging
and CLI policy are not an operating-system sandbox; execution can invoke host
commands. No permission is being changed by preparation.

Deliveries are under
`/Users/john/Downloads/TEE_A81_DOCAGENTS_UPDATE_20260911/{claude,codex}/`.
Both receive common manifests, protocol, execution instructions, evidence,
new usage/research/plan documents and exact accepted A79/A80 rollback artifacts.
Retain both accepted predecessor deliveries and private state. Do not commit,
publish or synchronize dependencies as part of candidate review. Follow the
execution packet for the already requested installation and client refresh.
