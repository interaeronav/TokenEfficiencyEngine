# 65 — Trust-kernel integration blueprint: the build sequence, grounded (2026-08-30)

Verification basis: consolidates research 61 (model), 62 (seams),
63 (hardening), 64 (simulation) into ONE build order, grounded in
reads this session of the two install points FP-1 depends on:
- `server.py:_tool()` wrapper — a SYNC choke (`with app.lock: fn(...)`)
  that ALREADY calls `app.response_log.record(name, result, request=)`
  on every call. Audit logging is therefore half-built at exactly the
  right seam, and a ContextVar set here is trivial (sync, no async).
- `jobs.submit(fn: Callable[[],dict])` stashes `fn` as a THUNK run
  later by a daemon worker — so `contextvars.copy_context()` at submit
  + `ctx.run(fn)` in the worker is a ~5-line, two-site change, not a
  call-site sweep.

This is the "how it actually goes in" doc. No new findings; it orders
the accumulated ones so the build cannot proceed unsafely.

## The dependency spine (each layer needs the one below)

```
L0 capability map        (verbs+resources; 103 tools tabled by module)
L1 grant table + default-deny   (config; read-tier open, else closed)
L2 caller context        (ContextVar @ _tool; copy_context @ jobs.submit)   <- FP-1
L3 taint set + derive()  (ids only; union on derive; orphan=tainted)        <- FP-5
L4 the ONE check         (registry.call + 3 other surfaces; coverage test)
L5 audit                 (extend response_log.record — already at the seam)
L6 shadow (CHOICE only)  (quality denials measured; SAFETY enforces now)    <- FP-2
L7 owner-signed flip     (typed-phrase, multi-signal; never a scalar)       <- FP-4
```

Rule: **no layer may be skipped or reordered.** L2 and L6 are the two
that MUST exist before ANY enforcement touches a side effect (research
64); L7 is the only thing that turns quality-denial enforcement on.

## L2 — caller context, at the two verified sites (FP-1)

```python
# kernel/trustctx.py
CALLER: ContextVar[str] = ContextVar("caller", default="content-derived")
```
- `_tool.wrapper`: `tok = CALLER.set("live-turn")` inside `with app.lock`,
  `CALLER.reset(tok)` in `finally`. A call arriving at the MCP boundary
  IS a live turn — the one place the class is minted, never accepted
  from below.
- `jobs.submit`: `ctx = copy_context()`; worker runs `ctx.run(fn)` — the
  snapshot re-installs the caller inside the daemon thread (threads do
  NOT inherit it; verified none today).
- chore/gateway entrypoints: read `CALLER.get()`; **absent/unknown ->
  treat as tainted** (fail-closed). Default is already the safe class.

## L4 — the one check, provably complete

`trust.check(capability, caller=CALLER.get(), project, taint)` slots
into `registry.call` beside the existing `disabled` refusal (verified
pattern). Completeness is structural, not vigilance:
- `VirtualTool.capability` REQUIRED -> a capability-less tool fails at
  STARTUP;
- a coverage test enumerates the four entry surfaces (registry, MCP
  handlers, jobs.submit, gateway/engine clients) and asserts each
  routes through `check`;
- the check composes with `jobs.may_admit` already at submit — trust
  answers "may this caller?", admission answers "can the machine?";
  both must pass, order: trust first (cheaper, fail-closed).

## L5 — audit is half-done

`response_log.record(name, result, request=kwargs)` already fires per
call at `_tool`. Extend its record with (capability, caller, taint,
grant-used, decision) — no new call site, one struct widened. Per-
project audit log = this stream filtered to side-effecting decisions.

## L6 — the shadow/safety split (FP-2, the correction)

Two separate switches, never one:
- `[scheduler] dispatch` — engine CHOICE; may shadow-first, replay-gated.
- `[trust] enforce` — SAFETY denials; the read tier and all high-risk
  capabilities (run-adhoc, write-config/policy, call-paid-engine)
  enforce from day one REGARDLESS of this switch; only taint-vs-quality
  denials wait for it. A broken `[trust]` file fails closed for side
  effects, open for reads (research 63).

## L7 — the flip is owner-signed (FP-4)

Turning `[trust] enforce` on for the quality-denial band requires an
owner typed-phrase after `tee_trust --rollout` shows: coverage across
capability classes, adversarial canaries passing, the weighted denial
budget. Never an automatic scalar a caller can steer.

## Interaction audit (does it break shipped subsystems?)

- **Jobs admission/backpressure**: composes — trust gate precedes
  `may_admit`; both refuse loudly, rule-6.
- **Gateway**: prefix + fingerprint already blunt impersonation (FP-3);
  add description-taint + local-name-collision refusal.
- **Router/swap**: `call-paid-engine` becomes a trust capability;
  tainted tasks can't reach it (FP-4 of research 63) — this finally
  gives SI-B16's `paid` flag teeth through the kernel, not a private
  check.
- **Scheduler shadow**: unchanged; `[trust] enforce` is its own switch.
- **Client policy (owner law, A43)**: the live-turn class is the ONLY
  untaint path and it maps to the client's own consent turn — the
  kernel complements the client's approval flow, never substitutes or
  bypasses it.

## Build order for T-1 (revised, dependency-safe)

1. L0 capability map + L1 grants + default-deny (read tier usable).
2. L2 caller ContextVar (both sites) + fail-closed chore entry.
3. L3 taint + `derive()`; L4 the check + startup guard + coverage test.
4. L5 audit widening.
5. High-risk capabilities enforce NOW (no shadow for safety).
6. L6 shadow the quality-denial band; L7 owner-signed flip.
7. THEN P0/P0b (pipeline schema + ad-hoc) as the kernel's first tenant.

## Verdict

The integration is a stack, not a patch: seven thin layers, two
(L2, L6) mandatory before any side-effect enforcement, each grounded
in a verified seam. The two hardest-sounding fixes (thread-hop taint,
shadow-safety split) are small and precise once located — FP-1 is
~5 lines at two sites, FP-2 is two config switches instead of one.
Nothing here is new capability; it is the safe assembly order for what
61-64 specified. Ready to build.
