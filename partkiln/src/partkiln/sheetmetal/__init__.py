"""Sheet metal, flat-first: the flat pattern is the model, the fold is derived.

A66 decision 4 in one sentence. `flat.py` holds the press brake's arithmetic
(bend allowance, outside setback, bend deduction, the flat length of a
chain) and writes the DXF/SVG a laser shop cuts from; `fold.py` derives the
folded solid from that same flat and owns the `Sheet` entity; `verbs.py`
puts both on the wire as `create sheet` and the `flat` kernel method.

Importing this package costs no OCP and no `partkiln.features`: the fold's
OCP imports all live inside functions, and every scalar a model reads back -
`t`, `k`, `bends`, `flat_mm`, `folded_bbox_mm`, `ba_total_mm`, `mass_g` - is
arithmetic that answers with no B-rep kernel installed. Importing
`partkiln.sheetmetal.verbs` is what registers the verb, and the document
does that lazily the first time a batch says `create sheet`.

The two numbers this lane is judged by (A66 P5b, fixture F7: T 2, R 2,
K 0.44, 90 deg, outside legs 50 and 30, W 40): BA 4.524 mm, flat 76.524 mm.
K = 0.44 is THIS kernel's declared choice inside the typical 0.3-0.5 range -
no standard fixes it; see `flat.py` for why, and for the DIN 6935 "k" that
is a different quantity entirely.
"""

from __future__ import annotations

from partkiln.sheetmetal.flat import (
    DEFAULT_K,
    DXF_INSUNITS_MM,
    DXF_LAYERS,
    FORMULA_SOURCE,
    K_NOTE,
    K_TYPICAL,
    Bend,
    Flange,
    Flat,
    Hole,
    bend_allowance,
    bend_deduction,
    bend_zone_volume,
    flat_length,
    flat_strip_volume,
    outside_setback,
)
from partkiln.sheetmetal.fold import (
    Sheet,
    flat_solid,
    folded_extents,
    folded_solid,
)

# Importing the verbs here is deliberate: `partkiln.methods` registers a
# placeholder `flat` for this phase that, when called, imports
# `partkiln.sheetmetal` and then looks for either a live `flat` in the kernel
# table or a module-level `flat_method`. Both are satisfied by this line and
# the alias under it, whichever module was imported first.
from partkiln.sheetmetal.verbs import _m_flat as flat_method

__all__ = [
    "DEFAULT_K",
    "DXF_INSUNITS_MM",
    "DXF_LAYERS",
    "FORMULA_SOURCE",
    "K_NOTE",
    "K_TYPICAL",
    "Bend",
    "Flange",
    "Flat",
    "Hole",
    "Sheet",
    "bend_allowance",
    "bend_deduction",
    "bend_zone_volume",
    "flat_length",
    "flat_method",
    "flat_solid",
    "flat_strip_volume",
    "folded_extents",
    "folded_solid",
    "outside_setback",
]
