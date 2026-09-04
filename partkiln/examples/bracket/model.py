"""The bracket itself: nine commands, one batch, one round trip.

This is worked example W1 of the A66 script with ONE deliberate change: the
chamfer runs BEFORE the slot is cut, not after. `plate:edges(of=end,
loop=outer)` picks up the slot's own top edges once the slot exists, and a
1 mm chamfer across a 4 mm slot fillet is not a chamfer OCCT will build - it
refuses `chamfer d=1.0 failed on 10 edge(s)`, correctly. Chamfering the outer
loop first resolves to the 8 edges the example means (4 straight + 4 fillet
arcs) and the whole batch lands.
"""

from __future__ import annotations

from typing import Any

from partkiln.client import LocalKernel

# Every length is a parameter or an expression over one, so `pk_script` with
# overrides is a part family and `param_set W=140mm` is a one-line edit.
PARAMS = {"W": "120mm", "H": "80mm", "T": "10mm", "PX": "100mm", "PY": "50mm"}

OPS: list[dict[str, Any]] = [
    {"op": "param_set", "props": dict(PARAMS)},
    {"op": "create", "kind": "part", "name": "bracket", "props": {"material": "steel_s275"}},
    {
        "op": "create",
        "kind": "sketch",
        "name": "base",
        "props": {"plane": "XY", "profile": [{"rect": ["W", "H"], "tag": "outer"}]},
    },
    {
        "op": "create",
        "kind": "extrude",
        "name": "plate",
        "props": {"sketch": "base", "distance": "T"},
    },
    {
        "op": "create",
        "kind": "fillet",
        "name": "f1",
        "props": {"edges": "plate:edges(dir=Z)", "r": "5mm"},
    },
    {
        "op": "create",
        "kind": "hole",
        "name": "h",
        # The frame is the face's own: origin = the world origin projected
        # onto plate.end, x along world X. So the pattern is written from the
        # corner, not from the centre, and stays parametric in W/H/PX/PY.
        "props": {
            "on": "plate.end",
            "at": [
                ["(W-PX)/2", "(H-PY)/2"],
                ["(W+PX)/2", "(H-PY)/2"],
                ["(W-PX)/2", "(H+PY)/2"],
                ["(W+PX)/2", "(H+PY)/2"],
            ],
            "std": "M6 clearance normal",
        },
    },
    {
        "op": "create",
        "kind": "chamfer",
        "name": "c1",
        "props": {"edges": "plate:edges(of=end, loop=outer)", "d": "1mm"},
    },
    {
        "op": "create",
        "kind": "sketch",
        "name": "slot_sk",
        "props": {
            "plane": "on:plate.end",
            "profile": [{"slot": [40, 8], "at": ["W/2", "H/2"], "tag": "slot"}],
        },
    },
    {
        "op": "create",
        "kind": "extrude",
        "name": "slot",
        "props": {"sketch": "slot_sk", "distance": "through", "mode": "cut"},
    },
]


def build() -> tuple[LocalKernel, list[dict[str, Any]]]:
    """Apply the batch. A refusal rolls the whole document back (Law 16)."""
    kernel = LocalKernel()
    return kernel, kernel.apply(OPS)["results"]


def feature_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The rows a diff would carry: id, delta, faces, and what a selector caught."""
    rows = []
    for row in results:
        if not str(row.get("id", "")).startswith("feat:"):
            continue
        rows.append(
            {
                "id": row["id"],
                "kind": row.get("kind"),
                "delta_mm3": row.get("delta_mm3"),
                "volume_mm3": row.get("volume_mm3"),
                "faces": row.get("faces"),
                "resolved": row.get("resolved") or {},
            }
        )
    return rows
