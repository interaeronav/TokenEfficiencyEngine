"""Constrained 2D sketches: the model, its scipy solver, and the profile presets.

Pure Python + numpy/scipy. `profile.py` (P2) is the only module in this
package that will touch OCCT, and it is not here yet.
"""

from __future__ import annotations

from partkiln.sketch.model import (
    CONSTRAINT_KINDS,
    DIM_KINDS,
    PLANES,
    Arc,
    Circle,
    Constraint,
    Dimension,
    Entity,
    Line,
    Point,
    Sketch,
)
from partkiln.sketch.presets import PRESETS, Expansion, expand
from partkiln.sketch.solver import SolveReport, solve

__all__ = [
    "CONSTRAINT_KINDS",
    "DIM_KINDS",
    "PLANES",
    "PRESETS",
    "Arc",
    "Circle",
    "Constraint",
    "Dimension",
    "Entity",
    "Expansion",
    "Line",
    "Point",
    "Sketch",
    "SolveReport",
    "expand",
    "solve",
]
