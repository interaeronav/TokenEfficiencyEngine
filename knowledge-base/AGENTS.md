---
id: meta.agents
title: Agent guide
domain: 00_meta
tags: [agents, usage, retrieval, prompting, citation]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources: []
---

# Agent guide

Instructions for any AI model or coding agent using this repository. Read this before answering a question from the corpus. This file doubles as `CLAUDE.md` — the same guidance applies.

## What this repository is

A curated, source-backed reference corpus of ~1.33 million words across 38 domains. It is a **knowledge source, not a decision authority**. It tells you what is known, how strongly it is known, and where to check.

## How to answer a question from it

1. **Identify the domain.** Match the question to one of the 38 domain folders. `manifest.json` carries every file's `id`, `title`, `tags`, `jurisdiction` and a summary — grep or load it rather than walking the tree.
2. **Read `00_overview.md` in the domain first.** Every domain has one, and it maps the rest of the folder.
3. **Read the specific file.** Files are numbered in reading order. `## Key facts` near the top carries the hard numbers.
4. **Check the flags before you commit to an answer.**
   - `confidence: high` — usable as stated.
   - `confidence: medium` — usable for orientation; verify before acting on it.
   - `confidence: low` or `status: needs-verification` — **do not present as fact.** Say what the file says and that it is unconfirmed.
   - Read the file's `## Open questions` section. It is there for you.
5. **Respect the jurisdiction markers.** `**[NA]**` is Namibia-only, `**[ZA]**` is South Africa-only. Do not carry a South African requirement into a Namibian answer, or the reverse — the two regimes differ in ways that matter (see `03_codes_standards/04_namibia-building-regulations.md`).
6. **Cite.** Every file has a `## Sources` block with real URLs. Pass the source through to the user rather than presenting corpus content as your own knowledge.

## The three things this corpus is systematically weak on

Assume these are unverified wherever they appear, in every domain:

- **Prices, rates and costs.** Southern African price lists are not publicly retrievable. Treat every figure as illustrative and say so.
- **Paywalled standards text.** SANS clause values in particular. The corpus reliably tells you *which standard and which clause* governs a question — that is its real value — but a specific deemed-to-satisfy number may be unconfirmed.
- **Labour output rates and waste factors.** Trade convention, not data.

## Frontmatter you can filter on

```yaml
id:            # dotted unique key, e.g. codes.sa.sans10400.part_k
domain:        # one of the 38 folder slugs
tags:          # lowercase hyphenated retrieval keywords
jurisdiction:  # global | namibia | south-africa | southern-africa | eu | us | uk
status:        # stable | draft | needs-verification
confidence:    # high | medium | low
updated:       # ISO date
sources:       # list of {title, url, publisher, accessed}
```

## Cross-domain routing

Questions frequently span domains. Common routes:

| Question is about | Read |
|---|---|
| A wall on the Okongo site | `16_walls_and_boundaries` → `03_codes_standards` → `18_namibia_context` → `07_materials_and_suppliers` |
| Paving specification and pricing | `17_paving_and_roads` → `11_logistics_remote_areas` (landed cost) |
| Kitchen or wardrobe joinery | `06_joinery_and_woodwork` → `20_furnishing_industry` → `19_interior_design` |
| Whether something is legal to build | `03_codes_standards` first, always, and check the jurisdiction |
| Water on site | `24_hydrology_arid` → `18_namibia_context` → `02_building_construction/09` |
| Visualising the building | `25_environmental_asset_creation` → `13`/`14`/`15` for the specific application |
| Site or terrain mapping | `23_cartography_and_mapping` → `18_namibia_context` |
| Climate-driven design decisions | `18_namibia_context/02` and `/09` → `01_architecture/05` |
| Hiring or paying anyone | `12_hr_construction`, and note the NA/ZA split |

## Writing new files into this corpus

Follow `00_meta/SCHEMA.md` exactly. Then:

- Research before writing. Fetch the source; do not write from memory and cite from memory.
- If you cannot verify a number, say so in the body and set `confidence` accordingly. A named gap is worth more than a plausible invention — a downstream agent can close a named gap and cannot detect an invention.
- Add a `## Sources` block with URLs you actually retrieved, and an `## Open questions` block naming what you could not confirm.
- Run `00_meta/validate.py` then `00_meta/rebuild.py` to regenerate `INDEX.md`, `manifest.json`, the source register and the verification register.

## What not to do

- Do not present a `needs-verification` figure as settled fact.
- Do not blend Namibian and South African regulatory requirements.
- Do not treat vendor marketing claims in the corpus as independent evidence — they are labelled as claims where they appear.
- Do not use `34_medical_field` or `35_health_and_fitness` to give personalised clinical or dietary advice. They document how the professions train and what the evidence says.
- Do not use `33_social_engineering_defence` as an attack reference. It is written as a defensive and awareness resource and should be used as one.
