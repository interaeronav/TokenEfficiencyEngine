---
id: meta.schema
title: File and Frontmatter Schema
domain: meta
tags: [schema, conventions, retrieval]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources: []
---

# Schema for this knowledge base

Every content file is UTF-8 Markdown with a YAML frontmatter block delimited by `---`.

## Required frontmatter keys

| Key | Type | Notes |
|---|---|---|
| `id` | string | Dotted, lowercase, unique. `<domain>.<topic>[.<subtopic>]` e.g. `codes.sa.sans10400.part_k` |
| `title` | string | Human title, sentence case |
| `domain` | string | One of the 16 top-level folder slugs |
| `tags` | list[string] | Lowercase, hyphenated, retrieval keywords |
| `jurisdiction` | string | `global`, `namibia`, `south-africa`, `southern-africa`, `eu`, `us`, `uk` |
| `status` | string | `stable`, `draft`, `needs-verification` |
| `confidence` | string | `high`, `medium`, `low` — how strongly the content is source-backed |
| `updated` | date | ISO `YYYY-MM-DD` |
| `sources` | list | Each item: `{title, url, publisher, accessed}` |

## Optional keys

`supersedes`, `related` (list of `id`s), `paywalled` (bool), `licence`, `applies_to`, `unit_system`.

## Body conventions

1. Open with a `# Title` H1 matching `title`.
2. Follow with a **Summary** paragraph of 2–5 sentences — this is what a retrieval system will surface first.
3. Use `## Key facts` early with a bullet list or table of hard numbers, dimensions, clause numbers, prices.
4. Mark every jurisdiction-specific requirement inline with `**[NA]**` (Namibia) or `**[ZA]**` (South Africa).
5. Use `> ⚠️` callouts for safety-critical or legally binding items.
6. Close with `## Sources` listing markdown links, and `## Open questions` where verification is still needed.
7. Never invent clause numbers, prices, standard numbers or dates. If unverified, mark `needs-verification` and say so.
8. Prefer SI units. Give currency as `N$` (Namibian dollar) or `R` (rand) with the date of the quote.

## Naming

Files are `NN_kebab-case-title.md`, numbered in reading order within their folder. `00_overview.md` is always the folder's entry point.
