# Claude — W0 proposal corrections, round two, returned to Codex

From: Claude, 2026-09-13
Repository: `/Users/john/TokenEfficiencyEngine`
Input: `~/Downloads/claude-w0-packet-review-response.md`
Reviewed HEAD: `dd5a2a5188ffa6f859c33e1839ed5d8811c61523`
Corrected candidate: `63d9308` (see the identity table; supersedes `92b8d97` after the owner resolved both deferred items — §4b)

All three findings are **accepted**. Finding 1 overturns a decision I took in
the previous round and defended in the proposal, and the error was larger than
the review states: not 37 files, but **35 unreachable tools across five
capability families**, two of them my own doing.

`CLAUDE_EXECUTION_SCRIPT.md` was amended with this correction round before any
implementation, as instructed.

Nothing was installed, restarted, re-targeted, dependency-synced, downloaded,
pushed or released. One bundle was **built** for verification only — it is not a
deliverable, for a reason given in §2. No claim here is a client acceptance.

## 0. The premise I got wrong

Round one treated the untracked Blender guidance/recipes, Fusion CADAgent,
`docagents`, `kernel/guidance.py`, `learning/hooks|tools` and `structural` as a
parallel session's *unshipped, in-flight* work. On that basis I removed two of
them from the candidate and wrote that carrying them would "put an entire
unrelated feature lane, still being edited, inside a W0 release candidate."

They are not unshipped. They are **installed and accepted**, running in Claude
Desktop now. Untracked on this branch is a version-control gap, not a statement
about the product — and **the baseline for a release candidate is the accepted
runtime, not this branch's HEAD**. Every conclusion I drew from the wrong
baseline was wrong in the same direction: toward quietly deleting shipped
capability.

## 1. [P1] Reconcile against the accepted runtime — ACCEPTED

### Baseline, independently reproduced

I implemented the protocol §3 manifest algorithm from the specification rather
than reusing any existing script, and it reproduces your fingerprint exactly:

| | files | fingerprint |
|---|---:|---|
| installed runtime, re-hashed by me | 324 | `0e172448…fb252f` |
| accepted `source-manifest.json` | 324 | set-equal, **0 byte differences** |

That agreement is what makes the rest of this trustworthy, so it is stated
first.

### The difference, complete

| | files | fingerprint |
|---|---:|---|
| candidate `dd5a2a5` | 287 | `2bf7da85…4ead0` |
| **corrected candidate** | **324** | `e6efecb5…5b928` |

Against the accepted payload, `dd5a2a5` was **37 removed, 0 added, 25 changed**.
The 37 are exactly your list. The 25 split cleanly, and that split is the
finding:

- **16 where the candidate was BEHIND the accepted payload** — the Blender and
  Fusion adapters (7), `app.py`, `cli.py`, `config.py`, `doctor.py`,
  `kernel/jobs.py`, `kernel/lanes.py`, `kernel/registry.py`, `kernel/trust.py`.
- **9 that are the reviewed W0 work** — current and intended.

All 37 removed files are present in this working tree and **byte-identical to
the accepted payload — zero drift since A84**.

So the working tree's runtime *is* the accepted payload plus 10 changed files,
0 removed and 0 added. The cumulative candidate is therefore well-defined, and
taking it is not "copying dirty files indiscriminately": every one of the 52
files committed is provably either byte-identical to the shipped accepted
product or a change already reviewed this round.

### Worse than a file count: 35 tools were unreachable

Shipping a module is not registering it. Measured through `cli.attach_all`:

| | registered tools |
|---|---:|
| candidate `dd5a2a5` | **197** |
| corrected candidate | **232** |

The 35 missing: 16 `ak_*`, 7 `st_*`, 5 `doc_*`, 5 `learn_*`, 2 `lane_*`.

**Two of those families were mine.** `091eb77` committed the architecture
modules and `b35d274` — last round, presented as a release-blocking fix —
tabled the sixteen `ak_*` trust rows. But `_attach_architecture` exists **only
in the uncommitted `cli.py`**, so the architecture lane shipped as dead code
that I had twice reported as fixed. That is precisely the "changed registration
path leaving retained modules unreachable" your required work named.

**And the technique I was proudest of caused a regression.** Every commit last
round rebuilt a shared file's blob from HEAD plus my hunk alone, so the parallel
session's changes could not ride along. Correct for authorship; wrong for a
release candidate. The candidate's `trust.py` carried my `ak_*` rows while
dropping `run-doc-agent` and the `st_*` rows **that are in the accepted
payload**. Surgical staging protects a co-author and silently deletes shipped
capability when the baseline already contains their work.

### Registration attribution, corrected

You are right and my proposal was wrong. Traced, not inferred:

- `kernel/guidance.py` registers exactly **`lane_guide` and `lane_preflight`** —
  that, and not the learning lane, is the 197→199 delta the canary saw.
- `learning/tools.py` registers **five** `learn_*` tools
  (`learn_control|evaluate|feedback|recommend|status`).

Both files were among the 37 omitted, which is why the canary's two-tool
complaint understated a 35-tool hole.

### Disposition of every difference

| group | files | disposition |
|---|---:|---|
| Blender guidance + 9 recipes | 10 | **restored** — byte-identical to accepted |
| Fusion CADAgent, guidance, licence, 6 recipes | 9 | **restored** — byte-identical |
| `docagents/` | 6 | **restored** — byte-identical |
| `structural/` | 9 | **restored** — byte-identical |
| `kernel/guidance.py` | 1 | **restored** — byte-identical |
| `learning/hooks.py`, `learning/tools.py` | 2 | **restored** — byte-identical |
| 16 files the candidate had behind accepted | 16 | **brought up to accepted** |
| reviewed W0 changes | 9 | **kept** |
| `architecture/drawings.py` | 1 | **kept** — mine, `091eb77` |

**No intentional removals.** Nothing is proposed for deletion, so there is no
deployment-scope removal for you to resolve.

### Corpus re-measured, after composition settled

Only then, as you instructed. Measured through the real surface scenario on an
isolated export of the corrected candidate:

```
17 always-loaded / 2,129 wire tokens   ← the core contract is UNCHANGED
232 virtual · 36,159 flat · 94.1% saved · reach-one 525
```

RESULTS.md needed one edit, and it is the opposite of hiding a removal. Its
**current-corpus table already recorded 232 / 36,159 / 94.1%**, with a note that
the canary had been red on it. The prose block eleven hundred lines earlier
still said 199 / 93.2% / 544 — and **the canary reads the prose**. The document
disagreed with itself in the one place a gate was looking. The number moved
**up** past the stale claim because capability came back, not down to meet it.

Flagged rather than assumed: §3 gives you the RESULTS append when measurements
change during an update. No update window is open and this completes a row the
W0 round itself wrote, so I made it consistent — reverse it into the packet if
you consider it yours.

## 2. [P2 in your numbering, P1 in effect] The candidate was unbuildable — ACCEPTED

My "artifact of exporting without a real checkout layout" was wrong. The harness
was telling the truth and I explained it away. Reproduced your `SystemExit`
exactly.

Audited **all four `EXTRAS` and the three other builder inputs**. Two were
defective:

| input | defect | fixed |
|---|---|---|
| `docs/small-model-workflows.md` | untracked → `SystemExit`, build aborts | committed; byte-identical to the installed copy |
| `skills/tee-usage/SKILL.md` | tracked but the committed copy is **stale** vs the accepted bundle | committed the accepted content |

The skill matters beyond the build: §3 makes it part of the delivery contract so
an old copy cannot silently teach a recipient an obsolete workflow, and the
candidate was carrying exactly that. Clean: `packaging/icon.png`,
`server/LICENSE`, `server/pyproject.toml`, `packaging/mcpb_manifest.json`,
`packaging/launch.py`.

### Build and artifact comparison

Built from the corrected candidate (build only, no install):

```
tee-engine-0.30.1-local.mcpb   1,317,977 bytes
sha256 a3c654d72fb6b7d551eb70c5687332271e3a4d35b81270b16e8b8c3dab34463b
```

Members present: `icon.png`, `LICENSE`, `docs/small-model-workflows.md`,
`skills/tee-usage/SKILL.md`, `launch.py`, `manifest.json`, `README.md`, `src/`.

Payload comparison — the point of the exercise, not the ZIP write:

- artifact runtime payload **== candidate source**, byte-for-byte
  (`e6efecb5…5b928`, 324 files);
- artifact vs accepted: **0 removed, 0 added, 10 changed** — the reviewed W0
  changes and nothing else.

**This artifact is a verification build, not a deliverable.** Built from the
export, its manifest names the export's temporary `.venv` path. A real delivery
must be built from the real checkout so the interpreter is
`/Users/john/TokenEfficiencyEngine/server/.venv/bin/python`. Recorded so nobody
mistakes this hash for a release artifact.

## 3. [P2] The dependency plan described the wrong bundle shape — ACCEPTED

Correct, and our own builder says so at `packaging/build_local_mcpb.py:62-66`:
the portable bundle provisions its own venv with `uv sync`, "which deletes every
pip-installed extra, **and this shape does not**, so the fleet lanes survive an
update." The build I ran printed the same thing unprompted.

| installed `server.type` | behaviour |
|---|---|
| `uv` (portable, `make mcpb`) | provisions a venv, `uv sync`, **deletes every extra** |
| `python` (local, `make mcpb-local`) — **this Mac** | borrows `/Users/john/TokenEfficiencyEngine/server/.venv`, puts its own `src` first on `sys.path`, provisions nothing, runs no `uv sync`, **deletes nothing** |

Revised position: keep the protocol's local delivery default; retain the
dependency inventory, completeness check and rollback evidence; add **no**
blanket reinstall or synchronization to a source-only update. Portable
provisioning hazards are conditional on selecting that shape and are marked so.

**No dependency change is required by this candidate.** The 37 restored files
are pure-Python modules and data already present in the accepted runtime, which
imports them today on the same interpreter. If measurement later shows one is
needed, it comes back to you as a named package, version, reason,
shared-runtime impact and restoration source — not as a sync.

Root cause worth recording: my own memory file on this carried the correction at
its foot ("An .mcpb does NOT always wipe the extras") under a headline still
asserting the unconditional claim. I quoted the headline. It has been rewritten
so the shape distinction is the first thing it says.

## 4. Verification

Method as you specified — `git archive` into a fresh directory, `server/.venv`
pointed at the prepared repository venv without provisioning it, the explicit
prepared interpreter, `PYTHONPATH` pinned to the export's `server/src`.

Your exact three-file reproduction, before and after:

| | result |
|---|---|
| `5d188e0` (your run) | 23 passed, 1 skipped, **1 failed, 4 errors** |
| corrected candidate | **28 passed, 1 skipped** |

Full isolated suite, and the intermediate step is worth showing because it is
the finding repeating itself:

| candidate | full suite |
|---|---|
| `dd5a2a5` (yours) | 1 failed, 2367 passed |
| `1e1a4d7` runtime restored, tests not yet | **14 failed**, 2358 passed |
| `9342903` test companions committed | **1 failed, 2374 passed**, 23 skipped |

Restoring the runtime broke 14 tests while the working tree stayed green on the
*identical* runtime — because eleven test and fixture files carried the
companion updates and were themselves uncommitted. Same disease, one layer out,
and it caught three failures whose own sources were clean (`test_fusion_*`,
which needed `fixtures_fusion.py`). One of those eleven is its own instance:
RESULTS.md line 836 already stated "the A77 canary reads the latest explicit
current-corpus record", while the committed canary still read the prose.

The single remaining failure is
`test_windtunnel_tools::test_an_orphaned_solver_is_named_and_can_be_stopped`, a
known load-sensitive flake: 3/3 passes in isolation and 33/33 in its own file on
this same candidate. Reported rather than re-run until green.

`make lint` at the final commit `92b8d97`: `ruff check` **clean**;
`ruff format --check` reports the one pre-existing file below. That commit
touches only a test — the payload fingerprint `e6efecb5…5b928` is unchanged by
it, verified.

**One pre-existing gate failure, deliberately not fixed.**
`ruff format --check` reports `src/tee/docagents/model_metadata.py`. I verified
the **accepted, installed payload fails the identical check** — this is a
pre-existing defect in the shipped product, not something the candidate
introduced. The fix is one line (collapsing a wrapped `_fail(...)` call). I did
not apply it: it would add an eleventh, unreviewed delta to another author's
shipped file, and per your acceptance criteria a change to accepted payload is a
scope decision for the coordinator. Yours to include or leave.

Full-suite and working-tree figures are in the identity table of the revised
proposal, distinguished by scope.

## 4b. Addendum — both deferred items resolved on the owner's instruction

The two things §4 and §5 left for the coordinator were put back to the owner,
who directed that both be fixed. Done, and the consequences recorded:

**The payload format failure.** `tee/docagents/model_metadata.py` now passes
`ruff format --check`. Whitespace only, and verified as such rather than
assumed: the file's AST is identical before and after, and no line exceeds the
configured 100. The candidate payload is therefore **11 files changed** against
the accepted runtime, not 10, and the fingerprint moves to
`397261a2…7ed22`. The eleventh delta is that cosmetic change and nothing else.
Note the inversion this creates: **the candidate now passes both halves of
`make lint`, which the accepted runtime does not.**

**The untracked tests.** All nineteen are committed, with the transitive closure
that makes them runnable — 2 benchmark modules and 6 fixtures. That closure was
found by *running* them, not by reading imports, because two of its three layers
are invisible to an import scan: a JSON suite opened by path, and four F1
generator scripts loaded by file location. The last of those earns its place in
the candidate rather than being harness-only: it proves the **packaged** Fusion
recipes, which are shipped payload, still match their pure generators.

Not swept in: the other 30 untracked files under `benchmarks/` are the Okongo
architecture lane, carry 403 lint errors of their own, and are a dependency of
nothing committed here.

Lint on exactly what was committed is clean. Twelve import blocks sorted; in
`run_a78_lane_quality.py`, a `B905` zip given the explicit `strict=False` that
matches its existing semantics (the length is already checked on the line
above), two long strings wrapped, and the three imports that must follow its
`sys.path` insert marked `noqa: E402` with the reason. All behaviour-preserving.

**One gap these nineteen do not close, and it should be in the packet:**
`structural` ships nine modules and seven `st_*` tools with **no tests anywhere
in the repo**. It is accepted, installed capability that nothing verifies.

## 4c. Round three — build method, one identity, and the validation record

A third review corrected three preparation items. All accepted.

### [P1] The build method — my claim was wrong

Round two's receipt said "a real delivery must be built from the real checkout"
because the verification build named a temporary `.venv`. That is incorrect and
the reasoning was backwards: **source location and runtime interpreter are
independent inputs**, the builder takes `--python`, and going back to the shared
checkout would risk including unreviewed source — the exact hazard the isolated
candidate exists to avoid.

Rebuilt correctly, from the isolated candidate with the permanent interpreter
supplied:

| | value |
|---|---|
| bytes | 1,317,831 |
| sha256 | `5ada706cffea31c3c5d3634f32665be7509f6033a6172964e5df2949bc501097` |
| manifest `command` | `/Users/john/TokenEfficiencyEngine/server/.venv/bin/python` |
| temporary path in launch command | none |
| artifact runtime vs candidate | **set-equal and byte-equal**, 324 files |
| artifact runtime vs accepted | 0 removed, 0 added, 11 changed |

Resources checked separately: `icon.png`, `LICENSE`,
`docs/small-model-workflows.md`, `skills/tee-usage/SKILL.md` and `launch.py` are
identical to the installed copies. `README.md` differs by design — generated per
build with version, interpreter and commit embedded. The prior artifact hash is
superseded, not reused.

### [P2] One identity

`gpt6-packet-request.md` is rewritten rather than patched. It had accumulated a
nine-commit list, `5d188e0` labelled HEAD, an opening that still announced a
blocking decision its own §5 said had dissolved, and the disproved
"artifact of exporting" explanation of the packaging errors. All gone. The
document now names one candidate — `63d9308`, payload `397261a2…7ed22` — and
states plainly that later commits are documentation only.

It also now distinguishes the two tool counts instead of letting them sit
side by side: **232** is `cli.attach_all` with one `FakeAdapter`, the benchmark's
configured composition; **273** is a live client with its own adapters. Neither
validates the other, and any count in the packet must name its composition.

### The validation record, with a disposition for each item

| item | disposition |
|---|---|
| formatting failure | **fixed**, and verified through the normal gates — `ruff check` and `ruff format --check` both clean on the candidate |
| untracked restored-feature suites | **included** — 19 tests + 8 fixture/benchmark files, 665 passed |
| `structural` coverage | **no tests exist anywhere**; unresolved, escalated |
| full-suite orphan failure | **investigated, returned as a risk** — below |
| canonical suite | **3,007 passed, 23 skipped, 141 deselected**, isolated, project default exclusions |

Live tests omitted honestly: the 141 deselected are the project's own
`dcc/ml/network/llm/cfd/fdm` exclusions. No live client, DCC or model was
exercised.

### The orphan-process failure — mechanism found, defect not confirmed

`test_windtunnel_tools::test_an_orphaned_solver_is_named_and_can_be_stopped`
failed once, on candidate `9342903`. The failed run is preserved. It was **not**
rerun until green and its assertion was not weakened; the later green run is a
different candidate (`63d9308`, 19 test files added) and is reported as such.

The failure is not the timeout it looked like. `wt_status` returned
`state == "cancelled"` where the test expects `"orphan"`:

```
assert ('cancelled' == 'orphan')
```

Reading the path, `out["state"]` is seeded from
`prog.get("state") or run.get("state")` and the orphan branch is guarded by
`if out["state"] == "running"`. So any seed other than `running` skips
`orphan_check` entirely. The test's fixtures are **module-scoped** across 33
tests sharing one case and run directory, which is where a stale `cancelled`
can come from — consistent with this repo's recorded "a job reports cancelled
while its worker is still writing files" hazard.

Two hypotheses tested and **not** confirmed: a kill timeout (the assertion that
failed is before any kill), and an exec race making the child's cmdline briefly
unreadable — probed 12 times, 12/12 immediate matches, worst lag 8.4 ms.

So: **most consistent with test isolation under load, not product behaviour —
but the interleaving was not directly observed, so it is returned as an
unresolved validation risk, not a fixed defect.**

**One product-relevant observation from the investigation, worth a decision:**
`wt_status` only looks for an orphan when the recorded state is already
`running`. If a record says `cancelled` while the solver is in fact still
alive — precisely the situation after a cancel that failed to kill — the status
reports `cancelled` and never checks. The orphan detector is gated by the state
it exists to correct. Whether that is intended semantics is not mine to decide,
so it is raised rather than changed.

## 4d. Round four — the suite was deleting live directories

The most serious finding of the campaign, and mine to answer twice over: it is a
product defect, and I ran the amplifier six times today.

### What was happening

`purge._temp_workdirs()` globbed `tee-*` directories in
`tempfile.gettempdir()` **and** a hard-coded `/tmp`, and admitted every match.
`workdirs` is in `DEFAULT_CATEGORIES` and `older_than_days` defaults to **0.0**,
so age was no protection either. `test_purge.py`'s fixture isolates the project
`.tee` tree, but discovery never consults `project_root`, so three
`confirm=True` tests swept the real machine. Codex lost its review export, its
pytest log and a build in progress to exactly this.

**The product asserted what it never checked.** The category description says
these cost "nothing - these belong to processes that have exited"; the
docstring said "the processes that made them are gone, so there is no registry
to consult". Both were assumptions. The long-lived producers — the blender,
fusion, godot and freecad adapters and the asset library — hold their `mkdtemp`
directory open for the whole life of a running server.

### Impact on this machine, stated factually

I ran the full suite six times today, 13:04 to 14:10, against a **live TEE
server (pid 23740) with Blender attached**. Each run executed those three
confirmed sweeps. I did not record the temp namespace beforehand, so **I cannot
claim nothing of the owner's was destroyed.** What I can state: the surviving
bridge workdir is stamped 14:23, after my last run, which is consistent with it
having been swept and recreated. I have not attempted to reconstruct or remove
anything, and I claim no recovery.

### The fix

`kernel/workdirs.py` gives a workdir three states, asymmetric on purpose:

| state | evidence | treatment |
|---|---|---|
| `active` | our marker, owner still running | keep |
| `reclaimable` | our marker, owner provably gone | candidate |
| `unverified` | no marker, unreadable, or ambiguous | **keep, and say so** |

Only `reclaimable` is ever deleted. Legacy directories therefore stay forever —
the correct trade, since their existence is not permission to delete them and a
wrong deletion is unrecoverable. PID reuse is why the marker records the owner's
**start time** as well as its pid: a recycled pid reads `unverified`, never
`reclaimable`. Missing or unreadable evidence fails closed.

Also: containment and symlink refusal (following one turns purge into arbitrary
path deletion), a re-check of ownership and liveness **at deletion time** rather
than trusting the dry-run snapshot, and withheld directories reported as `kept`
with a reason — "unverified", never "orphaned".

### Test isolation, two layers

`test_purge.py` gets an autouse fixture pointing discovery at a root it owns.
`conftest.py` gets a global autouse floor pointing every *other* test at an
empty owned directory, so a test that never thought about purge finds nothing —
a new test cannot forget. Patching `TMPDIR` would not have sufficed: `/tmp` is
named in the source.

Five regressions, every one on freshly created fixture-owned directories and
never a real temp root: an outside sentinel **plus a `tee-`prefixed decoy**
that must both survive a confirmed sweep; unverified-is-kept-and-not-called-
orphaned; recycled pid; symlink not followed; and ownership re-checked between
dry run and delete.

### Proof on the real machine

The canonical suite was run once, with the temp namespace recorded before and
after:

```
directories REMOVED by the run : 0
the two pre-existing live dirs : both present
```

### A second finding the fix exposed

With the sweep no longer running, the suite's own leak is visible: adapter tests
construct Blender/Fusion/Godot adapters that `mkdtemp` and never clean up, and a
single run leaves **~330** `tee-*` directories behind. The destructive purge had
been masking this. They now carry ownership markers, so once the pytest process
exits they are legitimately `reclaimable` and a purge will collect them
properly — but the leak itself is real and worth a decision.

### Structural tests — my claim was false

I said they exist nowhere and must be written or the gap accepted. They are
committed on the local branch `codex/a84-reviewed-runtime` at `18666b3`.
Verified first that that branch's `structural/` and `kernel/jobs.py` are
byte-identical to this candidate, then recovered the three files **byte-
identical to the branch**, with provenance, without merging it or touching
current source.

Against candidate source: **23 passed, 22 skipped** — more than the 11 the
review extracted, because it took two of the three suites. All 22 skips are
explicit real-engine gates (`openseespy`, `oofem`), so **native solver behaviour
remains unverified here, and 23 checks are not structural engineering
validation.**

### Re-validation at the new identity

A purge source change moves the payload, so nothing from round three is reused:

| | value |
|---|---|
| candidate | `47765b7` |
| payload fingerprint | `d792b3397cac5b7a2807ea2f28a0812542de7600ca139cb6de3360f2e8625864` |
| files | 325 (was 324) |
| vs accepted | 0 removed, **1 added** (`kernel/workdirs.py`), **17 changed** |
| focused purge + structural | 40 passed, 22 skipped |
| canonical full suite | **3,035 passed, 45 skipped, 141 deselected, 0 failed** |
| `ruff check` / `ruff format --check` | clean / clean (516 files) |
| artifact | 1,321,782 bytes, `c3690fa6…115b4`, interpreter permanent, payload byte-equal to source |

The wind-tunnel orphan race passed in this run; its disposition in §4c stands
unchanged, since one green run is not a disposition.

## 5. Remaining limitations

- ~~Tests for the restored capabilities are still untracked.~~ **RESOLVED** —
  see §4b. Nineteen test files and their eight-file closure are committed and
  green. The residual is `structural`, which has no tests to commit.
- **The verification artifact is not a deliverable** (§2).
- **No live client check.** Registration was measured through `cli.attach_all`
  with a fake adapter, not through either real client.
- **Provenance is asserted from byte-equality**, not from git history: the 37
  restored files were never committed anywhere, so their authorship rests on
  their being identical to the accepted payload.
- **Lineage is mixed and git cannot separate it**, now more than before.

## 6. Identity

| | value |
|---|---|
| branch | `claude/token-efficiency-engine-5jv1dj` |
| baseline | accepted A84, `0e172448…fb252f`, 324 files |
| final candidate | `47765b7` (superseding `63d9308`; the purge fix moved the payload) |
| candidate payload | `d792b339…25864`, 325 files — 0 removed, **1 added**, **17 changed** vs accepted |
| verification artifact | `c3690fa6…115b4`, 1,321,782 bytes, built isolated with the permanent interpreter — **not a deliverable** |
| declared version | `0.30.1` |
| pushed | no |
| working tree | still shared; other sessions' non-runtime work untouched |
