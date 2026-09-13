# GPT-6 — compose the execution packet for the W0 thinking-engine candidate

Prepared by Claude, 2026-09-13, for the owner to hand to GPT-6 / Codex.
Repository: `/Users/john/TokenEfficiencyEngine`.
Protocol: `docs/upgrade-coordination-protocol.md`, version 1.0.1.

## Assignment

This is a **stage A proposal** under §4 of the protocol, from the initiating
agent. It is not a packet, not a release, and not a claim that anything is ready
to install. Protocol 1.0.1 reserves packet authorship to you, and §1 makes
completion mean two live client receipts — neither of which exists.

**What I am asking for:** decide whether this candidate should become an update
at all, and if so compose the execution packet — one frozen source identity, the
appropriate delivery for each of the two client shapes, continuity checks and
rollback, per §2 and §3.

**One decision is blocking and is yours, not mine.** It is in §5 below. I found
it, verified it is inherited rather than introduced, and deliberately did not
fix it, because the correct value depends on what ships together.

## Operating rules for this handoff

- Existing authorization persists. Nothing here asks for new permissions.
- Nothing has been installed, restarted, configured, downloaded, pushed or
  released. `THINKING_ALLOWED` ships empty; thinking is off for every chore.
- The 17-tool always-loaded contract is unchanged. No new always-loaded tools.
- You own PROGRESS, DECISIONS and the RESULTS append during an update (§3,
  shared-ledger decision). I have written to all three **outside** an update
  window; if you open one, re-read them first — a parallel session is also
  editing this branch.
- Per §4A you inspect the actual client registrations yourself. I have
  deliberately **not** enumerated the two client shapes as fact here: my
  session did not inspect either installation, and a stale claim about what is
  installed is exactly the failure this round was about.

## 1. Source identity

| | value |
|---|---|
| branch | `claude/token-efficiency-engine-5jv1dj` |
| HEAD | `5d188e08c5773cd501c825fe87c727e3c1c3613a` |
| ahead of origin | 11 commits, **not pushed** |
| declared package version | `0.30.1` (`server/pyproject.toml:4`) |
| working tree | **NOT clean — 149 dirty paths** |

Nine commits form the candidate, `73a76e1^..HEAD`:

```
5d188e0  Record the W0 review corrections returned to Codex
8776cc3  Expect q35b, not q27b-bare, among the skipped rungs
589f2b0  Write IfcBuildingStorey.Elevation in project units, not metres
8e46ec9  Match capability words, not substrings, in the no-GUI-tool assertion
b35d274  Table the sixteen ak_ tools the architecture commit shipped untabled
e8f6ff9  Return the A79 Blender-lessons test to its own lane, out of the W0 candidate
0b188b5  W0 review: accept evidenced renames, bind floors to the executed mode, …
b45c379  Complete the W0 candidate: commit what committed code already imports
73a76e1  W0: a thinking engine, and a measured gate on when extra effort can help
```

**Mixed authorship you must account for (§2, "preserving uncommitted owner
work").** `c306138` — one commit *before* this range, already in history — took
three of a parallel session's in-flight files under version control at the
owner's direction. `b45c379` then committed two more modules those files
require. Four of the nine commits above touch files that session also edits
(`kernel/trust.py`, `extract/ifc.py`, `tests/test_learning_router.py`,
`tests/test_windtunnel_gui.py`). Every one was staged through a temporary index
with the blob rebuilt from HEAD plus my hunk alone, so none of their changes
rode along — but the *lineage* is mixed and git cannot separate it.

The remaining 149 dirty paths are theirs and are **not** in the candidate.

## 2. What changed, and for whom

### Client-visible

- **The tool contract is unchanged**: 17 always-loaded, 2,129 tokens on the wire
  (`benchmarks/RESULTS.md:202`). No new always-loaded tools.
- **Chores can actually run.** The previous default profile pointed at `:8080`,
  which does not answer, so every chore was degrading to its deterministic path.
- **`response_format` is now negotiated per endpoint.** The two local backends
  are inverted on it: MLX accepts and silently ignores it, vLLM refuses with
  HTTP 400 unless `llguidance` is installed. TEE sent it unconditionally, so it
  could not talk to the better backend at all.
- **Four new error codes may reach a client** — measured by diffing the code
  sets at `73a76e1^` and HEAD, not by reading the diff:
  `llm_no_answer`, `vlm_no_answer`, `llm_widening_refused`,
  `llm_widening_unproven`.
- **Reasoning never reaches a client.** It is read from whichever field the
  backend uses (`reasoning` on MLX, `reasoning_content` on vLLM), recorded, and
  stripped. That is what makes a thinking engine free in tokens-per-task.

### Machine-local, and will NOT travel with any package

- `.tee/llm-profile.json` was switched from `q14b` to `q27b-think`. The prior
  value is preserved at `.tee/llm-profile.json.bak-w0`.
- Two model weight sets were deleted: `Qwen2.5-Coder-14B-Instruct-4bit`
  (7.7 GB) and `Qwen3.5-9B-MLX-4bit` (5.6 GB) — `docs/PROGRESS.md:18013`. The
  27B on `:8087` is intact. Re-downloading the 14B is the only costly rollback
  step.
- `.tee/config.toml` was not touched.

A package installed on a machine without those endpoints will find the profile
unreachable. Per A76's law that is *not* a failed verification, and the lane
reports it as unreachable rather than as a quality signal — but it is worth
stating in the packet.

## 3. Evidence, and the method that matters

**Verify the candidate the way an external review did, not the way I first
did.** This working tree is dirty enough that a green suite here proves very
little — the review caught, and I then found four more instances of, committed
code depending on uncommitted work.

```sh
git archive <sha> | tar -x -C /tmp/cand         # clean export
ln -s <repo>/server/.venv /tmp/cand/server/.venv  # the bundle builder needs one
cd /tmp/cand/server
PYTHONPATH=/tmp/cand/server/src python -m ruff check src tests ../benchmarks
PYTHONPATH=/tmp/cand/server/src python -m pytest -q
```

The `PYTHONPATH` pin is load-bearing: without it the venv's editable install
imports the dirty checkout and falsely validates the export.

**Do not verify with `pytest -m "not dcc"`.** That REPLACES `addopts` rather
than narrowing it. The real default is
`-m 'not dcc and not ml and not network and not llm and not cfd and not fdm'`
(`server/pyproject.toml:235`). I mis-measured this suite for most of a session
on that mistake.

Results, each labelled by scope:

| scope | result |
|---|---|
| **`8776cc3`, isolated** — full suite | `make lint` clean; **1 failed, 2367 passed**, 23 skipped, 141 deselected, 4 errors |
| **`5d188e0` (HEAD), isolated** — the delta only | 16 passed, 1 skipped |
| **reviewed head `73a76e1`, isolated** | could not collect at all — `ImportError` |
| **working tree** | **3008 passed**, 22 skipped, 141 deselected |

Being exact about which sha carries which result, since that is the whole
subject of this round: the **full** isolated suite was run at `8776cc3`. HEAD
adds only this proposal's two sibling documents plus a 7-line widening of
`test_w0_review_corrections.py`; that file was re-run against an isolated export
of HEAD and passes. I have **not** re-run the full suite at `5d188e0`.

One skip in that run is by design and worth knowing before you read it as a
gap: the self-containment regression compares tracked against untracked files,
so it skips when there is no `.git` — which a `git archive` export has not. It
protects a checkout and a clone, not an export.

The single candidate failure is §5. Four `test_local_mcpb_build` errors also
appear in the isolated export; they are an artifact of exporting (the bundle
builder wants a real checkout layout), identical at the reviewed head, and pass
in the working tree.

## 4. Why there were nine commits and not three

An external review (Codex, `~/Downloads/claude-w0-review-response.md`) returned
four findings against `73a76e1`. All four were accepted, reproduced before being
changed, and are answered in
`docs/coordination/upgrades/TEE-20260913-W0-PROPOSAL/claude-review-corrections.md`.
Two are worth your attention when writing the packet's limitations:

- **A recorded conclusion was wrong and is now superseded.** The W0 work claimed
  `eps*q + (1-eps)*q**N` bounded what any retry could achieve. It is one model
  with unstated assumptions and it *understates* the floor — the retry-until-N
  recurrence gives 0.34375 at q = eps = 0.5, N = 3 where that form gives 0.3125.
  DECISIONS now carries a superseding entry; the evidence is preserved.
  The simulator itself was already correct, so no measured output was invalidated.
- **Five further defects surfaced only under isolated verification**, and one was
  release-blocking: `091eb77` registered sixteen `ak_*` tools with no trust-table
  row, and this repo refuses to boot on an untabled tool. Another was a silent
  factor of 1000 in IFC storey elevations. Both were green here and red on the
  candidate.

The general lesson, offered for the packet's continuity section: committed code
can depend on uncommitted work through **at least four** routes — a plain
import, a lazy import inside a function, a data file read by path, and a
registry row in a shared file. Only the first fails collection.

## 5. The blocking decision — yours

The candidate fails exactly one test:

```
test_a77_benchmark_canary.py::test_the_saving_is_computed_over_the_corpus_that_ships
AssertionError: RESULTS.md says 199 virtual tools; a served TEE now has 197.
```

- **Inherited, not introduced.** It fails identically against an isolated export
  of `73a76e1`, the head you reviewed.
- **Cause.** `eb7c898` recorded 199 in the tracked `RESULTS.md`, but the lane
  contributing those two tools reaches the server only through *uncommitted*
  edits to `app.py` plus untracked `learning/tools.py`. Committed code serves
  197. The canary cannot fire in this working tree, because here the number is
  true.
- **Why I left it.** 197 is right if this candidate ships alone; 199 is right if
  the learning-tools lane ships with it. That is a question about what goes into
  one release, which §1 makes yours, not mine. Changing another session's row
  unilaterally would either make the doc wrong for them or hide the conflict.

**Resolve it one of two ways in the packet:** land the learning-tools lane in
the same candidate, or correct the row to 197 and let that lane restore it.

## 6. Other open decisions, none taken

- **Version cut.** Currently `0.30.1`. Whether this candidate is a patch, a
  minor, or not a release at all is the owner's and yours.
- **Whether to release at all.** The client-visible change is small; the case
  for shipping is that chores are currently pointed at a dead endpoint.
- **`llguidance`.** Installing it in the vLLM environment would give TEE genuine
  server-enforced JSON for the first time. Not done, not in scope here.
- **The 14B re-download** (7.7 GB), only if rollback is wanted.

## 7. What I have not done, explicitly

No install, no client restart, no profile or model-configuration change beyond
the machine-local switch recorded in §2, no weight download, no push, no
release, no packet. No live-model measurement was taken in the correction round
— all of its evidence is offline: fake endpoints, seeded faults, deterministic
validators.

## 8. What the packet needs from §3 that I cannot supply

Listed so nothing is assumed already done:

- The frozen release manifest and its separate `.sha256`, over the whole shipped
  runtime tree normalized to the `tee/` prefix — not just `*.py`.
- Each target's actual registration, wrapper version, interpreter, resolved
  launch command and selected lanes, **re-inspected now** rather than taken from
  the 2026-09-10 record.
- The dependency inventory and required extras. Note the standing hazard: an
  `.mcpb` install rebuilds the venv from the lock and silently deletes the fleet
  extras, so the restore set must be derived from the current venv **before**
  any install, not from a remembered list.
- `skills/tee-usage/SKILL.md`'s hash and verification of each client's copy —
  it is modified in this working tree and therefore differs from HEAD.
- Rollback artifacts per target, plus the machine-local restoration in §2, which
  no artifact carries.

## Return

If you want changes to the candidate before it is packet-worthy, send them the
way the last review came — findings with reproductions — and I will work them
against the governing execution script, which already carries the W0 correction
round as an amendment.
