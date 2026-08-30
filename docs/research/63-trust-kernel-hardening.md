# 63 — Trust-kernel hardening: the four soft spots, attacked and fixed (2026-08-30)

Verification basis: an adversarial pass by the qmax engine (Qwen-Max,
4,249 tok billed; treated as INPUT, not authority — each fix checked
against code below); direct reads this session of `kernel/memory.py`
(remember/note store `{key: value}` with NO metadata) and the existing
path-traversal guards in `kb/tools.py` (`is_relative_to` + `resolve()`)
and `uefn/tools.py`. Extends research 61 (the model) and 62 (the
seams) with the edges those two left comfortable. The linchpin
verified first: caller-class is stamped at `server.py:_tool()` — the
MCP entry wrapper — and chores/router/jobs are called from INSIDE
handlers, never from the MCP layer, so a task cannot forge `live-turn`
from below. The four findings assume that holds.

## 1. Laundering through persistence (VERIFIED REAL)

Exploit: a tainted, web-derived chore summary is written via
`tee_remember` (or a `kb_propose` draft). `memory.remember` stores
only `{key: value}` — confirmed, no lineage field. A later session's
`tee_recall` reads it back as a clean value; taint is gone, and a
default-clean caller now acts on attacker-shaped content.

Fix (grounded): taint is persisted as first-class metadata bound to
the key + a content hash; reads rehydrate the taint; a value whose
label is missing or unverifiable defaults TAINTED (fail-closed on the
persistence boundary). A tainted task WRITING to memory/staging is
itself a side effect and cannot strip lineage. This is the one place
the id-based scheme must cross into stored bytes — everywhere else ids
suffice; here the label rides the store.

## 2. Capability granularity — verb+resource, not verb alone (VERIFIED REAL)

Exploit: a single `write-files` verb covers both `out/basemap.tif`
(inert) and `.tee/pipeline.toml` (grants FUTURE execution) or a
grants file (issues capability). A file write silently becomes
privilege escalation via path — exactly the "malicious paths" residual
qmax flagged in the first review.

Fix: capabilities are verb+resource-scope. `write-artifacts` is
limited to declared inert output prefixes; `write-config`,
`write-policy`, and any executable/loader path are SEPARATE
default-deny capabilities. Canonicalize every path (`resolve()`),
block symlinks and traversal, and treat policy/loader files as
meta-side-effects needing an explicit untainted owner grant. The
guard already exists in-repo (`kb_propose`'s `is_relative_to` belt);
this generalizes it into the capability check rather than each tool
re-implementing it.

## 3. Habituation — irreducible, so contained (HONEST)

Exploit: prompt fatigue turns live-turn approvals into rubber stamps;
an attacker floods low-risk prompts, then slips one dangerous grant
past a numbed owner. The human gate — the untaint path — degrades.

Fix, and its honest limit: make assent SCARCE and meaningful — prompt
only for high-blast-radius actions (grants, policy/loader writes,
paid egress), show the concrete effect/diff, require a typed phrase
(not a click) for grant/policy changes, add cooldowns and sampling
audits. Residual habituation is IRREDUCIBLE — no design removes it —
so the load-bearing defenses must NOT depend on human attention:
default-deny, taint-blocking, resource-scoped capabilities and
revocability all hold whether or not the human read the prompt. The
human gate is the last layer, never the only one.

## 4. Taint + egress — a paid engine is still an exit (VERIFIED REAL)

Exploit: a tainted task calls the owner-trusted `call-paid-engine`
with a prompt carrying secrets or web content; the provider sees it
(exfiltration through a *trusted* endpoint), or returns
attacker-shaped output used downstream. "Owner-configured" does not
mean "not an egress."

Fix: `call-paid-engine` is classified side-effecting EGRESS, so the
taint law denies it to tainted tasks unless the owner explicitly
approves that input set in a live turn; request fields are
schema-constrained and allowlisted (not free text), the call is
audit-logged, and the engine's RESPONSE is itself tainted (untrusted
in → untrusted out). This is where the trust kernel, SI-B16 (spend)
and SI-B18 (the sent/egress column) converge: egress must be
visible, bounded, and taint-gated together.

## What this adds to T-1's acceptance

- a memory/staging round-trip preserves taint (write tainted → new
  session reads it back still tainted);
- `write-artifacts` cannot write `.tee/` or a config/policy/loader
  path (canonicalized; symlink/traversal fixture);
- a tainted task is denied `call-paid-engine`, and a paid response is
  itself tainted;
- grant/policy changes require the typed-phrase path, not a bare
  approval.

## Verdict

None of the four defeats the trust kernel; all four sharpen it. Three
are verified-real against the code and get concrete fixes with in-repo
precedent; the fourth (habituation) is honestly irreducible and is
answered by making the human gate the last layer rather than the only
one. The through-line: taint must cross the persistence boundary,
capabilities must name resources not just verbs, and egress is a
side effect — all foldable into T-1 without changing its shape.
