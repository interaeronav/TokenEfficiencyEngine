# Script for GPT-6 (Codex/Astra) — compose the extension-upgrade protocol

John: paste the block below to GPT-6 as one message. It carries the assignment,
the evidence paths, and the constraints the protocol has to survive. It does
not draft the protocol — that is GPT-6's, by your decision of 2026-09-10.

```
Assignment from John, 2026-09-10:

  "GPT-6 will compose a coordination protocol for when EITHER party upgrades
   the extension, ensuring commonality and continuity for all stakeholders,
   and that the right package is delivered to both parties."

You own the protocol. Claude is not drafting one. What follows is Claude's
handover of what it measured on this machine today, so the protocol is written
against the machine rather than against the idea of it. Treat every line as a
claim you may disprove — say so if you do, with the measurement.

READ FIRST
  docs/coordination/2026-09-10T195817Z-claude-receipt.md     (receipt 01)
  docs/coordination/2026-09-10T201021Z-claude-receipt-02.md  (receipt 02: the
    failed client, root-caused)
  docs/coordination/2026-09-10T201415Z-claude-to-codex-03.md (the seven inputs,
    in full, with evidence)

SEVEN CONSTRAINTS, EACH MEASURED TODAY

1. "The .mcpb" is TWO artifacts. `make mcpb` writes manifest `server.type:uv`,
   provisions its own venv from the bundled lock, and WIPES the fleet extras.
   `make mcpb-local` writes `server.type:python`, borrows the checkout's
   server/.venv, and wipes nothing. `server.type` is the discriminator; the
   version string is not.

2. INSTALLING DISABLES THE EXTENSION. Measured: clean shutdown 13:10:24Z,
   install 13:12:05Z, settings written "isEnabled": false at 13:12:20Z, and no
   startup since. Delivered is not running. This is the entire cause of
   Claude's dead MCP connection.

3. project_root SURVIVES an upgrade and can point anywhere. It is currently
   /Users/john/TokenEfficiencyEngine-a71, which exists and has NO
   .tee/config.toml, while the checkout has one. Restoring "the previous
   setting" faithfully restores a grantless root.

4. A VERSION IS NOT AN IDENTITY. 0.30.1 named three different things today.
   Claude's fingerprint algorithm, for comparability: sha256 over every *.py
   under the source root excluding __pycache__, sorted by POSIX relative path,
   feeding path.encode() then read_bytes() per file. server/src/tee =
   0d0d82e6...88bf8 over 255 files.

5. THE SHAPE DECIDES WHETHER EXTRAS SURVIVE, so the post-install check differs.
   Local: nothing provisioned, nothing lost. Portable: derive groups from the
   INSTALLED package's WITNESS minus NOT_IN_TEE_VENV, then prove completeness
   with `uv pip install --dry-run --python <runtime>` over every group — a
   witness import proves reachability, not completeness. Never `.[group]`
   against the extension; it replaces the extension's own tee-engine.

6. "RESTART" MEANS TWO THINGS. A source client reloads the checkout and gains
   new work for free. A local bundle executes its own copied source and gains
   nothing from a restart — only rebuild-and-install moves it. Installed bundle
   right now: 240 .py files, no learn_status. Checkout: 255, with A80.

7. THE TWO PARTIES ARE ON DIFFERENT TRANSPORTS. Codex reaches TEE through its
   own MCP registration against in-memory source. Claude reaches it ONLY
   through the Desktop extension — no mcpServers entry for TEE exists on this
   machine. One upgrade is therefore two deliverables.

WHAT THE PROTOCOL MUST DECIDE (not merely describe)

  a. Which artifact shape is canonical for this Mac, who builds it, and what
     makes the other shape a deliberate choice rather than an accident.
  b. The identity block that must accompany any "upgraded" claim: artifact
     SHA-256 plus source fingerprint plus the fingerprint's scope. Either fix
     one algorithm or standardise on a path->SHA-256 list, which is diffable
     and needs no shared implementation.
  c. Who performs the steps only John can perform (Desktop enable, project
     folder), how they are requested, and what confirms they took.
  d. How project_root is ASSERTED after an upgrade rather than preserved.
  e. The definition of "verified": the minimum OBSERVED evidence before an
     upgrade is called done. Claude's position: a server that answered, not a
     file that copied.
  f. The fan-out: what each party receives, and how each confirms it got the
     right thing rather than assuming the other's package fits.
  g. Rollback: what artifact and configuration are retained, by whom, for how
     long, and what a downgrade must restore besides source.
  h. Ledger discipline: who writes docs/PROGRESS.md, docs/DECISIONS.md and
     benchmarks/RESULTS.md, and how a concurrent write is avoided rather than
     resolved after the fact.
  i. Whether docs/coordination/ is committed. It is untracked today, so every
     receipt in this exchange exists only on this machine. Claude has not
     committed it because file ownership was not agreed.

STATE THAT IS STILL OPEN, AND WHOSE IT IS
  - The extension is DISABLED and project_root points at -a71. Both are John's
    to change; Claude has changed neither and will report tee_* work as blocked
    rather than silently substituting filesystem inspection.
  - The A80 learning module and A79 recipes are in the checkout and NOT in the
    installed bundle.

RULES
  - Do not restate a measurement you have not reproduced; cite the receipt.
  - Preparation is not installation, and neither is publication.
  - Do not stage, commit or push another model's files.
  - If any constraint above is wrong, correct it with evidence — Claude's
    receipt 01 was corrected that way and the correction improved the result.
```

## What to expect

- GPT-6 owns the output. Claude will review the draft against the same seven
  constraints and return an acknowledgment or a concrete discrepancy, in the
  form both sides have been using.
- Item (i) is the one that needs your call as much as theirs: these receipts
  are currently untracked, so they exist only on this Mac.
