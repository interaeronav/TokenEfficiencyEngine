# GPT-6 — compose the execution packet for the W0 candidate

**Revision 4, 2026-09-13.** Rewritten, not patched: revisions 1 and 2
accumulated conflicting identities and two disproved explanations. This
document describes **one** candidate. The correction history lives in
`claude-packet-review-corrections.md`; nothing historical is repeated here as
current.

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
| **candidate commit** | `47765b7` (full id in the receipt's identity table) |
| **runtime payload fingerprint** | `d792b3397cac5b7a2807ea2f28a0812542de7600ca139cb6de3360f2e8625864` |
| runtime files | 325 |
| accepted A84 baseline | `0e172448d05b14a0a714bbecd4c79b0ba24cc9caa48bf9dd5db57f9680fb252f`, 324 files |
| delta vs accepted | **0 removed, 1 added, 17 changed** |
| declared version | `0.30.1` (`server/pyproject.toml:4`) |
| branch | `claude/token-efficiency-engine-5jv1dj`, **not pushed** |

`47765b7` is the commit everything below was **tested at**. Commits after it in
this directory are documentation only and do not touch the payload.

The one addition is `tee/kernel/workdirs.py`, the ownership and liveness check
the purge fix needs. Of the seventeen changed files, eleven are the reviewed W0
and architecture work plus the owner-instructed formatting correction; the other
six are the purge fix — `tee/purge.py` and the five producers that now mark the
scratch directory they own (`adapters/blender`, `adapters/fusion`,
`adapters/godot`, `adapters/freecad`, `assets/library`).

## 2. Current results, each bound to the source tested

All from a `git archive` of `63d9308` into a clean directory, `server/.venv`
symlinked to the prepared repository venv **without provisioning it**,
`PYTHONPATH` pinned to the export's `server/src`, and that venv's explicit
interpreter.

| check | result |
|---|---|
| canonical full suite | **3,035 passed, 45 skipped, 141 deselected, 0 failed** |
| `ruff check src tests ../benchmarks` | **clean** |
| `ruff format --check src tests` | **clean** (516 files) |
| focused: purge + structural | 40 passed, 22 skipped |
| restored-feature suites | 665 passed |
| real workdirs deleted by the suite | **0**, recorded before and after |
| verification build | succeeded; identity in §3 |

The 45 skips include 22 explicit real-engine gates in the recovered structural
suites (`openseespy`, `oofem`): **native solver behaviour is unverified here.**

The suite command is the project default. **Never substitute `-m "not dcc"`** —
it replaces `addopts` rather than narrowing it. The real exclusion set is
`-m 'not dcc and not ml and not network and not llm and not cfd and not fdm'`
(`server/pyproject.toml:235`).

One skip in the focused set is by design: the self-containment regression
compares tracked against untracked files and skips where there is no `.git`,
which a `git archive` export has not.

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
| bytes | 1,321,782 |
| sha256 | `c3690fa627ed3d1d38b773746bb6c277126b1916348051f842a313976b0115b4` |
| manifest `command` | `/Users/john/TokenEfficiencyEngine/server/.venv/bin/python` |
| temporary export path in launch command | **none** |

Payload comparison, which is the point rather than the ZIP write:

- artifact runtime **== candidate source**, complete set and byte equality,
  325 files, fingerprint `d792b339…25864`;
- artifact vs accepted: 0 removed, 1 added, 17 changed.

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
- **Four new error codes** may reach a client, measured by diffing the code sets
  at `73a76e1^` and the candidate: `llm_no_answer`, `vlm_no_answer`,
  `llm_widening_refused`, `llm_widening_unproven`.
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
git archive 47765b7 | tar -x -C /tmp/cand
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
3. **One intermittent test** — disposition in the receipt §4c. Investigated to a
   mechanism, not to a confirmed defect, and returned as a validation risk
   rather than rerun until green.
4. **Version cut.** Currently `0.30.1`. Patch, minor, or not a release.
5. **Whether to release at all.** The client-visible change is small; the case
   for shipping is that chores currently point at a dead endpoint.
6. **`llguidance`** in the vLLM environment would give genuine server-enforced
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
