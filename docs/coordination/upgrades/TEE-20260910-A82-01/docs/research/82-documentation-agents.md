# 82 — Cline and Aider as documentation workers

Owner request, 2026-09-11 local / 2026-09-10 UTC: integrate both agents to
automate documentation in any connected project, including TEE. Plan of record:
`CLAUDE_A81_SCRIPT.md`. Both tools run as separate optional processes; neither
becomes a new model-router rung or a bundled TEE dependency.

## Verified upstream interfaces

Cline npm 3.0.61 and Aider PyPI 0.86.2 were inspected and installed in independent
environments. Their official licences are Apache-2.0. Cline's current package
requires Node >=22, stricter than its installation page's older 20+ wording;
Aider's published requirement is Python >=3.10,<3.13. Package/source requirements
and actual installed help outrank remembered flags.
[Cline package metadata](https://registry.npmjs.org/cline/3.0.61),
[Aider package metadata](https://pypi.org/pypi/aider-chat/0.86.2/json),
[Cline pinned source](https://github.com/cline/cline/tree/31b0dd99003a3bf4bd6a4015feb76d44e657b321),
[Aider licence](https://github.com/Aider-AI/aider/blob/v0.86.2/LICENSE.txt).

Aider supports a one-shot message file, explicit editable targets and repeated
read-only evidence arguments. Main, weak and editor model roles are all fixed
to the selected route. Git operations, automatic tests/lint, shell suggestions,
analytics and update checks are disabled for this task. File lists are context
selection, not an OS access boundary.
[Scripting](https://aider.chat/docs/scripting.html),
[OpenAI-compatible endpoints](https://aider.chat/docs/llms/openai-compat.html),
[verified arguments](https://github.com/Aider-AI/aider/blob/v0.86.2/aider/args.py).

An explicit Aider env file does not isolate all credential discovery: its main
module also searches home/project dotenv and OAuth-key locations. The integration
therefore replaces the child environment and gives it a private home, working
directory, configuration and histories. No ambient provider selection survives.
[Configuration](https://aider.chat/docs/config/aider_conf.html),
[Aider startup implementation](https://github.com/Aider-AI/aider/blob/v0.86.2/aider/main.py).

Cline supports isolated config/data directories, a working directory, explicit
provider/model, JSON events and a timeout. Its current CLI defaults to tool
auto-approval; the integration sets that choice explicitly after TEE's grant
check and denies shell commands. A config-only probe verified the private
`providers.json` shape, allowing keys to stay out of command arguments.
[CLI reference](https://docs.cline.bot/cli/cli-reference),
[pinned auth source](https://github.com/cline/cline/blob/31b0dd99003a3bf4bd6a4015feb76d44e657b321/apps/cli/src/commands/auth.ts),
[pinned option source](https://github.com/cline/cline/blob/31b0dd99003a3bf4bd6a4015feb76d44e657b321/apps/cli/src/commands/program.ts).

Cline can finish an aborted task with exit zero. Acceptance requires its final
`run_result` to say `finishReason: completed`, then validates actual document
changes. Aider can likewise return after a failed edit, so its process status
is only one input to validation. Cline setup output cannot supply the final
task's completion event.
[Cline run implementation](https://github.com/cline/cline/blob/31b0dd99003a3bf4bd6a4015feb76d44e657b321/apps/cli/src/runtime/run-agent.ts).

## TEE design and limits

The workflow is prepare → queued worker → diff → checked application. Explicit
file selection bounds prompt content and preserves uncommitted source. Hashes
bind both the prepared source state and reviewed candidate. Each agent may
change only declared documentation outputs for application; policy, credentials,
source writes and coordination records are excluded. Existing memory, model
pins, grants, Git state and learning data are outside the task workspace.

The new `run-doc-agent` capability is explicit, high risk and taint-enforced.
It does not join a baseline or existing execution grant. Current grants and
model selection are rechecked before starting queued work. Paid loopback
profiles remain paid and require `call-paid-engine`. Version 1 accepts loopback
OpenAI-compatible routes only; remote-provider integration and unified accounting
for external worker calls are not implemented. Unknown usage is reported as
unknown. No paid probe is part of validation.

The worker replaces its environment, streams bounded logs, imposes a whole-run
deadline and owns a cancellable process group. Staging and CLI tool restrictions
are not a sandbox. A deliberately detached process would require OS isolation;
the permission description makes the worker's host execution authority explicit.

The existing registry and job hooks collect execution outcomes. A valid diff
does not prove factual prose quality, so no deterministic quality label or
trained-model improvement is claimed from these checks.

## Evidence

`output/docagents/installation-and-contracts.json` records actual versions,
help hashes, every generated flag, primary sources and the Cline configuration
probe. Aider's 108 isolated distributions pass dependency checks. TEE's shared
runtime was not changed by either optional installation.

On this Mac npm's `.bin/cline` resolves directly to the native arm64 executable,
not the package's Node wrapper. A version-only probe with `PATH=/usr/bin:/bin`
and no discoverable Node succeeds. Node 22+ is an installation requirement;
the selected managed Mac executable does not need it at runtime. The actual
Claude process was unavailable during this PATH check, so no Claude environment
observation is claimed from that isolated executable probe.

`output/docagents/surface-before.json` records the A77 fake-adapter fixture:
17 core tools / 2,129 wire tokens, 204 virtual tools / 31,903 tokens if flattened.
The real configured five-adapter project has a different virtual count; these
compositions must not be conflated. The matching A81 fixture reports 17 core /
2,129 wire tokens, 209 virtual / 32,427 flattened tokens. The five new tools add
524 flattened tokens and zero always-loaded tokens; reduction is 93.4% against
this flattened fixture. All eight A77 canary checks pass.

`output/docagents/real-cli-integration.json` preserves the complete real-CLI
evidence and earlier failures. The final fixture at `20260910T221548Z` passes
with Aider in 4.835 seconds and Cline in 2.154 seconds. Both receive the explicit
fixture endpoint/key/model, edit the declared README, pass the workspace diff,
and leave the original project unchanged. Conflicting owned parent configuration
does not reach the fixture. These timings measure orchestration with deterministic
HTTP replies, not model latency or documentation quality.

Three real-startup findings corrected assumptions that unit tests had missed:

- Aider discovers the parent Git root before honoring `--no-git`; a private bare
  repository and explicit `GIT_DIR` now prevent parent dotenv/model discovery.
- Cline's JSON mode requires a positional prompt before it reads stdin. A fixed,
  non-sensitive positional instruction satisfies the guard; actual task text
  stays on stdin. The initial FIFO-only explanation was incorrect: upstream
  accepts both a file and a pipe. The runner also gained independently tested
  nonblocking stdin delivery alongside log collection.
- Cline rejects an ISO timestamp ending `+00:00` and silently discards the
  provider configuration. Millisecond timestamps ending `Z` satisfy its schema.
  The failed probe made an unauthenticated default OpenAI request, which returned
  an authentication error. No owner credentials were copied or successful model
  inference performed. Subsequent Cline fixtures enforce loopback-only egress
  with a test-only macOS restriction; production staging is still not a sandbox.

Cline automatic updating is explicitly disabled to preserve the verified worker
version. These startup facts are grounded in the installed package and its
[provider schema](https://github.com/cline/cline/blob/31b0dd99003a3bf4bd6a4015feb76d44e657b321/sdk/packages/core/src/types/provider-settings.ts),
[CLI startup](https://github.com/cline/cline/blob/31b0dd99003a3bf4bd6a4015feb76d44e657b321/apps/cli/src/main.ts),
and [update command](https://github.com/cline/cline/blob/31b0dd99003a3bf4bd6a4015feb76d44e657b321/apps/cli/src/commands/update.ts).

All 155 new tests pass with warnings treated as errors: workspace 80, backend
31, process runner 28 and integrated tools 16. They exercise cancellation,
backpressure, log bounds, grant revocation, paid and tainted execution, queued
profile changes, one-shot tasks, review checksums, source conflicts, application
rollback and late cancellation. A simulated Darwin process-group permission/
reaping sequence now receives a bounded cleanup wait; it is consistent with an
earlier intermittent failure, whose exact origin was not established.

Strict affected-suite testing also reproduced an older test fixture's unclosed
HTTP listening socket. Tracemalloc located allocation in `fixtures_llm.py`,
which called shutdown but omitted server_close. The test-only cleanup repair
does not change shipped source. Failed attempts remain in `output/docagents/`.

The final affected suite passes **256 tests in 3.68 seconds**, including all
new tests and existing trust, jobs, registry, learning integration, canonical
attachment, search budget and local-package tests, with `-W error`. Ruff passes
for every A81 runtime/test change. This is an affected-suite claim, not a fresh
full repository test run. The A81 packet separately records archive/startup
checks and later actual-client acceptance.
