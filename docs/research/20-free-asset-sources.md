# 20 — Free asset sources, APIs, licensing (2026-08-22)

Programmatic 3D-asset/texture/HDRI sources for an automated agent. Verified
against live APIs and license/ToS pages; full per-source table in the
research transcript. TEE will cache files and emit attribution manifests,
so *asset license* and *site/API ToS* are tracked as SEPARATE fields.

## Tier-1 backends (in order)

1. **Poly Haven** — no-auth JSON API (`api.polyhaven.com`), 100% CC0,
   direct CDN URLs + MD5 hashes (cache keys), all three classes (989
   HDRIs / 851 textures / 521 models counted live), formats: blend, glTF,
   FBX, USD, EXR/HDR, full PBR sets; `/info` carries real-world
   `dimensions` (mm). Obligations: unique User-Agent + visible "Powered by
   Poly Haven" credit. Best tokens-per-asset economics.
2. **ambientCG** — no-auth `api/v2/full_json`, 100% CC0, richest PBR
   material catalog, real-world coverage in cm, zip variants 1K-8K.
   One-person project → cache-first, degrade gracefully; use
   `downloadLink` (stats) not `rawLink`.
3. **Poly Pizza** — API key, GLB-native low-poly aggregate (Google Poly
   archive + Kenney + Quaternius, ~10k), per-asset license fields
   (CC0/CC-BY filterable). Commercial API pricing UNVERIFIED — confirm.
4. **Smithsonian Open Access** — api.data.gov key, CC0 subset (~3k museum
   scans, heavy meshes), government-stable.
5. **Sketchfab (guarded, opt-in)** — Data API v3 + Download API, >1M
   downloadable, per-model license objects, GLB/glTF/USDZ only. OAuth
   per-user; 300 s URL expiry (cache the FILE, never the URL); strict
   attribution must travel with redistributed content. PLATFORM RISK:
   KitBash acquired Sketchfab + ArtStation from Epic 2026-08-10.

Tier-2: BlenderKit (mixed CC0/royalty-free; third-party API use not
sanctioned — needs written OK), Kenney/NASA via one-time local mirror
(CC0/PD). **Excluded**: Fab/Megascans (no public API; free-claim ended Dec
2024; automation = ToS gray zone), ShareTextures ("CC0" assets but ToS
bans automated downloads/addon embedding), OpenGameArt (no API + GPL
contamination), Objaverse/-XL (NC contamination + provenance disputes —
research corpus only).

## Traps (register-enforced)

- Site-level "CC0" ≠ pipeline access: check ToS separately per backend.
- Per-asset license mixing: map to SPDX; **allowlist** CC0-1.0,
  CC-BY-4.0/3.0 (CC-BY-SA-* behind a flag); fail CLOSED on NC/ND/unknown/
  "Standard"/GPL.
- Snapshot license text + URL AT DOWNLOAD TIME (platform churn: Megascans
  window closed, Sketchfab two owners in two years, BlenderKit mid-rebrand).
- Prefer first-party APIs over mirrors (Objaverse laundering lesson).
- Attribution survives redistribution: manifest travels with the cache and
  any export, not shown once at download.

## Attribution manifest (CC-BY 4.0 TASL-compliant)

Per cached asset: asset_id, title, author+profile URL, source_url
(canonical page, not CDN), source_backend, license_spdx, license_url,
license_verbatim, retrieved_at, file_hash, modifications, pre-rendered
credit_line. Emit JSON + a CREDITS.md renderer (BY lines mandatory, CC0
optional). Track (not build on): AssetFetch spec v0.4 — ambientCG runs the
only live endpoint.
