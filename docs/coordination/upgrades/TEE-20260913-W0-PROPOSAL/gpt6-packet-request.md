# GPT-6 — compose the execution packet for the W0 candidate

**Revision 8, 2026-09-13.** Rewritten, not patched: revisions 1 and 2
accumulated conflicting identities and two disproved explanations. This
document describes **one** candidate. The correction history lives in
`claude-packet-review-corrections.md`; nothing historical is repeated here as
current.

Revision 8 carries the round-eight corrections: process identity is now decided
from **real argument vectors** on both platforms rather than a flattened command
string that had lost the argument boundaries, a successful stop retires its
earlier failure everywhere status reads, and §4's response-size table is
**re-measured** — the previous one was hand-written, not measured, and is
withdrawn.

**GPT-6 reviewed this revision, closed both findings and the measurement
correction, and has since ACCEPTED this candidate for coordinated packet
preparation** — the correction review is closed and no further correction round,
rebuild or repeat suite is assigned for it. Three prose corrections it required are folded in
below — the withdrawn ratio claim, the over-broad cwd claim, and `stop_recovered`
described as what it actually is. **That acceptance is for packet preparation
only**: it is not an installation, not a release approval, and not a receipt from
either actual client.

Revision 4 carries a P1 product fix: `tee_purge` was deleting `tee-*`
directories by NAME, with no proof of ownership or that the owner had exited,
and the test suite exercised it against the real machine. See receipt §4d — the
payload identity below moves accordingly.

Prepared by Claude, initiating agent, for the owner to hand to GPT-6 / Codex.
Repository: `/Users/john/TokenEfficiencyEngine`.
Protocol: `docs/upgrade-coordination-protocol.md`, version 1.0.1.

## 1. Identity — the one candidate

| | value |
|---|---|
| **candidate commit** | `e6f95663274bcd74c754bf2aa1028ef4650bbca4` |
| **runtime payload fingerprint** | `df974f783145a49c435355e702339cb4836c14e0be44646bd86b288a960a90b7` |
| runtime files | 325 |
| accepted A84 baseline | `0e172448d05b14a0a714bbecd4c79b0ba24cc9caa48bf9dd5db57f9680fb252f`, 324 files |
| delta vs accepted | **0 removed, 1 added, 19 changed** |
| declared version | `0.30.1` (`server/pyproject.toml:4`) |
| branch | `claude/token-efficiency-engine-5jv1dj`, **not pushed** |

`e6f9566` is the commit everything below was **tested at**, superseding
`36453a0`. Commits after it in this directory are documentation only and do not
touch the payload — verified by recomputing the fingerprint after the docs
commit.

The one addition is `tee/kernel/workdirs.py`, the ownership and liveness check
the purge fix needs. The **nineteen** changed files are: eleven from the
reviewed W0 and architecture work plus the owner-instructed formatting
correction; six from the purge fix — `tee/purge.py` and the five producers that
now mark the scratch directory they own (`adapters/blender`, `adapters/fusion`,
`adapters/godot`, `adapters/freecad`, `assets/library`); and **two from the
wind-tunnel process-lifecycle fix**, `windtunnel/runner.py` and
`windtunnel/tools.py`, which revision 6 omitted from this explanation. Round
eight changed those same two files again; the file *count* is unchanged and the
fingerprint is not.

## 2. Current results, each bound to the source tested

Every row is a `git archive` of **`e6f95663274bcd74c754bf2aa1028ef4650bbca4`** into a clean directory,
`server/.venv` symlinked to the prepared repository venv **without provisioning
it**, `PYTHONPATH` pinned to that export's `server/src`, and that venv's
explicit interpreter. The export is not inside a git checkout — verified with
`git rev-parse --show-toplevel`, which reports "not a git repository" — so no
enclosing HEAD can be attributed to it.

| check | command | result |
|---|---|---|
| targeted | `pytest` over the **six named files** below | **119 passed, 22 skipped** — log `scratchpad/targeted_e6f9566.log` |
| canonical suite | `pytest -q` (project defaults) | **3,070 passed**, 45 skipped, 141 deselected, **0 failed** — 212.85 s, log `scratchpad/suite_e6f9566.log` |
| lint | `ruff check src tests ../benchmarks` | **clean** |
| format | `ruff format --check src tests` | **clean**, 516 files |
| real workdirs deleted | namespace diffed before/after the suite | **0** |
| verification build | §3 | succeeded |

The **six named files** in the targeted row — the wildcard form quoted in
revision 6 was not the selection that produced the result, it collects 286:

```
tests/test_windtunnel_runner.py  tests/test_structural.py
tests/test_windtunnel_tools.py   tests/test_structural_runner_limits.py
tests/test_purge.py              tests/test_structural_shutdown.py
```

**Each skip belongs to the command that produced it**, not to a carried-forward
label:

- the **22** in the focused row are explicit real-engine gates in the recovered
  structural suites (`openseespy`, `oofem`) — **native solver behaviour is
  unverified here**, and 54 checks are not structural engineering validation;
- the canonical suite's skips include those same 22 plus the suite's ordinary
  environment-gated skips;
- the **self-containment** regression skips only in an export, because it
  compares tracked against untracked files and a `git archive` has no `.git`.
  It appears in the corrections/canary/mcpb set, **not** in the focused
  purge+structural row above.

The suite command is the project default. **Never substitute `-m "not dcc"`** —
it replaces `addopts` rather than narrowing it. The real exclusion set is
`-m 'not dcc and not ml and not network and not llm and not cfd and not fdm'`
(`server/pyproject.toml:235`).

**Both halves of `make lint` pass on this candidate — the accepted runtime does
not.** `docagents/model_metadata.py` failed `ruff format --check` in the shipped
product; the eleventh delta is that fix.

## 3. Verification artifact

Built from the **isolated candidate** with the permanent interpreter supplied
explicitly. Source location and runtime interpreter are independent inputs, so
this needs no return to the shared checkout — which would risk including
unreviewed source.

```sh
/Users/john/TokenEfficiencyEngine/server/.venv/bin/python \
  packaging/build_local_mcpb.py \
  --python /Users/john/TokenEfficiencyEngine/server/.venv/bin/python \
  --out-dir ./verification-artifacts --build-dir ./verification-build
```

| | value |
|---|---|
| artifact | `tee-engine-0.30.1-local.mcpb` |
| absolute path | `/private/tmp/claude-501/-Users-john-TokenEfficiencyEngine/66bb34fa-ea68-4af7-9b78-9a82a2737fc4/scratchpad/cand-e6f9566/verification-artifacts/tee-engine-0.30.1-local.mcpb` |
| bytes | 1,327,902 |
| sha256 | `59de72c626590aa326309d386eff3230478c2cca119c7cb7312c17bec8e0cbb6` |
| manifest `command` | `/Users/john/TokenEfficiencyEngine/server/.venv/bin/python` |
| temporary export path in launch command | **none** |

Payload comparison, which is the point rather than the ZIP write:

- artifact runtime **== candidate source**, complete set and byte equality,
  325 files, fingerprint `df974f78…a90b7`;
- artifact vs accepted: 0 removed, 1 added, 19 changed.

Resources, usage skill and wrapper inputs checked separately against the
installed copies: `icon.png`, `LICENSE`, `docs/small-model-workflows.md`,
`skills/tee-usage/SKILL.md` and `launch.py` are **identical to installed**.
`README.md` differs by design — the builder generates it per build, embedding
version, interpreter and commit.

**This is a preparation artifact.** Not installed, not accepted, not a delivery.
Its hash is recorded so a packet can bind to it or supersede it.

## 4. What changes for a client

- **The always-loaded contract is unchanged**: 17 tools, 2,129 wire tokens.
- **Chores can actually run.** The previous default profile pointed at `:8080`,
  which does not answer, so every chore degraded to its deterministic path.
- **`response_format` is negotiated per endpoint.** The two local backends are
  inverted on it — MLX accepts and ignores it, vLLM refuses with HTTP 400 unless
  `llguidance` is present — so TEE could not reach the better backend at all.
- **Six new error codes** may reach a client, and they come from **two different
  comparisons** — the earlier revisions said "four" without naming which:
  - against **`73a76e1^`**, the pre-W0 baseline, the whole W0 change adds
    `llm_no_answer`, `vlm_no_answer`, `llm_widening_refused` and
    `llm_widening_unproven`;
  - against **`f20c9ee`**, the start of this correction sequence, the wind-tunnel
    fixes add `wt_stop_failed` and `wt_identity_unknown`.

  Six in total against the pre-W0 baseline; two of them are new since the
  correction sequence began.
- **Reasoning never reaches a client.** Read from whichever field the backend
  uses (`reasoning` on MLX, `reasoning_content` on vLLM), recorded, stripped.
- **Thinking is off for every chore.** `THINKING_ALLOWED` ships empty.

### Tool composition, and why two numbers are not interchangeable

The candidate registers **232 virtual tools** under the benchmark's configured
composition: `cli.attach_all` with a single `FakeAdapter`. That is what
`run_surface_scenario` and the A77 canary measure, and what `RESULTS.md`
records.

Codex's live `tee_status` reported **273 progressive tools**. That is a
different configuration — a real client with its own adapters and connections.
**The two are not comparable and neither validates the other.** Any count in the
packet must name its composition.

RESULTS.md's current-corpus table already recorded 232; its prose block, which
the canary reads, still said 199. Both now agree. Nothing was removed to reach
it — the number moved **up**, because restoring the accepted runtime brought
back 35 registered tools the earlier candidate had lost.

### Tool-response contract

Relative to `f20c9ee`, the later corrections introduce the **`unverified`** state
and surface **`stop_failed`** for an in-process run. Stale-cancelled
reconciliation and the associated note were already present in `f20c9ee` and are
preserved. `wt_case action=stop` may raise **`wt_stop_failed`** or
**`wt_identity_unknown`**. No new tool, nothing removed, the 17 always-loaded
schemas unchanged.

Two things this section previously got wrong, both narrowing the claim:

- **`identity`, `pid` and `note` are not new** — `f20c9ee` already emitted all
  three — **and neither is the stale-cancelled reconciliation.** That landed in
  the round-five fix, which is *at* `f20c9ee`, not after it. Only the
  `unverified` state and the in-process `stop_failed` are new.
- **`stop_recovered` is recovery metadata, not a `wt_status` response field.** An
  in-process retry records recovery in memory and the case store; an orphan retry
  also retires prior failure flags in `run.json` and `progress.json`. These paths
  should not be described as writing identical records. `_Lane.status` does not
  read the field, and no runtime change is proposed to make it do so.

**Revision 7's table was withdrawn: it was hand-written, not measured.** Its
"before" side was composed by hand and omitted a note and a pid that the
baseline already emitted, which is the whole of its "+30 / +53". Re-measured by
invoking the real `_Lane.status` from an isolated export of each named commit,
with identical controlled fixtures, fixed ids, no MCP envelope and no native
solver, scored with TEE's own `estimate_tokens` over the payload dict serialized
as compact JSON:

| response | `f20c9ee` | `36453a0` | round 8 | delta |
|---|---:|---:|---:|---:|
| normal running run | 30 | 30 | 30 | **0** |
| failed in-process stop | 21 | 26 | 26 | **+5** |
| unknown identity | 49 | 50 | 50 | **+1** |
| stale cancelled / live orphan | 61 | 74 | 74 | **+13** |

This reproduces the coordinator's independent measurement exactly. The ordinary
path is unchanged and the cost falls only where the old answer was wrong; the
table above is the comparison, and it needs no adjective from me. **Still a real
price for truthful information, not a free one** — a bounded response is not an
unchanged one.

## 5. Machine-local state, which no package carries

- `.tee/llm-profile.json` switched `q14b` → `q27b-think`; prior value preserved
  at `.tee/llm-profile.json.bak-w0`.
- Two weight sets deleted: `Qwen2.5-Coder-14B-Instruct-4bit` (7.7 GB) and
  `Qwen3.5-9B-MLX-4bit` (5.6 GB) — `docs/PROGRESS.md:18013`. The 27B on `:8087`
  is intact. Re-downloading the 14B is the only costly rollback step.
- `.tee/config.toml` untouched.

### Dependency behaviour — the local shape, correctly

| installed `server.type` | behaviour |
|---|---|
| `uv` (portable, `make mcpb`) | provisions a venv, `uv sync`, **deletes every extra** |
| `python` (local, `make mcpb-local`) — **this Mac** | borrows `/Users/john/TokenEfficiencyEngine/server/.venv`, puts its own `src` first on `sys.path`, provisions nothing, runs no `uv sync`, **deletes nothing** |

`packaging/build_local_mcpb.py:62-66` states this, and the build in §3 printed it
again unprompted. **No dependency change is required by this candidate**: the
restored files are pure-Python modules and data the accepted runtime already
imports on that same interpreter. Portable provisioning hazards apply only if
that different shape is selected.

## 6. Reproducing this exactly

```sh
git archive e6f9566 | tar -x -C /tmp/cand
ln -s /Users/john/TokenEfficiencyEngine/server/.venv /tmp/cand/server/.venv
cd /tmp/cand/server
PYTHONPATH=/tmp/cand/server/src /Users/john/TokenEfficiencyEngine/server/.venv/bin/python \
  -m ruff check src tests ../benchmarks
PYTHONPATH=/tmp/cand/server/src /Users/john/TokenEfficiencyEngine/server/.venv/bin/python \
  -m pytest -q
```

The `PYTHONPATH` pin is load-bearing: without it the venv's editable install
imports the dirty checkout and falsely validates the export.

## 7. Open items for the coordinator

1. **`structural` native-engine coverage.** Corrected in revision 4: the tests
   were not missing from the repository, only from this branch's candidate. They
   are recovered from `codex/a84-reviewed-runtime` at `18666b3` and give
   23 passed. What remains genuinely open is that all **22** of their skips are
   real-engine gates, so `openseespy`/`oofem` behaviour is unverified here.
2. **The suite leaks ~330 `tee-*` workdirs per run.** Adapter tests `mkdtemp`
   and never clean up. The destructive purge had been masking it. They now carry
   ownership markers, so a later purge collects them legitimately once the test
   process exits — but the leak is real.
3. **The validator trusts the marker's content.** An adversarial sweep found no
   new fail-open in six of seven attacks, but a marker rewritten in place with a
   dead-owner record makes a *live* directory reclaimable. Write access to the
   directory is required, and that already permits deletion, so it is not a
   privilege boundary — it is the limit of what the marker can prove. Receipt
   §4e.
4. ~~One intermittent test.~~ **RESOLVED at the source** — receipt §4f. It was
   test isolation plus a status detector gated by the state it corrects; both
   fixed, and it now passes because the mechanism is gone rather than because a
   rerun landed well.
   **And a related caution, from round eight:** exact-cwd matching failed
   whenever the two sides expressed the same directory through different symlink
   aliases — `_norm` used `normpath`, so the lane's `/var/…` never equalled the
   `/private/var/…` that `lsof` reports. Paths already in the same form matched
   correctly; the suite missed the alias case because pytest hands out an
   already-resolved `tmp_path`. It is `realpath` now, with a regression that
   builds an unresolved path on purpose. A test can pass because the harness
   handed it the easy shape.
5. **Version cut.** Currently `0.30.1`. Patch, minor, or not a release.
6. **Whether to release at all.** The client-visible change is small; the case
   for shipping is that chores currently point at a dead endpoint.
7. **`llguidance`** in the vLLM environment would give genuine server-enforced
   JSON for the first time. Not done, out of scope here.

## 8. What the packet still needs, which I cannot supply

- The frozen release manifest and its separate `.sha256`, over the whole shipped
  runtime tree normalized to `tee/`.
- Each target's actual registration, wrapper version, interpreter, resolved
  launch command and selected lanes, **re-inspected now**. Per §4A that
  inspection is yours; this session inspected no installation, and a stale claim
  about what is installed is the failure this preparation kept repeating.
- Rollback artifacts per target, plus the machine-local restoration in §5, which
  no artifact carries.

## 9. Scope statement

Nothing was installed, restarted, re-targeted, dependency-synced, downloaded,
pushed or released. One artifact was built for verification only. No client
receipt exists, is claimed, or may be invented: both actual clients return their
own acceptance during the later coordinated rollout.
