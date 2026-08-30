# 60 — The pipeline lane: declared steps for any project, builds and queries alike (2026-08-30)

Verification basis: the owner's finding (SI-B15) that TEE's 103
virtual tools are scene-side and cannot drive the DiversionPlanner
basemap build, plus the one op that DID earn its place —
`capture_terrain`'s `dem_diff`; repo reads (config schema, jobs,
machine ledger, K-layer scheduler shipped in A42); project survey on
this machine (DiversionPlanner-BaseMap: 36 py files, no `.tee/`;
OkongoSim: 39 py, has `.tee/`; TEE itself: has `.tee/`). Owner
directive, verbatim: make the pipeline work "for other projects and
queries not just diversion planner."

## The finding, stated precisely

TEE's virtual surface assumes a live scene: epoch/revision stamps,
diffs, checkpoints, an adapter holding state. A build pipeline has
none of it — its world is files in, files out, scripts between. So
the surface offers nothing, and the owner's basemap build could not
be driven at all. `dem_diff` worked for one reason worth naming: it
is a **declared headless operation** — a known command
(`qgis:rastercalculator`), typed inputs and outputs, run as a job,
answered as a compact report. Declaration, not scene state, is what
made it drivable. Generalize the declaration and the gap closes for
every project at once.

## Design: `.tee/pipeline.toml`, owned by the project

Each project declares its own steps in its own tracked config —
the `[kb]`/`[pins]` precedent, extended:

```toml
[[step]]
name    = "basemap"
kind    = "produce"                     # artifacts out
argv    = ["python", "builder/build_basemap.py", "--tile", "{tile}"]
params  = { tile = { type = "string", required = true } }
inputs  = ["data/atl08/**", "builder/build_basemap.py"]
outputs = ["out/basemap_{tile}.tif"]
cost    = { wall_s = [120, 900], footprint_gb = 4 }   # ledger + QoS hints

[[step]]
name    = "blunder_stats"
kind    = "query"                       # an ANSWER out, not artifacts
argv    = ["python", "builder/blunder_stats.py", "--json"]
inputs  = ["out/basemap_{tile}.tif"]
answer  = { format = "json", max_tokens = 400 }
```

Two step kinds is the whole generality argument:

- **produce** → artifacts; TEE answers with an artifact DIFF (which
  declared outputs changed, sizes, hashes, wall time) — never a log
  dump.
- **query** → an answer; TEE answers with the step's own structured
  output, budgeted and provenance-stamped. This is what makes the
  lane serve *queries*, not just builds: "how many blunders survived
  the screen?" is a declared step, not a scene operation.

## Why this is general by construction

- **Discovery by convention, never by path**: any project root whose
  `.tee/pipeline.toml` exists gets the lane; TEE hard-codes no
  project, no domain, no directory. DiversionPlanner is the first
  customer, not the definition.
- **The steps are the project's, not TEE's**: the owner writes what
  his scripts already do; TEE contributes execution discipline, not
  domain knowledge. The same lane serves OkongoSim renders, TEE's own
  benchmark battery, the A350 trainer's build — anything with a
  command line.
- **`dem_diff` generalizes into it**: one wrapped QGIS op becomes the
  worked example of a declared step, and its jobs/report shape is the
  lane's shape.

## What TEE already owns (the build is mostly wiring)

Jobs with budgeted progress; the machine ledger (footprint hints →
admission); the K-layer scheduler — **declared inputs/outputs make
steps literal task-graph nodes**, so the A42 scheduler dispatches
pipeline work with no new concepts; content-addressed hashing (the
staleness test); provenance stamps; `report_savings`; rule-6 errors;
the config loader with per-section validation.

New code is small: the declaration schema + validator, a runner
(argv, never a shell string), the staleness/DAG resolver, the
artifact differ, and the answer budgeter.

## Staleness and the DAG (make, but declared, scheduled and budgeted)

Steps form a graph through their declared inputs/outputs. A run asks
for a TARGET; TEE hashes declared inputs, compares against the
recorded run manifest, and executes only stale steps — reporting what
it skipped and why. Cheap, honest, and the reason a rebuild after a
one-file change is a sentence rather than a session.

## The trust law (non-negotiable)

TEE runs **declared steps only** — never a model-invented command.
`argv` arrays, never shell strings (no interpolation into a shell);
`{param}` substitution is typed, validated, and quoted as a single
argv element. The declaration file is owner-authored and
project-tracked: the same trust model as a launch config or a
Makefile. `pipeline_init` may DRAFT a candidate file by scanning a
project's scripts, but it never writes a runnable step without the
owner reading and committing it.

## Risks and gates

- **Shell injection / accidental power** → argv-only, typed params,
  declared steps, no `shell=True`, ever; fixtures prove a hostile
  param value lands as one inert argv element.
- **Runaway steps** → jobs pattern (timeouts, cancel), ledger
  admission via `footprint_gb`, batch QoS by default.
- **Log floods** → produce-steps answer with artifact diffs; failures
  return the tail only, rule-6 shaped, with the failing step named.
- **Staleness lying** → hashes over declared inputs, recorded per
  run; `--force` exists and says so in the report.
- **Project sprawl** → the lane is per-project by construction; no
  global registry, no cross-project state.

## Benchmark shape (generality proved, not asserted)

Research-48 style, on **two projects minimum** — DiversionPlanner
(a produce+query build) and one other already on this machine
(OkongoSim or TEE's own battery): tokens per completed build and per
answered query, TEE lane vs the naive pattern (paste the command,
paste the log, paste the output back into the conversation). One
project proves it works; two prove it is a lane and not a special
case.

## Verdict

Build it (A43 when directed). The gap the owner found is real and
structural, the fix is small because A42 already shipped the hard
parts, and generality is free if the declaration lives with the
project instead of in TEE. First customer: the DiversionPlanner
basemap. First proof of generality: a second project's steps running
through the same lane, in the same benchmark table.
