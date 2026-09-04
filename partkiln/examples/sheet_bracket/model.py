"""The L-bracket, flat first.

Flat-first is the whole point: the blank, the bend lines and the bend table
are arithmetic (`partkiln.sheetmetal.flat`), so the shop can have the DXF
while OCP is still warming (Law 17). The folded solid is the opt-in B-rep,
and this example prints both so the two can be compared - the folded body is
9 576.206 mm3 and the flat blank 9 557.356 mm3, and the +18.850 mm3 between
them is the K-factor's entire volumetric effect, not an error.

K = 0.44 is partkiln's declared default inside the usual 0.3-0.5 band. No
standard fixes it: pass `k` or a bend table for a production part.
"""

from __future__ import annotations

from typing import Any

from partkiln.client import LocalKernel

PARAMS = {"T": "2mm", "W": "50mm", "L1": "60mm", "L2": "40mm", "R": "2mm", "A": "90deg"}

# One `create sheet`: thickness, width across the bends, and the flange chain
# (the base first). Flanges are NAMED f1, f2 ... - a hole cites `flange: "f1"`,
# never an index (Law 13).
SHEET_OP: dict[str, Any] = {
    "op": "create",
    "kind": "sheet",
    "name": "brk",
    "props": {
        "t": "T",
        "width": "W",
        "k": 0.44,
        "material": "steel_dc01",
        "flanges": [{"len": "L1"}, {"len": "L2", "angle": "A", "r": "R", "dir": "up"}],
        "holes": [
            {"flange": "f1", "at": [20, 25], "std": "M5 clearance normal"},
            {"flange": "f1", "at": [45, 25], "std": "M5 clearance normal"},
        ],
    },
}


def build() -> tuple[LocalKernel, dict[str, Any]]:
    kernel = LocalKernel()
    results = kernel.apply([{"op": "param_set", "props": dict(PARAMS)}, SHEET_OP])["results"]
    return kernel, results[1]


def bend_table(sheet: Any) -> list[dict[str, Any]]:
    """BA, OSSB, BD and the bend-zone volume for every bend, from the formulas.

    The sheet row carries only the totals; a shop wants the per-bend numbers,
    and they are the same three functions the kernel used - so the table is
    derived, never re-typed.
    """
    from partkiln.sheetmetal import flat as F

    rows = []
    for bend in sheet.flat.bends:
        rows.append(
            {
                "bend": bend.name,
                "angle_deg": round(bend.angle_deg, 3),
                "r_inner_mm": round(bend.r_inner, 3),
                "k": round(bend.k, 4),
                "dir": bend.direction,
                "length_mm": round(bend.length, 3),
                "ba_mm": round(F.bend_allowance(bend.angle_deg, bend.r_inner, bend.t, bend.k), 3),
                "ossb_mm": round(F.outside_setback(bend.angle_deg, bend.r_inner, bend.t), 3),
                "bd_mm": round(F.bend_deduction(bend.angle_deg, bend.r_inner, bend.t, bend.k), 3),
                "zone_mm3": round(
                    F.bend_zone_volume(bend.angle_deg, bend.r_inner, bend.t, bend.length), 3
                ),
            }
        )
    return rows
