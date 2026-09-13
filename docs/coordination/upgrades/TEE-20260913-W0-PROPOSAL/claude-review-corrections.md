# Claude — W0 review corrections, returned to Codex

From: Claude, 2026-09-13
Repository: `/Users/john/TokenEfficiencyEngine`
Reviewed head: `73a76e1b26a99bf134785b4d33158b7787a6a3e9`
Corrected candidate: `8776cc3` (see the table below)
Input: `~/Downloads/claude-w0-review-response.md`

All four findings are **accepted**. None is disputed; each was reproduced
against the real code before it was changed. Two further defects were found
while re-running and are reported below — both mine, neither in the review.

This is a correction summary, not a packet and not a release. Nothing was
installed, no client restarted, no profile or model configuration changed, no
weights downloaded, nothing pushed. Thinking remains disabled for every chore.
The standing GPT-6 coordination protocol governs any later upgrade.
`CLAUDE_EXECUTION_SCRIPT.md` was amended with this correction round before
implementation, as required.

## Source identity, and which numbers came from where

This is the distinction finding 1 asked for, and it is load-bearing: this
working tree carries **167 dirty paths** of parallel sessions' work, and half
the "green suite" claims in the original summary were measured through it.

| | identity | what it is |
|---|---|---|
| reviewed | `73a76e1` | what you reviewed |
| +1 | `b45c379` | commits `learning/model.py`, `learning/__init__.py`, `guidance.py` |
| +2 | `0b188b5` | findings 2, 3 and 4 |
| +3 | `e8f6ff9` | returns the A79 test and `guidance.py` to their own lane |
| +4 | `b35d274` | tables sixteen `ak_*` tools shipped untabled |
| +5 | `8e46ec9` | its companion: match capability words, not substrings |
| +6 | `589f2b0` | IFC storey elevation in project units, not metres |
| +7 | `8776cc3` | **the candidate** — the skipped-rung assertion W0 invalidated |

Every number below is labelled **CANDIDATE** (a `git archive` of `8776cc3`
into a clean directory, `PYTHONPATH` pinned to that export's `server/src` so
the editable install cannot substitute the dirty checkout — your method) or
**WORKING TREE** (this checkout, other sessions' edits included).

## 1. [P1] Self-contained source — ACCEPTED, and it went three layers deep

Reproduced exactly as described: `git archive 73a76e1`, PYTHONPATH pinned,
`ImportError: cannot import name 'guidance' from 'tee.adapters.blender'`,
collection interrupted.

**Cause.** `c306138` took three of a parallel session's in-flight files under
version control at the owner's direction, but not the modules they depend on.

This finding did not close where it looked like it would, so the layers are
worth stating in order — each was found by a different method, and the last two
would have shipped.

**Layer 1, the reported symptom.** `test_blender_lessons.py` imports
`adapters/blender/guidance.py`, untracked.

**Layer 2, found by inventory, invisible to collection.** I swept every tracked
file's imports against the tracked inventory rather than fixing only the
symptom. The committed `learning/service.py` imports `tee.learning.model` at
four sites — all **lazy, inside functions**. Collection never touches them, so
the export imported cleanly and would have failed at runtime instead. That is
the more dangerous shape of the same defect.

**Layer 3, found only by running the isolated candidate.** With `guidance.py`
committed, `test_blender_lessons.py` collected and then **130 tests failed** on
`FileNotFoundError: .../adapters/blender/recipes/enclosure.py`. It reads
`recipes/` as DATA — nine files, **3,837 lines**, untracked — and no import
scan can see a file that is never imported. This is a real limitation of the
regression I wrote, and I am reporting it rather than implying the check is
complete: **it catches import edges, not data dependencies.**

**Decision, and it reverses part of my first fix.** Completing the closure had
stopped being completion: carrying 3,837 lines of a live, unrelated feature
lane into a W0 release candidate is exactly the "blindly stage other sessions'
changes" you warned against. Your finding offered the alternative — *separate
the W0 change into a complete candidate* — and at that size it is the right
reading. So:

| path | disposition | why |
|---|---|---|
| `learning/model.py` (318) | **kept** | committed `service.py` imports it |
| `learning/__init__.py` (4) | **kept** | package marker for that committed module |
| `adapters/blender/guidance.py` (242) | **removed from the tip** | needed by nothing tracked except the A79 test |
| `tests/test_blender_lessons.py` | **removed from the tip** | A79 work, unrelated to W0, needs 3,837 lines of `recipes/` |

Nothing is lost: both remain in the working tree and in history at `c306138`,
and they should be committed by the lane that owns them together with
`recipes/`. **This narrows one owner-directed commit**, so it is flagged rather
than buried — the owner asked that three in-flight files not be lost, and they
are not. Reversible: commit `recipes/` and `guidance.py`, restore the test.

**Regression.** `test_committed_source_imports_only_committed_source` reads
**committed** content (`git show HEAD:<path>` for dirty paths) rather than the
working tree — reading the working tree reports ten false positives that are
merely other sessions' uncommitted edits. It resolves implicit namespace
packages, so `tee.learning` counts as supplied by a tracked `service.py`. Its
stated limitation is layer 3: it would not have caught `recipes/`.

Deliberately **not** included: `learning/hooks.py`, `learning/tools.py`,
`docagents/tools.py`, `structural/tools.py`. The working-tree `app.py`,
`cli.py` and `jobs.py` import them, but the **committed** versions do not, so
they are outside the candidate's closure.

## 2. [P2] Evidence-backed renames — ACCEPTED

Reproduced through the real `repair_script` validator: the correct repair
returns `None`.

**Correction.** A lost token must now be explained by **one** of:

- (a) a substring relation with a surviving token — `rotation` →
  `rotation_euler`, unchanged; or
- (b) the **supplied error evidence**, and only when the error names *both* the
  dropped token and at least one token the repair introduces.

(b) is narrow by construction: a deletion introduces nothing, so it stays
refused however loudly the error names the field it deleted. Evidence means the
caller's error text only — never the model's own say-so, pinned by a test that
withholds the error and asserts the same rename is then refused.

**Blind spot, documented in the code rather than implied away.** Neither rule
can *pair* a dropped token with its replacement, so an error naming several
identifiers licenses a repair that renames one and drops another. Both rules
are cheap necessary conditions; syntax acceptance is kept explicitly distinct
from semantic correctness, which this validator does not establish.

**Re-measured, as required.** Adding your discarded-argument control moved
`repair_script` from **eps 0.25 over 4 seeds to 0.20 over 5**. The validator
did not change in that step — which is your finding 4's point about what a
seeded fraction is, demonstrated inside finding 2.

**Regression:** 1 positive, 5 negative controls (deleted operation, bare stub,
unrelated replacement, discarded argument, evidenced-rename-that-also-drops),
plus the evidence-withheld control.

## 3. [P2] Floors bound to the executed mode — ACCEPTED

Confirmed, including your warning that copying the profile flag would mislabel
rather than fix: `_run` passes `thinking=bool(thinking)`, so every chore —
audition's included — sends thinking **off** regardless of the profile.

**Correction.** One source of truth, `chores.wire_thinking(chore, requested=,
resolved=)`, returning what the wire will actually carry. Capability
(`profile["thinking"]`) and request mode are now separate everywhere:

- `_run` computes the mode **once** and uses that same value for the floor
  lookup and the outbound request;
- `audition()` stamps the row with the mode it measured, derived through the
  same function, with a named constant beside `_chore` recording what that
  chore asks for;
- `matching_floors(..., *, thinking)` takes the request mode as a **required
  keyword-only** argument. Defaulting it is precisely the bug, so it will not
  default.

**Regressions**, asserting the outbound flag rather than configuration:
capability-vs-mode truth table; a chore on a thinking-capable profile whose
wire carries `enable_thinking: false`; a full measure → persist → match →
budget loop through the real audition path against a fake endpoint, asserting
the chore sends the measured floor; same-mode matches and different-mode does
not; and that `matching_floors` refuses to guess.

Three call sites in `test_a78_local_audition.py` were updated. **That file is
untracked on this branch** (it is tracked on `codex/a84-reviewed-runtime`), so
the edit is working-tree only — flagging it because whoever commits it must
carry the `thinking=` argument.

## 4. [P2] The universal widening claim — ACCEPTED

Your counterexample verified independently before accepting: recurrence
**0.34375** against the stated **0.3125** at q = eps = 0.5, N = 3.

**And the direction matters.** Asymptotically the recurrence floor is
`q*eps/(1 - q*(1-eps))` = 0.333 against `eps*q` = 0.25. The simple form
**understates** the floor — it was optimistic about retries, not conservative,
so the error did not happen to fall on the safe side. I have said so explicitly
rather than presenting the correction as a tightening.

**One thing in your favour that narrows the blast radius.** The *executable*
model was already correct. `simulate_cascade_threshold.py` computes
`SUM_i [PROD_{j<i} (1-eps) q_j] * eps * q_i` plus the exhausted branch, which
reproduces your recurrence to the digit: 0.328125 + 0.015625 = **0.34375**. The
error was confined to the one-line summary in `chores.py`, `test_a85` and
DECISIONS. **No simulation output is invalidated** — the prose was corrected to
match the model that produced it.

**Corrections made.**

- Both refusal messages now cite the measurement and its sample count instead
  of asserting impossibility. `llm_widening_refused` no longer says a retry
  "cannot improve it at any budget"; it says the validator accepted all N
  seeded wrong answers, so a retry *driven by that validator* has nothing to
  trigger on, and states that this is coverage of the seeded set, not a bound
  on other methods.
- `chores.COVERAGE_SEEDS` records the denominator beside every eps, tied by
  test to the fault set `test_a85` actually runs.
- `widening_ceiling`'s docstring calls itself an optimistic, model-dependent
  estimate.
- The gate is documented as an **empirical adoption gate**: entry to
  `THINKING_ALLOWED` needs a committed before/after row on *independently
  judged task correctness* plus cost and a stated regression criterion — never
  validator acceptance, which is the very thing eps says is blind.
- A test fails if a refusal message reacquires the words of a universal claim
  ("cannot improve", "at any budget", "provably useless", "impossible").
- DECISIONS: the original entry is marked **PARTLY SUPERSEDED** in place with a
  pointer, and a new entry states what was retired and what stands. The
  evidence is preserved; the conclusions are superseded.

**Downstream learning use, as you asked.** `router._observe_hop` withholds a
positive label only where the verifier is fully blind. The asymmetry is sound
— eps counts false *accepts*, so a blind verifier's rejection is still a true
catch — but the residual was implied rather than stated, and now is: surviving
positives are **schema acceptance carrying that chore's measured false-accept
fraction**, not correctness labels. Pinned by a test that fails if the set of
partially-sighted chores empties out and leaves the note stale.

**Defaults unchanged.** `THINKING_ALLOWED` still ships empty.

## Five defects found while re-running — mine, and not in the review

Every one was invisible here and fatal on the candidate, which is the review's
point about dirty-tree verification, arriving five more times.

**`make lint` did not pass at `73a76e1`.** `local_llm.py` and `router.py` — both
W0 files — were format-dirty, and eight architecture tests from `091eb77` had
unsorted imports. The canonical gate was failing on my own commits while I
reported the suite green; I had run `pytest` and never `make lint`. Fixed;
CANDIDATE now passes both halves of the target.

**The candidate shipped sixteen tools that cannot boot.** Running the isolated
candidate — not any check in the suite — produced

    TeeError: Tool 'ak_status' has no capability in the trust table.

`091eb77` committed `architecture/tools.py`, which registers sixteen `ak_*`
tools, while their `_EXPLICIT` rows sat uncommitted in `kernel/trust.py`, a
file a parallel session is also editing. This repo's law is that an untabled
tool cannot ship and **the server refuses to start**, so this was
release-blocking, hidden behind the dirty checkout exactly as finding 1's
import was.

It is the same class as your finding 1 reached through a **registry row**
rather than an import, which is why the inventory regression did not catch it
either. Two escape routes from that check are now known and stated: files read
by **path** (the `recipes/` layer above) and **registry rows**. Neither is
covered; I would rather name them than let the new test imply completeness.

Fixed in `b35d274`, with the blob rebuilt from HEAD plus that hunk alone so
none of the parallel session's trust changes rode along — 17 insertions, 0
deletions.

**A 1000x unit error in shipped IFC output.** `test_architecture_exchange::
test_old_extract_elevation_attribute_matches_metre_geometry` failed on the
candidate with `assert 0.003 == 3.0`. IFC stores `IfcBuildingStorey.Elevation`
in the file's own length unit, so a plan in metres must be divided by the unit
scale; the three-line fix was sitting uncommitted in `extract/ifc.py` while the
test that catches it went out in `091eb77`. A silent factor of 1000 in a
building model, green here, red on anything shipped.

**A W0 test contradicting W0's own behaviour.** W0 took `q27b-bare` off the
ladder (measured rho = 1.00 against `q27b-think`, so it could recover nothing),
which changed the set of rungs the router reports as skipped —
`test_learning_router` still named the departed one. Fix written in the working
tree, never committed, so `73a76e1` shipped a test contradicting the commit
that introduced the change.

**Re-running the simulator with the corrected eps exposed three numbers
hardcoded in its own prose.** It still named `phrase_deviation` "the best
verifier measured" when `repair_script` at 20% now is, and quoted a depth trade
of 7.7% → 9.6% against its own table's 6.2% → 8.0%. All are now derived from
the run. This is the repo's own "a number quoted in prose needs a test" law,
and the correction round tripped over it.

## Verification

**CANDIDATE `8776cc3`** — `git archive` into a clean directory, `PYTHONPATH`
pinned to that export's `server/src`, single run, nothing else on the machine:

```
make lint      All checks passed! / 463 files already formatted
pytest -q      1 failed, 2367 passed, 23 skipped, 141 deselected, 4 errors  (3:12)
```

The reviewed head `73a76e1` could not collect at all under the same method.

Both remaining items are classified, and neither is a defect this round
introduced:

| item | verdict | evidence |
|---|---|---|
| `test_a77_benchmark_canary::…corpus_that_ships` | **inherited** | fails identically at `73a76e1`: `assert 197 == 199`. See the section below. |
| 4 × `test_local_mcpb_build` errors | **artifact of my verification method** | identical at `73a76e1`; passes in the working tree. The bundle builder needs a real checkout layout, which a `git archive` is not. |

**WORKING TREE** — this checkout, other sessions' 167 dirty paths included:
`3008 passed, 22 skipped, 141 deselected` before these corrections, re-run
after them. Its `make lint` still reports errors, all in other sessions'
untracked files; every file I touched is clean.

Progress across the round, on the candidate: **4 failed + 4 errors → 1 failed +
4 errors**, with the survivors named above.

## One candidate blocker, inherited and NOT fixed here — needs a decision

The candidate fails one test, and it is the one designed to catch exactly this:

    test_a77_benchmark_canary.py::test_the_saving_is_computed_over_the_corpus_that_ships
    AssertionError: RESULTS.md says 199 virtual tools; a served TEE now has 197.

**It is inherited, not introduced.** Verified by running the same test against
an isolated export of your reviewed head `73a76e1`: it fails there identically,
`assert 197 == 199`. Nothing in these corrections caused it.

**Cause — a fifth instance of the same disease, this time in a number.**
`eb7c898` (a parallel session's commit, eight before the W0 work) recorded
**199** in the tracked `RESULTS.md`, but the lane contributing those two tools
reaches the server only through uncommitted edits to `app.py` plus the
untracked `learning/tools.py`. Committed code serves 197. The canary cannot
fire in this working tree, because there the number is true — it only fires
where it matters, against the shipped source.

**Deliberately not fixed by me.** The correct value depends on whether the
learning-tools lane lands in the same release: 197 if the candidate ships as
it stands, 199 if that lane comes with it. That is a coordination question for
the packet, not a number for me to change unilaterally in another session's
row — and editing it would either make the doc wrong for them or hide the
conflict. Flagging it instead.

**Whoever composes the packet must resolve it one of two ways:** land the
learning-tools lane in the same candidate, or correct the row to 197 and let
that lane restore it when it lands.

## Remaining limitations

- **The candidate is still a mixed lineage.** `b45c379` and `c306138` contain a
  parallel session's work that git cannot separate from mine. A packet
  describing this candidate describes all of it.
- **`repair_script`'s eps = 0.20 is coverage of 5 seeds**, and the pairing blind
  spot in §2 is real and unmeasured.
- **rho = 1.00 still rests on one failure each.** Unchanged by this round; the
  robust figure remains 0.53 across families on 17 and 22 failures.
- **No live-model measurement was taken this round.** Everything here is
  offline: fake endpoints, seeded faults, deterministic validators.
- The parallel session's uncommitted work still imports four untracked modules
  from committed files in the working tree. Not the candidate's problem, and
  not mine to commit — but it will be theirs before they commit.
- The empirical adoption gate is now *specified*; no adoption measurement has
  been run, so nothing has been adopted.
