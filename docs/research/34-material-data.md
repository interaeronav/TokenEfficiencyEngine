# 34 — Material property data: sources, licenses, schema (2026-08-22)

## License-clean backbone (bulk-encodable)

CC0: **physicallybased.info** (86 materials, all with density — a
physics seed, not just render values), **refractiveindex.info**
(spectral n/k, explicit commercial OK), **RGL-EPFL measured BRDFs**
(prefer over MERL), **Wikidata** structured statements. CC-BY:
Materials Project (low relevance — DFT crystals). MERL 100: only via
the 2023 Zenodo CC-BY-SA release → copyleft quarantine or skip.

## Traps

NIST general = public domain, BUT **NIST SRD is copyright-protected by
statute (15 USC 290e)** — no bulk encoding. MatWeb: look-up-only (sells
DB licenses; ToS bot-blocked, treat restrictive). MakeItFrom /
Engineering ToolBox: all-rights-reserved, cite-only. **ArcSim measured
cloth: non-profit-only — cannot ship**; workaround: encode fabric GSM
ranges as cited facts, solver stiffness stays game_plausible tier.
Eurocode NUMERIC characteristic values are facts — encodable with
clause citations (the standard texts are copyrighted). EU sui-generis
database right bars bulk extraction from EU-protected databases.

## Okongo engineering ranges (cited into reference tables)

Concrete C20/25-C30/37 per EN 1992-1-1 Table 3.1 (fck/fcm/fctm/Ecm;
ρ 2500 kg/m³ per EN 1991-1-1); timber C16/C24 per EN 338 (fm,k 16/24
MPa, E 8/11 GPa, ρk 310/350); steel S235/S355 (E 210 GPa, ρ 7850);
glass ρ 2500 / E ≈ 70 GPa; masonry as typical_range; thermal via
CIBSE A3 / BR 443 (brick 0.77 W/m·K, softwood 0.13).

## The mapping problem (engineering value → solver parameter)

Blender rigid-body Friction is NOT a Coulomb coefficient and **Bullet
combines contact friction MULTIPLICATIVELY** (0.5 × 0.5 = 0.25) →
per-body √μ note when physical behavior is wanted; Calculate Mass =
volume × density is honest. UE UPhysicalMaterial: density in g/cm³,
combine modes, raise_mass_to_power = explicit non-physical fudge.
**UsdPhysicsMaterialAPI is the clean vocabulary** (Coulomb semantics,
kg/m³); glTF KHR_physics_rigid_bodies draft mirrors it.

## Schema (A20)

Three tiers per material fact — render / physics / engineering — every
leaf value carrying source + license + as_of + honesty label:
`measured | standard_value (characteristic, conservative) |
typical_range | derived | game_plausible`, with per-engine caveats in
notes. SimReady requires properties but records NO provenance — TEE's
schema exceeds the state of the art; no existing open library couples
all three tiers.
