# TEE KB — querying the Expert Knowledge Base

The `kb_*` tools give any TEE client sourced, budgeted answers from the
Expert Knowledge Base (38 domains, 401 files, ~1.4M words) without pasting
documents into context. The corpus is imported reference (decision A30):
every response carries the corpus's own `confidence` / `jurisdiction` /
`status` flags verbatim, and `needs-verification` or low-confidence content
arrives labelled, never bare.

## Activation

The module activates when a corpus root resolves, in this order:

1. `[kb] root` in the project's `.tee/config.toml` (absolute, `~`, or
   relative to the project root). An explicitly configured root is used
   even if broken, so a typo fails loud with the fix instead of the module
   quietly vanishing.
2. `<project>/knowledge-base/` when it holds a `manifest.json`.
3. The TEE source checkout's own `knowledge-base/` mirror.

With none of the three, the module stays inactive — no tools, no errors.

```toml
# .tee/config.toml
[kb]
root = "/path/to/TokenEfficiencyEngine/knowledge-base"
max_tokens = 800   # optional: default kb_read budget (cap 4000)
```

## OkongoSim wiring

OkongoSim already talks to TEE (pins, editor ops), so the KB lands with no
plugin change — one section in the same tracked `.tee/config.toml` that
carries the pin namespace:

```toml
[pins]
namespace = "tee_pin"

[kb]
root = "../TokenEfficiencyEngine/knowledge-base"  # adjust to the local clone
```

The in-repo mirror is the recommended root — stable, versioned, and drift
is a git event. The owner's Dropbox copy (`02 Okongo Oneleiwa Project/12
Expert Knowledge Base`) works as a fallback root; there, Dropbox sync can
move files under the index, which `kb_status` reports as drift.

## The four tools

All four are virtual tools (zero always-loaded tokens) — find them with
`tee_search_tools`, e.g. query "knowledge".

- `kb_status` — corpus totals, domain table, index freshness, and a drift
  report against the corpus's own `manifest.json`. `rebuild=true` re-reads
  the manifest and re-hashes the corpus.
- `kb_search` — keyword query plus exact filters (`domain`,
  `jurisdiction`, `confidence`, `status`). Hit lists only: id, title,
  domain, confidence, one-line summary. Default 8 rows, cap 20.
- `kb_read` — one file by id. Without `section`: the section list and the
  file's flags. With `section`: that section's text, token-budgeted
  (`max_tokens`, default 800, cap 4000), with the file's `## Sources`
  block riding along so the citation is never lost.
- `kb_facts` — the `## Key facts` blocks of matched files (query or ids):
  the metrics lane for cross-referencing real-world numbers.

Example session, driving OkongoSim:

```
kb_search {"query": "concrete block paving bedding sand", "jurisdiction": "southern-africa"}
kb_read   {"id": "paving.block_paving", "section": "Key facts"}
kb_facts  {"query": "cement lead time okongo logistics"}
```

## Rules that ride on every answer

- The corpus grounds nothing until re-checked against the source its
  frontmatter cites — the citation travels with the answer for exactly
  that purpose.
- The DCC-software domains (`13_*` Unreal, `14_*` Blender, `15_*` Fusion)
  are never an API source; `docs/research/` outranks them, always
  (CLAUDE.md rule).
- TEE never writes into the corpus. Index cache lives under
  `<project>/.tee/kb/`; the corpus regenerates itself with its own
  `00_meta/rebuild.py`.

## Doctor

`tee doctor` includes a `kb` check: root resolution, manifest readability,
and the drift count, each with its one-line fix.
