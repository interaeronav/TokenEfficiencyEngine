# 40 — Unreal Engine trajectory 2026–2028 (2026-08-22)

## The roadmap is over; the merge is the roadmap

Epic's public roadmap portal now carries **no forward-looking tab at
all** (parsed the portal data directly: 881 cards, tabs 5.0–5.8 only).
Official words: 5.8 is "the last planned major release for UE5…
reserving the option to release a 5.9, if needed" (maintenance-only).
5.8.1 shipped 2026-07-28. Plan for **5.8.1 as a long-lived baseline**:
gaps that exist now will likely never be fixed in UE5 — TEE's
gap-fillers are durable, not stopgaps.

## UE6 (as stated at State of Unreal, Jun 2026)

UE5 + UEFN unify over two years; Early Access "end of 2027-ish", full
release ≈ 2029. Three stated priorities: (1) **Verse as THE gameplay
model** — C++/Blueprints deprecate when conversion tools mature (no
hard break promised); (2) portability via open standards (glTF/USD
first-class; Fab cross-game Verse modules; the Lore VCS open-sourced
MIT); (3) **"MCP support as productivity multipliers" — MCP is a
stated UE6 pillar.** Scene Graph is the new object model "built from
scratch on Verse", replacing the actor framework; materials, meshes
and Niagara become Verse classes with statically validatable APIs;
distributed STM planned; Cascade removed. **Python's future in UE6 is
unaddressed by Epic** (survival signal: UEFN MCP requires Python
Editor Scripting). Validates A4 doubly: the surface TEE proxies is now
load-bearing strategy for Epic itself.

## MCP evolution facts

5.8.0 shipped 830 tools / 52 toolsets. 5.8.1 changed things TEE must
absorb: SSE framing fix; **"Disable transactions during tool script
execution" — script edits are no longer bundled into one transaction,
so TEE must own checkpoint/rollback and cannot lean on Epic's undo**;
conditional MetaHumanGenerator registration → probe the catalog per
hotfix (keyed on engine version + `list_toolsets` catalog hash +
per-toolset schema hash). Aug 20: UEFN toolsets (the UE6 preview).
Community pain validating TEE's whole thesis: 75K-token property
lists, 1M-token inline PNGs, no batch primitives, silent
save-during-PIE no-op, session tied to editor lifetime. Correction to
doc 07: **StartPIE EXISTS in 5.8 final** (the preview-era gap list is
stale — re-probe before building fillers). Requested-not-present:
landscape toolset, Fab toolset (adjacent to A13). Auth: still
loopback-only with no roadmap → TEE owns the trust boundary durably.

## PCG is being built for LLMs

5.8 PCG Primitives card, verbatim: "fully parameterized and
documented… can be understood and used by LLMs when connected through
the MCP server", plus a Python Data Processor node — direct
confirmation of A21's parameterize-prebuilt-graphs pattern.

## Epic's genAI posture

Model-agnostic interface (Claude/Gemini/Codex named); in-editor
diffusion tools "early 2027" (single source); Fab requires AI
disclosure + offers a NoAI tag; Sweeney is anti-labeling. Epic is NOT
building: token economics, cross-DCC orchestration, license hygiene,
verification layers, extraction — **TEE's differentiators are
unclaimed**; Epic's asset generation slots in as a future gated A14
backend.

## Distilled risk register

Version-gated toolset probing (catalog/schema hashes) parallel to the
Blender shim firewall; abstract TEE stable IDs so one contract maps to
an Actor refPath (UE5) OR a Scene Graph entity (UEFN/UE6) — prototype
against the UEFN Entity toolset NOW, it is the shipping UE6 preview;
keep TEE toolsets thin for a Verse-era port; favor the Verse-as-text
lane (cheaper per token than K2 graph machinery) over
Blueprint-specific investment. No Python-API deprecations in 5.8 (the
surface is expanding); legacy FBX removal never dated; 5.7→5.8 had no
hard breaks.
