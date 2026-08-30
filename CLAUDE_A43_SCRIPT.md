# A43 build script — the pipeline lane: declared steps for any project

**What this builds** (owner directive, 2026-08-30): the general
pipeline lane from `docs/research/60-pipeline-lane.md` — the design of
record; read it first. Origin: SI-B15 — TEE's 103 virtual tools are
scene-side and could not drive the DiversionPlanner basemap build;
`capture_terrain`'s `dem_diff` earned its place by being a DECLARED
HEADLESS OPERATION, and this campaign generalizes that shape. The lane
must serve **any project and both kinds of work** — builds that
produce artifacts and queries that return answers — with
DiversionPlanner as first customer, never as the definition.

Inherits every standing law by reference (A33 rules; surface LAW
2,028/17 — the lane ships as virtual tools, zero always-loaded growth;
bars are the floor; A30/A31; fakes/fixtures before live; jobs pattern
for long work; owner-only decisions; >2 GB gate; machine etiquette;
never concurrent with another campaign; degrade-to-static for anything
touching the scheduler).

A one-paste prompt for a fresh session:

> Read CLAUDE.md, then CLAUDE_A43_SCRIPT.md, then research doc 60,
> then the last dated entries of docs/PROGRESS.md. Call tee_status and
> tee_recall first and use TEE's own tools as co-pilot throughout.
> Work the phases in order from where the evidence says they stand —
> schema and hostile fixtures before any runner, two projects before
> any generality claim, benchmarks before claims. Stop and report if
> any phase's premise no longer holds.

## Laws (this campaign's own, from research 60)

- **Declared by default; ad-hoc only through the owner's gate**
  (research 60 addendum, owner challenge 2026-08-30). Declared steps
  are the norm and the ONLY thing anything automatic may run. A
  per-project `[pipeline] allow_adhoc` (default FALSE — the
  `allow_code_exec` precedent) permits `pipeline_adhoc {argv}` from a
  LIVE HUMAN TURN only: refused for jobs, queued/scheduled work,
  chores, gateway-fronted calls, and any path whose provenance
  includes fetched or third-party content. Untrusted content can
  never cause execution — that invariant does not bend.
- `argv` arrays only — no shell strings, no `shell=True`, ever.
  `{param}` substitution is typed, validated, and lands as ONE argv
  element (proven by a hostile-value fixture).
- **The declaration belongs to the project**, in its tracked
  `.tee/pipeline.toml`. TEE hard-codes no project, path, or domain.
- **The bound is the point, not the ceremony** (addendum 2): an
  always-allowed TEE tool must confer a BOUNDED capability. Hence:
  narrow by construction (exact argv; no shell/globs; `params` typed
  AND constrained by enum/pattern — an unconstrained `make {target}`
  is refused as a laundered allowlist); **TEE never writes
  `pipeline.toml`** (the adopt flow emits `.tee/pipeline.proposed.toml`
  for the owner to move — fixture: any write attempt to the real file
  fails); **trust-on-first-use per project** — the approved
  declaration file is hash-pinned, and an unapproved or CHANGED file
  refuses to run with the diff named (a cloned repo's pipeline.toml is
  attacker-authored by definition); and every run is audit-logged
  (argv, params, caller class, exit, artifacts).
- **Answers, not logs**: produce-steps report artifact diffs;
  query-steps report their own structured output, budgeted; failures
  return the tail, rule-6 shaped, naming the step.
- **Generality is proven, not asserted**: no completion claim until a
  SECOND project's steps run through the same lane unmodified.

## T-1 — The trust kernel FIRST (research 61; the pipeline is its first tenant)

Do not give the pipeline a fifth private flag. Build the single
decision point: capabilities (verbs), grants (per project, default
deny), caller classes read from the A42 task graph, and the taint law
(a task with untrusted inputs may never invoke a side-effecting
capability; untainting only by live human turn). Ship `tee_trust`
(virtual) for visibility, rule-6 refusals naming the missing grant AND
the config file actually loaded (closes SI-B17), and per-project audit
logging. Retrofit the four existing flags as capability aliases with
fixtures proving identical behavior. Shadow-measure taint decisions
against A42's recorded traces BEFORE enforcement goes live (the
scheduler precedent).

Integration specifics are research 62 (verified against the code):
the check slots into `ToolRegistry.call` beside the existing
`disabled` refusal; completeness is STRUCTURAL, not vigilance —
`VirtualTool` gains a REQUIRED `capability` field so a capability-less
tool fails at STARTUP, plus a coverage test enumerating all four entry
surfaces (registry, MCP handlers, `jobs.submit`, engine/backend
clients); taint is a property of an ID, not a string — affordable
precisely because `TaskDescriptor.inputs` are already
"ids/pointers, never payloads" — with `caller` and `taint` added as
optional fields; enforcement rides `ShadowRecorder`/`replay` and flips
on only when replay over A42's real traces shows zero false denials;
failure modes decided in advance (fail CLOSED for side-effecting
capabilities, fail OPEN for the read tier — a broken trust file must
never brick `kb_search` and must always brick `run-adhoc`); migration
maps the 103 tools by module in one table and keeps legacy flags as
aliases so existing configs are untouched.

Acceptance: startup refuses a capability-less tool; the coverage test
enumerates all four surfaces; default-deny holds with no grants file
while the read tier still answers; each legacy flag behaves
identically through its alias; a tainted fixture task is refused
naming what tainted it and a live-turn untaint succeeds; shadow replay
shows zero false denials before enforcement flips; overhead ≤0.05 ms
published beside the gateway's number; full battery bars unchanged.

Hardening from research 63 (qmax adversarial pass, verified): taint
must CROSS the persistence boundary — `tee_remember`/`kb_propose`
store a taint label bound to key+content-hash, reads rehydrate it, a
missing label defaults TAINTED (memory.remember carries no lineage
today — confirmed); capabilities are verb+RESOURCE — `write-artifacts`
(declared inert prefixes only) is separate from `write-config` /
`write-policy` / executable paths, every path canonicalized with the
`kb_propose` symlink/traversal belt generalized into the check;
`call-paid-engine` is side-effecting EGRESS — denied to tainted tasks
without live-turn owner approval, its request fields allowlisted, its
RESPONSE tainted (converges with SI-B16 spend + SI-B18 sent columns);
grant/policy changes need a typed-phrase confirmation, not a bare
approval, because habituation is irreducible and the human gate must
be the LAST layer, never the only one.

Extended acceptance: a memory/staging round-trip preserves taint;
`write-artifacts` cannot touch `.tee/` or a config/policy/loader path
(canonicalized, symlink/traversal fixture); a tainted task is denied
`call-paid-engine` and a paid response reads back tainted; grant
changes require the typed-phrase path.

## P0 — Schema, validator, hostile fixtures (no runner yet)

The `[[step]]` schema (name, kind=produce|query, argv, params with
types, inputs, outputs, cost{wall_s, footprint_gb}, answer{format,
max_tokens}); config-loader integration with per-section validation in
the existing style; `pipeline_list` (virtual) reading a project's
declarations. Fixtures FIRST: malformed declarations refuse with the
exact fix; a param value containing shell metacharacters, spaces, and
quotes lands as one inert argv element; unknown step names list the
declared ones. Acceptance: schema + fixtures green with no runner in
existence.

## P0b — The ad-hoc door and the adopt flow (research 60 addendum)

`[pipeline] allow_adhoc` config + `pipeline_adhoc {argv}` behind it,
with the live-human-turn invariant enforced at the call site and
FIXTURES for every refusal path (job caller, scheduled caller, chore
caller, gateway-fronted caller, fetched-provenance caller). Ad-hoc
runs are unscheduled, uncached and labelled "ad-hoc, not declared" in
their report and provenance. **The adopt flow**: after a successful
ad-hoc run, TEE offers the declaration it would write — argv,
inputs/outputs inferred from what the run actually touched, measured
cost — which the owner accepts into `.tee/pipeline.toml`. Acceptance:
refusal fixtures green; one live ad-hoc → adopt → the adopted step
re-runs as a declared step, recorded.

## P1 — The runner and the artifact differ

Execute a declared step as a job: argv assembly, cwd = project root,
timeout, cancel, output capture bounded. Produce-steps → artifact
diff (declared outputs: changed/created/unchanged, sizes, hashes,
wall time). Query-steps → the declared answer format, budgeted to
`max_tokens`, provenance-stamped (step, argv hash, inputs hash,
started/finished). Failures → tail + rule-6 line naming the step.
Ledger: register with the declared `footprint_gb`, batch QoS default.
Acceptance: both kinds run green on fixture steps; a deliberately
failing step returns one honest line + tail, no log flood.

## P2 — Staleness and the DAG

Hash declared inputs; record a run manifest per step; `pipeline_run
<target>` resolves the graph and executes only stale steps, reporting
skips with their reason. `force = true` runs anyway and says so.
Acceptance: fixture graph — touch one input, exactly the dependent
steps re-run; nothing else moves; a second immediate run is a no-op
with a compact "all fresh" answer.

## P3 — Scheduler integration (K-layer, no new concepts)

Declared inputs/outputs make steps task-graph nodes: register them
with the A42 scheduler so pipeline work is dispatched, admitted, and
metered like everything else (batch class, aging, backpressure);
`report_savings` gains pipeline rows. Degrade-to-static holds: with
the scheduler off, steps run sequentially exactly as in P1.
Acceptance: a mixed run (pipeline step + chore + reconstruction)
places sanely, shown in the meter; the same run with the kernel off
completes identically, slower.

## P4 — First customer: the DiversionPlanner basemap

Author `.tee/pipeline.toml` in `~/DiversionPlanner-BaseMap` WITH the
owner (his scripts, his flags — TEE writes no domain knowledge):
`build_basemap` as produce, the blunder/stats scripts as queries,
`dem_diff` referenced as the worked example of a declared op.
`pipeline_init` ships here too — it DRAFTS a candidate file by
scanning a project's scripts and never writes a runnable step the
owner has not read. Three authoring routes must all work by the end
of this phase: init-draft, hand-write, and P0b's adopt-after-ad-hoc
(the discovery route — expected to be the one most used in anger). Acceptance: the basemap build runs end to end
from one sentence in a chat; a query step answers in ≤400 tokens;
the whole exchange recorded.

## P5 — Generality: the second project (the law)

Run the same lane over a second project already on this machine
(OkongoSim's render/export steps, or TEE's own benchmark battery —
pick by what serves the owner). Nothing in `server/` may change to
make it work; if something must, that is a generality bug to fix in
the lane. Acceptance: second project's steps run unmodified, recorded
side by side with P4.

## P6 — The benchmark and close-out

Research-48 row per project: tokens per completed build and per
answered query, lane vs naive (paste command, paste log, paste output
into the conversation). Full battery: every bar holds. Suites + CI
green; `docs/setup-pipeline.md` written (schema, the trust law, the
init flow, two worked examples); SI-B15 ticked; artifacts rebuilt +
rehearsed; campaign ledger with wrong-way numbers explained;
`report_savings` quoted on the closing session; `tee_remember` the
close-out. Version by semver (expected 0.8.0 — additive lane); the
owner tags.
