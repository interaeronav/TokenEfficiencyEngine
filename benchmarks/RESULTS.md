# Token benchmark results

Same live headless Blender, same wire protocol, two interface styles:
**naive** (one code request per op + full scene dump after every
mutation + full-res screenshots - the dominant existing-bridge
pattern) vs **TEE** (typed batches, diffs, compact summaries,
geometric assertions, budgeted capture). Metric: estimated context
tokens of all requests + responses (chars/3.5; images
ceil(w/28)*ceil(h/28)).

| Scenario | Naive tokens | Naive calls | TEE tokens | TEE calls | Saving |
|---|---|---|---|---|---|
| donut-class modelling | 4,431 | 9 | 295 | 3 | 93.3% |
| 100-object populate + what-changed | 49,283 | 23 | 5,311 | 3 | 89.2% |
| material pass over 10 objects | 11,590 | 22 | 980 | 2 | 91.5% |
| layout verification | 2,926 | 2 | 36 | 1 | 98.8% |
| **total** | **68,230** | | **6,622** | | **90.3%** |

## Extraction: ingest-once vs media re-billing

A simulated 4-session build over one media set (DXF plan,
vector-PDF sheet, walkthrough video, DJI SRT, 3 site photos, audio
brief - the in-repo synthetic fixtures). **Naive** re-attaches the
media to context every session (raw DXF text, sheet render, photos,
video frames, transcript). **TEE** ingests once - deterministic local
extraction, zero tokens while it runs - then every session reads
compact facts from the content-addressed store, plus one bounded
contact sheet and one 300-token detail crop in total.

| | Tokens | Round-trips/attaches | Saving |
|---|---|---|---|
| naive re-attach | 65,048 | 44 | |
| TEE ingest-once | 4,467 | 12 | 93.1% |

Fixture media are deliberately tiny; real drawing sets, 4K site
photos and drone footage widen the gap by an order of magnitude.

## Script lane: the conformance fix loop as one call (Phase 8)

The same 3-wall repair (check, fix each conflict, recheck)
executed as separate tool rounds vs one `tee_script` call whose
intermediate tool results never enter model context.

| | Context tokens | Rounds | Saving |
|---|---|---|---|
| separate tool rounds | 332 | 5 | |
| one tee_script call | 173 | 1 | 47.9% |

The script's cost is flat in loop length while round-based
cost grows linearly, so the saving widens with every extra
conflict. (Leaner per-round responses narrow the headline
percentage without costing a token - both arms got cheaper.)

## Assets: find-select-place (Phase 9)

Find, license-check, scale, place, and verify 3 sofas.
**Prior art** is the wire-measured community-integration flow
(docs/research/22): mandatory strategy prompt, per-provider
status round-trips, alphabetical catalog slices, per-candidate
inline previews, before/after screenshots. **TEE** is measured
live in this run: one faceted search (<=5 ranked rows), three
checkpointed imports with the scale policy, one relational
placement plan solved+validated server-side, one render-free
verification report - zero images.

| | Tokens | Calls | Saving |
|---|---|---|---|
| prior-art flow | 12,767 | 25 | |
| TEE | 762 | 6 | 94.0% |

## Physics: settle cost + variance floor (Phase 11)

A 4-body rigid settle (sequential frame stepping, quiescence
early-out) reports compact facts instead of per-frame data:

- settle report: ~202 tokens (0.0 s wall time, zero tokens while stepping)
- two-run determinism variance floor on this machine: **0.00 mm** - settle assertions use a 5 mm tolerance, safely above it (A19: same-machine only; never asserted across builds)

## Unreal: level population + Blueprint function (Phase 5c)

*(not re-run this pass - scenario skipped on this machine; last measured values kept)*

Live UE 5.8.1 editor with Epic's official MCP server. The naive
side is not a straw man - it is the workflow Epic's own
`unreal-mcp` skill prescribes: `list_toolsets`, then
`describe_toolset` for each toolset you intend to use, then one
`call_tool` per operation, reading the level back as refPaths
plus a transform call per actor. TEE uses compact signatures, one
typed batch for the whole population, short session ids, and one
verified Blueprint macro.

| | Context tokens | Round-trips | Saving |
|---|---|---|---|
| naive (describe_toolset + call_tool per op) | 38,331 | 32 | |
| TEE | 2,346 | 4 | **93.9%** |

The schema dumps dominate the naive side: one
`describe_toolset(BlueprintTools)` alone is ~18,000 tokens, more
than six times TEE's entire always-loaded tool surface. Every UE
tool call is also serialized on the editor's game thread at
~0.37 s, so the round-trip reduction is wall-clock as well as
tokens.

## Tool surface: progressive disclosure (P4/A6)

The always-loaded MCP surface, measured as the wire actually
carries it (`by_alias`, `exclude_none` - what the SDK sends). A
bare `model_dump()` counts ~490 tokens of `null` padding for
fields no client ever sees, so it overstates the surface by ~20%.

| | Tools | Tokens |
|---|---|---|
| TEE always-loaded (wire) | 17 | **2,033** |
| same, by `model_dump()` | 17 | 2,500 |
| flat server, one tool per capability | 137 | 15,454 |

Registering all seven modules (extract, assets, design, physical,
pins, uefn, kb) adds **0 tokens** to the always-loaded
surface - the 120 tools they contribute live behind the
meta-tools. Reaching one costs 548 tokens (one search +
one describe), so the flat design only pays off in a session that
uses more than ~28 distinct long-tail tools.

## Jurisdiction: legal force per regime (Phase 15.2)

One 7-element plan, checked under every regime TEE knows. The
same conflicts carry different legal force, so the responses
differ in severity, not just in wording.

| Region | Resolves to | Rules | Cap | Findings | Capped | Tokens |
|---|---|---|---|---|---|---|
| `US` | US | irc | CODE | 4 | 0 | 386 |
| `ZA` | ZA | sans | CODE | 7 | 0 | 967 |
| `NA-local-authority` | NA-local-authority | sans | STD | 7 | 7 | 1,176 |
| `NA-settlement` | NA-settlement | sans | STD | 7 | 7 | 1,068 |
| `NA-communal` | NA-communal | sans | STD | 7 | 7 | 1,209 |
| `NA` | NA-unresolved | sans | HEUR | 7 | 7 | 1,144 |

Answering the same question without TEE means reading the
applicable-law files into context - which regime governs the
site, and what the adopted standard requires:

| | Tokens | Saving |
|---|---|---|
| read the code corpus (4 files) | 32,086 | |
| one `plaus_check` | 1,399 | **95.6%** |

The `jurisdiction` block costs 48-383 tokens depending on the
regime; communal land carries the longest advisory because it
is where 'no code applies' is most easily misread as 'anything
goes'. It repeats on every call, so a session running many
checks under one regime pays it each time - per-session
suppression is the obvious next saving and is not yet built.

## Knowledge Base: sourced answer vs pasted corpus (Phase 16)

The task: what bedding-sand and jointing-sand spec applies to
concrete block paving, with a citation. The naive side pastes
the corpus's own INDEX.md to find the file, then the whole file
(without the module, sections are not addressable). TEE runs one
kb_search and one budgeted kb_read of the 'Key facts' section,
with the file's Sources block and confidence/jurisdiction flags
riding along.

| | Tokens | Calls | Saving |
|---|---|---|---|
| paste INDEX.md (50,762) + full file (6,708) | 57,470 | | |
| kb_search + kb_read | 1,865 | 2 | **96.8%** |

Unlike the paste, the kb_* answer cannot arrive without its
confidence and jurisdiction flags - `needs-verification` content
is labelled in the response itself (A30/A31), not in a rule the
session has to remember.

## Web lookup: five documentation questions (A34)

The task: answer each question from its documentation page, cited.
The naive arm pays the page's own clean visible text in context -
what a good host-side fetch tool injects; raw HTML is 2-30x worse
(research 49). TEE pays the tool arguments plus the budgeted,
cited tee_web_lookup answer.

| Question | Page text | tee_web_lookup | Saving |
|---|---|---|---|
| when must free() be called on a bmesh? | 22,752 | 589 | **97.4%** |
| how thick should the bedding sand layer be? | 5,225 | 585 | **88.8%** |
| how do I test whether an address is private? | 9,569 | 604 | **93.7%** |
| what is the maximum line length and its exceptions? | 13,008 | 589 | **95.5%** |

Total 50,554 -> 2,367 tokens (**95.3% saved**). The tool's one-time always-loaded cost is 180 tokens on the canonical wire - repaid by the first question of the session.

- https://pypi.org/project/trimesh/ answered with its bot-challenge variant; excluded

## Gateway: fronting a many-tool MCP backend (A37)

The task: list a project folder, read its config, read its 2,000-line
build log - against secure-filesystem-server@0.2.0 (14 tools), the
official filesystem reference server. **Naive** is the backend's own
README pattern: every tool schema in context for the whole session
(3,706 tokens before the first call) plus raw results.
**TEE** fronts the same live server through the existing meta-tools
(always-loaded delta: 0, asserted by test), pays one search + one
describe to reach the tools, and budgets results with the truncation
reported (1 of 3 results trimmed here - the
2,000-line log arrives as a bounded excerpt with the raise-max_tokens
fix named, which is the point).

| | Tokens | Calls | Saving |
|---|---|---|---|
| naive (schemas in context + raw results) | 35,238 | 3 | |
| TEE (meta-tool reach + budgeted results) | 1,425 | 5 | **96.0%** |

## Senses — what an image question costs the HOST (A47/A48 P0)

Frame `DJI_0100_0060.jpg` (3840x2160), one question, two hosts.

| host | how it sees | host tokens |
|---|---|---|
| seeing | `tee_media`, full frame | 10,764 |
| seeing | `tee_media`, default budget (1002x563) | 756 |
| blind | `sense_describe` (local model reads it) | 65 |

**11.6x** cheaper than a budgeted image, **165.6x** than the full frame. 14.6s wall, `off_machine_calls: 0`, provider claude-qwen-vl (local, 17.0 GB).

This supersedes an informal *33x* quoted during A47, which compared the
PROVIDER's input tokens against the answer rather than what a host pays.
Both arms here are measured host-side. The provider still reads ~2,065
tokens of pixels — for free, on a model that bills nothing, which is the
point rather than the headline.

## Fabrication: tokens per completed drawing-set (A37)

*(not re-run this pass - scenario skipped on this machine; last measured values kept)*

The task: a 600x400x18 mm panel with a pocketed slot, dimensioned
drawing sheet, STEP out - against live FreeCAD 1.1.3. **Naive** is
the FreeCAD-MCP genre pattern: every tool schema in context, one op
per call, a screenshot in every response, the 'blueprint' as pixels.
**TEE** solves sketches server-side, compiles each batch to ONE
bridge script, budgets read-backs, and derives the sheet FROM the
model (dimension values read from the document - the research-52
'not suitable' failure mode structurally closed).

| | Tokens | Calls | Saving |
|---|---|---|---|
| naive (schemas + per-op screenshots) | 10,655 | 6 | |
| TEE (solved batches + sheet files) | 805 | 4 | **92.4%** |

## Garment lane: draft, sew, drape, fit (A53)

One tee block - 4 panels, 10 seams, 5,076 particles - drafted, arranged on a body, draped and
measured. The naive arm reads what a model must read WITHOUT compact state:
every panel outline, then the draped mesh. The TEE arm is one batch, its
diff, and one `sk_fit` call.

| arm | tokens | calls |
| --- | ---: | ---: |
| naive (outlines + draped mesh) | 80,553 | 5 |
| tee (batch + diff + sk_fit) | 573 | 2 |
| **saved** | **99.3%** | |

Drape took 5.1 s; seams closed to 0.584 mm mean; worn: True.
The always-loaded surface is unchanged at 17 tools - seamkiln joins through
the Adapter protocol and six `sk_*` virtual tools.

## Scheduler: the mixed-load row (A42 K4, 2026-08-29)

*(not re-run this pass - scenario skipped on this machine; last measured values kept)*

Identical live workload per arm (2 real reconstructions + 8 real
hillshade jobs + 6 live routed chores), quiet machine:

| arm | makespan s | interactive p95 s | chores | client tok |
|---|---|---|---|---|
| static (FIFO) | 15.0 | 11.65 | 6/6 | 0 |
| **scheduled** (QoS+reservation+greedy) | 16.4 | **7.18 (−38%)** | 6/6 | 0 |

Interactive latencies, static: 8.02–12.33 s; scheduled: 2.45–7.38 s —
the entire distribution shifted, first interactive done in 2.45 s vs
8.02. The +1.4 s makespan premium is the reserved worker's stated
price. No head-of-line blocking — the named mechanism, delivered.
**The scheduler earns its existence; the off-switch remains.**

## The pipeline lane: two real projects (A43 P6, 2026-08-30)

*(not re-run this pass - scenario skipped on this machine; last measured values kept)*

`benchmarks/run_p6_pipeline.py`, measured on this machine against the
owner's own projects — nothing stubbed. The naive column is what actually
lands in context without the lane: the command pasted in, then whatever
the command prints, plus a listing of the outputs when artifacts are the
point. Nothing is trimmed by hand on either side.

| project | step | kind | naive tok | lane tok | saved | wall |
|---|---|---|---|---|---|---|
| basemap | plan | produce | 298 | **76** | **−74.5%** | 0.22 s |
| basemap | selftest | query | 51 | 59 | +15.7% | 0.05 s |
| okongosim | dimensions_selftest | query | 414 | 415 | −0.2% | 0.56 s |
| okongosim | validate_catalog | query (fails) | 170 | 210 | +23.5% | 0.05 s |
| basemap | verify | query (fails) | 51 | 75 | +47.1% | 133.5 s |
| basemap | selftest, asked again | query | 51 | **42** | **−17.6%** | 0.00 s vs 0.05 s |
| basemap | verify, asked again | query (fails) | 51 | 75 | +47.1% | 133.5 s — **re-ran** |

**Read this honestly: the lane wins decisively in one place and loses
slightly in another, and the losing rows are not a rounding error.**

**Where it wins.** A produce step replaces a build log with a diff over
what the step declared it would write: 298 tokens of scope counts,
geocell totals and "wrote …" lines become 76 tokens naming three files,
their sizes and their hashes. That is the case the lane exists for, and
it gets better as the build gets chattier, because the answer's size is
set by the declaration rather than by the tool's verbosity.

**Where it loses.** On a query whose command is short and whose output
is already one line, the lane returns that same line plus a step name and
two hashes, so it costs 8–40 tokens MORE than pasting the command would.
Those tokens buy a command that cannot be misremembered, an inputs hash
that says what the answer was computed from, and the refusal envelope
around it. That is a real trade and it is stated rather than averaged
away.

**The repeat rows are the interesting ones.** A successful query asked a
second time is answered from the record: fewer tokens and no wall clock
at all. A FAILING query asked again re-runs in full — 133 seconds — and
that is correct, not a miss: only successful runs are recorded, so a
failing check is never cached into looking fixed.

**Not counted in the naive column, and it favours naive:** constructing
the basemap command means reading a 40-line runbook and copying 16 argv
elements exactly. Getting that wrong is the friction this whole project
exists to remove, and the benchmark charges the naive path nothing for
it.

**Two lane trims came out of these numbers**, both measured before and
after: provenance dropped the step name and start time it was repeating
from the payload and the manifest (and shortened its hashes to 8 hex),
and terminal colour codes are stripped from captured output — worth ~20
tokens on one project's test output, where each escape costs ten
characters once JSON-encoded. A cached answer also now returns in the
same compact shape as a fresh one; it had been arriving in a fatter
envelope than the answer it replaced, at 81 tokens against 59.

## The headless fleet: compact answers (A45 P2, 2026-08-31)

*(not re-run this pass - scenario skipped on this machine; last measured values kept)*

Each row is one answer from a fleet family. **Naive** is that family's own
natural output — the full solution vector, every portfolio weight, the
provider's raw JSON, the whole equity curve. **TEE** is the compact answer
plus a stable id; the naive form remains reachable through the family's
`_detail` call, which is the point rather than a caveat.

| scenario | naive | TEE | saved |
|---|---|---|---|
| `solve_program`, 400 variables / 250 non-zero | 1,489 | 127 | **91.5%** |
| `quant_optimize`, 120-asset universe | 666 | 266 | **60.1%** |
| `bi_query`, 3 rows against a live Cube 1.7.30 | 673 | 60 | **91.1%** |
| `trade_backtest`, 2,000 bars | 2,860 | 170 | **94.1%** |
| **total** | **5,688** | **623** | **89.0%** |

Measured on this machine with TEE's own `estimate_tokens`, against live
services where one exists — the Cube row is its actual HTTP response, not
a model of one. The quant row is the weakest and is stated as such: a
120-asset weight vector is not enormous to begin with, so compaction buys
less there than it does on a solver or a time series.

The always-loaded surface is **unchanged at 17 tools / 2,028 tok** across
the whole campaign: every fleet tool is virtual, reached through
`tee_search_tools` → `tee_call`.

*Generated by `benchmarks/run_benchmarks.py` against Blender 5.2.0 LTS (headless, TEE bridge).*
