# A82 — next Claude action after Codex restart

John has resumed and restarted GPT. This note supersedes the sleeping-owner
timing in the earlier handoff; the frozen release and protocol are unchanged.

**Codex has accepted its actual A82 runtime. Claude review, installation and
actual-client acceptance remain pending.** The installed Claude payload still
matches accepted A79/A80 on disk; restarting that old bundle will not install A82.

Update: TEE-20260910-A82-01 revision 1.
Frozen manifest SHA-256:
`961adc95f587a287e97ce09c5daeac51748398ad76e67a1df824acb7b7df6339`.
Common payload: `ac6474bab36e1c52e6b92276a97af060f3ca37db85645a5d55b5aac0a687ea52`,
293 files. Both deliveries and all 127 common files were reverified unchanged.

## Claude-ready instructions

1. Read the protocol and exact release/execution packet in
   `/Users/john/Downloads/TEE_A82_ARCHITECTURE_UPDATE_20260911/claude/`.
   Review the candidate and return a `received` receipt bound to its frozen
   manifest, recording any failure. Review remains necessary: Codex's owner-led
   restart occurred before Claude reviewed this candidate.
2. After review passes, install through Claude Desktop's extension controls:
   `/Users/john/Downloads/TEE_A82_ARCHITECTURE_UPDATE_20260911/claude/tee-engine-0.30.1-a82-local.mcpb`.
   Its SHA-256 is `98f5116fe1c51b62062571cdf81d4f0039d3bc34815aafcf7c951c0768c3c3e2`
   and size is 1,138,535 bytes. Keep the extension enabled and select
   `/Users/john/TokenEfficiencyEngine`. Preserve the separate a71 namespace.
3. Reconnect the actual Claude client. Verify its own installed source, borrowed
   interpreter, 17 core / 261 virtual tools with the main corpus, 15 preserved
   lessons, five learning / five documentation / eleven architecture descriptors,
   and healthy ak_status, doc_status and learn_status. Compare complete resource
   and dependency identities to the frozen evidence. Do not substitute a harness
   or filesystem check for actual-client observations.
4. Preserve QMAX and the existing sole call-paid-engine grant. run-doc-agent is
   still pending a separate owner decision after both new clients recognize it.
   Record execution unavailable meanwhile. No worker/model invocation is needed
   to accept installation. Do not change shared dependencies or the dirty source.
5. Save your own timestamped runtime-upgrade receipt, with accepted only after
   the required observed checks pass, and return its path to John/GPT-6. GPT-6
   owns the shared ledger and will reconcile both receipts before closure.

Codex's receipt is
`/Users/john/TokenEfficiencyEngine/docs/coordination/upgrades/TEE-20260910-A82-01/receipts/20260911T060123Z-codex-accepted.md`.
It records 17 core / 261 virtual, all 15 guide hashes and 21 descriptor matches,
healthy learning, ready QMAX and workers, unchanged 148/10 dependency metadata,
and a fresh private continuity backup. Architecture's worldwide rule framework
does not establish verified worldwide law; live Unreal and professional
approval limits remain unchanged. No source rebuild or new release revision is
needed if identities remain equal. Preserve all frozen deliveries and rollback.

This file is prepared for John's local handoff. It has not been sent to Claude.
