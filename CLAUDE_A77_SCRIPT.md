# CLAUDE_A77_SCRIPT.md — the benchmark tells the truth

**Owner directive (2026-09-08):** *"start A77 P0"*, then *"continue all phases
without my input"*. The campaign's subject was chosen by the session from
measured evidence, recorded in `docs/DECISIONS.md`, and is reversible.

Campaign **A77**; research doc **78** the design of record; server
**0.29.0 → 0.30.0**. `A77` and doc `78` were confirmed free in both series
immediately before the first commit — a check A75 learned the hard way, having
been written as A74 while a parallel session pushed A74 first.

## Read this first

`CLAUDE.md` says TEE's core metric is **tokens per completed user task** and
that *every design decision is judged by that metric first*. That metric lives
in `benchmarks/RESULTS.md` — 26 sections, 85 tabled numbers — and **nothing
re-runs it and nothing asserts it**. This campaign is not about making the
numbers better. It is about making them true, and making them fail when they
stop being true.

## Orientation for a cold session

- Repo `/Users/john/TokenEfficiencyEngine`, branch
  **`claude/wind-tunnel-aerodynamic-integration-hcsa7u`**. A parallel session
  works this same branch: read `docs/PROGRESS.md` first, commit through a
  temporary index with explicit paths, never `git add -A`, `git reset -q` after
  each, and edit the shared docs in place.
- Suites: `cd server && uv run --no-sync pytest -q` · `make lint`. **Never
  `uv sync` in `server/`** — it drops the pip-installed extras.
- **Surface invariant: 17 always-loaded tools.** A77 adds ZERO tools. It is a
  campaign about measurement, not capability.

## Measured facts (2026-09-08 — build ON them)

1. **A real server serves 210 tools** (17 always-loaded + 193 virtual). **The
   benchmark harness measures 141.** 52 tools — **27 % of the long tail** — are
   invisible to it.
2. **Three lanes are attached by `cmd_serve` and not by the harness**:
   `windtunnel` (A72), `flightdyn` (A75), `engines` (A76). Every campaign since
   A72 widened the gap and nothing failed.
3. **`run_surface_scenario` reports 89.6 % saved** over that 141-tool corpus.
   The true figure is unknown and is larger — a headline that drifts in TEE's
   own favour is still one nobody has earned.
4. **`RESULTS.md` has 26 sections and 85 tabled numbers; no test references the
   file at all.** The surface COUNT has nine assertions; the surface token
   FIGURE has none, which is the shape of the recorded lesson *"a number quoted
   in prose needs a test"*.
5. `INSTRUCTIONS_CAP_BYTES` is 2,048 and `instructions()` currently renders
   **1,583 bytes (77 %)** in its rich form — not degraded, but a ceiling that
   every lane pushes toward, with a silent two-step fallback behind it.

## Phases

- **P0** — doc 78, this script, `78-evidence/drift.py` and its log, the ruling
  in `DECISIONS.md` (subject chosen by the session, on evidence), the
  `00-index.md` row. *Acceptance:* every fact carries the command that produced
  it; the drift script reads the lane lists out of the source rather than
  restating them, so the measurement cannot go stale the way its subject did.
- **P1** — **one source of truth for what a server is.** `cmd_serve` and the
  harness build the same registry from the same list. A test asserts they agree
  and names any lane present in one and not the other. *Acceptance:* deleting a
  lane from either side fails the suite; the benchmark's virtual-tool count
  equals the served registry's.
- **P2** — **re-measure every runnable row**, and label every unrunnable one
  with the date it was taken and what it needs. *Acceptance:* a count of
  runnable vs held sections stated before the work, and each re-measured figure
  recorded with its command. A row that moved is a finding, written up, not
  quietly overwritten.
- **P3** — **the canary.** The invariants worth pinning get asserted: the
  always-loaded surface figure, the corpus size a saving is computed over, and
  each lane's headline ratio within a stated band. *Acceptance:* changing a
  lane's tool count fails a test that names the row it invalidated. A band wide
  enough not to fire on noise, and stated in the test.
- **P4** — close: `CLAUDE.md` bullet, CHANGELOG **0.30.0**, PROGRESS block with
  what is held and why, version ×3, `make mcpb` + clean-unzip verify.

## Laws

1. **A measurement nothing re-runs is a declaration with a date on it.**
2. **The harness builds the server that ships**, from the same list, or the
   suite fails.
3. **A held row is dated and labelled, never deleted and never quietly kept.**
4. **A number is never changed to make a ratio look better.** A row that moved
   is written up as a finding.
5. **A canary that fires on noise gets silenced**, so bands are stated and wide
   enough to mean something.
6. Zero tools added. The surface stays 17.

## Non-goals

Re-measuring rows that need hardware this machine lacks, and pretending
otherwise · deleting superseded numbers rather than dating them · asserting all
85 figures · optimising any benchmark · touching another session's in-flight
lane.

## Amendments learned while building

*(Append here as the build teaches; the script is amended, not improvised
around.)*
