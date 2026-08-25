# Expert Knowledge Base

A 38-domain, ~401-file, ~1.4M-word reference library covering the Okongo
Oneleiwa house-building project (Ohangwena Region, Namibia) and adjacent
technical fields, plus a set of broader personal-interest domains the
owner chose to bring into this repository alongside it.

## What this is, and what it is not

This corpus is **imported reference material**, mirrored verbatim from
the owner's private Dropbox knowledge base into this repository by owner
decision (2026-08-25). It is distinct from `docs/research/`:

- `docs/research/` is TEE's own build-grounding corpus — deep-research
  passes run by this project's own agents, verified against primary
  sources at the time TEE was designed, cited per finding, and written
  specifically to justify TEE's engineering decisions (see
  `docs/DECISIONS.md`).
- `knowledge-base/` is **pre-authored elsewhere**, following its own
  schema (`00_meta/SCHEMA.md`) and its own verification discipline
  (`00_meta/VERIFICATION.md`, `00_meta/source-register.md` — 1,811 cited
  sources across the corpus). TEE did not author or re-verify it; it is
  mirrored faithfully, frontmatter and all.

Only a narrow, explicitly-wired subset of this corpus feeds TEE's actual
tool behavior today — see "What TEE actually consumes" below. The rest
is static reference text: browsable, citable, and available to any
session working on TEE or on the Okongo project, but not read by any
TEE tool at runtime unless stated otherwise.

## Scope

Not all 38 domains are about building or 3D tooling. Roughly a third are
directly on-topic for TEE and the Okongo build (codes/standards,
Namibia context, materials, construction trades, the three DCC
software domains, environmental-asset creation); the rest are
personal-interest domains (health, finance, aviation, medicine,
semiconductors, etc.) that the owner chose to keep alongside it rather
than exclude. See `INDEX.md` for the full domain table with file and
word counts, and each domain's `00_overview.md` for a one-page summary.

## What TEE actually consumes

- `03_codes_standards` (SANS 10400 parts register, Namibia building
  regulations) feeds the Namibia/South Africa jurisdiction defaults in
  `server/src/tee/physical/` — the gap tracked since Phase 11 as
  "SANS 10400 has not been added for Okongo jurisdiction defaults." See
  `docs/DECISIONS.md` for the entry recording this wiring, and the
  jurisdiction source citation left in the plausibility rules file
  itself.
- Everything else is reference-only for now. Wiring more of it into
  TEE's tools (materials data into `server/src/tee/assets/materials.py`,
  the Namibia context into site/climate defaults, the DCC-software
  domains into `docs/research/` grounding) is future work, tracked as
  such rather than promised.

## Provenance

Source: `/02 Okongo Oneleiwa Project/12 Expert Knowledge Base/` in the
owner's Dropbox, generated 2026-08-25 (per `INDEX.md`'s own
timestamp). Mirrored into this repository the same day. Every file
carries its original YAML frontmatter (`id`, `sources`, `confidence`,
`jurisdiction`, `status`) — treat `confidence: low` or
`status: needs-verification` markers as exactly that: unresolved,
not settled fact.
