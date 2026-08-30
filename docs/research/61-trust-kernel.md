# 61 — The trust kernel: one capability model, taint-aware, progressively granted (2026-08-30)

Verification basis: repo survey this session — TEE today carries FOUR
unrelated permission flags (`allow_code_exec`, `allow_local`,
`allow_sa`, per-backend `enable`) and provenance/caller concepts
already spread across eight kernel modules (adapter, contract, jobs,
machine, shadow, local_llm, chores, router); research 60 + its two
addenda (the pipeline trust law and the qmax critique); the owner's
question, verbatim: how to integrate this logic so TEE serves MORE
projects "without being a tool that can be taken advantage of by
malicious actors or codes."

## The finding: TEE grew a permission system without naming it

Every capability so far shipped its own gate, in its own style, with
its own default. That works until capabilities COMPOSE — and they now
do: a gateway-fronted backend can return content that steers a chore
that could trigger a pipeline step that writes files. No single flag
can reason about that chain, because each flag only knows itself.
Adding a fifth flag for the pipeline lane repeats the mistake at the
exact moment the surface gets its first execution capability.

## The model: one decision, three axes, default deny

A single `trust` module answers ONE question everywhere:
**may THIS caller invoke THIS capability on THIS project right now?**

1. **Capability** — the verb, not the tool: `read-scene`, `read-kb`,
   `fetch-web`, `run-declared-step`, `run-adhoc`, `exec-code`,
   `write-files`, `call-paid-engine`, `front-backend`. Tools map to
   capabilities; new tools inherit an existing verb or declare a new
   one (a reviewable event, not a new flag).
2. **Grant** — how the owner authorized it, per project: a config
   line, a hash-pinned declaration file, or live-turn consent.
   Absent grant = refusal, always (default deny).
3. **Caller class** — who is asking: `live-turn`, `chore`, `job`,
   `scheduled`, `gateway-fronted`, `content-derived`. The A42 task
   graph already stamps this; the trust kernel reads it instead of
   each feature re-deriving it.

## Taint: the one law that covers every ingestion path

The scattered rules ("web content is inert", "backend descriptions are
data", "KB prose grounds nothing", "a cloned repo's declarations are
attacker-authored") are all the same law, so state it once:

> A task whose inputs include untrusted content is TAINTED, and a
> tainted task may never invoke a side-effecting capability.

Taint propagates along the task graph A42 already built — that is why
this is affordable now and would not have been a year ago. It composes
by construction: no new rule is needed when a future capability
arrives, and no ingestion path can be forgotten. Untainting is
possible only by a live human turn (the owner reading the thing and
acting), which is exactly the consent MCP clients' "always allow"
removes.

## Progressive trust: how safety stops fighting usefulness

Projects do not start dangerous or useless — they start **read-only
and immediately valuable**: KB answers, budgeted web lookups, scene
reads, declared *query* steps. Nothing in that tier can change a byte,
so onboarding a new project costs the owner no risk decision at all.
Widening is per capability, per project, one line each, and always
revocable:

| tier | grants | what it unlocks |
|---|---|---|
| read (default) | none needed | kb, web lookup, scene/state reads, query steps |
| build | `run-declared-step` + hash-pinned declarations | produce steps, artifact diffs, the DAG |
| explore | `run-adhoc` | live-turn ad-hoc commands + the adopt flow |
| power | `exec-code`, `call-paid-engine` | the existing escape hatches, now uniform |

This is the answer to "more useful to more projects": the *useful*
default tier carries no execution risk, so breadth costs nothing —
and each step up is a sentence the owner writes, not a switch a model
can flip.

## Visibility, because ungrantable is unusable

- `tee_trust` (virtual, zero always-loaded cost): what may this
  project do, which grants are active, which file granted them, what
  is pinned, what was refused recently and why.
- Every refusal is rule-6 shaped: the capability, the caller class,
  the missing grant, and the EXACT line to add — plus the config file
  actually loaded (closing SI-B17, where an edit-that-went-nowhere
  was indistinguishable from a bug).
- Every side-effecting call is audit-logged per project.

## Retrofit, without behavior change

`allow_code_exec` → `exec-code`; `allow_local` → `fetch-web` scope;
`allow_sa` → an assets-license grant; gateway `enable` →
`front-backend` per backend; the unenforced `paid = true` (SI-B16) →
`call-paid-engine`, which finally gives it teeth. Each mapping ships
with a fixture proving identical behavior before and after; the flags
stay valid as aliases so no existing config breaks.

## Risks and gates

- **Over-engineering** → ONE decision point, no policy language: TOML
  grants only, no expressions, no roles, no inheritance. If it needs a
  DSL it is wrong.
- **Taint false-positives blocking real work** → a taint refusal must
  name what tainted the task and offer the live-turn path; measured on
  the A42 traces before it goes live (shadow first, per the scheduler
  precedent).
- **Grant sprawl** → `tee_trust` lists everything in one screen;
  grants are plain lines in one file per project.
- **Performance** → one dict lookup per call; overhead measured and
  published like the gateway's.

## Verdict

Build the trust kernel FIRST and make the pipeline lane its first
tenant, rather than giving the pipeline a fifth private flag. It
converts TEE's accumulated ad-hoc gates into one reviewable model,
makes the composition risks reasonable-about, and — via the read-only
default tier — makes breadth across projects free instead of scary.
Recorded as A44; the A43 script gains it as its foundation phase.
