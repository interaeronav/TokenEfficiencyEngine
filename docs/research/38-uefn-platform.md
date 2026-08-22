# 38 — UEFN platform state (2026-08-22)

## What UEFN is (automation-relevant identity)

A specialized UE editor build with Verse-only scripting (no Blueprints,
no C++), ~4,698 Creative device variants, and the Scene Graph
entity/component model in Beta (publishable islands since Jun 2025 —
and per State of Unreal 2026, Scene Graph IS the UE6 gameplay
framework). Projects are `.uefnproject` with cloud-backed Unreal
Revision Control; Epic open-sourced the **Lore** VCS (MIT) and ships a
`lore.exe` CLI (clone/commit/branch/merge/bisect — needs a cached UEFN
auth token and the project closed in the editor; no build/validate/
publish verbs). **There is no headless UEFN**: Windows-only, GUI open,
logged in.

## UEFN MCP (v42.00, 2026-08-20) — the anchor fact

Epic's Unreal MCP (the UE 5.8 plugin) is now built into UEFN, **beta**:
enable BOTH "Python Editor Scripting" and "UEFN MCP Toolsets" under
Beta Access; loopback HTTP+SSE at `127.0.0.1:8000/mcp`, server name
`unreal-mcp`, NO auth; console commands include
`GenerateClientConfig ClaudeCode`. Toolsets are UEFN-specific — NOT the
full 52 of UE 5.8 (no Blueprint/PCG/Sequencer/material workflows):
Toolset Registry (discovery meta) plus **Verse** (read/edit/compile/
search with agent loops on compile errors), **Entity / Verse Scene
Graph** (create/index/edit entities, components, transforms),
**Device** (catalog browse, placement, `@editable` property edits),
**Session** (Play-in-Client launch/stop, HOT Verse push into a running
session, client log reads). A UMG-UI toolset is claimed in the 42.00
notes but absent from the MCP doc page (UNVERIFIED discrepancy); one
extraction claimed "no longer experimental" — the docs say beta; treat
beta as authoritative.

Known issues: LUF↔XYZ coordinate/transform mismatch (active bug class —
normalize in the TEE proxy); MCP calls run serially on the game thread
and can hitch/hang the editor; enabling MCP toolsets broke
`init_unreal.py` (day-2 bug). Python scripting (v40.00, Python 3.11)
was CVar-gated behind an ACCOUNT allow-list through mid-Aug; whether it
is self-service at MCP launch is UNVERIFIED → TEE must detect
missing-Beta-Access and surface the remediation. Python property writes
are allow-listed: anything not displayed in the UI fails validation.

## Automation verdicts

- **Drivable today:** the Verse loop (edit→compile→diagnose), device
  placement/config, Scene Graph entity ops, playtest sessions (needs a
  logged-in Fortnite client on the same machine), Lore VCS, analytics.
- **Partial:** bulk Python world-building (allow-list), asset import.
- **Human-only:** cook/memory calculation (GUI), publish (web Creator
  Portal + IARC rating + moderation queue). Never promise closed-loop
  publish.
- **Analytics is free:** the public **Fortnite Data API**
  (`api.fortnite.com/ecosystem/v1`) serves per-island minutes played,
  retention and CCU-class metrics, 7-day lookback, unauthenticated.

## Budgets

100,000 memory units per area (per-position with Level Streaming;
cook-time computed; all referenced assets count). 400 MB download cap is
a 2023 figure (current value UNVERIFIED). NoMipmaps textures fail
validation.

## Creator economy (why the wedge matters)

Over $1B cumulative payouts (State of Unreal, Jun 2026); creator islands
took 47% of all Fortnite player hours in May 2026; the engagement pool is
40% of eligible net Item Shop revenue. **Nov 1 2025 formula change: only
ever-paying players count** (community reports payouts down ~70% at the
same CCU). In-island V-Bucks transactions live Jan 9 2026 (100% of value
to creators through Jan 2027, then 50%; disclosed-odds random items
allowed). Islands are single-genre by rule; dominant genres: box PvP,
zone wars, RvB, tycoons, prop hunt, deathruns. Rule 1.7.1 bans
recreating Epic IP not provided in UEFN.
