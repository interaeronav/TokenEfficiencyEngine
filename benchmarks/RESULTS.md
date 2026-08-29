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
| naive re-attach | 65,052 | 44 | |
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
| TEE always-loaded (wire) | 17 | **2,028** |
| same, by `model_dump()` | 17 | 2,494 |
| flat server, one tool per capability | 103 | 11,274 |

Registering all seven modules (extract, assets, design, physical,
pins, uefn, kb) adds **0 tokens** to the always-loaded
surface - the 86 tools they contribute live behind the
meta-tools. Reaching one costs 545 tokens (one search +
one describe), so the flat design only pays off in a session that
uses more than ~20 distinct long-tail tools.

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
| kb_search + kb_read | 1,899 | 2 | **96.7%** |

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
| TEE (meta-tool reach + budgeted results) | 1,614 | 5 | **95.4%** |

## Fabrication: tokens per completed drawing-set (A37)

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

*Generated by `benchmarks/run_benchmarks.py` against Blender 5.2.0 LTS (headless, TEE bridge).*

## Routing: the four-arm benchmark (A42 R4, 2026-08-29)

24 mixed-difficulty cases (6 trap/control + 16 size-ladder + 2 field
phrasing cases from the T6 dry-run report), live engines, quiet
machine; the routed arm's swap seconds inside its wall, ledger
respected.

| arm | verified | wall s | server tok | client tok |
|---|---|---|---|---|
| all-q14b | 21/24 | 50.8 | 21,172 | 0 |
| **routed** | **24/24** (22 local + 2 escalated) | 125.8 | per-engine metered | **1,667** |
| all-q27b (swap-in 0.8 s, warm) | 18/24 | 211.7 | 21,172 | 0 |
| all-client (reference) | 24/24 by construction | — | 0 | 19,603 |

The routed arm is the only one matching the reference tier's verified
quality, at **91.5% fewer client tokens** than all-client: 22/24
verified locally, the 2 known both-engines-fail cases (the rerank
cliff) escalated with budgeted pointer-only briefs (escalation rate
0.083; 3 implicit swaps counted). all-q27b is WORSE than all-q14b
(18 vs 21) at 4x the wall — the R0 non-monotonic ladder, re-proven on
the adoption row. **The router earns adoption.**
