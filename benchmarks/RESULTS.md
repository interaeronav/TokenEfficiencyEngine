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
| separate tool rounds | 337 | 5 | |
| one tee_script call | 173 | 1 | 48.7% |

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

## Flight dynamics: a polar becomes an aircraft that flies (A75)

The lane's whole loop on a generated aircraft — probe, generate from an
eight-point polar, trim, take the modes, then fly the trim for a minute — against
what a model must otherwise read to reach the same answer.

| Arm | Tokens | Calls |
|---|---|---|
| naive (the aircraft XML authored and read back, the property catalogue, 60 s of six states at 120 Hz, the raw A and B) | 131,179 | — |
| TEE (`fd_probe` to `fd_fly`, digests only) | **835** | 5 |

**Saving: 99.4%** — a factor of 157. Per call: `fd_probe` 128, `fd_aircraft` 90,
`fd_trim` 128, `fd_modes` 334, `fd_fly` 155.

_A77 P2 re-measured this: it read **898** and was taken by hand in a shell, with
no scenario behind it. `run_flightdyn_scenario` now re-runs it like every other
row. It holds rather than guesses when jsbsim is absent._

The naive arm is dominated by one term: the time history is 125,206 of its
131,179 tokens, and it grows linearly with every second flown and every state
watched — sixty seconds of *six* states here, where the model has 656 properties
available and a mission is not a minute. The TEE arm is flat: the reply is the
trim state, the verdict and the mode table whatever the flight length, capped at
64 elements per array and 2 KB per string, and a test asserts the whole reply
stays under 4 KB.

The mode table is why the lane is cheap rather than merely terse. A and B at a
trim point are 950 tokens raw and 363 as a digest that has already named each
mode by its modal participation — and they are where stability derivatives and
handling qualities start, so the expensive part of a flight-dynamics answer is a
small matrix rather than a trajectory.

_(recorded 2026-09-07 on the owner's Mac against jsbsim 1.3.1, through
`app.registry.call` with the real engine; token counts by the repo's own
`estimate_tokens`.)_
_Flight dynamics: re-measured this run at 835 tokens over 5 calls._


## Engine lane: is the router's table still true? (A76)

`eng_scan` then `eng_reconcile` on the owner's live stack, against what a model
must otherwise read to answer "which local engines can this machine actually
use, and are the router's numbers still true".

| Arm | Tokens | Calls |
|---|---|---|
| naive (`machine.py`, `profiles.py`, `router.py`, `llm/tools.py`, `local_llm.py`, the head of `chores.py`, `.tee/config.toml`, the shim's `litellm.yaml`) | 21,979 | — |
| TEE (`eng_scan` 57 + `eng_reconcile` 289) | **346** | 2 |

**Saving: 98.4%** — a factor of 64, on a machine with **nothing running**.

_W0 (2026-09-13) moved this row **311 → 346**, and the canary caught it on the
same run that caused it. The cause is not drift: `q27b-think` was added to
`ENGINES`, so `eng_reconcile` has one more engine to report (254 → 289 tokens);
`eng_scan` is unchanged at 57 because the scenario still pins every endpoint to
a closed port. A row that grows because the table it summarises grew is the
number doing its job. Re-measured, not adjusted._

_A77 P2 re-measured this and found the row was not reproducible. It read **375**,
taken against a live stack where `eng_scan` had endpoints to describe; the
scenario pins every endpoint to a closed port, where the same call costs 57.
Both are true and they answer different questions, which is why the row says
which one it is._

_And P3's canary immediately caught the same mistake again: the row moved
**311 → 364** between two runs an hour apart, because `eng_scan` genuinely
probes localhost and the owner's model stack had come back up — so the
"hermetic" scenario was measuring the developer's machine. It is now pinned to a
port nothing can answer and returns 311 on three consecutive runs with the stack
up. **The cost scales with what is answering**: 57 tokens for `eng_scan` against
nothing, 75 against four live endpoints. A benchmark number that omits the
machine state it was taken in cannot be re-run — the campaign's own thesis,
caught by the campaign's own gate, on the campaign's own row._

**And the naive arm does not answer the question.** Four of the eight routes the
shim advertises return HTTP 200 with empty content; that fact is in none of
those eight files and costs a live probe. Reading everything TEE knows about its
engines still leaves you unable to say which of them work.

The larger cost is not the digest. A wrong `ENGINES` row is paid on every chore,
for as long as it stands: the registry declares `q27b-bare` at 3.07–9.69 s and
an audition measured 44–47 s on the same machine, so the ladder was sorting on a
number five times off. Every chore routed on that order pays for it.

_(recorded 2026-09-07 on the owner's Mac through `app.registry.call` against the
live stack; token counts by the repo's own `estimate_tokens`.)_
_Engine lane: re-measured this run at 311 tokens over 2 calls._


## Tool surface: progressive disclosure (P4/A6)

The always-loaded MCP surface, measured as the wire actually
carries it (`by_alias`, `exclude_none` - what the SDK sends). A
bare `model_dump()` counts ~490 tokens of `null` padding for
fields no client ever sees, so it overstates the surface by ~20%.

| | Tools | Tokens |
|---|---|---|
| TEE always-loaded (wire) | 17 | **2,129** |
| same, by `model_dump()` | 17 | 2,596 |
| flat server, one tool per capability | 216 | 31,464 |

Attaching **every lane a served TEE has** adds **0 tokens** to the
always-loaded surface - the **199** tools they contribute live
behind the meta-tools, a **93.2%** saving. Reaching one costs 544
tokens (one search + one describe), so the flat design only pays
off in a session that uses more than ~57 distinct long-tail tools.

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
| how thick should the bedding sand layer be? | 5,164 | 585 | **88.7%** |
| how do I test whether an address is private? | 9,569 | 604 | **93.7%** |
| what is the maximum line length and its exceptions? | 13,008 | 589 | **95.5%** |
| what does trimesh do and what are its core dependencies? | 12,022 | 578 | **95.2%** |

Total 62,515 -> 2,945 tokens (**95.3% saved**). The tool's one-time always-loaded cost is 180 tokens on the canonical wire - repaid by the first question of the session.

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

**11.6x** cheaper than a budgeted image, **165.6x** than the full frame. 14.5s wall, `off_machine_calls: 0`, provider claude-qwen-vl (local, 17.0 GB).

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

One tee block - 4 panels, 10 seams, 4,461 particles - drafted, arranged on a body, draped and
measured. The naive arm reads what a model must read WITHOUT compact state:
every panel outline, then the draped mesh. The TEE arm is one batch, its
diff, and one `sk_fit` call.

| arm | tokens | calls |
| --- | ---: | ---: |
| naive (outlines + draped mesh) | 73,098 | 5 |
| tee (batch + diff + sk_fit) | 669 | 2 |
| **saved** | **99.1%** | |

Drape took 8.0 s; seams closed to 0.19 mm mean; worn: True.
The always-loaded surface is unchanged at 17 tools - seamkiln joins through
the Adapter protocol and fourteen `sk_*` virtual tools (six at A53; the A65
audit added `sk_hardware`, `sk_avatar`, `sk_touch`, `sk_handoff` and friends).

## Garment lane: dress, zip, walk, hand off (A65)

A zipped jacket - 5 panels, 11,924 particles - wrap-arranged and DRESSED on the
figure, zipped, walked 4 frames at the gait's own speed, and handed off to Blender.
The naive arm reads what a model must read WITHOUT compact state: every panel
outline, the dressed mesh, the mesh again for every frame of the walk, and the
hardware as geometry. The TEE arm is one batch, its diff, and one `sk_hardware`
call.

| arm | tokens | calls |
| --- | ---: | ---: |
| naive (outlines + dressed mesh + per-frame meshes + hardware) | 526,350 | 11 |
| tee (batch + diff + sk_hardware) | 1,471 | 2 |
| **saved** | **99.7%** | |

The batch took 34.1 s end to end; 1 zipper fitted. Surface unchanged: 17 tools.

## Mechanical CAD: sketch -> features -> drawing -> STEP (A66)

*(not re-run this pass - scenario skipped on this machine; last measured values kept)*

One mounting bracket - 9 ops, 26 faces, 64 edges, 91,159.605 mm3 - sketched,
extruded, filleted, drilled to ISO 273, slotted, chamfered, and read back. The
TEE arm is ONE batch, its diff, and one `pk_measure` call.

Two naive arms, both named, because a model without compact state has two
honest ways to learn this part and both are expensive:

| arm | tokens | calls |
| --- | ---: | ---: |
| naive (a): face/edge inventory + 3x 1024x768 shots + the SVG sheet | 8,404 | 6 |
| naive (b): the STEP file as text | 25,311 | 1 |
| tee (batch + diff + pk_measure) | 1,532 | 2 |
| **saved vs (a)** | **81.8%** | |

The inventory alone is 3,038 tok and the three screenshots 3,108 -
and neither answers "is the minimum wall over 2 mm", which is what the
question actually was. The batch took 0.06 s.
Surface unchanged: 17 tools.

## Mechanical CAD: one parameter moves (A66)

*(not re-run this pass - scenario skipped on this machine; last measured values kept)*

`param_set T=12mm` on the same bracket. TEE answers with the blast radius -
changed: plate, f1, h, slot; unchanged: c1 - and the part's new volume
(109,430.458 mm3). The naive arm has no such report, so it re-reads
the 26-face inventory and takes the three screenshots again.

| arm | tokens | calls |
| --- | ---: | ---: |
| naive (re-read the inventory + 3 shots) | 6,156 | 5 |
| tee (the changed list) | 162 | 1 |
| **saved** | **97.4%** | |

The regen took 0.05 s. Surface unchanged: 17 tools.

## Point-cloud scan prep: level, scale-check, section (A67)

A 279,352-point room scan taken from raw file to a scale-verified DXF the owner can trace.

| Arm | Tokens | Calls |
|---|---|---|
| naive (reads the cloud, every 40th point) | 91,820 | 2 |
| TEE (`pc_open` to `pc_slice`, digests only) | 697 | 6 |

**Saving: 99.2%.** The naive arm is already being flattered - reading 1 point in 40 is far more generous than a real tool that returns what it holds. The lane's own cap (no array over 64 elements, no string over 2 KB) is what keeps the TEE arm flat as the cloud grows: the same five calls cost the same whether the scan is 280 K points or 15 M.


## Lane routing: no lane is the hub (A68)

One server composed like the Desktop manifest (blender, partkiln, seamkiln; declared default: none), every call through the real MCP layer. A row completes its task the way a model that knows nothing about lanes would: no adapter=; if refused and the refusal names the lane, retry with it; if it does not, ask tee_status and then retry.

| Task | Calls | Tokens | What happened |
|---|---|---|---|
| partkiln batch, adapter omitted | 1 | 232 | by kind; pass adapter= to pin |
| seamkiln batch, adapter omitted | 1 | 91 | by kind; pass adapter= to pin |
| tee_script calling kb_status | 1 | 564 | 0 Blender checkpoint(s) |
| tee_scene_summary, adapter omitted | 1 | 103 | lanes overview |
| render a partkiln part | 2 | 395 | pk_export into= then tee_capture |

Always-loaded surface 17 tools / **2,129** wire tokens; instructions **1702 B**; 176 virtual tools registered; search recall over this composition limit 3: 35/57, limit 5: 38/57, limit 8: 38/57, limit 10: 38/57.

Before A68 (same scenario, same composition, declared default blender): partkiln batch 3 calls / 731 tok and seamkiln batch 3 / 562 (refused `blender_error`, no lane in the fix, asked tee_status, retried); tee_script calling kb_status 1 / 586 with 1 Blender checkpoint; tee_scene_summary 1 / 26 (one lane's rows, not the server's lanes); render a partkiln part 4 / 477 (pk_export, as_ingest, as_import, tee_capture); surface 17 tools / 2,033 tok; instructions 433 B; recall limit 3: 29/33, 5: 32/33, 8: 33/33, 10: 33/33.


## Fusion lane: sketch, extrude, fillet, measure (A69)

A 120 x 80 x 10 mm plate with a 2 mm fillet, then its volume and bounding box.
Measured on the suite's fake adsk (Fusion has no headless build): the scripts are
the ones a live Fusion receives, only the geometry is arithmetic. The naive arm
is what a model does without the lane - write the Fusion API script itself (the
script TEE compiles is the fairest stand-in), run it through an execute-script
door, and read the design back as a listing. The TEE arm is one batch, its diff,
and one `fu_measure`.

| arm | tokens | calls |
| --- | ---: | ---: |
| naive (write the script, run it, read the design back) | 9,840 | 2 |
| tee (batch + diff + fu_measure) | 270 | 2 |
| **saved** | **97.3%** | |

The batch script the lane sends is 4,872 tokens the model never
reads; the diff it reads instead is 147 tokens. Read back:
96,000 mm3, bbox [120.0, 80.0, 10.0] mm.

The always-loaded surface is unchanged at 17 tools - Fusion joins through the
Adapter protocol and six `fu_*` virtual tools. Live numbers wait for the smoke in
docs/fusion-lane.md.

## Fusion lane v2: a dimensioned bracket with holes, a chamfer, a revolve and a joint (A70)

A bracket the way a person asks for it: a rectangle constrained and dimensioned to
`width` / `height` user parameters and extruded into its own component, two
through holes on the top face, a chamfer on that face's edges, a post extruded
into a second component, a pin revolved about x, and a revolute joint between the
two components - one batch. Measured on the suite's fake adsk, as above: the
scripts are the ones a live Fusion receives, only the geometry is arithmetic. The
naive arm writes the script itself, runs it, and reads the design back.

| arm | tokens | calls |
| --- | ---: | ---: |
| naive (write the script, run it, read the design back) | 13,196 | 2 |
| tee (batch + diff + fu_measure) | 1,143 | 2 |
| **saved** | **91.3%** | |

12 ops made 19 entities. The batch script the lane sends is
7,192 tokens the model never reads; the diff it reads instead is
628 tokens. The plate reads back 95,315.8 mm3 (two
holes bored) in a [120.0, 80.0, 10.0] mm box - the dimensions drove the 100 x 50
rectangle to 120 x 80 before the extrude. The always-loaded surface is unchanged at
17 tools. Live numbers wait for the smoke in docs/fusion-lane.md (steps 7-11).

## Wind-tunnel lane: geometry, panel sweep, RANS, verdict (A72)

The script's W1 batch: a tapered wing built and swept through six angles by VSPAERO, then a NACA 2412 section meshed (16,000 cells), solved by simpleFoam (143 iterations, verdict converged), polled three times, read, pictured and exported - on the fake engines, whose files match the real ones in shape and per-iteration size.

| Arm | Tokens | Calls |
|---|---|---|
| naive (dictionaries, three log tails, the coefficient file, checkMesh, the script, the polar and span loads) | 19,174 | 16 |
| TEE (`wt_probe` to `wt_export`, digests only) | 2,994 | 15 |

**Saving: 84.4%.** The naive arm grows with every iteration the solver takes (736 bytes of log per simpleFoam step, measured on v2606) and with every point in the polar; the TEE arm is flat: no array over 64 elements, no string over 2 KB, a verdict and an uncertainty label on every number. On the real engines the same calls measured 55 / 181 / 162 / 97 / 21-87 / 163 / 88 / 33 tokens (probe, case, mesh, run, status, result, view, export; research doc 72 3.5).


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

## Local model lane control (A78, 2026-09-10)

*(not re-run this pass - scenario skipped on this machine; last measured values kept)*

**Six fresh tasks, actual application readback: 0/6 with the generic discovery
contract, 6/6 with compact lane guides.** Exact local model:
`mlx-community/Qwen3.8-27B-8bit`, explicit `http://127.0.0.1:8080/v1` route.
One generation per task/arm, temperature 0, 1,800-token completion budget;
unchanged raw model operations, no success through escalation. Fusion strict
readback ran on 2705.1.11. These live-machine observations are not a
deterministic compression canary or proof of AETHER-level quality.

| Live task | Generic contract | Guided |
| --- | ---: | ---: |
| Blender world dimensions/location | Fail | Pass |
| Blender existing camera lens/aim/active selection | Fail | Pass |
| Blender material assignment and geometry preservation | Fail | Pass |
| Fusion sketch/extrude dimensions, origin and volume | Fail | Pass |
| Fusion driving parameter revision with explicit units | Fail | Pass |
| Fusion real through-hole and removed volume | Fail | Pass |
| **Completed tasks** | **0/6** | **6/6** |

| Generation-only metric | Generic contract | Guided |
| --- | ---: | ---: |
| Provider prompt tokens | 1,960 | 3,767 |
| Provider completion tokens | 2,253 | 1,769 |
| Provider total tokens | 4,213 | 5,536 |
| Cached prompt tokens, already included | 975 | 0 |
| Sequential generation wall time | 156.03 s | 117.45 s |

Guidance increased total tokens; the gain is completed work. These totals
exclude supervising-client effort, guide retrieval and application transport.
Baseline cost per completed task is undefined at zero completions. Both arms
produced six parseable envelopes; that was not counted as geometry success.
Protected fixture state was preserved in all twelve strict executions;
Blender negative controls detect material, visibility and modifier changes.

Method limit: the baseline is a frozen generic pre-A78 `tee_batch` description,
without full old documentation; the candidate gets one relevant card. Both
arms execute against the corrected current adapters, so guide and API changes
are not isolated. One run per case, fixed arm order and different cache states
do not establish a general latency improvement. Initial short-model-name
addressing failures are retained separately and not scored as model quality.

Surface before/after: **17 core tools / 2,129 wire tokens unchanged**;
197 → 199 virtual tools; flat schema 31,283 → 31,464 estimated tokens;
reach-one cost 544; rounded progressive-disclosure saving **93.2%**.

Evidence: [frozen tasks](fixtures/a78_lane_quality.json),
[generation summary](../output/tee-efficiency-audit/benchmark/generation-summary.json),
[strict Blender baseline](../output/tee-efficiency-audit/live/baseline-strict/blender-grades.json),
[strict Blender guided](../output/tee-efficiency-audit/live/guided-strict/blender-grades.json),
[strict Fusion baseline](../output/tee-efficiency-audit/live/baseline-fusion-strict/fusion_manifest.json),
[strict Fusion guided](../output/tee-efficiency-audit/live/guided-fusion-strict/fusion_manifest.json),
[preservation controls](../output/tee-efficiency-audit/live/blender-strict-negative-controls.json).
The [runner](run_a78_lane_quality.py) records prompts/hashes/raw answers and
provider usage separately from estimates. See [research note 79](../docs/research/79-smaller-model-lane-control.md)
for profile/budget fixes, scope limitations and the future quality ladder.

The harder composed brief completed native Fusion modelling, a driving revision,
real OBJ transfer and saved-file reopening, but **failed visual/design acceptance**
after two Fusion and five Blender calls. It consumed 36,735 provider tokens
across all attempts, with explicit host staging/diagnostic assistance. The final
partial scene has a real hollow opening but an incorrect overall length,
inward winding, faceting and poor framing/material realization. This is not
AETHER parity. See the [full report](../output/tee-efficiency-audit/composed/blender/report.json)
and [reviewed PDF](../output/tee-efficiency-audit/composed/A78_Qwen_Component_Partial.pdf).

The experiment also led to bounded line/occurrence diagnostics for guarded
Python, before its automatic scene checkpoint. The unchanged first failed
program now identifies both lines 25 and 269; the next identifies line 268.
[Replay](../output/tee-efficiency-audit/python-feedback-replay.json).
Final default suite: **2,153 passed, 20 skipped, 141 deselected**, 153.93 s;
changed-file Ruff clean. [Test log](../output/tee-efficiency-audit/regression-complete.log).

## A79 — CADAgent local modelling (2026-09-10)

`run_a79_cadagent_live.py` on real Fusion **2705.1.15** through :8766;
[`80-evidence/live.json`](../docs/research/80-evidence/live.json) is the retained
successful run. Six cases passed, including STEP volume measured independently
by OCCT 7.9.3, F3D reopen, failed-batch rollback and foreign-document checkpoint
refusal. End-to-end harness time **9.411 s**. Geometry work per case was
0.216–0.425 s; exports/verification/cleanup are additional and included only in
the total. No cloud or local model was called.

| Case | Measured volume mm³ | Batch request + diff estimated tokens |
|---|---:|---:|
| Open inward shell | 11,712 | 219 |
| Closed inward shell | 15,744 | 213 |
| Closed outward shell | 19,584 | 213 |
| Rectangular six-hole plate | 79,246.017763 | 341 |
| Circular four-hole disc | 49,762.827633 | 322 |
| Three cubes, negative spacing | 375 | 317 |

Token rows measure only operation payload + batch diff, excluding verification,
exports, discovery, schema loading and host supervision. They are not provider
usage or tokens per completed user task and establish no general savings claim.

Before/after core schema cost is unchanged: **17 tools / 2129 estimated wire
tokens**. The existing generic surface scenario through `cli.attach_all` is
unchanged and uses `FakeAdapter`; the Fusion-specific comparison separately
measures nine `fu_` virtual schemas, **1207 → 1230** (+23 discovery-description
tokens), with **zero new tools**. A fresh Fusion stdio server also measured
17 / 2129 and passed six read-only calls in **0.671 s**. See
[`80-evidence/`](../docs/research/80-evidence/).

Two hardware-independent harness errors were preserved, then a real geometry
defect was found: leaving rectangular direction two unset generated nine
overlapping bodies for a request for three. Explicit count 1 / distance 0
fixed it without weakening the geometry gate. Final affected regressions:
**315 passed in 8.48 s**, including **82** focused CADAgent tests; Ruff clean.

*Earlier standard rows are generated by `benchmarks/run_benchmarks.py`; A79 uses
the explicit Fusion harness named above.*


### A79 P4 — authored advanced Fusion lessons (2026-09-10)

Three complete CADAgent guidance recipes replayed on Fusion 2705.1.15: constrained
ventilated enclosure, revolved flanged hub and revolute component study. All three
passed geometry and driven revisions, independent STEP solid bounds/placement/
volume and F3D reopening. Joint sweep: 0/45/90/0/45°. Total 11.503 s including
exports/reopens; creation/revision/readback 3.065 s. This is authored replay,
not independent model performance or an agent-to-agent savings comparison.

Core schema remains 17 tools / 2,129 estimated wire tokens. Default Fusion guide
index: 198 → 272 estimated tokens. Opt-in lessons: enclosure 1,338, flange 1,872,
joint 1,742 tokens. Creation+first-revision input/diffs: 962/822/587; excludes
retrieval, lifecycle, exports, native readback and extra motion samples. JSON
resources load only for a selected topic. Full MCP and geometric evidence:
[research 80 advanced section](../docs/research/80-cadagent-integration.md).
331 affected tests passed in 7.85 s. Live results are tied to this Fusion build
and machine; no general runtime claim is made.

### A79 P5 — difficult F1-inspired Fusion lessons (2026-09-10)

Three authored recipes replayed on Fusion 2705.1.15: articulated wing, sixty
radial cooling passages and a lightened suspension wishbone. All three native
models, parameter revisions and F3D reopens passed; 17 retained geometry
readbacks were independently revalidated. Continuous wing clearance has a
conservative lower bound of 16.534711 mm over the specified 0–25° joint motion,
after accounting for vertex matching tolerance. Four targeted corruptions are
rejected while body counts and total volumes remain unchanged.

Total live harness time: **16.053 s**, including exports, STEP checks and archive
reopens; construction/revision/native readback: **5.171 s**. The independent
brake reference was prepared separately in that run. The current harness also
regenerates that reference and audits its channel topology, so the retained
16.053 s is not a timing for this additional work. The portable reference path
was tested separately without another Fusion modelling run.

| Lesson | First creation/revision input + diff tokens | Full opt-in lesson tokens |
|---|---:|---:|
| Active wing | 1,714 | 3,422 |
| Radial brake passages | 1,164 | 3,871 |
| Suspension wishbone | 1,513 | 3,446 |

Batch tokens exclude discovery, staged wing assembly, additional motion,
lifecycle, native readback and exports. Full lesson tokens measure the guide
payload before the MCP success envelope. The default index is **272 → 266**
estimated tokens; its final MCP response is 278. Core schemas remain **17 tools /
2,129 estimated wire tokens**. Fresh stdio discovery/preflight took **0.375 s**.
These are authored replay and disclosure measurements, not provider usage,
independent model performance or a saving against another agent.

Wing and wishbone STEP volume checks pass. The original brake STEP fails the
unchanged 0.1 mm³ analytic gate by **+12.8021875 mm³**, due to approximate mouth
intersection curves, and retains `step_exact_volume_match=false`. Its editable
native archive passes. A separately authored OCCT reference STEP passes at
**−0.0000484 mm³**, including shared-edge adjacency of each channel to both rims.
This reference is not credited as a successful Fusion STEP translation.

379 affected tests passed in 7.94 s; 90 focused checks passed after the final
recipe documentation change. All six lesson JSON resources were verified
byte-for-byte inside the built wheel. Evidence:
[research 80](../docs/research/80-cadagent-integration.md),
[live summary](../docs/research/80-evidence/f1-live-summary.json),
[MCP](../docs/research/80-evidence/f1-guidance-mcp.json),
[tests](../docs/research/80-evidence/f1-tests.json).

### A79 P6 — nine Blender lessons, including fabric (2026-09-10)

Native **Blender 5.2.0 LTS** replay passes for the six Fusion counterparts,
a compact modern house, texture workshop and woven-fabric study. The retained
successful cases sum to **108.257906 s**, including independent exports, native
reopens and renders; the build/inspect/revise/inspect stages sum to **21.364825 s**.
These are sums from separate successful runs, not one uninterrupted suite.
Final inspector audits, combined-library assembly and package checks are
additional. No model was called; this measures authored replay, not autonomous
model performance or tokens per completed user task.

| Opt-in build card | Estimated tokens |
| --- | ---: |
| Enclosure | 3,714 |
| Flanged hub | 3,762 |
| Joint | 3,015 |
| Active wing | 3,914 |
| Ventilated brake | 3,986 |
| Wishbone | 4,468 |
| House | 8,386 |
| Textures | 8,504 |
| Fabric | 6,979 |

Full build cards contain complete standalone Python programs and are loaded only
on explicit request. These token estimates exclude execution replies, exports,
render inspection and host supervision. The default Blender index changes
**170→268 estimated tokens**. The always-loaded surface remains **17 tools /
2,129 estimated wire tokens**; fresh MCP discovery and all nine build-card
reads pass in **0.388122 s**. Nine packaged sources match the checkout byte for
byte. No provider usage or savings comparison is implied.

All **61 mesh** exports pass independent PLY and GLB geometry readback. The
native nine-scene library reopens with every current inspector passing and
unchanged geometry hashes. Mesh approximations retain their declared accuracy
bounds; they are not exact CAD solids. GLB material appearance remains unbaked
and unverified. Fabric's material revision changes yarn cell width 4→6 mm,
roughness and sheen while preserving the authored folds and metre UV metric.
All 18 fabric corruptions are rejected. The owner's 649-object AETHER geometry
and materials are unchanged. **190 affected tests pass, 31 deselected, 0.71 s**;
Ruff and diff checks pass.

[Live and export summary](../docs/research/80-evidence/blender-live-summary.json),
[validation](../docs/research/80-evidence/blender-validation.json),
[MCP disclosure](../docs/research/80-evidence/blender-guidance-mcp.json),
[package](../docs/research/80-evidence/blender-package.json),
[usage and limitations](../docs/blender-lessons.md).

## A80 — local continuous learning (2026-09-10)

The current served corpus below was measured through the existing
`run_surface_scenario`, which constructs the server with `cli.attach_all` and
reads its actual MCP schemas. Earlier tables remain historical measurements.
The A77 canary reads the latest explicit current-corpus record, keeps exact tool
counts and its existing token/saving tolerance bands, and additionally guards
the flat corpus token cost.

| Measurement | Virtual tools | Always-loaded tools | Wire tokens | Flat schema tokens | Disclosure saving |
| --- | ---: | ---: | ---: | ---: | ---: |
| Before A80 | 199 | 17 | 2,129 | 31,464 | 93.2% |
| Current served corpus (A80) | 204 | 17 | 2,129 | 31,903 | 93.3% |

The five new learning tools add **439 estimated tokens** to the flat corpus and
zero always-loaded tools or wire tokens. Reaching the existing representative
tool still costs 544 estimated tokens. The percentage above measures progressive
disclosure, not savings caused by learned routing. Evidence:
[before](../output/learning/surface-before.json),
[after](../output/learning/surface-after.json).

The controlled local replay executes real TEE validators with authored strategy
outputs; it calls no language model and seeds no production learning data.
Both fixed and learned policies complete **40/40 tasks**. Attempts fall
**60→40**, and estimated request/response tokens fall **1,660→1,120 (32.53%)**.
Measured attempt time falls **14.572→12.381 ms**, while total wall time including
decisions rises **14.741→29.217 ms**, about **1.98× slower**. The tiny fixture
therefore demonstrates fewer attempts and estimated exchange tokens, with a
measured end-to-end time regression. It does not establish real-world design
quality, provider usage or general task-speed improvement.

The replay also verifies model persistence and a later drift rollback to static
ordering with promotion paused. These are distinct from the predictive-loss
checks used to admit a candidate. Full controlled evidence:
[replay](../output/learning/replay-20260910T194335592664Z/evidence.json).
See [the learning guide](../docs/continuous-learning.md) and
[research 81](../docs/research/81-continuous-learning.md) for the label domains,
held-out evaluation protocol, limits and other campaign measurements.

A paired current-source registry microbenchmark measures learning disabled and
enabled on the same no-op read fixture, after 100 warm-up calls in each arm.
Over 5,000 timed calls, disabled takes **0.032758 s** and enabled takes
**0.520780 s**: approximately **0.097604 ms added per call**, including numeric
observation and bounded retention. App boot and warm-up are excluded. The first
automatic fit occurs during warm-up; the timed portion is shorter than the
five-second throttle and includes no additional fit. This isolates ordinary
observation overhead, not peak training cost. The older pre-change timing uses
a different fixture and is retained separately without a paired speed claim.
[Paired overhead evidence](../output/learning/overhead-paired-final.json),
[retained runner](../output/learning/measure_overhead.py).

The full default server suite initially reports **2,547 passed, one failed,
20 skipped and 141 deselected in 193.58 s**. Its only failure was the old Fusion
vocabulary test: it recognized direct dispatch arms but omitted A79's delegated
CADAgent emitter. The corrected test measures delegation for every declared
CADAgent kind and rejects a control with the shell route removed. Product code
did not change for this correction. Final focused verification across Fusion,
CADAgent, lane routing, learning, guidance and benchmark canaries passes
**536 tests, one skipped, three deselected in 10.46 s**; relevant Ruff checks
pass. The full suite was not repeated after the test-only correction.
[Initial full suite](../output/learning/full-tests.log),
[final focused verification](../output/learning/final-focused-tests.log).

### A81 — Cline/Aider documentation surface (2026-09-10 UTC)

Paired calls to the existing `run_surface_scenario` use the same temporary
project and fake-adapter composition. Five documentation capabilities add zero
core tools and zero always-loaded tokens. The flat alternative grows by 524
tokens; this measures tool-disclosure cost, not documentation quality or model
token savings. Real five-adapter projects have a different virtual count.

| Measurement | Virtual tools | Core tools | Wire tokens | Flat schema tokens | Saving |
|---|---:|---:|---:|---:|---:|
| Before A81 | 204 | 17 | 2,129 | 31,903 | 93.3% |
| Current served corpus (A81) | 209 | 17 | 2,129 | 32,427 | 93.4% |

Reaching the fixed benchmark capability remains 544 tokens in both runs.
Evidence: [before](../output/docagents/surface-before.json) and
[after](../output/docagents/surface-after.json). CLI protocol-fixture outcomes
and affected-test results are recorded separately when complete; a fixture
provider is not a measure of model reasoning quality.

### A82 architecture — canonical served surface (2026-09-10 UTC)

Measured through the existing canonical served fixture, after adding eleven
progressively disclosed architectural tools. Before: 209 virtual tools,
32,427 flattened schema tokens; after: 220 virtual, 33,947 flattened tokens.
The 17 always-loaded tools remain 2,129 wire tokens. Reaching one discovered
tool costs 525 tokens in this corpus (544 before); this is a surface measurement,
not a completed architectural-design task cost or a model-quality benchmark.
Evidence: `output/architecture/surface-before.json` and `surface-after.json`.

| Measurement | Virtual | Core | Wire tokens | Flat tokens | Saving |
|---|---:|---:|---:|---:|---:|
| Current served corpus (A82 architecture) | 220 | 17 | 2,129 | 33,947 | 93.7% |

| Current served corpus (W0) | 232 | 17 | 2,129 | 36,159 | 94.1% |

_Measured 2026-09-13 through `cli.attach_all`, reach-one 525 tokens. The row moved
**220 → 232 virtual tools** and W0 added **none of them**: the twelve are A83/A84
lanes that shipped without re-measuring this row, and the A77 canary had been red
on it since. Recorded here because a number nobody re-runs is a declaration with a
date on it — the campaign that finds a stale row owns re-measuring it, not the
campaign that quoted it last. Always-loaded stays **17 tools / 2,129 wire tokens**:
W0 added a profile, an engine row and a chore argument, no tools._

### A84 isolated structural candidate (not installed)

Affected regression: **1,156 passed, 2 browser-gated skips**, 92.46 s. Separate
native Okongo roof-strip demonstration: ten runs across five scenarios, both
OpenSeesPy and OOFEM; 24 centroid-axis candidates checked. Real Chrome report
workflow passes desktop and 390 px mobile layouts with all ten scenarios.

| Identical main-corpus fake composition | Before A83 RC2 | A84 candidate |
|---|---:|---:|
| Always-loaded tools / wire tokens | 17 / 2,129 | 17 / 2,129 |
| Progressive tools | 225 | 232 |
| Flattened schema tokens | 35,104 | 36,155 |

The complete core schema hash is unchanged. The separately labelled canonical
fixture without the main-corpus override serves 228 progressive tools and costs
35,531 tokens flattened. Both extracted full five-adapter/shared-corpus delivery
harnesses pass 30 checks each at 17 core / 273 progressive tools. None is an
actual-client upgrade or acceptance receipt. Native control results are recorded
in output/updates/TEE-20260911-A84-01/evidence/benchmark-final; source models and
all numerical/synthetic assumptions remain distinct from building acceptance.

A84 owner extension — complete roof/wall preliminary study: **282 native runs**
passed analytic displacement/force controls across five conditional roof-strip
models and 136 wall case/restraint combinations, each in OpenSeesPy and OOFEM.
The 34 wall geometry groups cover 117 eligible full-height source-wall strips.
All 14 roof systems / 17 planes, 166 wall entities and 41 openings were audited;
44 provenance entries include visual review of all 17 full-design PDF pages.

The combined browser review passes all 180 selections, 239 displayed pressure
cases and 478 native-value comparisons, plus pressure/E scaling, no-model states,
invalid/overflow input, four coordinate plan clicks and 390 px mobile layout.
The initial hidden-control/overflow defects and their fixes are retained. Copied
report-link completeness is checked separately. Source and runtime fingerprints
remain unchanged. Unit loads, reference moduli and boundary hypotheses do not
constitute material, structural capacity, local wind or foundation acceptance.

## Router cascade: measured q and rho per rung (W0, 2026-09-13)

`simulate_cascade_threshold.py` took verifier coverage, latency and load from
measurement and two inputs on faith: the per-rung error rate q, and the
correlation rho between rung failures. `measure_rung_correlation.py` measures
both by running ONE labelled task set through every reachable rung and
correlating their failures. Labels are known by construction, so grading needs
no judge: a drift family must be answered `needs_verification`, a grounded one
`grounded`. Serialized on purpose - the rungs share a local model server, so
concurrent requests would contend for the GPU and corrupt both signals.

**Generated tasks** (`benchmarks/rung1/gen_distill.py`, 7 families, 35 tasks):

| rung | endpoint | q | wall |
|---|---|---:|---:|
| 14B-coder | :8082 | 14.3% | 48.2 s |
| 9B-general | :8082 | 31.4% | 31.5 s |
| 27B-mlx | :8082 | 0.0% | 174.9 s |
| 27B-vllm | :8087 | 0.0% | 94.4 s |

rho(14B, 9B) = **0.43**. rho for the 27B pair was **not computable**: both
scored 35/35, and a rung with no variance carries no correlation information.
The harness reports `n/a` rather than 0 - a ceiling effect, not independence.

**Hard tasks** (`benchmarks/hard_triage_tasks.py`, 6 families, 36 tasks), built
because of that ceiling. They attack the two shortcuts a model can take instead
of weighing evidence - seductive-but-insufficient context (a signature for the
WRONG function, a deprecation with no installed version, a near-miss symbol)
and sufficient-but-buried (a valid enum under six frames of noise, a chained
traceback whose root cause is the first exception). Both directions, so a model
cannot win by always deferring:

| rung | q (generated) | q (hard) | wall |
|---|---:|---:|---:|
| 14B-coder | 14.3% | **47.2%** | 50.4 s |
| 9B-general | 31.4% | **61.1%** | 37.1 s |
| 27B-mlx | 0.0% | **2.8%** | 229.3 s |
| 27B-vllm | 0.0% | **2.8%** | 126.1 s |

| rho | 14B-coder | 9B-general | 27B-mlx | 27B-vllm |
|---|---:|---:|---:|---:|
| 14B-coder | - | 0.53 | 0.18 | 0.18 |
| 9B-general | 0.53 | - | 0.13 | 0.13 |
| 27B-mlx | 0.18 | 0.13 | - | **1.00** |
| 27B-vllm | 0.18 | 0.13 | **1.00** | - |

**rho = 1.00 for q27b-think vs q27b-bare** - the same Qwen3.8-27B weights on two
backends. Both failed, on the IDENTICAL task. The cascade's independence
precondition is violated exactly where predicted: the second rung cannot
recover anything the first got wrong, because it is the same model reaching the
same conclusion on a different server.

**The caveat is large and the number must always carry it: that rho rests on
ONE failure each.** With a single failure per rung, phi can only be 1.00 (same
task) or negative (different task) - it has no resolution in between. It is a
directionally confirmed prediction, not a tight estimate; what raises it above
a coin flip is that it agrees with the mechanism (identical weights,
temperature 0, identical prompt). The cross-family figures rest on 17 and 22
failures and are the robust ones: **0.53 between two different families** is
itself well short of the independence a cascade assumes, while the 27B is
genuinely near-independent of the small rungs at 0.13-0.18 - which is where
depth earns its keep.

**Consequences for the simulation.** Feeding measured q back in moves the
headline from 90.3% right / 9.6% wrong (assumed uniform q=0.30) to **95.6%
right / 4.4% wrong** - the assumption had been overstating silent errors by
more than double. Rung credit under measured q: q14b+a2 86%, dsflash 7%,
q27b-think 3%, q27b-bare 0%, q35b 0%. Real data also exposed a defect in the
simulator: q = 0.0 drove `_norm_cdf_inv(1.0)` into `log(0)`, so it could not
represent a rung that never fails. Fixed.

Reproduce: `uv run --no-sync python ../benchmarks/measure_rung_correlation.py
[--hard] --tasks N`. Not reproducible across machines - it measures the engines
this one serves, and a rung that is not answering is scored as not-a-failure
(A76: an unreachable engine supplies no quality label).
