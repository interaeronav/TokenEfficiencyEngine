# `drafting` — a standards critic for technical drawings

Two tiers, because "conforming" and "readable" are different properties:

| Tier | Reads | Catches |
|---|---|---|
| **1 — conformance** (`critic.py`) | the **specification** | text below 2,5 mm, a light border, an invented scale, a missing north point, an orphan section, an empty title block |
| **2 — legibility** (`legibility.py`) | the **plotted sheet** | text on text, a cut line through a room name, a panel over a note, anything outside the frame |

Tier 1 is pure stdlib. Tier 2 needs matplotlib, because it measures artists
that only exist once the figure has been drawn.

```python
from drafting.critic import critique
from drafting import loop

report = critique(drawing_set)          # what is wrong
result = loop.run(drawing_set, ...)     # fix it, then check again, until fixed point
```

## Why the critic reads a spec and not a PDF

A finding has to be actionable. `critique` names a field; the corrector edits
that field; the sheet is drawn again from the corrected data. Critiquing a
rendered PDF would let you *see* a fault and leave you no handle to fix it.

Tier 2 exists because that argument has a limit: collisions are a property of
the plot, not of the data, and a sheet can satisfy every numeric rule while a
section line runs through a room name.

## Provenance — read this before trusting a number

The rules come from TEE's Knowledge Base entry `arch.drawing_documentation`
(`confidence: medium`, `jurisdiction: southern-africa`), which cites **SANS
10143 Building drawing practice** through public transcriptions. **They have
not been checked against the purchased SANS text.** Every rule therefore
carries a `firmness`:

- `sans10143` — the KB attributes it to SANS 10143 and the value is specific
- `convention` — ordinary practice the KB states without attribution
- `house` — this module's own choice, declared as such

Nothing here is presented as a quotation from a standard nobody has read. Use
it as a drafting assistant; do not cite it to a building authority.

## Two things it will not do

**It will not invent a value a human owns.** An unset checker's initials print
as `— NOT SET —` in red. A drawing that looks signed off and is not is worse
than one that visibly is not.

**It will not silently improve anything.** Every edit comes back as a finding
marked `autofixed`, so the whole list of changes made on your behalf is
readable in one place.
