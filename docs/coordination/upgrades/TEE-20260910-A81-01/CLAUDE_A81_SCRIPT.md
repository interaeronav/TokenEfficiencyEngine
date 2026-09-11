# A81 — Cline and Aider documentation automation

Owner request: integrate Cline and Aider into TEE to automate documentation.
Confirmed scope: **any connected project, including TEE**. Preserve the main
project's QMAX pin and existing paid-engine grant. Research 82 records verified
interfaces. This script amends the master plan before implementation.

## P0 — grounded interfaces and baseline

- [x] Read current progress, upgrade protocol and execution/trust/engine seams.
- [x] Close the preceding A79/A80 update with both actual-client receipts.
- [x] Verify official Cline/Aider CLI interfaces and isolated installed versions;
  neither executable was initially on PATH. Keep their environments separate
  from TEE's shared runtime. Do not download model weights or change endpoints.
- [x] Capture the current 17-core surface and relevant benchmark baseline.

## P1 — bounded documentation workflow

- [x] Add a project-owned `docagents` package with compact virtual tools for
  status, preparation, execution, diff review and application; zero new core
  tools. Cline/Aider are agent workers, not new model-router rungs.
- [x] Copy explicitly selected text inputs and documentation targets into an
  isolated staging directory. Bound files/bytes, reject traversal/symlinks and
  exclude credentials, source writes, Git metadata, policy/agent instructions
  and upgrade-coordination records from application. A staging directory is
  not an OS sandbox; state that execution can invoke host commands.
- [x] Resolve the current TEE profile without changing its pin. Configure each
  worker explicitly and isolate its state/environment; never silently use its
  default cloud provider. Preserve paid classification even for loopback routes.
- [x] Use a distinct, explicit `run-doc-agent` capability for autonomous worker
  execution, with taint enforcement and current-grant checks before spawn.
  Preparation/diff/application use the appropriate existing capabilities. Do
  not add grants to the owner's project as part of implementation.
- [x] Run long tasks through jobs with bounded logs, wall limits and cancellation
  of the owned process group. Validate both CLI completion and resulting files;
  a process exiting zero alone does not certify documentation quality.
- [x] Apply only reviewed allowed outputs with source-fingerprint conflict
  checks and rollback copies. Never auto-commit, push or edit owner policy.
  Integrate existing learning hooks as execution evidence, not quality labels.

## P2 — prove behavior and document use

- [x] Test exact CLI invocations and refusal paths, environment isolation,
  provider/pin preservation, paid/taint/grant checks, output bounds, cancellation,
  path constraints, partial failure and concurrent source changes. Use owned
  fixtures; do not run paid inference as a validation probe.
- [x] Verify both real installed CLI help/configuration surfaces and run them
  against an owned deterministic OpenAI protocol fixture. This tests transport,
  configuration and actual edits, not inference quality. No real paid or local
  model inference is part of validation; do not replace QMAX to make a test pass.
- [x] Run affected checks and measure the actual served surface/token change.
  Write usage docs, research evidence, decisions and progress.

## P3 — coordinate delivery

- [ ] Compose a new GPT-6 update packet, freeze the final runtime/resources and
  build matching Claude MCPB and Codex source deliveries with continuity and
  rollback. Retain the accepted A79/A80 set.
- [ ] Deliver concrete artifacts and execution-permission instructions. Any
  required owner UI/permission action is the last step after preparation.
- [ ] Obtain both actual-client acceptance receipts before calling A81 rollout
  complete. A prepared or tested integration is not an installed-client claim.

## Measured amendments

The real CLI fixture found parent Git discovery before Aider honors `--no-git`,
Cline's positional-prompt guard before stdin, and Cline's requirement for a
provider timestamp ending `Z`. Each was corrected and exercised with the real
installed executable. The invalid timestamp caused one unauthenticated default
OpenAI request returning an authentication error; no owner key or successful
inference was involved. Final Cline fixtures restrict egress to loopback.

Process tests additionally reproduced a macOS permission/reaping race during
group cleanup; bounded reaping handles that sequence. Strict affected-suite
validation found an older fake HTTP server fixture missing `server_close()`;
repairing the fixture preserves the warning gate. Evidence is recorded in
research 82 and `output/docagents/`.

Final affected suite: **256 passed** with warnings treated as errors, including
155 new tests and existing trust/job/registry/learning/disclosure/package checks.
Ruff passes. The eight existing A77 benchmark canaries also pass. Candidate
archive probes and actual-client acceptance remain distinct P3 work below the
source validation boundary.
