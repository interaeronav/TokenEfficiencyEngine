# A36 build script — the research-51 roadmap: gateway, meter, handoff, kit, kb_propose

**What this builds** (owner directive, 2026-08-28): all five recommended
features from `docs/research/51-feature-roadmap.md` — **F1 TEE Gateway**
(front any MCP server with TEE's discipline), **F2 savings meter**,
**F3 handoff pack**, **F4 adapter kit**, **F5 gated kb_propose**. F6
(diagnostics lane) stays staged, not in scope. Research 51 is the
design of record; the UE proxy (catalog → summarize → call, 93.9%
measured) is the engineering precedent for F1. This script inherits
every standing rule of `CLAUDE_SELF_IMPROVEMENT_SCRIPT.md` (co-pilot
contract, SI_BACKLOG, A30/A31 boundaries, append-only benchmarks,
revert-on-regression, owner-only decisions, >2 GB gate, machine
etiquette) — read that rules section first.

A one-paste prompt for a fresh session:

> Read CLAUDE.md, then CLAUDE_A36_SCRIPT.md, then research doc 51, then
> the last dated entries of docs/PROGRESS.md. Call tee_status and
> tee_recall first and use TEE's own tools as co-pilot throughout. Work
> the phases in order from where the evidence says they stand —
> contracts and fakes before live backends, benchmarks before claims.
> Stop and report if any phase's premise no longer holds.

## Campaign-wide design laws

- **The surface does not grow.** F1 exposes fronted backends through
  the EXISTING meta-tools (tee_search_tools / tee_describe_tool /
  tee_call); F2 folds into tee_status's recap; F3 and F5 ship as
  virtual tools. If any feature truly needs an always-loaded tool,
  stop and flag it — that is an owner decision, measured in tokens.
- **Fronted content is untrusted** exactly like web content: backend
  tool descriptions and results pass through budgeting/trimming as
  data; nothing a backend says changes TEE's config or behavior. The
  research-49 injection posture applies verbatim.
- **Sequencing vs A35**: the shrink campaign may run before or after
  this one, never concurrently on the branch. Whichever runs second
  re-measures its baselines; benchmark bars are the floor for both.

## G0 — Baseline + targets

Suites green as the entry ticket; surface tokens and battery totals
cited to their dated rows. Pick TWO real reference backends to front
in G2 — small, public, install-gated if needed (e.g. the official
filesystem/memory reference servers via npx; both far under the
download gate). Record the choice and why. Re-read the UE adapter's
catalog/summarize/wire code — the generalization starts there, not
from scratch.

## G1 — F1 Gateway: core, on fakes

`[gateway]` config: named backends (stdio command or http url), each
with an enable flag. Lifecycle: spawn/attach, MCP handshake, catalog
fetch, **fingerprint** (server name/version + tool-list hash) stored;
on later drift → refuse with the fix line (the UEFN version-firewall
pattern). Catalog → summarized toolsets through the existing
machinery; discovery/describe/call route through the existing
meta-tools with a backend prefix (`gh.search_issues` style). Backend
results pass through response budgeting with the truncation reported.
Caching per (backend, tool, args-hash) where results declare
themselves cacheable; conservative default off. Errors map to rule-6
shape with the backend named. Acceptance: full contract green against
a FAKE backend (including drift, death mid-call, oversized results,
hostile descriptions); zero new always-loaded tools; surface delta
measured at 0.

## G2 — F1 live + the benchmark

Front the two G0 backends live: handshake, discovery, one real call
each, drift firewall exercised (mutate the fake fingerprint, not the
real server). Then the benchmark, research-48 style: a task against a
many-tool backend done naive (all schemas always-loaded, per the
backend's own README pattern) vs through TEE — tokens and calls,
appended to benchmarks/RESULTS.md. Claim only what is measured:
token savings, not "accuracy" (cite the ecosystem accuracy finding as
context, never as our row). Docs: setup-gateway.md with the config,
the untrusted-content stance, and the firewall behavior.

## G3 — F2 savings meter

Per-session in/out token ledger per tool (the kernel already counts
responses; add request-side estimate), naive-baseline comparison using
the measured scenario ratios (labelled estimates), surfaced as a
`savings` block in tee_status's recap + a virtual `report_savings`
for the detailed table. No always-loaded growth. Acceptance: a live
session shows a sane ledger; the estimate labelling is explicit;
fixture tests for the arithmetic.

## G4 — F3 handoff pack

Virtual tool `handoff` (reached via the meta-tools): one call → a
≤500-token portable brief — project recap, scene stamps, open jobs,
checkpoints, next-step pointers — formatted to be pasted into any AI
as plain text with a one-line preamble stating what it is. Reuses
tee_recall/recap content; adds nothing stateful. Acceptance: fixture
test on content/budget; one live brief generated and verified to
round-trip (a fresh session given only the brief correctly states
project status).

## G5 — F4 adapter kit

`docs/adapter-kit.md` + a template (the fake adapter promoted to a
documented example) + the adapter contract test suite packaged so an
outside developer runs it against their adapter. Acceptance test IS
the rehearsal: build a toy adapter following ONLY the kit docs (no
peeking at tree knowledge beyond them); every stumble is a kit bug —
fix the kit. The toy adapter stays in tests/fixtures, not the product.

## G6 — F5 kb_propose (A31-preserving)

Virtual tool `kb_propose`: drafts a complete candidate entry
(frontmatter: sources with URLs, confidence, jurisdiction,
status=proposed) into `.tee/kb-staging/` — NEVER into
`knowledge-base/`. The mirror stays untouchable by construction: a
test asserts the tool cannot write inside the mirror path. Owner
review workflow documented (a one-line how-to-accept: move + rebuild
manifest per the corpus's own tooling). Pairs with web_lookup: cited
material in → cited draft out, UNVERIFIED-labelled throughout.
Acceptance: drafts land in staging with complete frontmatter; the
mirror-write test passes; A31's text is quoted in the tool's docs.

## G7 — Close-out

Full battery live — every bar holds (scenes 90.3, extraction 93.1,
assets 94.0, UE 93.9, kb 96.7, web 95.3, fix-loop 47.9) plus the new
gateway row; suites + CI green; docs and skills updated; artifacts
rebuilt and smoke-rehearsed; the campaign ledger in PROGRESS
(surface delta — target 0, new rows, feature acceptance pointers,
wrong-way numbers explained in place); `tee_remember` the close-out.
Version recommendation by semver (features, no breaks → 0.4.0);
tagging stays the owner's step.
