# 51 — What to build next: feature research for a better, more useful TEE (2026-08-28)

Verification basis: open-web research run 2026-08-28 (sources cited
inline); internal grounding by direct read of SI_BACKLOG, PROGRESS's
descoped/deferred lists, COMMERCIAL_READINESS, and the A32 mission;
owner-context grounding from the owner's live projects (UE digital
twin, terrain basemap tooling, aviation workflows, heavy local-model
use). Where a claim is a market observation from secondary sources it
is labelled as such — nothing here is a benchmark row.

## The question (owner ask, 2026-08-28)

What other features would make TEE better and more useful?

## External findings that shape the answer

1. **Agents drown in tools.** 2026 ecosystem surveys report production
   agent stacks run 5–9 MCP servers concurrently, and above ~9
   tool-selection accuracy drops (Totalum's 2026 ranking write-up;
   consistent across the curated lists at Taskade/Cubitrek/Gamut).
   Popular categories: code, search, databases, communication, design,
   browser automation. This is a *token and attention* problem — TEE's
   exact specialty, currently applied only to DCCs.
2. **The DCC-adapter whitespace is thinner than it looks.** Godot has
   several live MCP servers (GDAI, Coding-Solo, slangwald and more);
   QGIS has an official-directory plugin and QGIS Connect. But every
   one inspected follows the naive pattern TEE was built to replace
   (per-op tools, raw scene/debug dumps). The precedent that matters:
   TEE's Unreal adapter does NOT reimplement Epic's server — it fronts
   it and measures 93.9% saved. Fronting beats reimplementing.
3. **What hosts install first**: filesystem, GitHub, docs/search,
   memory. TEE overlaps none of these — it complements them, and
   could *discipline* them (below).

## Candidate features, scored

Axes: mission fit (tokens per completed task), owner usefulness (his
real projects), build cost, whitespace (does the ecosystem already do
it), risk. Verdicts are recommendations; building anything is an owner
decision (next free number: A36).

### F1 — TEE Gateway: front ANY MCP server with TEE's discipline ★ build first

One TEE feature that wraps other MCP servers the way the UE adapter
wraps Epic's: their hundreds of tool schemas stay server-side; the
client sees TEE's existing meta-surface (search_tools / describe /
call), plus budgets, response trimming, caching, and batch where the
backend allows it. The 5–9-server accuracy ceiling is exactly this
problem; the UE proxy (830 tools → 3 meta-tools, 93.9% measured) is
exactly this solution, already shipped once. Godot and QGIS arrive
"for free" as disciplined front-ends over their existing servers —
no first-party adapters to maintain. Mission fit: maximal — this is
"help any AI" applied to the whole ecosystem, not just DCCs. Cost:
medium (generalize the catalog/summarize/call machinery that exists;
per-backend quirks are the long tail). Risk: schema drift in fronted
servers → the version-firewall pattern already exists (UEFN).

### F2 — Savings meter: `tee_report` ★ build second (small)

A per-session ledger of tokens in/out per tool with a naive-baseline
comparison, answerable in one call and appended to the recap ("this
session: 14 calls, ~2.1k tok; naive-pattern estimate ~29k; 92%
saved"). The server already counts response tokens; the baselines
already exist in benchmarks. Value: live proof of the product's core
claim, per user, per session — the commercial story tells itself, and
regressions surface in the wild. Cost: small. Risk: baseline honesty —
label estimates as estimates, reuse the measured scenario ratios.

### F3 — Handoff pack: `tee_handoff` ★ build third (small)

One call → a ~500-token portable brief: project recap, scene state
stamps, open jobs, next-step pointers — designed to be pasted into ANY
AI (not just MCP hosts) to continue work. Attacks the "lost context
between sessions" friction named in the README's why-list; tee_recall
already builds most of the content. Cost: small. Also the cheapest
possible demo of TEE to someone who has never installed it.

### F4 — Adapter kit (SDK, contract tests, template) — stage after F1

Docs + a template repo + the fake-adapter contract test suite as a
public kit so third parties build adapters TEE never has to maintain.
Commercial reach play. F1 reduces its urgency (fronting > porting),
but the kit is what makes the ecosystem come to TEE. Cost: medium
(mostly documentation discipline; the contracts exist).

### F5 — `kb_propose`: gated KB authoring — personal-value pick

The KB is deliberately read-only (A31). A `kb_propose` that drafts a
new entry (frontmatter, citations, confidence flags) into a staging
area for OWNER review — never auto-merged — turns the 401-file corpus
into a living library while keeping A31 intact. Pairs naturally with
web_lookup (cited material in, cited draft out). Cost: small-medium.

### F6 — Diagnostics lane: "why does this render look wrong"

ue_look/VLM + scene facts + a rule table (lighting, scale, materials)
→ one budgeted diagnosis. Useful, showy; medium cost; niche next to
F1–F3. Stage behind them.

### Considered and NOT recommended now, with reasons

- **First-party Godot/QGIS adapters**: crowded space; F1 fronts the
  incumbents instead (and QGIS-via-gateway still serves the owner's
  terrain work directly).
- **Windows/Linux support**: real commercial gate, but a platform
  matrix is a cost decision, not a feature — stays on the
  COMMERCIAL_READINESS owner list.
- **URL watch/monitoring, schedulers**: outside MCP's request/response
  grain; hosts do this better.
- **Multi-client shared sessions**: no demonstrated need; locking
  complexity high.
- **More model lanes**: A34 just closed; the re-gate note in PROGRESS
  covers when to revisit.

## Recommended order and the decision

**F1 → F2 → F3** as one campaign (the two smalls ride along F1's
release), then F4/F5 by owner appetite. F1 is the strategic bet: it
converts TEE from "the token-efficient DCC server" into "the token
discipline layer for any agent's whole toolbox" — A32 made literal,
with a measured precedent already in the repo. Building = A36 on the
owner's word; the campaign script pattern (A34/A35) applies.

Sources (2026 ecosystem surveys and directories):
Totalum "Best MCP Servers 2026", Taskade "15 Best MCP Servers",
Cubitrek "Best MCP Servers in 2026", Gamut curated list, mcpservers.org
(Godot entries), plugins.qgis.org (QGIS MCP plugin), gdaimcp.com,
github.com/Coding-Solo/godot-mcp, mcpmarket.com/server/qgis-connect.
