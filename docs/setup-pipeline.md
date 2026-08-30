# The pipeline lane

Most projects are not a live scene. They are files in, scripts between,
files out — and TEE's virtual surface assumed a scene it could stamp,
diff and checkpoint, so a build pipeline had nothing to hold onto. One
operation always worked anyway: `dem_diff`, because it was a **declared
headless operation** with named inputs and named outputs. Declaration,
not live scene state, is what makes work drivable. The pipeline lane
generalises that declaration, so the gap closes for every project at
once.

A project declares its own steps in its own tracked
`.tee/pipeline.toml`. TEE never writes that file.

## What a declaration looks like

```toml
[[step]]
name    = "plan"
kind    = "produce"
argv    = ["python3", "builder/build.py", "--cells", "{cell}", "--out", "{out}"]
params  = { cell = { type = "string", pattern = "^[NS][0-9]{2}[EW][0-9]{3}$" } }
inputs  = ["builder/build.py", "sources.yaml"]
outputs = ["{out}/plan.json", "{out}/manifest.json"]
env     = { PROJ_NETWORK = "ON" }
cost    = { wall_s = [1, 5], footprint_gb = 0.5 }
```

| field | meaning |
|---|---|
| `name` | lower-case identifier; how you ask for the step |
| `kind` | `produce` (artifacts out) or `query` (an answer out) |
| `argv` | **a list, never a string.** TEE runs no shell |
| `params` | typed and constrained; `{name}` substitutes into `argv`, `env`, `inputs`, `outputs` |
| `inputs` | what the step reads — this is what staleness is measured against |
| `outputs` | what a produce step writes — this is what the diff reports |
| `env` | environment overlaid on the real one; same constraint law as `argv` |
| `answer` | a query's `format` (`text`/`json`) and `max_tokens` budget |
| `cost` | `wall_s` hint (doubled for the timeout) and `footprint_gb` for the ledger |

## The laws, and why each one is there

**argv arrays only, never a shell string.** A string is the one mistake
that turns a bounded capability into a shell, so a declaration that hands
over a string is refused rather than parsed.

**Every param used in `argv` must be constrained** by `enum` or
`pattern`. An unconstrained `make {target}` is refused as a laundered
allowlist: it looks declared while granting arbitrary execution. The
bound is the point, not the ceremony. A value that passes its constraint
lands as exactly ONE argv element, so spaces, quotes and semicolons in it
are inert data.

**`env` obeys the same law as `argv`.** An environment variable is a
process input like any other, and a free string there would reopen the
same hole less visibly — nobody reads the environment when they read a
command.

**Trust on first use.** The approved declaration is hash-pinned per
machine in `.tee/pipeline.pin`. An unapproved or CHANGED declaration
refuses to run and names the change; a cloned repo's `pipeline.toml` is
attacker-authored by definition. Deleting the pin revokes everything.

**Untrusted content can never cause execution.** A task that has read a
web page, a fetched document or a fronted backend's output is TAINTED,
and a tainted task may not run a declared step — the refusal is
immediate, not a shadow-mode note. Only a live human turn lifts it.

**TEE never writes `.tee/pipeline.toml`, and never approves its own
inputs.** Both proposal routes below write somewhere else and tell you to
move the result yourself.

## Three ways to author it

**1. Draft from your own scripts.** `pipeline_init` reads the project's
entry points — docstrings, required flags, whether they use argparse or
bare `sys.argv` — and writes `.tee/pipeline.proposed.toml`. Every block
in it is **commented out**, so the draft copied verbatim into
`pipeline.toml` declares exactly zero steps. A scan of your build scripts
is a guess about your intent, and a guess must not become permission to
run something just because it is valid TOML. Uncomment what you want,
replace each `<FILL>`, and state the inputs and outputs it really
touches.

**2. Hand-write it.** The schema above is the whole surface. Refusals
name the exact fix.

**3. Run it once, then adopt it.** The discovery route, and the one most
used in anger: you do not know the step until you have run the command.
`pipeline_adhoc` runs one argv list — live human turn only, and only when
the project has opted in with `[pipeline] allow_adhoc = true` AND the
separate `run-adhoc` grant. `pipeline_adopt` then writes the declaration
TEE *would* write, inferred from what the run actually touched, into
`.tee/pipeline.proposed.toml` for you to move.

## Turning it on

`.tee/config.toml` in the project:

```toml
[trust]
grants = ["run-declared-step"]

[pipeline]
allow_adhoc = false
```

`run-declared-step` permits running steps that are declared AND approved,
and nothing else. `run-adhoc` is a separate capability, deliberately
absent by default: with only the grant above, nothing can execute
anything this project has not declared and you have not read.

## Running it

`pipeline_list` shows what is declared and whether it is approved.
`pipeline_run` takes a step name and its params. It resolves the DAG —
if step B reads a path step A writes, B depends on A, and nobody writes
that edge — hashes the declared inputs against the run manifest, and runs
only what is stale, naming every skip with its reason. `force = true`
runs anyway and says so.

* A **produce** step answers with an artifact diff over its declared
  outputs: created, changed, unchanged, with sizes and hashes.
* A **query** step answers with its own output in the declared format,
  held to the declared budget. A successful answer is recorded, so the
  same unchanged question is answered for free instead of re-run. A
  FAILING one is never recorded — a failing check must not be cached into
  looking fixed.
* A **failure** is one line naming the step plus a bounded tail. Never a
  log dump.

Steps are ordinary jobs: batch class, admitted by the scheduler, holding
their declared footprint in the machine ledger, metered beside chores and
reconstructions. With the scheduler off they run sequentially and produce
byte-identical artifacts.

## Two worked examples

Both are recorded end to end in
[`pipeline-first-customer.md`](pipeline-first-customer.md).

**A terrain build** (`~/DiversionPlanner-BaseMap`): five steps whose
flags come straight out of the project's own runbook. The builder runs
end to end in plan mode in 0.2 s and answers with a diff over the three
files it declared. The real cell build — tens of gigabytes, hours — is
declared too, so it can be launched by name, but it is never what a vague
sentence resolves to.

**A game project** (`~/OkongoSim`): three steps, one of which runs
headless inside Blender's bundled python with Blender's own `--`
separator sitting in `argv` as an ordinary string. It shares nothing with
the terrain project except the shape of a declaration, and running it
needed no change to `server/` at all.

## What it costs

Measured, in [`../benchmarks/RESULTS.md`](../benchmarks/RESULTS.md). The
short version: a produce step is **−74.5%** against pasting the command
and its log, because a diff replaces a build log. A short-output query
costs 8–40 tokens MORE than pasting it, and those tokens buy a command
that cannot be misremembered plus the hashes saying what the answer came
from. Repeated successful queries are free in both tokens and wall clock.
