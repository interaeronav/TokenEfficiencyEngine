# 78-evidence — what produced the numbers in research doc 78

Produced on the **owner's Mac** on 2026-09-08 against the branch tip. One
script, stdlib plus the server's own imports; it starts nothing and measures
only what the repo already contains.

```bash
cd server && uv run --no-sync python ../docs/research/78-evidence/drift.py
```

| file | what |
|---|---|
| `drift.py` | builds the server `cmd_serve` builds, builds the one the benchmark harness builds, and reports the gap. Reads the lane lists out of the SOURCE rather than restating them, so it cannot itself go stale the way the thing it measures did |
| `drift-2026-09-08.log` | what it printed |

**The finding.** A real server serves **210 tools** (17 always-loaded + 193
virtual). The benchmark harness measures **141 virtual tools** — **52 tools, 27
per cent of the long tail, are invisible to it**, because `windtunnel` (A72),
`flightdyn` (A75) and `engines` (A76) are attached by `cmd_serve` and not by
`run_benchmarks.py`. Its headline "89.6 % saved" is computed over the corpus it
can see rather than the one that ships; through the real list it is **93.2 %
over 197 virtual tools**, so the stale number understated the saving rather than
flattering it.

**And nothing would have caught it.** `RESULTS.md` carries 26 sections and 85
tabled numbers; `grep -rl RESULTS.md server/tests` returns nothing.

One deliberate choice in the script: the two lane lists are extracted with
regexes over `cli.py` and `run_benchmarks.py` rather than written down here. A
measurement of staleness that hard-codes what it measures would go stale in the
same way, and this file would then be one more number nobody re-ran.
