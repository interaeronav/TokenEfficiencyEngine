"""The two parts and the assembly that holds them.

A stepped shaft (one revolve of a six-point profile about X) and a housing
(one extrude of a square along X, one bore through it). Both are parametric
in the same seven parameters, so `D_B` is the fit and nothing else has to
move when it changes.

The refs the mates use are NAMES, never indices (Law 13): the journal is
`body.p.1` because it is the revolved image of the profile's second line,
and it stays `body.p.1` when the collar grows. `pk_query` with
`body:faces(type=cylinder)` is how you find that out without guessing.
"""

from __future__ import annotations

from typing import Any

from partkiln.client import LocalKernel

PARAMS = {
    "D_J": "20mm",  # journal diameter - what runs in the bore
    "D_C": "30mm",  # collar diameter
    "L_J": "60mm",  # journal length
    "L_C": "20mm",  # collar length
    "D_B": "20.2mm",  # bore diameter: the fit, and the only number that sets it
    "BOX": "60mm",  # housing section
    "DEPTH": "30mm",  # housing depth along the bore axis
}

PART_OPS: list[dict[str, Any]] = [
    {"op": "param_set", "props": dict(PARAMS)},
    {"op": "create", "kind": "part", "name": "housing", "props": {"material": "steel_s275"}},
    {
        "op": "create",
        "kind": "sketch",
        "name": "hsk",
        "props": {"plane": "YZ", "profile": [{"rect": ["BOX", "BOX"], "tag": "outer"}]},
    },
    {
        "op": "create",
        "kind": "extrude",
        "name": "case",
        "props": {"sketch": "hsk", "distance": "DEPTH"},
    },
    {
        "op": "create",
        "kind": "hole",
        "name": "bore",
        "props": {"on": "case.end", "at": [["BOX/2", "BOX/2"]], "dia": "D_B"},
    },
    {"op": "create", "kind": "part", "name": "shaft", "props": {"material": "steel_s275"}},
    {
        "op": "create",
        "kind": "sketch",
        "name": "prof",
        "props": {
            "plane": "XZ",
            "profile": [
                {
                    "poly": [
                        [0, 0],
                        [0, "D_J/2"],
                        ["L_J", "D_J/2"],
                        ["L_J", "D_C/2"],
                        ["L_J+L_C", "D_C/2"],
                        ["L_J+L_C", 0],
                    ],
                    "tag": "p",
                }
            ],
        },
    },
    {
        "op": "create",
        "kind": "revolve",
        "name": "body",
        "props": {"sketch": "prof", "axis": "X", "part": "shaft"},
    },
]

# The bore wall and the journal wall, by name. Both mates use the same pair:
# the insert states the design intent, the joint gives the motion a value.
BORE = "housing.bore.1.wall"
JOURNAL = "shaft.body.p.1"

# Deliberately placed WRONG (15 mm short of the bore, but on its axis) so the
# insert mate has something to solve. The solved pose is the answer.
ASM_OPS: list[dict[str, Any]] = [
    {"op": "create", "kind": "component", "props": {"part": "housing"}},
    {"op": "create", "kind": "component", "props": {"part": "shaft", "at": [-15, 30, 30]}},
    {
        "op": "create",
        "kind": "mate",
        "name": "ins",
        "props": {"type": "insert", "a": BORE, "b": JOURNAL},
    },
    {"op": "create", "kind": "revolute", "name": "j1", "props": {"a": BORE, "b": JOURNAL}},
]


def build_parts() -> tuple[LocalKernel, list[dict[str, Any]]]:
    kernel = LocalKernel()
    return kernel, kernel.apply(PART_OPS)["results"]
