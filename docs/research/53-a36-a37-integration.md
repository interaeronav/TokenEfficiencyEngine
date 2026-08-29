# 53 — Integrating the roadmap build (A36) with the fabrication lane (A37) (2026-08-28)

Verification basis: research 51 and 52 (the two designs of record),
the A36 script's laws, open-web check of the FreeCAD MCP landscape
(2026-08-28, sources inline), and the live kb_search grounding from
research 52. This doc is the composition map; it adds no new feature
scope beyond 51 + 52.

## Why integrate (the seams are real, not cosmetic)

1. **The Gateway changes how the CAD lane is built.** Research 52
   assumed a first-party FreeCAD adapter. But `neka-nat/freecad-mcp`
   exists and is maintained (10 tools incl. execute-Python and FEM;
   an in-FreeCAD RPC addon + external stdio server — the Blender-
   bridge topology). Research 51's law — fronting beats
   reimplementing — applies: the Gateway can front it for the long
   tail, and TEE's own fabrication lane stays thin.
2. **The adapter kit gets its rehearsal for free.** A36's kit
   acceptance was "build a toy adapter from the kit docs alone."
   Building the REAL FreeCAD fabrication toolset from the kit is the
   honest version of that test — every stumble is a kit bug found by
   a real consumer.
3. **kb_propose and joinery_check close a loop.** joinery_check lifts
   KB facts through A30 re-verification; whatever that verification
   learns (and whatever web_lookup finds in hardware catalogues)
   flows back as kb_propose drafts for owner review.
4. **Meter and handoff are riders.** Fabrication sessions are long
   and multi-stage — exactly what the savings ledger and the portable
   brief are for; the fabrication benchmark becomes a meter fixture.

## The FreeCAD decision, made a probe not an opinion

Hybrid architecture, settled by measurements in the first phase:

- **Front** neka-nat's server through the Gateway for discovery, the
  Python escape hatch, and FEM — its responses (screenshot-prone, per
  the genre) get the Gateway's budgets and trimming regardless.
- **Build thin** TEE's own fabrication toolset (typed sketch/solid/
  assembly batch ops, TechDraw drawing pipeline, STEP/DXF/glTF
  export, joinery_check integration) — the parts that need TEE's
  checkpoints, diffs and report contracts, which no fronted naive
  server provides.
- **One bridge, not two**: if the probe shows neka-nat's in-FreeCAD
  RPC addon is solid, TEE's thin lane rides THE SAME bridge; only if
  it fails the probe does TEE ship its own minimal bridge (Blender-
  bridge lineage). The drift-firewall fingerprints it either way.
- **Probe criteria** (pass/fail, recorded): headless or GUI-required?
  (TechDraw headless export proven separately — upstream #5710);
  round-trip latency; response token shape; crash behavior on a bad
  op; license (it must pass the lint to be recommended in docs).

## Phase order for the merged campaign (rationale)

Gateway core (fakes) must precede any fronting; the kit must precede
the FreeCAD lane (rehearsal law); kb_propose ships with the joinery
lane so re-verified facts have somewhere to go; Home Builder rides
the EXISTING Blender adapter so it can proceed in parallel with
Gateway work whenever the machine is otherwise idle; meter/handoff
land before close-out so the final benchmark session exercises them;
boards last (consumes renders from both lanes). A35 (shrink) stays a
separate campaign, never concurrent on the branch.

## Risks specific to the integration

- **Double-bridge drift**: mitigated by the one-bridge rule + the
  fingerprint firewall.
- **GUI-required addon vs headless ambition**: probed day one; the
  recorded fallback is FreeCADCmd for TEE's lane with the addon only
  for fronted extras.
- **Scope gravity**: the merged campaign is large; the script keeps
  every A36 law (zero surface growth, untrusted fronted content,
  bars as floor) and phases small enough that any single session
  closes at least one acceptance.

Sources: github.com/neka-nat/freecad-mcp (+ README, releases, addon
tree), pulsemcp.com/servers/neka-nat-freecad, mcpservers.org entry;
research 51/52 sources stand for everything else.

## Addendum 3 (2026-08-29): the P0 probes ran — one bridge, decided by measurement

Installs (owner-approved batch): FreeCAD 1.1.3 arm64 (620 MB dmg, SHA256
verified, 2.5 GB unpacked; the security release), Home Builder 5.1.0
(19.3 MB, blender_org repo; operator namespaces live headless), and
neka-nat/freecad-mcp (14 MB clone, MIT — passes the lint).

**Probe A — TechDraw under freecadcmd** (1.1.3; binary moved to
`Contents/Resources/bin/freecadcmd`): parametric modeling, TechDraw
page + view + DIMENSION creation, **DXF page export** (writeDXFPage,
6,498 B) and **STEP export** all PASS fully headless. **SVG page export
does not exist headless** (the module exposes only exportSVGEdges /
writeDXFPage / writeDXFView; the DrawPage object has no svg/pdf
methods) and **PDF is GUI-bound** ("Cannot load Gui module in console
application") — upstream #5710 confirmed live on 1.1.3.

**Probe B — the neka-nat bridge, fronted through the TEE gateway**
(uvx freecad-mcp --only-text-feedback → addon RPC :9875 in the GUI
process; the addon imports FreeCADGui at module top — GUI-required by
construction): connect 5.36 s (first uvx fetch included), **15 tools**
(incl. execute_code, execute_code_async, FEM, parts library) pinned as
FreeCADMCP@/4007534df97c; raw catalog schemas 5,422 tok naive vs 0
always-loaded through the gateway (describe = 144 tok); **call latency
0.01–0.05 s** end to end; geometry round-trip verified (box volume
24000.0); **bad op answers a clean one-line text error, no crash,
backend alive after**; text mode 26–38 tok/op.

**The one-bridge decision: neka-nat's bridge IS the lane's GUI
transport.** TEE ships no second bridge. The fabrication lane (P4)
drives modeling through typed ops over this bridge (execute_code where
a typed op is missing), and renders SVG/PDF drawing sheets via
TechDrawGui THROUGH the same bridge — the #5710 fallback and the
one-bridge rule satisfied by the same process. freecadcmd remains the
headless vehicle for CI contract tests and for batch DXF/STEP export
paths that need no GUI. Fronting stays as measured in P2; the drift
firewall covers addon upgrades.
