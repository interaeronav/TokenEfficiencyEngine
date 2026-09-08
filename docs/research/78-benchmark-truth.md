# 78 — the benchmark tells the truth: tokens per task, measured against the server that ships

Design of record for **A77** (`CLAUDE_A77_SCRIPT.md` is the plan). Written
2026-09-08. Every number below was produced on the owner's Mac on that date by
`78-evidence/drift.py`; nothing here is remembered.

## 1. The observation

`CLAUDE.md` opens by saying TEE's core metric is **tokens per completed user
task**, and that *every design decision is judged by that metric first*. That
metric lives in `benchmarks/RESULTS.md`: 26 sections, **85 tabled numbers**.

Nothing re-runs them. Nothing asserts them. `grep -rl RESULTS.md server/tests`
returns nothing at all.

So the file that carries the project's stated first principle is a set of
measurements that were true on the day each was taken, and have been
declarations ever since. That is precisely the finding A76 landed against
`kernel/machine.py::ENGINES` — *a table of claims wearing the word "measured" in
a string field* — turned on the thing the repo says it judges everything by.

## 2. The drift, measured

It is not theoretical. The harness has fallen behind the server it measures:

| | |
|---|---:|
| a real server serves (every lane `cmd_serve` attaches) | **210 tools** — 17 always-loaded + 193 virtual |
| the benchmark's own harness measures | **141 virtual tools** |
| **invisible to the benchmark** | **52 tools — 27 % of the long tail** |

Three lanes `cmd_serve` attaches are absent from `benchmarks/run_benchmarks.py`:
**`windtunnel`** (A72), **`flightdyn`** (A75) and **`engines`** (A76). Every
campaign since A72 added tools the benchmark cannot see.

The consequence is not cosmetic. `run_surface_scenario` reports

```
surface: 17 always-loaded tools = 2129 tok on the wire; 141 virtual tools
would cost 20545 tok flat (89.6% saved); reach one = 548 tok
```

**89.6 % is computed over the corpus the harness can see, not the one that
ships.** The saving progressive disclosure actually delivers is larger — and
unknown, because nothing has measured it since A72. A headline number that
drifts *in TEE's favour* is still a number nobody has earned.

## 3. Why this is a lane-shaped problem and not a chore

Three properties make it worth a campaign rather than an afternoon:

1. **It recurs by construction.** Every lane added since A72 has widened the
   gap, and nothing failed. The next lane widens it further. A fix that only
   adds the three missing lanes is a fix with a half-life of one campaign.
2. **The repo has already been bitten by exactly this.** The recorded lesson is
   *"a number quoted in prose needs a test — the surface figure went stale for
   four commits because only the tool COUNT had a canary."* The count had a
   canary; the token figure did not. Here, neither does.
3. **It is the one metric with no owner.** Licences have a gate. The tool
   surface has nine assertions. Trust has a table. Tokens per task — the stated
   first principle — has nothing.

## 4. The design

**One source of truth for what a server is.** `cmd_serve` and the benchmark
harness must build the same registry from the same list, so a lane cannot be
attached to one and not the other. A test asserts they agree, and it fails when
they diverge — which is the canary the surface figure never had.

**Every runnable row re-measured, and every unrunnable row labelled.** Some
sections need a DCC, a solver, or a live model stack. Those are not deleted and
not quietly left to rot: they carry the date they were taken and what they need,
so a reader can tell a current number from a historical one at a glance.

**The numbers that can be asserted, are.** Not all 85 — a token count that moves
by three is not a regression. The invariants worth pinning are the ones a change
would break silently: the always-loaded surface, the corpus size the saving is
computed over, and each lane's headline ratio within a stated band.

## 5. What this campaign will not do

Re-measure rows that need hardware this machine does not have, and pretend
otherwise. Delete history — a superseded number is dated, not removed. Chase
every one of the 85 figures into a test; a canary that fires on noise teaches
people to silence it. Change any measured number to make a ratio look better.

## 6. Open questions

1. **How many of the 26 sections are runnable on this machine today?** Some need
   Blender, OpenFOAM, a live model stack. P1 counts them before promising.
2. **What is the true saving?** 89.6 % is over 141 tools; the real corpus is
   193. The honest figure is unknown until P2 runs.
3. **Where does the shared lane list live** — `cli.py`, a new module, or a data
   file both import? P1 decides on the smallest seam.
4. **Does any current row fail its own re-measurement?** If a lane's ratio has
   genuinely moved, that is a finding, not a fix.

## 7. Sources

`benchmarks/RESULTS.md`, `benchmarks/run_benchmarks.py`,
`server/src/tee/cli.py::cmd_serve`, and `78-evidence/drift.py` →
`drift-2026-09-08.log`.
