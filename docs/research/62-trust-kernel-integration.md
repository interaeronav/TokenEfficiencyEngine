# 62 — Integrating the trust kernel into TEE: the seams, verified (2026-08-30)

Verification basis: direct reads this session of `kernel/registry.py`
(the virtual-tool dispatch), `kernel/shadow.py` (A42's TaskDescriptor
+ ShadowRecorder + replay), `app.py` (registry construction, adapter
resolution, status/recap), and the module inventory (11 kernel modules,
2,998 lines). Design of record: research 61 (the model). This doc is
the *how*: where the check goes, how taint actually propagates through
existing structures, and how it lands without breaking 790 tests.

## Finding 1 — there is a real choke point, and it already has the pattern

`ToolRegistry.call()` is three lines: `_require` → `_validate` →
`handler(args)`. And `_require` ALREADY refuses on a per-project
policy — the `disabled` set, raising `tool_disabled` with a rule-6
fix. So the trust check is not a new concept at this seam; it is a
second predicate beside an existing one:

```
call(name, args) → _require (exists) → _validate (exists)
                 → trust.check(capability_of(tool), caller, project)   ← new
                 → handler(args)
```

## Finding 2 — but the registry is not the ONLY entry surface

Verified: the 17 always-loaded tools are served by the MCP handlers,
not the registry; jobs enter through `jobs.submit`; chores and the
router call engine code directly; gateway-fronted calls arrive through
the backend client. So "one decision point" must mean **one decision
FUNCTION with a proven-complete set of call sites**, not one call site.

The proof-of-completeness must be structural, not vigilance:

- **Registration-time enforcement.** `VirtualTool` gains a required
  `capability` field; a tool registered without one fails AT STARTUP.
  A future contributor cannot add a capability-bearing tool that
  silently escapes the kernel — the server refuses to boot instead.
- **An entry-surface coverage test** that enumerates the four surfaces
  (registry, MCP handlers, jobs.submit, engine/backend clients) and
  asserts each routes through `trust.check`. A new surface added
  without a check fails this test.

That pair is what turns "we remembered everywhere" into "it cannot be
forgotten".

## Finding 3 — taint is affordable ONLY because TEE passes ids, not payloads

`TaskDescriptor` already declares `inputs`/`outputs` as *"ids/pointers,
never payloads"* — the same discipline that makes TEE token-efficient
(research 58's unified-memory analogy). That is exactly what makes
taint tracking cheap and possible:

> Taint is a property of an **id**, not of a string. A task inherits
> taint if any input id is tainted.

Sources that mint tainted ids: `web_lookup` extracts, gateway backend
results, KB reads, extract facts derived from third-party media, and
declarations from an unapproved/changed pipeline file. Each already
returns identified content — nothing new to plumb. Payload-level taint
would be impossible (prose pasted into a prompt loses provenance); id
level is a dict lookup.

`TaskDescriptor` needs two fields — `caller` (the class; `kind` already
carries chore|job|swap|gateway, three of the six) and `taint` (the
inherited set) — both optional, both defaulting to today's behavior.

## Finding 4 — A42 already shipped the way to validate this safely

`ShadowRecorder.record(task, actual)` computes what the shadow policy
WOULD have chosen, stores a delta, and `replay()` runs accumulated
traces. The trust kernel rides the same machinery: **shadow-first
enforcement.** For a period, every `trust.check` records
allow/deny-it-would-have-made beside what actually happened. The
kernel goes enforcing only when the replay shows zero false denials on
real recorded work — the same discipline that let the scheduler go
live. This is the difference between a security layer that ships and
one that gets disabled the first time it blocks something real.

## Failure modes, decided in advance

- **Kernel raises / config unreadable** → fail CLOSED for
  side-effecting capabilities, fail OPEN for the read tier. A broken
  trust file must never brick `kb_search`; it must always brick
  `run-adhoc`. (Read-tier-open is safe precisely because that tier
  cannot change a byte — research 61's tier table is what makes this
  split defensible.)
- **No grants file at all** → the read tier works; anything else
  refuses with the exact line to add. New projects therefore work
  immediately and safely, which is the adoption story.
- **Taint false positive** → refusal names the tainting id and its
  source, and offers the live-turn path; measured in shadow before
  enforcement.

## Migration without breaking 790 tests

1. `capability` defaults to a read verb for the 103 existing virtual
   tools, assigned per module (all `kb_*` → `read-kb`, `as_*` reads →
   `read-assets`, mutations → `write-scene`), reviewed once in one
   table rather than 103 decisions.
2. The four existing flags become **aliases** that grant their
   capability, so every existing `.tee/config.toml` keeps working
   untouched; fixtures assert identical behavior before/after for each.
3. Suites: the whole battery must pass with the kernel present and
   shadow-only; then again with enforcement on and the default grants.
   Any bar that moves is a defect in the mapping, not a new normal.

## Performance budget

One dict lookup per call (capability→grant) plus a set membership
(taint). The comparable measured overhead is the gateway's
+0.007 ms/call (A38). Budget: **≤0.05 ms per call, measured and
published** beside the gateway's number; anything above that is a
design error, not a tuning problem.

## Acceptance (what T-1 must prove)

Startup refuses a capability-less tool; the coverage test enumerates
all four entry surfaces; default-deny holds with no grants file while
the read tier still answers; each legacy flag behaves identically
through its alias; a tainted fixture task is refused naming what
tainted it; a live-turn untaint succeeds; shadow replay over A42's
recorded traces shows zero false denials before enforcement flips;
overhead ≤0.05 ms published; full battery bars unchanged.

## Verdict

The integration is smaller than the concept, because three of the four
pieces already exist in shipped code: a choke point with a refusal
pattern, a task descriptor that speaks in ids, and a shadow recorder
with replay. What is genuinely new is the grant table, the capability
mapping, and the taint set — plus the two structural tests that make
completeness a property of the build rather than a promise.
