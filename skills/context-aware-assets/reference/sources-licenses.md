# Source and license matrix

Authoritative gate: CC0-1.0, CC-BY-4.0/3.0 always; CC-BY-SA-* only when
the project set `[assets] allow_sa = true`; NC/ND/GPL/unknown NEVER cache
(fail-closed, no override). `as_sources()` shows what is enabled live.

| backend | assets | site ToS notes | needs |
|---|---|---|---|
| polyhaven | all CC0-1.0 | unique User-Agent; "Powered by Poly Haven" credit in docs | nothing |
| ambientcg | all CC0-1.0 | cache-first courtesy (one-person project) | nothing |
| polypizza | per-asset CC0/CC-BY | rate limits | TEE_POLYPIZZA_KEY |
| smithsonian | CC0-flagged records only | api.data.gov limits | TEE_SMITHSONIAN_KEY |
| sketchfab | per-model, incl. NC/ND (gated) | 300 s URL expiry; attribution display rules; volatile ownership (KitBash 2026-08) | `[assets] sketchfab=true` + token |
| local | user's own files | — | `as_ingest` |

Excluded by decision (do not request): Fab/Megascans (no API),
ShareTextures (ToS bans automation), OpenGameArt (GPL contamination),
Objaverse (provenance), BlenderKit API (needs written permission).

Attribution is automatic: every cached asset carries a TASL+SPDX manifest
with the license text snapshotted at download time; `as_credits()`
renders CREDITS.md (required credits vs courtesy CC0 credits). Run it
before any delivery.

Generated assets (as_generate) additionally carry `ai_generated`
provenance: pure AI output is not copyrightable in the US (USCO 2025);
set-dressing quality only — hero assets are curated, not generated.
Generated-3D is hosted-only (tripo/meshy, keyed, behind the usual cost
confirmation); prefer the curated library sources and the procedural
lane before reaching for generation.
