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
| donut-class modelling | 4,431 | 9 | 349 | 3 | 92.1% |
| 100-object populate + what-changed | 49,283 | 23 | 6,585 | 3 | 86.6% |
| material pass over 10 objects | 11,590 | 22 | 1,420 | 2 | 87.7% |
| layout verification | 2,926 | 2 | 36 | 1 | 98.8% |
| **total** | **68,230** | | **8,390** | | **87.7%** |

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
| TEE ingest-once | 4,464 | 12 | 93.1% |

Fixture media are deliberately tiny; real drawing sets, 4K site
photos and drone footage widen the gap by an order of magnitude.

## Script lane: the conformance fix loop as one call (Phase 8)

The same 3-wall repair (check, fix each conflict, recheck)
executed as separate tool rounds vs one `tee_script` call whose
intermediate tool results never enter model context.

| | Context tokens | Rounds | Saving |
|---|---|---|---|
| separate tool rounds | 470 | 5 | |
| one tee_script call | 173 | 1 | 63.2% |

The script's cost is flat in loop length while round-based cost
grows linearly (~130 tok/conflict): measured 17.7% / 63.2% /
76.3% saved at 1 / 3 / 5 conflicts, approaching 100% as loops
grow.

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
| TEE | 828 | 6 | 93.5% |

## Physics: settle cost + variance floor (Phase 11)

A 4-body rigid settle (sequential frame stepping, quiescence
early-out) reports compact facts instead of per-frame data:

- settle report: ~222 tokens (0.0 s wall time, zero tokens while stepping)
- two-run determinism variance floor on this machine: **0.00 mm** - settle assertions use a 5 mm tolerance, safely above it (A19: same-machine only; never asserted across builds)

## Unreal: level population + Blueprint function (Phase 5c)

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
| naive (describe_toolset + call_tool per op) | 38,334 | 32 | |
| TEE | 2,349 | 4 | **93.9%** |

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
| TEE always-loaded (wire) | 16 | **2,465** |
| same, by `model_dump()` | 16 | 2,959 |
| flat server, one tool per capability | 96 | 11,292 |

Registering all seven modules (extract, assets, design, physical,
pins, uefn, kb) adds **0 tokens** to the always-loaded
surface - the 80 tools they contribute live behind the
meta-tools. Reaching one costs 725 tokens (one search +
one describe), so the flat design only pays off in a session that
uses more than ~15 distinct long-tail tools.

## Jurisdiction: legal force per regime (Phase 15.2)

One 7-element plan, checked under every regime TEE knows. The
same conflicts carry different legal force, so the responses
differ in severity, not just in wording.

| Region | Resolves to | Rules | Cap | Findings | Capped | Tokens |
|---|---|---|---|---|---|---|
| `US` | US | irc | CODE | 4 | 0 | 402 |
| `ZA` | ZA | sans | CODE | 7 | 0 | 992 |
| `NA-local-authority` | NA-local-authority | sans | STD | 7 | 7 | 1,206 |
| `NA-settlement` | NA-settlement | sans | STD | 7 | 7 | 1,098 |
| `NA-communal` | NA-communal | sans | STD | 7 | 7 | 1,239 |
| `NA` | NA-unresolved | sans | HEUR | 7 | 7 | 1,174 |

Answering the same question without TEE means reading the
applicable-law files into context - which regime governs the
site, and what the adopted standard requires:

| | Tokens | Saving |
|---|---|---|
| read the code corpus (4 files) | 32,089 | |
| one `plaus_check` | 1,452 | **95.5%** |

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
| paste INDEX.md (50,641) + full file (6,708) | 57,349 | | |
| kb_search + kb_read | 1,951 | 2 | **96.6%** |

Unlike the paste, the kb_* answer cannot arrive without its
confidence and jurisdiction flags - `needs-verification` content
is labelled in the response itself (A30/A31), not in a rule the
session has to remember.

*Generated by `benchmarks/run_benchmarks.py` against Blender 5.2.0 LTS (headless, TEE bridge).*
