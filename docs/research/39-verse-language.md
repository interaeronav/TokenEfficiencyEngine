# 39 — Verse language state (2026-08-22)

## Language design (what codegen must respect)

Deterministic functional-logic language: **failure is control flow** —
an expression can produce no value at all (not null, not an error), and
failure contexts are exactly `if` conditions, `for`/`first` domains, and
`<decides>` bodies. State mutation inside a failure context is
speculative: all-or-nothing commit. `and`/`or`/`not` are left-to-right
choice over failable alternatives.

**Effects (2026):** exclusive specifiers `<converges>` / `<computes>` /
`<transacts>` (the default; implies reads, writes, allocates); additive
`<reads>` `<writes>` `<allocates>` `<suspends>` `<decides>`
(suspends+decides cannot combine); effect subtyping (fewer effects =
subtype). **`<varies>` was removed in the v30.00 effects redesign
(Sept 2024)** — the canonical stale-training-data hallucination.
Book-only, UNVERIFIED as shipped: `dictates`, `<predicts>`.

**STM is core:** transactions roll back all effects on abort;
`GetSecondsSinceEpoch()` is stable within a transaction. C++ interop via
**AutoRTFM** (custom Clang fork; Fortnite servers since v28.10). A new
purpose-built Verse VM ("5x faster than our old VM", all C++-backed
functions transactional) was presented at REBASE/ICFP 2025 by Epic.

**Concurrency:** structured `sync`/`race`/`rush`/`branch` + unstructured
`spawn` → `task(t)` with `Await()`/`Cancel()`; cancellation is
cooperative at suspension points only. **Live variables (`var live` +
`await`/`upon`/`when`) are documented but NOT released** — mask them.

**Types:** types are first-class values; `where` parametric
polymorphism; `subtype`/`castable_subtype` metatypes; literal-only
refinements; arrays/tuples covariant, map keys contravariant; classes/
interfaces nominal, everything else structural; no implicit conversions.
Persistence: module-scoped `weak_map(player, t)` vars auto-persist;
custom types need `<persistable><final>`; persistable types are
effectively permanent schemas (publication-time compatibility
enforcement; open enums extensible post-publish, closed not).

Academic anchor: the Verse Calculus (ICFP 2023, Augustsson/Peyton
Jones/Sweeney et al.); no successor paper 2024–2026; SPJ's OPLSS'26
course "Types, Semantics, and Verification" signals unpublished
verification work in flight.

## Tooling reality (the automatability question)

**There is no public Verse compiler or CLI.** Sanctioned compile paths:
UEFN itself, the bundled VS Code LSP attached to a running UEFN
(`verse-lsp-latest.exe`, requires the UEFN-generated workspace —
headless repurposing UNVERIFIED/fragile), and now the UEFN MCP Verse
toolset. Internal CLI VMs exist (`VerseTestScriptCmdVM` /
`VerseCLRVM` in Epic's fortniteMain, post-UE6-reorg) but need internal
access. VerseLspCE (MIT + UE EULA) proves Verse is checkable outside
UEFN only by building UE source. Sweeney promised a permissively
licensed OSS compiler + spec "possibly as soon as 2025" (Jun 2024) —
**not shipped as of 2026-08**. The best public spec is
**verselang/book: CC0, 19 chapters, actively updated** — it tracks head
of development (ahead of shipped UEFN), so bundle it as the offline
language reference with unreleased features masked per target version.

## API surface & drift history

The authoritative API surface is the per-build read-only
`*.digest.verse` files (`Fortnite`, `UnrealEngine`, `Verse`, plus
per-project `Assets`) — plain Verse declarations, parseable. Module
paths are internet-domain style (`Fortnite.com/...`,
`UnrealEngine.com/Temporary/UI` — the UI module is literally namespaced
"Temporary" — `Verse.org/SceneGraph`). Version breaks worth a firewall
row each: 23.20 module hierarchy; **30.00 effects redesign**; 36.00
Scene Graph beta + new coordinate system; 41.00 skeletal-anim API;
41.10 Quest API + camera components; 42.00 MCP-in-UEFN +
`GetPassengers` → `GetOccupants` deprecation.

## LLM × Verse

Generic LLMs fail at Verse — documented in forums and acknowledged by
Epic staff. Hallucination classes: pre-23.20 module paths, pre-30.00
effect signatures (`<varies>`), renamed/removed members, invented
device methods absent from the digest. Epic's Developer Assistant is a
copilot (no editor mutation; backbone UNVERIFIED); its codegen model
was upgraded in v41.20. **No published quantitative evals of LLM Verse
generation exist anywhere** — all quality claims are anecdotal.

## Automatability verdict

Authoritative validation without UEFN in the loop: **no, today.** The
best offline approximation — and the one that kills the dominant
failure class — is **digest-grounded symbol/signature linting**: parse
the digests and verify every identifier, member, effect specifier and
`listenable` subscription the model emits, without claiming full
type/effect checking. When a live editor is present, compile through
the UEFN MCP Verse toolset. TEE therefore needs: a digest facts lane
pinned per ecosystem version + digest diffing; a validated template
corpus keyed to digest version; a compiler-error → one-line-fix map
(including the known stale-validation false-positive class); and the
CC0 book bundled for semantics grounding.
